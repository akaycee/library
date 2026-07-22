import type { ReactNode } from 'react';
import { Box, IconButton, Paper, Stack, Tooltip, Typography } from '@mui/material';
import LocalLibraryIcon from '@mui/icons-material/LocalLibrary';
import MenuBookIcon from '@mui/icons-material/MenuBook';
import VerifiedUserIcon from '@mui/icons-material/VerifiedUser';
import GroupsIcon from '@mui/icons-material/Groups';
import Brightness4Icon from '@mui/icons-material/Brightness4';
import Brightness7Icon from '@mui/icons-material/Brightness7';
import { useColorMode } from '../ColorMode';

const HIGHLIGHTS: { icon: ReactNode; text: string }[] = [
  { icon: <MenuBookIcon />, text: 'Track every book and where it lives' },
  { icon: <GroupsIcon />, text: 'Roles for administrators, librarians, and borrowers' },
  { icon: <VerifiedUserIcon />, text: 'Secure, private, and works fully offline' },
];

/** Centered, branded frame for unauthenticated pages (login, sign-up, reset).
 * On wider screens it shows a decorative brand panel beside the form. */
export default function AuthLayout({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle?: string;
  children: ReactNode;
}) {
  const { mode, toggle } = useColorMode();

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        p: 2,
        bgcolor: 'background.default',
      }}
    >
      <Tooltip title={mode === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}>
        <IconButton
          onClick={toggle}
          aria-label="Toggle dark mode"
          sx={{ position: 'fixed', top: 16, right: 16 }}
        >
          {mode === 'dark' ? <Brightness7Icon /> : <Brightness4Icon />}
        </IconButton>
      </Tooltip>

      <Paper
        elevation={4}
        sx={{ width: '100%', maxWidth: 900, display: 'flex', overflow: 'hidden', minHeight: 520 }}
      >
        {/* Decorative brand panel — hidden on small screens */}
        <Box
          sx={{
            display: { xs: 'none', md: 'flex' },
            flexDirection: 'column',
            justifyContent: 'space-between',
            width: '45%',
            p: 5,
            color: '#fff',
            background: 'linear-gradient(150deg, #1d4ed8 0%, #0f766e 100%)',
          }}
        >
          <Stack direction="row" spacing={1.5} alignItems="center">
            <LocalLibraryIcon sx={{ fontSize: 34 }} />
            <Typography variant="h5" fontWeight={700}>
              Library
            </Typography>
          </Stack>

          <Box>
            <Typography variant="h4" fontWeight={700} sx={{ mb: 1 }}>
              Inventory made simple.
            </Typography>
            <Typography variant="body1" sx={{ opacity: 0.9, mb: 3 }}>
              A calm, easy-to-use system for your library.
            </Typography>
            <Stack spacing={2}>
              {HIGHLIGHTS.map((h) => (
                <Stack key={h.text} direction="row" spacing={1.5} alignItems="center">
                  <Box sx={{ opacity: 0.95, display: 'flex' }}>{h.icon}</Box>
                  <Typography variant="body2" sx={{ opacity: 0.95 }}>
                    {h.text}
                  </Typography>
                </Stack>
              ))}
            </Stack>
          </Box>

          <Typography variant="caption" sx={{ opacity: 0.7 }}>
            Local-first · Secure · Accessible
          </Typography>
        </Box>

        {/* Form column */}
        <Box
          sx={{
            flex: 1,
            p: { xs: 3, sm: 5 },
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'center',
          }}
        >
          <Stack alignItems="center" spacing={1} sx={{ mb: 3 }}>
            <Box
              sx={{
                width: 52,
                height: 52,
                borderRadius: '50%',
                display: { xs: 'grid', md: 'none' },
                placeItems: 'center',
                color: '#fff',
                background: 'linear-gradient(135deg, #1d4ed8, #0f766e)',
              }}
            >
              <LocalLibraryIcon />
            </Box>
            <Typography variant="h5" component="h1" textAlign="center">
              {title}
            </Typography>
            {subtitle && (
              <Typography variant="body2" color="text.secondary" textAlign="center">
                {subtitle}
              </Typography>
            )}
          </Stack>
          {children}
        </Box>
      </Paper>
    </Box>
  );
}
