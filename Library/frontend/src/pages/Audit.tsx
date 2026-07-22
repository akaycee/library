import { useCallback, useEffect, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Chip,
  FormControl,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from '@mui/material';
import AppLayout from '../components/AppLayout';
import { api, ApiError, type AuditEntry } from '../services/api';

const PAGE_SIZE = 50;

/** Render the JSON `detail` field into a short, human-readable summary. */
function formatDetail(detail: string | null): string {
  if (!detail) return '';
  try {
    const parsed = JSON.parse(detail);
    if (parsed && typeof parsed === 'object' && parsed.changes) {
      return Object.entries(parsed.changes as Record<string, { from: unknown; to: unknown }>)
        .map(([field, c]) => `${field}: ${c.from ?? '∅'} → ${c.to ?? '∅'}`)
        .join('; ');
    }
    if (parsed && typeof parsed === 'object' && parsed.values) {
      return Object.entries(parsed.values as Record<string, unknown>)
        .filter(([, v]) => v !== null && v !== undefined && v !== '')
        .map(([field, v]) => `${field}: ${v}`)
        .join('; ');
    }
    return detail;
  } catch {
    return detail;
  }
}

export default function Audit() {
  const [entries, setEntries] = useState<AuditEntry[]>([]);
  const [actions, setActions] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);

  const [action, setAction] = useState('');
  const [q, setQ] = useState('');
  const [from, setFrom] = useState('');
  const [to, setTo] = useState('');
  const [offset, setOffset] = useState(0);
  const [reachedEnd, setReachedEnd] = useState(false);

  const load = useCallback(
    async (nextOffset: number) => {
      setError(null);
      try {
        const rows = await api.listAudit({
          action: action || undefined,
          q: q.trim() || undefined,
          start: from ? `${from}T00:00:00` : undefined,
          end: to ? `${to}T23:59:59` : undefined,
          limit: PAGE_SIZE,
          offset: nextOffset,
        });
        setEntries((prev) => (nextOffset === 0 ? rows : [...prev, ...rows]));
        setReachedEnd(rows.length < PAGE_SIZE);
        setOffset(nextOffset);
      } catch (err) {
        setError(err instanceof ApiError ? err.message : 'Unable to load the audit trail.');
      }
    },
    [action, q, from, to],
  );

  useEffect(() => {
    api
      .auditActions()
      .then(setActions)
      .catch(() => setActions([]));
  }, []);

  // Reload from the top whenever a filter changes.
  useEffect(() => {
    load(0);
  }, [load]);

  return (
    <AppLayout>
      <Typography variant="h5" component="h1" sx={{ mb: 2 }}>
        Audit trail
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} role="alert">
          {error}
        </Alert>
      )}

      <Paper sx={{ p: 2, mb: 3 }}>
        <Stack direction={{ xs: 'column', md: 'row' }} spacing={2} alignItems={{ md: 'center' }}>
          <FormControl sx={{ minWidth: 200 }} size="small">
            <InputLabel id="action-label">Action</InputLabel>
            <Select
              labelId="action-label"
              label="Action"
              value={action}
              onChange={(e) => setAction(e.target.value)}
            >
              <MenuItem value="">
                <em>All actions</em>
              </MenuItem>
              {actions.map((a) => (
                <MenuItem key={a} value={a}>
                  {a}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          <TextField
            label="User (actor or target)"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            size="small"
          />
          <TextField
            label="From"
            type="date"
            value={from}
            onChange={(e) => setFrom(e.target.value)}
            size="small"
            InputLabelProps={{ shrink: true }}
          />
          <TextField
            label="To"
            type="date"
            value={to}
            onChange={(e) => setTo(e.target.value)}
            size="small"
            InputLabelProps={{ shrink: true }}
          />
          {(action || q || from || to) && (
            <Button
              onClick={() => {
                setAction('');
                setQ('');
                setFrom('');
                setTo('');
              }}
            >
              Clear
            </Button>
          )}
        </Stack>
      </Paper>

      <Paper elevation={0} sx={{ border: '1px solid', borderColor: 'divider' }}>
        <Table aria-label="Audit entries">
          <TableHead>
            <TableRow>
              <TableCell>When</TableCell>
              <TableCell>Action</TableCell>
              <TableCell>Actor</TableCell>
              <TableCell>Target</TableCell>
              <TableCell>Details</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {entries.length === 0 && (
              <TableRow>
                <TableCell colSpan={5}>
                  <Typography color="text.secondary">No matching audit entries.</Typography>
                </TableCell>
              </TableRow>
            )}
            {entries.map((e) => {
              const changes = formatDetail(e.detail);
              return (
                <TableRow key={e.id} hover>
                  <TableCell sx={{ whiteSpace: 'nowrap' }}>
                    {new Date(e.created_at).toLocaleString()}
                  </TableCell>
                  <TableCell>
                    <Chip label={e.action} size="small" variant="outlined" />
                  </TableCell>
                  <TableCell>{e.actor ?? <em>system</em>}</TableCell>
                  <TableCell>
                    {e.target ??
                      (e.entity_type ? (
                        <Typography variant="body2" color="text.secondary">
                          {e.entity_type}
                        </Typography>
                      ) : (
                        '—'
                      ))}
                  </TableCell>
                  <TableCell>
                    {e.reason}
                    {changes && (
                      <Typography variant="caption" color="text.secondary" display="block">
                        {changes}
                      </Typography>
                    )}
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </Paper>

      {!reachedEnd && entries.length > 0 && (
        <Box sx={{ mt: 2, display: 'flex', justifyContent: 'center' }}>
          <Button onClick={() => load(offset + PAGE_SIZE)}>Load more</Button>
        </Box>
      )}
    </AppLayout>
  );
}
