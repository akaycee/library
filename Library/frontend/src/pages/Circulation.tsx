import { useCallback, useEffect, useState, type FormEvent } from 'react';
import {
  Alert,
  Box,
  Button,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  FormControl,
  FormControlLabel,
  FormLabel,
  Paper,
  Radio,
  RadioGroup,
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
import { api, ApiError, type LoanView } from '../services/api';

export default function Circulation() {
  const [loans, setLoans] = useState<LoanView[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const [barcode, setBarcode] = useState('');
  const [borrower, setBorrower] = useState('');
  const [days, setDays] = useState('14');
  const [busy, setBusy] = useState(false);

  // Quick-create borrower dialog state.
  const [createOpen, setCreateOpen] = useState(false);
  const [pwMode, setPwMode] = useState<'generate' | 'set'>('generate');
  const [newPassword, setNewPassword] = useState('');
  const [createBusy, setCreateBusy] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);

  // Renewal dialog state (staff choose how many days to extend).
  const [renewTarget, setRenewTarget] = useState<LoanView | null>(null);
  const [renewDays, setRenewDays] = useState('7');

  const refresh = useCallback(async () => {
    try {
      setLoans(await api.listLoans());
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Unable to load loans.');
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  /** Runs a checkout for the given borrower username. */
  async function runCheckout(borrowerUsername: string): Promise<void> {
    const code = barcode.trim();
    await api.checkout(code, borrowerUsername.trim(), Number(days));
    setNotice(`Checked out ${code} to ${borrowerUsername.trim()}.`);
    setBarcode('');
    setBorrower('');
    await refresh();
  }

  async function onCheckout(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    setNotice(null);
    try {
      await runCheckout(borrower);
    } catch (err) {
      // A missing borrower (404 whose message mentions the borrower) offers a
      // quick-create path; anything else is a plain error.
      if (err instanceof ApiError && err.status === 404 && /borrower/i.test(err.message)) {
        setPwMode('generate');
        setNewPassword('');
        setCreateError(null);
        setCreateOpen(true);
      } else {
        setError(err instanceof ApiError ? err.message : 'Checkout failed.');
      }
    } finally {
      setBusy(false);
    }
  }

  async function onCreateAndCheckout() {
    setCreateBusy(true);
    setCreateError(null);
    let created;
    try {
      created = await api.createBorrower(
        borrower.trim(),
        pwMode === 'set' ? newPassword : undefined,
      );
    } catch (err) {
      // Creation itself failed — nothing was persisted; stay in the dialog.
      setCreateError(err instanceof ApiError ? err.message : 'Could not create the borrower.');
      setCreateBusy(false);
      return;
    }

    // The account now exists. Surface any one-time password IMMEDIATELY so it can
    // never be discarded, even if the checkout that follows fails.
    setCreateOpen(false);
    const pwNote = created.temporary_password
      ? ` Temporary password: ${created.temporary_password} — they must change it on first sign-in.`
      : '';
    const code = barcode.trim();
    try {
      await api.checkout(code, created.username, Number(days));
      setBarcode('');
      setBorrower('');
      await refresh();
      setNotice(`Created borrower “${created.username}” and checked out ${code}.${pwNote}`);
    } catch (err) {
      // Borrower was created but checkout failed. Keep the credentials on screen
      // and leave the form filled so the librarian can simply retry the checkout
      // (the borrower now exists, so it will no longer prompt to create).
      await refresh();
      setNotice(`Borrower “${created.username}” was created.${pwNote}`);
      setError(
        `Checkout did not complete: ${
          err instanceof ApiError ? err.message : 'unknown error'
        }. The borrower exists now — you can try the checkout again.`,
      );
    } finally {
      setCreateBusy(false);
    }
  }

  async function onReturn(loan: LoanView) {
    setError(null);
    try {
      await api.returnLoan(loan.id);
      await refresh();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Return failed.');
    }
  }

  async function onRenew(loan: LoanView) {
    setRenewTarget(loan);
    setRenewDays('7');
  }

  async function onConfirmRenew() {
    if (!renewTarget) return;
    setError(null);
    try {
      await api.renewLoan(renewTarget.id, Number(renewDays));
      setRenewTarget(null);
      await refresh();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Renewal failed.');
      setRenewTarget(null);
    }
  }

  return (
    <AppLayout>
      <Typography variant="h5" component="h1" sx={{ mb: 2 }}>
        Circulation
      </Typography>

      {error && <Alert severity="error" sx={{ mb: 2 }} role="alert">{error}</Alert>}
      {notice && <Alert severity="success" sx={{ mb: 2 }}>{notice}</Alert>}

      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" sx={{ mb: 1 }}>Check out</Typography>
        <Box component="form" onSubmit={onCheckout}>
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} alignItems="flex-start">
            <TextField label="Barcode" value={barcode} onChange={(e) => setBarcode(e.target.value)} required />
            <TextField label="Borrower username" value={borrower} onChange={(e) => setBorrower(e.target.value)} required />
            <TextField label="Loan period (days)" type="number" value={days} onChange={(e) => setDays(e.target.value)} required inputProps={{ min: 1 }} sx={{ width: 160 }} />
            <Button type="submit" variant="contained" size="large" disabled={busy}>
              {busy ? 'Checking out…' : 'Check out'}
            </Button>
          </Stack>
        </Box>
      </Paper>

      <Typography variant="h6" sx={{ mb: 1 }}>Active loans</Typography>
      <Paper elevation={0} sx={{ border: '1px solid', borderColor: 'divider' }}>
        <Table aria-label="Active loans">
          <TableHead>
            <TableRow>
              <TableCell>Title</TableCell>
              <TableCell>Barcode</TableCell>
              <TableCell>Borrower</TableCell>
              <TableCell>Due</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {loans.length === 0 && (
              <TableRow>
                <TableCell colSpan={5}>
                  <Typography color="text.secondary">No active loans.</Typography>
                </TableCell>
              </TableRow>
            )}
            {loans.map((l) => (
              <TableRow key={l.id} hover>
                <TableCell>{l.title_name}</TableCell>
                <TableCell sx={{ fontFamily: 'monospace' }}>{l.barcode}</TableCell>
                <TableCell>{l.borrower_username}</TableCell>
                <TableCell>
                  {new Date(l.due_at).toLocaleDateString()}{' '}
                  {l.overdue && <Chip label="overdue" color="error" size="small" />}
                </TableCell>
                <TableCell align="right">
                  <Button size="small" onClick={() => onRenew(l)} disabled={l.overdue}>
                    Renew
                  </Button>
                  <Button size="small" variant="contained" onClick={() => onReturn(l)}>
                    Return
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Paper>

      <Dialog open={Boolean(renewTarget)} onClose={() => setRenewTarget(null)} fullWidth maxWidth="xs">
        <DialogTitle>Renew loan</DialogTitle>
        <DialogContent>
          <DialogContentText sx={{ mb: 2 }}>
            Extend “{renewTarget?.title_name}” for {renewTarget?.borrower_username} by how many days?
          </DialogContentText>
          <TextField
            label="Days"
            type="number"
            value={renewDays}
            onChange={(e) => setRenewDays(e.target.value)}
            fullWidth
            inputProps={{ min: 1 }}
            autoFocus
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setRenewTarget(null)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={onConfirmRenew}
            disabled={!renewDays || Number(renewDays) < 1}
          >
            Renew
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog open={createOpen} onClose={() => setCreateOpen(false)} fullWidth maxWidth="xs">
        <DialogTitle>Create borrower “{borrower.trim()}”?</DialogTitle>
        <DialogContent>
          <DialogContentText sx={{ mb: 2 }}>
            No active borrower named “{borrower.trim()}” was found. Create one now and check
            the copy out to them.
          </DialogContentText>
          {createError && (
            <Alert severity="error" sx={{ mb: 2 }} role="alert">
              {createError}
            </Alert>
          )}
          <FormControl>
            <FormLabel id="pw-mode-label">Initial password</FormLabel>
            <RadioGroup
              aria-labelledby="pw-mode-label"
              value={pwMode}
              onChange={(e) => setPwMode(e.target.value as 'generate' | 'set')}
            >
              <FormControlLabel
                value="generate"
                control={<Radio />}
                label="Generate a temporary password"
              />
              <FormControlLabel value="set" control={<Radio />} label="Set a password" />
            </RadioGroup>
          </FormControl>
          {pwMode === 'set' && (
            <TextField
              label="Password"
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              fullWidth
              sx={{ mt: 1 }}
              autoComplete="new-password"
            />
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={onCreateAndCheckout}
            disabled={createBusy || (pwMode === 'set' && newPassword.length === 0)}
          >
            {createBusy ? 'Creating…' : 'Create & check out'}
          </Button>
        </DialogActions>
      </Dialog>
    </AppLayout>
  );
}
