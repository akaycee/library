import { useCallback, useEffect, useState, type FormEvent } from 'react';
import { Link as RouterLink, useNavigate, useParams } from 'react-router-dom';
import {
  Alert,
  Box,
  Button,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  MenuItem,
  Paper,
  Select,
  Stack,
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
import LocationPicker from '../components/LocationPicker';
import { api, ApiError, type CopyStatus, type CopyView, type TitleDetail as TitleDetailType } from '../services/api';

const MANUAL_STATUSES: CopyStatus[] = ['available', 'lost', 'withdrawn'];

export default function TitleDetail() {
  const { id = '' } = useParams();
  const navigate = useNavigate();
  const [title, setTitle] = useState<TitleDetailType | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const [addOpen, setAddOpen] = useState(false);
  const [moveCopy, setMoveCopy] = useState<CopyView | null>(null);
  const [deleteTitleOpen, setDeleteTitleOpen] = useState(false);
  const [editOpen, setEditOpen] = useState(false);

  const [copyLocation, setCopyLocation] = useState('');
  const [copyBarcode, setCopyBarcode] = useState('');
  const [busy, setBusy] = useState(false);

  // Edit-title form fields
  const [editName, setEditName] = useState('');
  const [editAuthor, setEditAuthor] = useState('');
  const [editIsbn, setEditIsbn] = useState('');
  const [editMediaType, setEditMediaType] = useState('');

  const refresh = useCallback(async () => {
    try {
      setTitle(await api.getTitle(id));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Unable to load the title.');
    }
  }, [id]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  async function onAddCopy(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await api.addCopy(id, { location_id: copyLocation, barcode: copyBarcode || undefined });
      setAddOpen(false);
      setCopyLocation('');
      setCopyBarcode('');
      setNotice('Copy added.');
      await refresh();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Could not add the copy.');
    } finally {
      setBusy(false);
    }
  }

  async function onMove(e: FormEvent) {
    e.preventDefault();
    if (!moveCopy) return;
    setBusy(true);
    setError(null);
    try {
      await api.updateCopy(moveCopy.id, { location_id: copyLocation });
      setMoveCopy(null);
      setCopyLocation('');
      await refresh();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Could not move the copy.');
    } finally {
      setBusy(false);
    }
  }

  async function onStatus(copy: CopyView, status: CopyStatus) {
    setError(null);
    try {
      await api.setCopyStatus(copy.id, status);
      await refresh();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Could not change the status.');
    }
  }

  async function onDeleteCopy(copy: CopyView) {
    setError(null);
    try {
      await api.deleteCopy(copy.id);
      await refresh();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Could not delete the copy.');
    }
  }

  async function onDeleteTitle() {
    setError(null);
    try {
      await api.deleteTitle(id);
      navigate('/catalog');
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Could not delete the title.');
      setDeleteTitleOpen(false);
    }
  }

  function openEdit() {
    if (!title) return;
    setEditName(title.name);
    setEditAuthor(title.author ?? '');
    setEditIsbn(title.isbn ?? '');
    setEditMediaType(title.media_type ?? '');
    setError(null);
    setEditOpen(true);
  }

  async function onEditTitle(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await api.updateTitle(id, {
        name: editName,
        author: editAuthor.trim() === '' ? null : editAuthor,
        isbn: editIsbn.trim() === '' ? null : editIsbn,
        media_type: editMediaType.trim() === '' ? null : editMediaType,
      });
      setEditOpen(false);
      setNotice('Title updated.');
      await refresh();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Could not update the title.');
    } finally {
      setBusy(false);
    }
  }

  if (!title) {
    return (
      <AppLayout>
        {error && <Alert severity="error" role="alert">{error}</Alert>}
      </AppLayout>
    );
  }

  return (
    <AppLayout>
      <Button component={RouterLink} to="/catalog" sx={{ mb: 2 }}>
        ← Back to catalog
      </Button>

      {error && <Alert severity="error" sx={{ mb: 2 }} role="alert">{error}</Alert>}
      {notice && <Alert severity="success" sx={{ mb: 2 }}>{notice}</Alert>}

      <Paper sx={{ p: 3, mb: 3 }}>
        <Stack direction="row" alignItems="flex-start">
          <Box sx={{ flexGrow: 1 }}>
            <Typography variant="h5" component="h1">{title.name}</Typography>
            <Typography color="text.secondary">
              {title.author ?? 'Unknown author'}
              {title.media_type ? ` · ${title.media_type}` : ''}
              {title.isbn ? ` · ISBN ${title.isbn}` : ''}
            </Typography>
          </Box>
          <Stack direction="row" spacing={1}>
            <Button variant="outlined" onClick={openEdit}>
              Edit
            </Button>
            <Button color="error" onClick={() => setDeleteTitleOpen(true)}>
              Delete title
            </Button>
          </Stack>
        </Stack>
      </Paper>

      <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
        <Typography variant="h6" sx={{ flexGrow: 1 }}>Copies</Typography>
        <Button variant="contained" startIcon={<AddIcon />} onClick={() => setAddOpen(true)}>
          Add copy
        </Button>
      </Box>

      <Paper elevation={0} sx={{ border: '1px solid', borderColor: 'divider' }}>
        <Table aria-label="Copies">
          <TableHead>
            <TableRow>
              <TableCell>Barcode</TableCell>
              <TableCell>Location</TableCell>
              <TableCell>Status</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {title.copies.length === 0 && (
              <TableRow>
                <TableCell colSpan={4}>
                  <Typography color="text.secondary">No copies yet.</Typography>
                </TableCell>
              </TableRow>
            )}
            {title.copies.map((c) => (
              <TableRow key={c.id} hover>
                <TableCell sx={{ fontFamily: 'monospace' }}>{c.barcode}</TableCell>
                <TableCell>{c.location_path}</TableCell>
                <TableCell>
                  {c.status === 'checked_out' ? (
                    <Chip label="checked out" color="warning" size="small" />
                  ) : (
                    <Select
                      size="small"
                      value={c.status}
                      onChange={(e) => onStatus(c, e.target.value as CopyStatus)}
                      aria-label={`Status for ${c.barcode}`}
                    >
                      {MANUAL_STATUSES.map((s) => (
                        <MenuItem key={s} value={s}>{s}</MenuItem>
                      ))}
                    </Select>
                  )}
                </TableCell>
                <TableCell align="right">
                  <Button size="small" onClick={() => { setMoveCopy(c); setCopyLocation(c.location_id); }}>
                    Move
                  </Button>
                  <Button size="small" color="error" onClick={() => onDeleteCopy(c)}>
                    Delete
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Paper>

      {/* Add copy */}
      <Dialog open={addOpen} onClose={() => setAddOpen(false)}>
        <DialogTitle>Add copy</DialogTitle>
        <Box component="form" onSubmit={onAddCopy}>
          <DialogContent sx={{ minWidth: 380 }}>
            {error && <Alert severity="error" sx={{ mb: 2 }} role="alert">{error}</Alert>}
            <LocationPicker value={copyLocation} onChange={setCopyLocation} required />
            <TextField label="Barcode (optional)" fullWidth margin="normal" value={copyBarcode} onChange={(e) => setCopyBarcode(e.target.value)} helperText="Leave blank to auto-generate." />
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setAddOpen(false)}>Cancel</Button>
            <Button type="submit" variant="contained" disabled={busy || !copyLocation}>
              {busy ? 'Saving…' : 'Save'}
            </Button>
          </DialogActions>
        </Box>
      </Dialog>

      {/* Move copy */}
      <Dialog open={moveCopy !== null} onClose={() => setMoveCopy(null)}>
        <DialogTitle>Move copy {moveCopy?.barcode}</DialogTitle>
        <Box component="form" onSubmit={onMove}>
          <DialogContent sx={{ minWidth: 380 }}>
            {error && <Alert severity="error" sx={{ mb: 2 }} role="alert">{error}</Alert>}
            <LocationPicker value={copyLocation} onChange={setCopyLocation} required />
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setMoveCopy(null)}>Cancel</Button>
            <Button type="submit" variant="contained" disabled={busy || !copyLocation}>
              {busy ? 'Moving…' : 'Move'}
            </Button>
          </DialogActions>
        </Box>
      </Dialog>

      {/* Edit title */}
      <Dialog open={editOpen} onClose={() => setEditOpen(false)}>
        <DialogTitle>Edit title</DialogTitle>
        <Box component="form" onSubmit={onEditTitle}>
          <DialogContent sx={{ minWidth: 380 }}>
            {error && <Alert severity="error" sx={{ mb: 2 }} role="alert">{error}</Alert>}
            <TextField label="Title" fullWidth required margin="normal" value={editName} onChange={(e) => setEditName(e.target.value)} autoFocus />
            <TextField label="Author" fullWidth margin="normal" value={editAuthor} onChange={(e) => setEditAuthor(e.target.value)} />
            <TextField label="ISBN" fullWidth margin="normal" value={editIsbn} onChange={(e) => setEditIsbn(e.target.value)} />
            <TextField label="Media type" fullWidth margin="normal" value={editMediaType} onChange={(e) => setEditMediaType(e.target.value)} helperText="e.g., Book, DVD, Magazine" />
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setEditOpen(false)}>Cancel</Button>
            <Button type="submit" variant="contained" disabled={busy}>
              {busy ? 'Saving…' : 'Save'}
            </Button>
          </DialogActions>
        </Box>
      </Dialog>

      {/* Delete title */}
      <Dialog open={deleteTitleOpen} onClose={() => setDeleteTitleOpen(false)}>
        <DialogTitle>Delete title</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Delete "{title.name}"? A title can only be deleted when it has no copies.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteTitleOpen(false)}>Cancel</Button>
          <Button color="error" variant="contained" onClick={onDeleteTitle}>Delete</Button>
        </DialogActions>
      </Dialog>
    </AppLayout>
  );
}
