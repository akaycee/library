import { useState, type FormEvent } from 'react';
import { useNavigate, Link as RouterLink } from 'react-router-dom';
import { Alert, Box, Button, Link, TextField, Typography } from '@mui/material';
import { ApiError } from '../services/api';
import { useAuth } from '../auth/AuthContext';
import AuthLayout from '../components/AuthLayout';

export default function Login() {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const me = await login(username, password);
      // Admin-created / bootstrap accounts must set a new password first.
      if (me.force_password_change) {
        navigate('/force-change', { state: { mode: 'normal' } });
      } else {
        navigate('/');
      }
    } catch (err) {
      // The API client already returns friendly, indistinguishable messages.
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError('Unable to reach the server. Please check your connection and try again.');
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <AuthLayout title="Sign in" subtitle="Welcome back to the library">
      <Box component="form" onSubmit={onSubmit} noValidate>
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
          inputProps={{ 'aria-label': 'Username' }}
        />
        <TextField
          label="Password"
          type="password"
          fullWidth
          required
          margin="normal"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          autoComplete="current-password"
          inputProps={{ 'aria-label': 'Password' }}
        />
        <Button
          type="submit"
          variant="contained"
          fullWidth
          size="large"
          sx={{ mt: 2 }}
          disabled={submitting}
        >
          {submitting ? 'Signing in…' : 'Sign in'}
        </Button>
      </Box>
      <Typography variant="body2" sx={{ mt: 2 }}>
        New here?{' '}
        <Link component={RouterLink} to="/signup">
          Create an account
        </Link>
      </Typography>
      <Typography variant="body2" sx={{ mt: 1 }}>
        <Link component={RouterLink} to="/forgot-password">
          Forgot your password?
        </Link>
      </Typography>
    </AuthLayout>
  );
}
