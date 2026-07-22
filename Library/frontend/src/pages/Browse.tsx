import { useCallback, useEffect, useState, type FormEvent } from 'react';
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Grid,
  InputAdornment,
  Stack,
  TextField,
  Typography,
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import AppLayout from '../components/AppLayout';
import { api, ApiError, type BrowseItem } from '../services/api';

function availabilityChip(item: BrowseItem) {
  if (item.available_count > 0) {
    return (
      <Chip
        label={`${item.available_count} of ${item.total_count} available`}
        color="success"
        size="small"
      />
    );
  }
  return <Chip label="Not available" size="small" />;
}

export default function Browse() {
  const [items, setItems] = useState<BrowseItem[]>([]);
  const [query, setQuery] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loaded, setLoaded] = useState(false);

  const load = useCallback(async (q?: string) => {
    setError(null);
    try {
      setItems(await api.browse(q));
      setLoaded(true);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Unable to load the catalog.');
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  function onSearch(e: FormEvent) {
    e.preventDefault();
    load(query.trim() || undefined);
  }

  return (
    <AppLayout>
      <Typography variant="h5" component="h1" sx={{ mb: 2 }}>
        Browse the catalog
      </Typography>

      <Box component="form" onSubmit={onSearch} sx={{ mb: 3 }}>
        <Stack direction="row" spacing={1}>
          <TextField
            fullWidth
            placeholder="Search by title, author, or ISBN"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            inputProps={{ 'aria-label': 'Search the catalog' }}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon />
                </InputAdornment>
              ),
            }}
          />
          <Button type="submit" variant="contained">
            Search
          </Button>
        </Stack>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} role="alert">
          {error}
        </Alert>
      )}

      {loaded && items.length === 0 ? (
        <Typography color="text.secondary">No titles match your search.</Typography>
      ) : (
        <Grid container spacing={2}>
          {items.map((item) => (
            <Grid item xs={12} sm={6} md={4} key={item.id}>
              <Card sx={{ height: '100%' }}>
                <CardContent>
                  <Typography variant="h6">{item.name}</Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                    {item.author ?? 'Unknown author'}
                    {item.media_type ? ` · ${item.media_type}` : ''}
                  </Typography>
                  {availabilityChip(item)}
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}
    </AppLayout>
  );
}
