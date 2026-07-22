import type { ReactNode } from 'react';
import { useState } from 'react';
import { Link as RouterLink, useLocation } from 'react-router-dom';
import {
  AppBar,
  Avatar,
  Box,
  Button,
  Chip,
  Container,
  IconButton,
  ListItemIcon,
  ListItemText,
  Menu,
  MenuItem,
  Stack,
  Toolbar,
  Tooltip,
  Typography,
} from '@mui/material';
import LocalLibraryIcon from '@mui/icons-material/LocalLibrary';
import PeopleAltIcon from '@mui/icons-material/PeopleAlt';
import LockResetIcon from '@mui/icons-material/LockReset';
import AccountTreeIcon from '@mui/icons-material/AccountTree';
import MenuBookIcon from '@mui/icons-material/MenuBook';
import SearchIcon from '@mui/icons-material/Search';
import SwapHorizIcon from '@mui/icons-material/SwapHoriz';
import ReceiptLongIcon from '@mui/icons-material/ReceiptLong';
import DashboardIcon from '@mui/icons-material/Dashboard';
import HistoryIcon from '@mui/icons-material/History';
import KeyboardArrowDownIcon from '@mui/icons-material/KeyboardArrowDown';
import LogoutIcon from '@mui/icons-material/Logout';
import Brightness4Icon from '@mui/icons-material/Brightness4';
import Brightness7Icon from '@mui/icons-material/Brightness7';
import { useAuth } from '../auth/AuthContext';
import { useColorMode } from '../ColorMode';

function initials(name: string): string {
  return name.slice(0, 2).toUpperCase();
}

/** Shared application shell: a branded top bar with role-aware navigation and a
 * user chip + logout. Wraps the page content in a centered container. */
export default function AppLayout({
  children,
  maxWidth = 'lg',
}: {
  children: ReactNode;
  maxWidth?: 'sm' | 'md' | 'lg';
}) {
  const { user, logout } = useAuth();
  const { mode, toggle } = useColorMode();
  const location = useLocation();
  const isAdmin = user?.role === 'administrator';
  const isStaff = isAdmin || user?.role === 'librarian';

  const [moreAnchor, setMoreAnchor] = useState<null | HTMLElement>(null);
  const moreOpen = Boolean(moreAnchor);

  // Less-frequent staff destinations live in a "More" overflow menu.
  const moreItems: { to: string; label: string; icon: ReactNode }[] = [];
  if (isAdmin) {
    moreItems.push({ to: '/users', label: 'Manage users', icon: <PeopleAltIcon fontSize="small" /> });
    moreItems.push({ to: '/reset-queue', label: 'Password resets', icon: <LockResetIcon fontSize="small" /> });
  }
  if (isStaff) {
    moreItems.push({ to: '/audit', label: 'Audit', icon: <HistoryIcon fontSize="small" /> });
  }
  const moreActive = moreItems.some((m) => m.to === location.pathname);

  const navLink = (to: string, label: string, icon: ReactNode) => (
    <Button
      component={RouterLink}
      to={to}
      startIcon={icon}
      color="inherit"
      sx={{
        opacity: location.pathname === to ? 1 : 0.85,
        bgcolor: location.pathname === to ? 'rgba(255,255,255,0.16)' : 'transparent',
      }}
    >
      {label}
    </Button>
  );

  return (
    <Box sx={{ minHeight: '100vh', bgcolor: 'background.default' }}>
      <AppBar position="sticky" elevation={0}>
        <Toolbar sx={{ gap: 1, bgcolor: '#143a9e' }}>
          <LocalLibraryIcon sx={{ mr: 1 }} />
          <Typography
            variant="h6"
            component={RouterLink}
            to="/"
            sx={{ color: 'inherit', textDecoration: 'none', fontWeight: 700, mr: 2 }}
          >
            Library
          </Typography>

          <Stack direction="row" spacing={0.5} sx={{ flexGrow: 1 }} alignItems="center">
            {navLink('/', 'Home', <LocalLibraryIcon />)}
            {navLink('/browse', 'Browse', <SearchIcon />)}
            {!isStaff && navLink('/my-loans', 'My loans', <ReceiptLongIcon />)}
            {isStaff && navLink('/circulation', 'Circulation', <SwapHorizIcon />)}
            {isStaff && navLink('/dashboard', 'Dashboard', <DashboardIcon />)}
            {isStaff && navLink('/catalog', 'Catalog', <MenuBookIcon />)}
            {isStaff && navLink('/locations', 'Locations', <AccountTreeIcon />)}
            {moreItems.length > 0 && (
              <>
                <Button
                  color="inherit"
                  endIcon={<KeyboardArrowDownIcon />}
                  onClick={(e) => setMoreAnchor(e.currentTarget)}
                  aria-haspopup="menu"
                  aria-expanded={moreOpen ? 'true' : undefined}
                  aria-controls={moreOpen ? 'more-menu' : undefined}
                  sx={{
                    opacity: moreActive ? 1 : 0.85,
                    bgcolor: moreActive ? 'rgba(255,255,255,0.16)' : 'transparent',
                  }}
                >
                  More
                </Button>
                <Menu
                  id="more-menu"
                  anchorEl={moreAnchor}
                  open={moreOpen}
                  onClose={() => setMoreAnchor(null)}
                  anchorOrigin={{ vertical: 'bottom', horizontal: 'left' }}
                  transformOrigin={{ vertical: 'top', horizontal: 'left' }}
                >
                  {moreItems.map((m) => (
                    <MenuItem
                      key={m.to}
                      component={RouterLink}
                      to={m.to}
                      selected={location.pathname === m.to}
                      onClick={() => setMoreAnchor(null)}
                    >
                      <ListItemIcon>{m.icon}</ListItemIcon>
                      <ListItemText>{m.label}</ListItemText>
                    </MenuItem>
                  ))}
                </Menu>
              </>
            )}
          </Stack>

          <Tooltip title={mode === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}>
            <IconButton color="inherit" onClick={toggle} aria-label="Toggle dark mode" sx={{ mr: 1 }}>
              {mode === 'dark' ? <Brightness7Icon /> : <Brightness4Icon />}
            </IconButton>
          </Tooltip>

          {user && (
            <Stack direction="row" spacing={1.5} alignItems="center">
              <Chip
                avatar={<Avatar>{initials(user.username)}</Avatar>}
                label={`${user.username} · ${user.role}`}
                variant="outlined"
                sx={{
                  color: 'inherit',
                  bgcolor: '#143a9e',
                  borderColor: 'rgba(255,255,255,0.5)',
                  '& .MuiChip-label': { fontWeight: 600 },
                  '& .MuiChip-avatar': { bgcolor: '#0b3aa0', color: '#fff' },
                }}
              />
              <Button
                color="inherit"
                onClick={() => logout()}
                startIcon={<LogoutIcon />}
                sx={{ bgcolor: '#1c47b8', '&:hover': { bgcolor: '#2a58d0' } }}
              >
                Log out
              </Button>
            </Stack>
          )}
        </Toolbar>
      </AppBar>

      <Container maxWidth={maxWidth} sx={{ py: 4 }}>
        {children}
      </Container>
    </Box>
  );
}
