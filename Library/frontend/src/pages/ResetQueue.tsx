import { useEffect, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material';
import AppLayout from '../components/AppLayout';
import { api, ApiError, type PendingResetView } from '../services/api';

export default function ResetQueue() {
  const [requests, setRequests] = useState<PendingResetView[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [issued, setIssued] = useState<{ username: string; password: string } | null>(null);

  async function refresh() {
    try {
      setRequests(await api.listResetRequests());
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Unable to load reset requests.');
    }
  }

  useEffect(() => {
    refresh();
  }, []);

  async function onIssue(r: PendingResetView) {
    setError(null);
    try {
      const res = await api.issueReset(r.id);
      setIssued({ username: r.username, password: res.temporary_password });
      await refresh();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Could not issue a temporary password.');
    }
  }

  return (
    <AppLayout maxWidth="md">
      <Typography variant="h5" component="h1" sx={{ mb: 2 }}>
        Password reset requests
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} role="alert">
          {error}
        </Alert>
      )}

      <Paper elevation={0} sx={{ border: '1px solid #e6e9f0' }}>
        <Table aria-label="Reset requests">
          <TableHead>
            <TableRow>
              <TableCell>Username</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Requested</TableCell>
              <TableCell align="right">Action</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {requests.length === 0 && (
              <TableRow>
                <TableCell colSpan={4}>
                  <Typography color="text.secondary">No pending requests.</Typography>
                </TableCell>
              </TableRow>
            )}
            {requests.map((r) => (
              <TableRow key={r.id} hover>
                <TableCell>{r.username}</TableCell>
                <TableCell>{r.status}</TableCell>
                <TableCell>{new Date(r.requested_at).toLocaleString()}</TableCell>
                <TableCell align="right">
                  <Button size="small" variant="contained" onClick={() => onIssue(r)}>
                    Issue temporary password
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Paper>

      <Dialog open={issued !== null} onClose={() => setIssued(null)}>
        <DialogTitle>Temporary password for {issued?.username}</DialogTitle>
        <DialogContent>
          <DialogContentText component="div">
            Give this one-time password to the user in person or by phone. It is shown{' '}
            <strong>only once</strong> and expires after use or a set time.
            <Box
              sx={{
                mt: 2,
                p: 2,
                bgcolor: 'grey.100',
                borderRadius: 1,
                fontFamily: 'monospace',
                fontSize: '1.1rem',
                wordBreak: 'break-all',
              }}
              data-testid="temp-password"
            >
              {issued?.password}
            </Box>
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setIssued(null)} variant="contained">
            Done
          </Button>
        </DialogActions>
      </Dialog>
    </AppLayout>
  );
}
