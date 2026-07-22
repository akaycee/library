import { useEffect, useState, type FormEvent } from 'react';
import {
  Alert,
  Box,
  Button,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  MenuItem,
  Paper,
  Select,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from '@mui/material';
import PersonAddIcon from '@mui/icons-material/PersonAdd';
import AppLayout from '../components/AppLayout';
import { api, ApiError, type Role, type UserAdminView } from '../services/api';

const ROLES: Role[] = ['administrator', 'librarian', 'borrower'];

export default function Users() {
  const [users, setUsers] = useState<UserAdminView[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);

  // Create-user form state
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState<Role>('librarian');
  const [submitting, setSubmitting] = useState(false);

  async function refresh() {
    try {
      setUsers(await api.listUsers());
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Unable to load users.');
    }
  }

  useEffect(() => {
    refresh();
  }, []);

  async function onCreate(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setNotice(null);
    setSubmitting(true);
    try {
      await api.createUser(username, password, role);
      setNotice(`Created ${username}.`);
      setDialogOpen(false);
      setUsername('');
      setPassword('');
      setRole('librarian');
      await refresh();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Could not create the user.');
    } finally {
      setSubmitting(false);
    }
  }

  async function onRoleChange(id: string, newRole: Role) {
    setError(null);
    setNotice(null);
    try {
      await api.changeRole(id, newRole);
      await refresh();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Could not change the role.');
    }
  }

  async function onToggleStatus(u: UserAdminView) {
    setError(null);
    setNotice(null);
    try {
      await api.setStatus(u.id, u.status === 'active' ? 'deactivated' : 'active');
      await refresh();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Could not update the status.');
    }
  }

  return (
    <AppLayout>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
        <Typography variant="h5" component="h1" sx={{ flexGrow: 1 }}>
          User management
        </Typography>
        <Button variant="contained" startIcon={<PersonAddIcon />} onClick={() => setDialogOpen(true)}>
          Add user
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} role="alert">
          {error}
        </Alert>
      )}
      {notice && (
        <Alert severity="success" sx={{ mb: 2 }}>
          {notice}
        </Alert>
      )}

      <Paper elevation={0} sx={{ border: '1px solid #e6e9f0' }}>
        <Table aria-label="Users">
          <TableHead>
            <TableRow>
              <TableCell>Username</TableCell>
              <TableCell>Role</TableCell>
              <TableCell>Status</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {users.map((u) => (
              <TableRow key={u.id} hover>
                <TableCell>{u.username}</TableCell>
                <TableCell>
                  <Select
                    size="small"
                    value={u.role}
                    onChange={(e) => onRoleChange(u.id, e.target.value as Role)}
                    aria-label={`Role for ${u.username}`}
                  >
                    {ROLES.map((r) => (
                      <MenuItem key={r} value={r}>
                        {r}
                      </MenuItem>
                    ))}
                  </Select>
                </TableCell>
                <TableCell>
                  <Chip
                    label={u.status}
                    color={u.status === 'active' ? 'success' : 'default'}
                    size="small"
                  />
                </TableCell>
                <TableCell align="right">
                  <Button size="small" onClick={() => onToggleStatus(u)}>
                    {u.status === 'active' ? 'Deactivate' : 'Reactivate'}
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Paper>

      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)}>
        <DialogTitle>Add user</DialogTitle>
        <Box component="form" onSubmit={onCreate}>
          <DialogContent>
            <TextField
              label="Username"
              fullWidth
              required
              margin="normal"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              autoComplete="off"
            />
            <TextField
              label="Temporary password"
              type="password"
              fullWidth
              required
              margin="normal"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              helperText="At least 8 characters, including a letter and a number. The user must change it on first login."
              autoComplete="new-password"
            />
            <Select
              fullWidth
              value={role}
              onChange={(e) => setRole(e.target.value as Role)}
              sx={{ mt: 2 }}
              aria-label="Role"
            >
              {ROLES.map((r) => (
                <MenuItem key={r} value={r}>
                  {r}
                </MenuItem>
              ))}
            </Select>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setDialogOpen(false)}>Cancel</Button>
            <Button type="submit" variant="contained" disabled={submitting}>
              {submitting ? 'Creating…' : 'Create'}
            </Button>
          </DialogActions>
        </Box>
      </Dialog>
    </AppLayout>
  );
}
