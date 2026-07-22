import { useState, type FormEvent } from 'react';
import { useNavigate, Link as RouterLink } from 'react-router-dom';
import { Alert, Box, Button, Link, TextField, Typography } from '@mui/material';
import { api, ApiError } from '../services/api';
import { useAuth } from '../auth/AuthContext';
import AuthLayout from '../components/AuthLayout';

export default function SignUp() {
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
      await api.register(username, password);
      await login(username, password);
      navigate('/');
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.status === 409 ? 'That username is already taken. Please choose another.' : err.message);
      } else {
        setError('Unable to reach the server. Please check your connection and try again.');
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <AuthLayout title="Create your account" subtitle="Sign up to borrow from the library">
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
          autoComplete="new-password"
          helperText="At least 8 characters, including a letter and a number."
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
          {submitting ? 'Creating account…' : 'Create account'}
        </Button>
      </Box>
      <Typography variant="body2" sx={{ mt: 2 }}>
        Already have an account?{' '}
        <Link component={RouterLink} to="/login">
          Sign in
        </Link>
      </Typography>
    </AuthLayout>
  );
}
