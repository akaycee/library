import { useEffect, useState, type FormEvent } from 'react';
import { Link as RouterLink } from 'react-router-dom';
import {
  Alert,
  Box,
  Button,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Link,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import AppLayout from '../components/AppLayout';
import { api, ApiError, type TitleView } from '../services/api';

export default function Catalog() {
  const [titles, setTitles] = useState<TitleView[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [open, setOpen] = useState(false);
  const [name, setName] = useState('');
  const [author, setAuthor] = useState('');
  const [isbn, setIsbn] = useState('');
  const [mediaType, setMediaType] = useState('');
  const [busy, setBusy] = useState(false);

  async function refresh() {
    try {
      setTitles(await api.listTitles());
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Unable to load the catalog.');
    }
  }

  useEffect(() => {
    refresh();
  }, []);

  async function onCreate(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await api.createTitle({
        name,
        author: author || undefined,
        isbn: isbn || undefined,
        media_type: mediaType || undefined,
      });
      setOpen(false);
      setName('');
      setAuthor('');
      setIsbn('');
      setMediaType('');
      await refresh();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Could not add the title.');
    } finally {
      setBusy(false);
    }
  }

  return (
    <AppLayout>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
        <Typography variant="h5" component="h1" sx={{ flexGrow: 1 }}>
          Catalog
        </Typography>
        <Button variant="contained" startIcon={<AddIcon />} onClick={() => setOpen(true)}>
          Add title
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} role="alert">
          {error}
        </Alert>
      )}

      <Paper elevation={0} sx={{ border: '1px solid', borderColor: 'divider' }}>
        <Table aria-label="Titles">
          <TableHead>
            <TableRow>
              <TableCell>Title</TableCell>
              <TableCell>Author</TableCell>
              <TableCell>Type</TableCell>
              <TableCell align="right">Copies</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {titles.length === 0 && (
              <TableRow>
                <TableCell colSpan={4}>
                  <Typography color="text.secondary">No titles yet. Add your first one.</Typography>
                </TableCell>
              </TableRow>
            )}
            {titles.map((t) => (
              <TableRow key={t.id} hover>
                <TableCell>
                  <Link component={RouterLink} to={`/catalog/${t.id}`}>
                    {t.name}
                  </Link>
                </TableCell>
                <TableCell>{t.author ?? '—'}</TableCell>
                <TableCell>{t.media_type ?? '—'}</TableCell>
                <TableCell align="right">
                  <Chip label={t.copy_count} size="small" />
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Paper>

      <Dialog open={open} onClose={() => setOpen(false)}>
        <DialogTitle>Add title</DialogTitle>
        <Box component="form" onSubmit={onCreate}>
          <DialogContent sx={{ minWidth: 380 }}>
            {error && (
              <Alert severity="error" sx={{ mb: 2 }} role="alert">
                {error}
              </Alert>
            )}
            <TextField label="Title" fullWidth required margin="normal" value={name} onChange={(e) => setName(e.target.value)} autoFocus />
            <TextField label="Author" fullWidth margin="normal" value={author} onChange={(e) => setAuthor(e.target.value)} />
            <TextField label="ISBN" fullWidth margin="normal" value={isbn} onChange={(e) => setIsbn(e.target.value)} />
            <TextField label="Media type" fullWidth margin="normal" value={mediaType} onChange={(e) => setMediaType(e.target.value)} helperText="e.g., Book, DVD, Magazine" />
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setOpen(false)}>Cancel</Button>
            <Button type="submit" variant="contained" disabled={busy}>
              {busy ? 'Saving…' : 'Save'}
            </Button>
          </DialogActions>
        </Box>
      </Dialog>
    </AppLayout>
  );
}
