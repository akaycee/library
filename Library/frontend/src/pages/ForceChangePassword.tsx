import { useState, type FormEvent } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Alert, Box, Button, TextField } from '@mui/material';
import { ApiError } from '../services/api';
import { useAuth } from '../auth/AuthContext';
import AuthLayout from '../components/AuthLayout';

/**
 * Forced password change. Two modes:
 * - 'forced' (default): the user arrived via a temporary-password login
 *   (restricted session) — only a new password is required.
 * - 'normal': a full-session user whose account requires a change on first
 *   login — the current (temporary/initial) password is required.
 */
export default function ForceChangePassword() {
  const navigate = useNavigate();
  const location = useLocation();
  const { changePassword } = useAuth();
  const mode = (location.state as { mode?: string } | null)?.mode ?? 'forced';
  const needsCurrent = mode === 'normal';

  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    if (newPassword !== confirm) {
      setError('The new passwords do not match.');
      return;
    }
    setSubmitting(true);
    try {
      await changePassword(newPassword, needsCurrent ? currentPassword : undefined);
      navigate('/');
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        setError(
          needsCurrent
            ? 'Your current password is incorrect.'
            : 'Your session has expired. Please start the reset again.',
        );
      } else {
        setError(err instanceof ApiError ? err.message : 'Unable to change the password.');
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <AuthLayout
      title="Set a new password"
      subtitle="For your security, choose a new password before continuing."
    >
      <Box component="form" onSubmit={onSubmit} noValidate>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }} role="alert">
            {error}
          </Alert>
        )}
        {needsCurrent && (
          <TextField
            label="Current password"
            type="password"
            fullWidth
            required
            margin="normal"
            value={currentPassword}
            onChange={(e) => setCurrentPassword(e.target.value)}
            autoComplete="current-password"
          />
        )}
        <TextField
          label="New password"
          type="password"
          fullWidth
          required
          margin="normal"
          value={newPassword}
          onChange={(e) => setNewPassword(e.target.value)}
          helperText="At least 8 characters, including a letter and a number."
          autoComplete="new-password"
        />
        <TextField
          label="Confirm new password"
          type="password"
          fullWidth
          required
          margin="normal"
          value={confirm}
          onChange={(e) => setConfirm(e.target.value)}
          autoComplete="new-password"
        />
        <Button type="submit" variant="contained" fullWidth size="large" sx={{ mt: 2 }} disabled={submitting}>
          {submitting ? 'Saving…' : 'Save new password'}
        </Button>
      </Box>
    </AuthLayout>
  );
}
