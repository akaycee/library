import { useCallback, useEffect, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Chip,
  Grid,
  List,
  ListItem,
  ListItemText,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material';
import AutoStoriesIcon from '@mui/icons-material/AutoStories';
import LibraryBooksIcon from '@mui/icons-material/LibraryBooks';
import SwapHorizIcon from '@mui/icons-material/SwapHoriz';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import WarningAmberIcon from '@mui/icons-material/WarningAmber';
import PeopleAltIcon from '@mui/icons-material/PeopleAlt';
import LockResetIcon from '@mui/icons-material/LockReset';
import type { ReactNode } from 'react';
import AppLayout from '../components/AppLayout';
import { api, ApiError, type DashboardSummary } from '../services/api';

function StatCard({
  label,
  value,
  icon,
  accent,
}: {
  label: string;
  value: number;
  icon: ReactNode;
  accent?: boolean;
}) {
  return (
    <Paper sx={{ p: 2.5, height: '100%', display: 'flex', gap: 2, alignItems: 'center' }}>
      <Box
        aria-hidden
        sx={{
          width: 48,
          height: 48,
          borderRadius: 2,
          display: 'grid',
          placeItems: 'center',
          color: '#fff',
          bgcolor: accent ? 'error.main' : 'primary.main',
        }}
      >
        {icon}
      </Box>
      <Box>
        <Typography variant="h4" component="p" sx={{ fontWeight: 700, lineHeight: 1.1 }}>
          {value}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {label}
        </Typography>
      </Box>
    </Paper>
  );
}

const ACTIVITY_LABELS: Record<string, string> = {
  'loan.checkout': 'Checked out',
  'loan.return': 'Returned',
  'loan.renew': 'Renewed',
};

function daysOverdue(dueAt: string): number {
  const ms = Date.now() - new Date(dueAt).getTime();
  return Math.max(0, Math.floor(ms / 86_400_000));
}

export default function Dashboard() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      setSummary(await api.dashboardSummary());
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Unable to load the dashboard.');
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  async function onReturn(loanId: string) {
    setError(null);
    try {
      await api.returnLoan(loanId);
      await refresh();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Return failed.');
    }
  }

  const stats = summary
    ? [
        { label: 'Titles', value: summary.titles, icon: <AutoStoriesIcon /> },
        { label: 'Copies', value: summary.copies, icon: <LibraryBooksIcon /> },
        { label: 'On loan', value: summary.on_loan, icon: <SwapHorizIcon /> },
        { label: 'Available', value: summary.available, icon: <CheckCircleIcon /> },
        { label: 'Overdue', value: summary.overdue, icon: <WarningAmberIcon />, accent: true },
        { label: 'Active borrowers', value: summary.active_borrowers, icon: <PeopleAltIcon /> },
        { label: 'Pending resets', value: summary.pending_resets, icon: <LockResetIcon /> },
      ]
    : [];

  return (
    <AppLayout>
      <Typography variant="h5" component="h1" sx={{ mb: 2 }}>
        Dashboard
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} role="alert">
          {error}
        </Alert>
      )}

      <Grid container spacing={2} sx={{ mb: 3 }}>
        {stats.map((s) => (
          <Grid item xs={12} sm={6} md={3} key={s.label}>
            <StatCard label={s.label} value={s.value} icon={s.icon} accent={s.accent} />
          </Grid>
        ))}
      </Grid>

      <Grid container spacing={3}>
        <Grid item xs={12} md={7}>
          <Typography variant="h6" sx={{ mb: 1 }}>
            Overdue loans
          </Typography>
          <Paper elevation={0} sx={{ border: '1px solid', borderColor: 'divider' }}>
            <Table aria-label="Overdue loans">
              <TableHead>
                <TableRow>
                  <TableCell>Borrower</TableCell>
                  <TableCell>Item</TableCell>
                  <TableCell>Due</TableCell>
                  <TableCell align="right">Days over</TableCell>
                  <TableCell align="right">Action</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {summary && summary.overdue_loans.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={5}>
                      <Typography color="text.secondary">
                        Nothing overdue — you&apos;re all caught up.
                      </Typography>
                    </TableCell>
                  </TableRow>
                )}
                {summary?.overdue_loans.map((l) => (
                  <TableRow key={l.id} hover>
                    <TableCell>{l.borrower_username}</TableCell>
                    <TableCell>{l.title_name}</TableCell>
                    <TableCell>{new Date(l.due_at).toLocaleDateString()}</TableCell>
                    <TableCell align="right">
                      <Chip label={daysOverdue(l.due_at)} color="error" size="small" />
                    </TableCell>
                    <TableCell align="right">
                      <Button size="small" variant="contained" onClick={() => onReturn(l.id)}>
                        Return
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </Paper>
        </Grid>

        <Grid item xs={12} md={5}>
          <Typography variant="h6" sx={{ mb: 1 }}>
            Recent activity
          </Typography>
          <Paper elevation={0} sx={{ border: '1px solid', borderColor: 'divider' }}>
            <List aria-label="Recent activity" dense>
              {summary && summary.recent_activity.length === 0 && (
                <ListItem>
                  <ListItemText
                    primaryTypographyProps={{ color: 'text.secondary' }}
                    primary="No circulation activity yet."
                  />
                </ListItem>
              )}
              {summary?.recent_activity.map((a, i) => (
                <ListItem key={`${a.created_at}-${i}`} divider={i < summary.recent_activity.length - 1}>
                  <ListItemText
                    primary={`${ACTIVITY_LABELS[a.action] ?? a.action}${a.reason ? ` — ${a.reason}` : ''}`}
                    secondary={new Date(a.created_at).toLocaleString()}
                  />
                </ListItem>
              ))}
            </List>
          </Paper>
        </Grid>
      </Grid>
    </AppLayout>
  );
}
