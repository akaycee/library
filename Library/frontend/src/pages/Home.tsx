import { Link as RouterLink } from 'react-router-dom';
import type { ReactNode } from 'react';
import {
  Box,
  Button,
  Card,
  CardActions,
  CardContent,
  Grid,
  Paper,
  Stack,
  Typography,
} from '@mui/material';
import PeopleAltIcon from '@mui/icons-material/PeopleAlt';
import LockResetIcon from '@mui/icons-material/LockReset';
import AccountTreeIcon from '@mui/icons-material/AccountTree';
import MenuBookIcon from '@mui/icons-material/MenuBook';
import SwapHorizIcon from '@mui/icons-material/SwapHoriz';
import ReceiptLongIcon from '@mui/icons-material/ReceiptLong';
import AutoStoriesIcon from '@mui/icons-material/AutoStories';
import AppLayout from '../components/AppLayout';
import { useAuth } from '../auth/AuthContext';

interface ActionCard {
  title: string;
  description: string;
  icon: ReactNode;
  to: string;
  cta: string;
  disabled?: boolean;
}

export default function Home() {
  const { user } = useAuth();
  const isAdmin = user?.role === 'administrator';
  const isStaff = isAdmin || user?.role === 'librarian';

  const cards: ActionCard[] = [];
  if (isStaff) {
    cards.push({
      title: 'Circulation',
      description: 'Check out copies to borrowers, return them, and renew active loans.',
      icon: <SwapHorizIcon fontSize="large" color="primary" />,
      to: '/circulation',
      cta: 'Open circulation',
    });
    cards.push({
      title: 'Catalog',
      description: 'Add titles and physical copies, assign them to locations, and manage status.',
      icon: <MenuBookIcon fontSize="large" color="primary" />,
      to: '/catalog',
      cta: 'Open catalog',
    });
    cards.push({
      title: 'Locations',
      description: 'Organize the library into rooms, shelves, rows, or any structure you like.',
      icon: <AccountTreeIcon fontSize="large" color="primary" />,
      to: '/locations',
      cta: 'Manage locations',
    });
  }
  if (isAdmin) {
    cards.push({
      title: 'Manage users',
      description: 'Create staff and borrower accounts, assign roles, and deactivate access.',
      icon: <PeopleAltIcon fontSize="large" color="primary" />,
      to: '/users',
      cta: 'Open user management',
    });
    cards.push({
      title: 'Password resets',
      description: 'Review reset requests and issue one-time temporary passwords.',
      icon: <LockResetIcon fontSize="large" color="primary" />,
      to: '/reset-queue',
      cta: 'Open reset queue',
    });
  }
  if (!isStaff) {
    cards.push({
      title: 'Browse the catalog',
      description: 'Search available books and media by title, author, or ISBN.',
      icon: <MenuBookIcon fontSize="large" color="primary" />,
      to: '/browse',
      cta: 'Browse catalog',
    });
    cards.push({
      title: 'My loans',
      description: 'See the items you currently have checked out and their due dates.',
      icon: <ReceiptLongIcon fontSize="large" color="primary" />,
      to: '/my-loans',
      cta: 'View my loans',
    });
  }

  return (
    <AppLayout>
      <Paper
        sx={{
          p: { xs: 3, md: 4 },
          mb: 4,
          color: 'primary.contrastText',
          background: 'linear-gradient(120deg, #1d4ed8 0%, #0f766e 100%)',
        }}
      >
        <Stack direction="row" spacing={2} alignItems="center">
          <AutoStoriesIcon sx={{ fontSize: 44 }} />
          <Box>
            <Typography variant="h4" component="h1">
              Welcome, {user?.username}
            </Typography>
            <Typography variant="body1" sx={{ opacity: 0.9 }}>
              You are signed in as {user?.role}.
            </Typography>
          </Box>
        </Stack>
      </Paper>

      <Typography variant="h6" sx={{ mb: 2 }}>
        Quick actions
      </Typography>
      <Grid container spacing={3}>
        {cards.map((c) => (
          <Grid item xs={12} sm={6} md={4} key={c.title}>
            <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
              <CardContent sx={{ flexGrow: 1 }}>
                <Stack spacing={1.5}>
                  {c.icon}
                  <Typography variant="h6">{c.title}</Typography>
                  <Typography variant="body2" color="text.secondary">
                    {c.description}
                  </Typography>
                </Stack>
              </CardContent>
              <CardActions sx={{ p: 2, pt: 0 }}>
                <Button
                  component={RouterLink}
                  to={c.to}
                  variant="contained"
                  disabled={c.disabled}
                  fullWidth
                >
                  {c.cta}
                </Button>
              </CardActions>
            </Card>
          </Grid>
        ))}
      </Grid>
    </AppLayout>
  );
}
