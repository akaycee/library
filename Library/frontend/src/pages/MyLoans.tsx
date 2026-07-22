import { useEffect, useState } from 'react';
import {
  Alert,
  Chip,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material';
import AppLayout from '../components/AppLayout';
import { api, ApiError, type LoanView } from '../services/api';

export default function MyLoans() {
  const [loans, setLoans] = useState<LoanView[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    api
      .myLoans()
      .then((l) => {
        setLoans(l);
        setLoaded(true);
      })
      .catch((err) => setError(err instanceof ApiError ? err.message : 'Unable to load your loans.'));
  }, []);

  return (
    <AppLayout>
      <Typography variant="h5" component="h1" sx={{ mb: 2 }}>
        My loans
      </Typography>

      {error && <Alert severity="error" sx={{ mb: 2 }} role="alert">{error}</Alert>}

      {loaded && loans.length === 0 ? (
        <Typography color="text.secondary">You have no items checked out.</Typography>
      ) : (
        <Paper elevation={0} sx={{ border: '1px solid', borderColor: 'divider' }}>
          <Table aria-label="My loans">
            <TableHead>
              <TableRow>
                <TableCell>Title</TableCell>
                <TableCell>Due</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {loans.map((l) => (
                <TableRow key={l.id} hover>
                  <TableCell>{l.title_name}</TableCell>
                  <TableCell>
                    {new Date(l.due_at).toLocaleDateString()}{' '}
                    {l.overdue && <Chip label="overdue" color="error" size="small" />}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Paper>
      )}
    </AppLayout>
  );
}
