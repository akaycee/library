import { useState, type FormEvent } from 'react';
import { useNavigate, Link as RouterLink } from 'react-router-dom';
import { Alert, Box, Button, Divider, Link, TextField, Typography } from '@mui/material';
import { api, ApiError } from '../services/api';
import AuthLayout from '../components/AuthLayout';
import { useAuth } from '../auth/AuthContext';

export default function ForgotPassword() {
  const navigate = useNavigate();
  const { loginTemporary } = useAuth();

  // Request a reset
  const [reqUsername, setReqUsername] = useState('');
  const [reqDone, setReqDone] = useState(false);
  const [reqError, setReqError] = useState<string | null>(null);

  // Use a temporary password
  const [username, setUsername] = useState('');
  const [tempPassword, setTempPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function onRequest(e: FormEvent) {
    e.preventDefault();
    setReqError(null);
    try {
      await api.requestReset(reqUsername);
      setReqDone(true);
    } catch (err) {
      setReqError(err instanceof ApiError ? err.message : 'Unable to submit the request.');
    }
  }

  async function onTempLogin(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await loginTemporary(username, tempPassword);
      navigate('/force-change', { state: { mode: 'forced' } });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Unable to sign in with that password.');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <AuthLayout title="Reset your password">
      <Typography variant="subtitle1" sx={{ mt: 1 }}>
        Step 1 — Ask an administrator for a reset
      </Typography>
      <Box component="form" onSubmit={onRequest} noValidate>
        {reqError && (
          <Alert severity="error" sx={{ mb: 2 }} role="alert">
            {reqError}
          </Alert>
        )}
        {reqDone ? (
          <Alert severity="success" sx={{ my: 2 }}>
            If that account exists, an administrator has been notified. They will give you a
            temporary password.
          </Alert>
        ) : (
          <>
            <TextField
              label="Username"
              fullWidth
              required
              margin="normal"
              value={reqUsername}
              onChange={(e) => setReqUsername(e.target.value)}
              autoComplete="username"
            />
            <Button type="submit" variant="outlined" sx={{ mt: 1 }}>
              Request reset
            </Button>
          </>
        )}
      </Box>

      <Divider sx={{ my: 3 }} />

      <Typography variant="subtitle1">Step 2 — I have a temporary password</Typography>
      <Box component="form" onSubmit={onTempLogin} noValidate>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }} role="alert">
            {error}
          </Alert>
        )}
        <TextField
          label="Username"
          fullWidth
          required
          margin="normal"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          autoComplete="username"
        />
        <TextField
          label="Temporary password"
          type="password"
          fullWidth
          required
          margin="normal"
          value={tempPassword}
          onChange={(e) => setTempPassword(e.target.value)}
          autoComplete="one-time-code"
        />
        <Button type="submit" variant="contained" sx={{ mt: 1 }} disabled={submitting}>
          {submitting ? 'Continuing…' : 'Continue'}
        </Button>
      </Box>

      <Typography variant="body2" sx={{ mt: 3 }}>
        <Link component={RouterLink} to="/login">
          Back to sign in
        </Link>
      </Typography>
    </AuthLayout>
  );
}
