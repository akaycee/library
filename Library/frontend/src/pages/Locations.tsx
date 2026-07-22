import { useEffect, useMemo, useState, type FormEvent } from 'react';
import {
  Alert,
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  MenuItem,
  Paper,
  TextField,
  Typography,
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import AppLayout from '../components/AppLayout';
import LocationTree from '../components/LocationTree';
import { api, ApiError, type LocationNode } from '../services/api';

type Dialog =
  | { kind: 'create'; parent: LocationNode | null }
  | { kind: 'rename'; node: LocationNode }
  | { kind: 'move'; node: LocationNode }
  | { kind: 'delete'; node: LocationNode }
  | null;

interface FlatOption {
  id: string;
  label: string;
}

function flattenForSelect(
  nodes: LocationNode[],
  excludeId: string,
  level = 0,
  out: FlatOption[] = [],
): FlatOption[] {
  for (const n of nodes) {
    if (n.id === excludeId) continue; // exclude node + its subtree
    out.push({ id: n.id, label: `${'\u00A0\u00A0'.repeat(level)}${n.name}` });
    flattenForSelect(n.children, excludeId, level + 1, out);
  }
  return out;
}

export default function Locations() {
  const [tree, setTree] = useState<LocationNode[]>([]);
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [dialog, setDialog] = useState<Dialog>(null);

  // form fields
  const [name, setName] = useState('');
  const [typeLabel, setTypeLabel] = useState('');
  const [moveTarget, setMoveTarget] = useState<string>('');
  const [busy, setBusy] = useState(false);

  async function refresh() {
    try {
      setTree(await api.listLocations());
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Unable to load locations.');
    }
  }

  useEffect(() => {
    refresh();
  }, []);

  function openCreate(parent: LocationNode | null) {
    setName('');
    setTypeLabel('');
    setError(null);
    setNotice(null);
    setDialog({ kind: 'create', parent });
  }
  function openRename(node: LocationNode) {
    setName(node.name);
    setTypeLabel(node.type_label ?? '');
    setError(null);
    setNotice(null);
    setDialog({ kind: 'rename', node });
  }
  function openMove(node: LocationNode) {
    setMoveTarget('');
    setError(null);
    setNotice(null);
    setDialog({ kind: 'move', node });
  }

  const moveOptions = useMemo(
    () => (dialog?.kind === 'move' ? flattenForSelect(tree, dialog.node.id) : []),
    [dialog, tree],
  );

  async function submit(e: FormEvent) {
    e.preventDefault();
    if (!dialog) return;
    setBusy(true);
    setError(null);
    try {
      if (dialog.kind === 'create') {
        await api.createLocation(name, dialog.parent?.id ?? null, typeLabel || null);
        // Reveal the new child by expanding its parent.
        if (dialog.parent) {
          setExpanded((prev) => new Set(prev).add(dialog.parent!.id));
        }
        setNotice(`Added "${name}".`);
      } else if (dialog.kind === 'rename') {
        await api.updateLocation(dialog.node.id, { name, type_label: typeLabel || null });
        setNotice('Location updated.');
      } else if (dialog.kind === 'move') {
        await api.moveLocation(dialog.node.id, moveTarget || null);
        setNotice('Location moved.');
      } else if (dialog.kind === 'delete') {
        await api.deleteLocation(dialog.node.id);
        setNotice('Location deleted.');
      }
      setDialog(null);
      await refresh();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Something went wrong.');
    } finally {
      setBusy(false);
    }
  }

  return (
    <AppLayout>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
        <Typography variant="h5" component="h1" sx={{ flexGrow: 1 }}>
          Locations
        </Typography>
        <Button variant="contained" startIcon={<AddIcon />} onClick={() => openCreate(null)}>
          Add location
        </Button>
      </Box>

      {error && !dialog && (
        <Alert severity="error" sx={{ mb: 2 }} role="alert">
          {error}
        </Alert>
      )}
      {notice && (
        <Alert severity="success" sx={{ mb: 2 }}>
          {notice}
        </Alert>
      )}

      <Paper elevation={0} sx={{ border: '1px solid', borderColor: 'divider', p: 1 }}>
        <LocationTree
          nodes={tree}
          expanded={expanded}
          onExpandedChange={setExpanded}
          onAddChild={openCreate}
          onRename={openRename}
          onMove={openMove}
          onDelete={(node) => setDialog({ kind: 'delete', node })}
        />
      </Paper>

      {/* Create / Rename dialog */}
      <Dialog open={dialog?.kind === 'create' || dialog?.kind === 'rename'} onClose={() => setDialog(null)}>
        <DialogTitle>
          {dialog?.kind === 'create'
            ? dialog.parent
              ? `Add sub-location under "${dialog.parent.name}"`
              : 'Add location'
            : 'Rename location'}
        </DialogTitle>
        <Box component="form" onSubmit={submit}>
          <DialogContent>
            {error && (
              <Alert severity="error" sx={{ mb: 2 }} role="alert">
                {error}
              </Alert>
            )}
            <TextField
              label="Name"
              fullWidth
              required
              margin="normal"
              value={name}
              onChange={(e) => setName(e.target.value)}
              autoFocus
            />
            <TextField
              label="Type label (optional)"
              fullWidth
              margin="normal"
              value={typeLabel}
              onChange={(e) => setTypeLabel(e.target.value)}
              helperText="e.g., Room, Shelf, Row — or anything you like."
            />
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setDialog(null)}>Cancel</Button>
            <Button type="submit" variant="contained" disabled={busy}>
              {busy ? 'Saving…' : 'Save'}
            </Button>
          </DialogActions>
        </Box>
      </Dialog>

      {/* Move dialog */}
      <Dialog open={dialog?.kind === 'move'} onClose={() => setDialog(null)}>
        <DialogTitle>Move "{dialog?.kind === 'move' ? dialog.node.name : ''}"</DialogTitle>
        <Box component="form" onSubmit={submit}>
          <DialogContent sx={{ minWidth: 360 }}>
            {error && (
              <Alert severity="error" sx={{ mb: 2 }} role="alert">
                {error}
              </Alert>
            )}
            <TextField
              select
              label="New parent"
              fullWidth
              margin="normal"
              value={moveTarget}
              onChange={(e) => setMoveTarget(e.target.value)}
            >
              <MenuItem value="">(Top level / root)</MenuItem>
              {moveOptions.map((o) => (
                <MenuItem key={o.id} value={o.id}>
                  {o.label}
                </MenuItem>
              ))}
            </TextField>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setDialog(null)}>Cancel</Button>
            <Button type="submit" variant="contained" disabled={busy}>
              {busy ? 'Moving…' : 'Move'}
            </Button>
          </DialogActions>
        </Box>
      </Dialog>

      {/* Delete confirmation */}
      <Dialog open={dialog?.kind === 'delete'} onClose={() => setDialog(null)}>
        <DialogTitle>Delete location</DialogTitle>
        <DialogContent>
          {error && (
            <Alert severity="error" sx={{ mb: 2 }} role="alert">
              {error}
            </Alert>
          )}
          <DialogContentText>
            Delete "{dialog?.kind === 'delete' ? dialog.node.name : ''}"? A location can only be
            deleted when it has no sub-locations and no items.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialog(null)}>Cancel</Button>
          <Button color="error" variant="contained" onClick={submit} disabled={busy}>
            {busy ? 'Deleting…' : 'Delete'}
          </Button>
        </DialogActions>
      </Dialog>
    </AppLayout>
  );
}
