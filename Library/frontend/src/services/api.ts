/** API client. Uses same-origin cookies for auth and echoes the CSRF token
 * (double-submit) on state-changing requests. */

export interface UserPublic {
  id: string;
  username: string;
  role: 'administrator' | 'librarian' | 'borrower';
}

export interface Me extends UserPublic {
  force_password_change: boolean;
}

export type Role = 'administrator' | 'librarian' | 'borrower';
export type UserStatus = 'active' | 'deactivated';

export interface UserAdminView {
  id: string;
  username: string;
  role: Role;
  status: UserStatus;
  force_password_change: boolean;
  created_at: string;
}

export interface PendingResetView {
  id: string;
  username: string;
  status: string;
  requested_at: string;
}

export interface IssuedTemporaryPassword {
  temporary_password: string;
  expires_at: string;
}

export interface LocationNode {
  id: string;
  name: string;
  type_label: string | null;
  parent_id: string | null;
  children: LocationNode[];
}

export interface LocationView {
  id: string;
  name: string;
  type_label: string | null;
  parent_id: string | null;
}

export type CopyStatus = 'available' | 'checked_out' | 'lost' | 'withdrawn';

export interface TitleView {
  id: string;
  name: string;
  author: string | null;
  isbn: string | null;
  media_type: string | null;
  copy_count: number;
}

export interface CopyView {
  id: string;
  barcode: string;
  location_id: string;
  location_path: string;
  status: CopyStatus;
  condition: string | null;
}

export interface TitleDetail {
  id: string;
  name: string;
  author: string | null;
  isbn: string | null;
  media_type: string | null;
  copies: CopyView[];
}

export interface BrowseItem {
  id: string;
  name: string;
  author: string | null;
  media_type: string | null;
  available_count: number;
  total_count: number;
}

export interface LoanView {
  id: string;
  copy_id: string;
  barcode: string;
  title_name: string;
  borrower_username: string;
  borrowed_at: string;
  due_at: string;
  renewal_count: number;
  overdue: boolean;
}

export interface ActivityView {
  action: string;
  reason: string | null;
  created_at: string;
}

export interface DashboardSummary {
  titles: number;
  copies: number;
  on_loan: number;
  available: number;
  overdue: number;
  active_borrowers: number;
  pending_resets: number;
  overdue_loans: LoanView[];
  recent_activity: ActivityView[];
}

export interface CreatedBorrower {
  id: string;
  username: string;
  role: Role;
  status: UserStatus;
  created_at: string;
  temporary_password: string | null;
}

export interface AuditEntry {
  id: string;
  action: string;
  actor: string | null;
  target: string | null;
  entity_type: string | null;
  entity_id: string | null;
  reason: string | null;
  detail: string | null;
  created_at: string;
}

export interface AuditQuery {
  action?: string;
  q?: string;
  start?: string;
  end?: string;
  limit?: number;
  offset?: number;
}

function readCookie(name: string): string | null {
  const match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
  return match ? decodeURIComponent(match[2]) : null;
}

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  const mutating = method !== 'GET' && method !== 'HEAD';
  if (mutating) {
    const csrf = readCookie('library_csrf');
    if (csrf) headers['X-CSRF-Token'] = csrf;
  }
  const resp = await fetch(`/api/v1${path}`, {
    method,
    headers,
    credentials: 'same-origin',
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (!resp.ok) {
    let detail = friendlyStatusMessage(resp.status);
    try {
      const data = await resp.json();
      detail = extractDetail(data?.detail) ?? detail;
    } catch {
      /* non-JSON body; keep the status-based message */
    }
    throw new ApiError(resp.status, detail);
  }
  if (resp.status === 204) return undefined as T;
  return (await resp.json()) as T;
}

function friendlyStatusMessage(status: number): string {
  if (status === 401) return 'Incorrect username or password.';
  if (status === 403) return 'You are not allowed to do that.';
  if (status === 409) return 'That value is already in use.';
  if (status === 429) return 'Too many attempts. Please wait a moment and try again.';
  if (status >= 500) return 'Something went wrong on our end. Please try again.';
  return 'Please check your input and try again.';
}

/** Normalize FastAPI/Pydantic error detail (string or validation array) into a
 * single human-readable message. */
function extractDetail(detail: unknown): string | null {
  if (!detail) return null;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) {
    const messages = detail
      .map((item) => (item && typeof item === 'object' && 'msg' in item ? String(item.msg) : null))
      .filter(Boolean) as string[];
    if (messages.length) return messages.join(' ');
  }
  return null;
}

export const api = {
  register: (username: string, password: string) =>
    request<UserPublic>('POST', '/auth/register', { username, password }),
  login: (username: string, password: string) =>
    request<Me>('POST', '/auth/login', { username, password }),
  logout: () => request<{ status: string }>('POST', '/auth/logout'),
  me: () => request<Me>('GET', '/auth/me'),

  // Administrator user management
  listUsers: () => request<UserAdminView[]>('GET', '/admin/users'),
  createUser: (username: string, password: string, role: Role) =>
    request<UserAdminView>('POST', '/admin/users', { username, password, role }),
  changeRole: (id: string, role: Role) =>
    request<UserAdminView>('PATCH', `/admin/users/${id}/role`, { role }),
  setStatus: (id: string, status: UserStatus) =>
    request<UserAdminView>('PATCH', `/admin/users/${id}/status`, { status }),

  // Password reset (email-free)
  requestReset: (username: string) =>
    request<{ status: string }>('POST', '/auth/reset-requests', { username }),
  loginTemporary: (username: string, temporary_password: string) =>
    request<Me>('POST', '/auth/login-temporary', { username, temporary_password }),
  changePassword: (new_password: string, current_password?: string) =>
    request<Me>('POST', '/auth/change-password', { new_password, current_password }),
  listResetRequests: () => request<PendingResetView[]>('GET', '/admin/reset-requests'),
  issueReset: (id: string) =>
    request<IssuedTemporaryPassword>('POST', `/admin/reset-requests/${id}/issue`),

  // Inventory locations (staff)
  listLocations: () => request<LocationNode[]>('GET', '/locations'),
  createLocation: (name: string, parentId: string | null, typeLabel: string | null) =>
    request<LocationView>('POST', '/locations', {
      name,
      parent_id: parentId,
      type_label: typeLabel,
    }),
  updateLocation: (id: string, body: { name?: string; type_label?: string | null }) =>
    request<LocationView>('PATCH', `/locations/${id}`, body),
  moveLocation: (id: string, newParentId: string | null) =>
    request<LocationView>('PATCH', `/locations/${id}/move`, { new_parent_id: newParentId }),
  deleteLocation: (id: string) => request<void>('DELETE', `/locations/${id}`),

  // Catalog (staff)
  listTitles: () => request<TitleView[]>('GET', '/titles'),
  createTitle: (body: { name: string; author?: string; isbn?: string; media_type?: string }) =>
    request<TitleView>('POST', '/titles', body),
  getTitle: (id: string) => request<TitleDetail>('GET', `/titles/${id}`),
  updateTitle: (
    id: string,
    body: {
      name?: string;
      author?: string | null;
      isbn?: string | null;
      media_type?: string | null;
    },
  ) => request<TitleView>('PATCH', `/titles/${id}`, body),
  deleteTitle: (id: string) => request<void>('DELETE', `/titles/${id}`),
  addCopy: (titleId: string, body: { location_id: string; barcode?: string; condition?: string }) =>
    request<CopyView>('POST', `/titles/${titleId}/copies`, body),
  updateCopy: (id: string, body: { location_id?: string; condition?: string }) =>
    request<CopyView>('PATCH', `/copies/${id}`, body),
  setCopyStatus: (id: string, status: CopyStatus) =>
    request<CopyView>('PATCH', `/copies/${id}/status`, { status }),
  deleteCopy: (id: string) => request<void>('DELETE', `/copies/${id}`),

  // Browse & search (any authenticated role)
  browse: (q?: string) =>
    request<BrowseItem[]>('GET', `/browse${q ? `?q=${encodeURIComponent(q)}` : ''}`),

  // Circulation (staff mutations + lists; /mine for any role)
  listLoans: (overdueOnly?: boolean) =>
    request<LoanView[]>('GET', `/loans${overdueOnly ? '?status_filter=overdue' : ''}`),
  myLoans: () => request<LoanView[]>('GET', '/loans/mine'),
  checkout: (barcode: string, borrowerUsername: string, loanPeriodDays: number) =>
    request<LoanView>('POST', '/loans', {
      barcode,
      borrower_username: borrowerUsername,
      loan_period_days: loanPeriodDays,
    }),
  returnLoan: (id: string) => request<LoanView>('POST', `/loans/${id}/return`),
  renewLoan: (id: string, days: number) => request<LoanView>('POST', `/loans/${id}/renew`, { days }),

  // Dashboard (staff)
  dashboardSummary: () => request<DashboardSummary>('GET', '/dashboard/summary'),

  // Borrower quick-create (staff) — from the circulation desk
  createBorrower: (username: string, password?: string) =>
    request<CreatedBorrower>('POST', '/borrowers', {
      username,
      password: password && password.length ? password : null,
    }),

  // Audit trail (staff, read-only)
  auditActions: () => request<string[]>('GET', '/audit/actions'),
  listAudit: (query: AuditQuery = {}) => {
    const params = new URLSearchParams();
    if (query.action) params.set('action', query.action);
    if (query.q) params.set('q', query.q);
    if (query.start) params.set('start', query.start);
    if (query.end) params.set('end', query.end);
    if (query.limit != null) params.set('limit', String(query.limit));
    if (query.offset != null) params.set('offset', String(query.offset));
    const qs = params.toString();
    return request<AuditEntry[]>('GET', `/audit${qs ? `?${qs}` : ''}`);
  },
};
