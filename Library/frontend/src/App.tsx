import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { Box, CircularProgress } from '@mui/material';
import { AuthProvider, useAuth } from './auth/AuthContext';
import Login from './pages/Login';
import SignUp from './pages/SignUp';
import Home from './pages/Home';
import Users from './pages/Users';
import ForgotPassword from './pages/ForgotPassword';
import ForceChangePassword from './pages/ForceChangePassword';
import ResetQueue from './pages/ResetQueue';
import Locations from './pages/Locations';
import Catalog from './pages/Catalog';
import TitleDetail from './pages/TitleDetail';
import Browse from './pages/Browse';
import Circulation from './pages/Circulation';
import MyLoans from './pages/MyLoans';
import Dashboard from './pages/Dashboard';
import Audit from './pages/Audit';

function RequireAuth({ children }: { children: React.ReactElement }) {
  const { user, loading } = useAuth();
  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 8 }}>
        <CircularProgress aria-label="Loading" />
      </Box>
    );
  }
  return user ? children : <Navigate to="/login" replace />;
}

function RequireAdmin({ children }: { children: React.ReactElement }) {
  const { user, loading } = useAuth();
  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 8 }}>
        <CircularProgress aria-label="Loading" />
      </Box>
    );
  }
  if (!user) return <Navigate to="/login" replace />;
  return user.role === 'administrator' ? children : <Navigate to="/" replace />;
}

function RequireStaff({ children }: { children: React.ReactElement }) {
  const { user, loading } = useAuth();
  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 8 }}>
        <CircularProgress aria-label="Loading" />
      </Box>
    );
  }
  if (!user) return <Navigate to="/login" replace />;
  return user.role === 'administrator' || user.role === 'librarian' ? (
    children
  ) : (
    <Navigate to="/" replace />
  );
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<SignUp />} />
          <Route path="/forgot-password" element={<ForgotPassword />} />
          <Route path="/force-change" element={<ForceChangePassword />} />
          <Route
            path="/users"
            element={
              <RequireAdmin>
                <Users />
              </RequireAdmin>
            }
          />
          <Route
            path="/reset-queue"
            element={
              <RequireAdmin>
                <ResetQueue />
              </RequireAdmin>
            }
          />
          <Route
            path="/locations"
            element={
              <RequireStaff>
                <Locations />
              </RequireStaff>
            }
          />
          <Route
            path="/catalog"
            element={
              <RequireStaff>
                <Catalog />
              </RequireStaff>
            }
          />
          <Route
            path="/catalog/:id"
            element={
              <RequireStaff>
                <TitleDetail />
              </RequireStaff>
            }
          />
          <Route
            path="/browse"
            element={
              <RequireAuth>
                <Browse />
              </RequireAuth>
            }
          />
          <Route
            path="/my-loans"
            element={
              <RequireAuth>
                <MyLoans />
              </RequireAuth>
            }
          />
          <Route
            path="/circulation"
            element={
              <RequireStaff>
                <Circulation />
              </RequireStaff>
            }
          />
          <Route
            path="/dashboard"
            element={
              <RequireStaff>
                <Dashboard />
              </RequireStaff>
            }
          />
          <Route
            path="/audit"
            element={
              <RequireStaff>
                <Audit />
              </RequireStaff>
            }
          />
          <Route
            path="/"
            element={
              <RequireAuth>
                <Home />
              </RequireAuth>
            }
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
