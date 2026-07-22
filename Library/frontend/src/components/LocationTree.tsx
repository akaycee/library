import { useMemo, useRef, useState, type KeyboardEvent } from 'react';
import { Box, Chip, IconButton, Tooltip, Typography } from '@mui/material';
import ChevronRightIcon from '@mui/icons-material/ChevronRight';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import AddIcon from '@mui/icons-material/Add';
import EditIcon from '@mui/icons-material/Edit';
import DriveFileMoveIcon from '@mui/icons-material/DriveFileMove';
import DeleteOutlineIcon from '@mui/icons-material/DeleteOutline';
import type { LocationNode } from '../services/api';

interface FlatItem {
  node: LocationNode;
  level: number;
  hasChildren: boolean;
}

function flatten(nodes: LocationNode[], expanded: Set<string>, level = 1, out: FlatItem[] = []) {
  for (const node of nodes) {
    const hasChildren = node.children.length > 0;
    out.push({ node, level, hasChildren });
    if (hasChildren && expanded.has(node.id)) {
      flatten(node.children, expanded, level + 1, out);
    }
  }
  return out;
}

export interface LocationTreeProps {
  nodes: LocationNode[];
  expanded: Set<string>;
  onExpandedChange: (next: Set<string>) => void;
  onAddChild: (parent: LocationNode) => void;
  onRename: (node: LocationNode) => void;
  onMove: (node: LocationNode) => void;
  onDelete: (node: LocationNode) => void;
}

/** Accessible tree with ARIA roles and keyboard navigation (arrow keys). */
export default function LocationTree({
  nodes,
  expanded,
  onExpandedChange,
  onAddChild,
  onRename,
  onMove,
  onDelete,
}: LocationTreeProps) {
  const [focusedId, setFocusedId] = useState<string | null>(nodes[0]?.id ?? null);
  const refs = useRef<Map<string, HTMLDivElement>>(new Map());

  const visible = useMemo(() => flatten(nodes, expanded), [nodes, expanded]);

  function toggle(id: string, open?: boolean) {
    const next = new Set(expanded);
    const shouldOpen = open ?? !next.has(id);
    if (shouldOpen) next.add(id);
    else next.delete(id);
    onExpandedChange(next);
  }

  function focus(id: string | null) {
    if (!id) return;
    setFocusedId(id);
    refs.current.get(id)?.focus();
  }

  function onKeyDown(e: KeyboardEvent, item: FlatItem) {
    const idx = visible.findIndex((v) => v.node.id === item.node.id);
    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        focus(visible[Math.min(idx + 1, visible.length - 1)]?.node.id ?? null);
        break;
      case 'ArrowUp':
        e.preventDefault();
        focus(visible[Math.max(idx - 1, 0)]?.node.id ?? null);
        break;
      case 'ArrowRight':
        e.preventDefault();
        if (item.hasChildren && !expanded.has(item.node.id)) toggle(item.node.id, true);
        else if (item.hasChildren) focus(item.node.children[0]?.id ?? null);
        break;
      case 'ArrowLeft':
        e.preventDefault();
        if (item.hasChildren && expanded.has(item.node.id)) toggle(item.node.id, false);
        else if (item.node.parent_id) focus(item.node.parent_id);
        break;
      case 'Enter':
      case ' ':
        if (item.hasChildren) {
          e.preventDefault();
          toggle(item.node.id);
        }
        break;
      case 'Home':
        e.preventDefault();
        focus(visible[0]?.node.id ?? null);
        break;
      case 'End':
        e.preventDefault();
        focus(visible[visible.length - 1]?.node.id ?? null);
        break;
    }
  }

  if (nodes.length === 0) {
    return (
      <Typography color="text.secondary" sx={{ p: 2 }}>
        No locations yet. Add your first one to get started.
      </Typography>
    );
  }

  return (
    <Box role="tree" aria-label="Locations" sx={{ py: 1 }}>
      {visible.map((item, posInLevel) => {
        const { node, level, hasChildren } = item;
        const isOpen = expanded.has(node.id);
        const isFocused = focusedId === node.id;
        return (
          <Box
            key={node.id}
            role="treeitem"
            aria-level={level}
            aria-expanded={hasChildren ? isOpen : undefined}
            aria-label={node.name}
            tabIndex={isFocused || (focusedId === null && posInLevel === 0) ? 0 : -1}
            ref={(el: HTMLDivElement | null) => {
              if (el) refs.current.set(node.id, el);
              else refs.current.delete(node.id);
            }}
            onFocus={() => setFocusedId(node.id)}
            onKeyDown={(e) => onKeyDown(e, item)}
            sx={{
              display: 'flex',
              alignItems: 'center',
              gap: 1,
              pl: 1 + (level - 1) * 3,
              pr: 1,
              py: 0.75,
              borderRadius: 1,
              outline: 'none',
              '&:hover': { bgcolor: 'action.hover' },
              '&:focus-visible': { boxShadow: (t) => `inset 0 0 0 2px ${t.palette.primary.main}` },
            }}
          >
            {hasChildren ? (
              <IconButton
                size="small"
                aria-label={isOpen ? `Collapse ${node.name}` : `Expand ${node.name}`}
                onClick={() => toggle(node.id)}
                tabIndex={isFocused ? 0 : -1}
              >
                {isOpen ? <ExpandMoreIcon /> : <ChevronRightIcon />}
              </IconButton>
            ) : (
              <Box sx={{ width: 34 }} />
            )}

            <Typography sx={{ fontWeight: 500 }}>{node.name}</Typography>
            {node.type_label && <Chip label={node.type_label} size="small" variant="outlined" />}

            <Box sx={{ flexGrow: 1 }} />

            <Tooltip title="Add sub-location">
              <IconButton size="small" aria-label={`Add sub-location under ${node.name}`} onClick={() => onAddChild(node)} tabIndex={isFocused ? 0 : -1}>
                <AddIcon fontSize="small" />
              </IconButton>
            </Tooltip>
            <Tooltip title="Rename">
              <IconButton size="small" aria-label={`Rename ${node.name}`} onClick={() => onRename(node)} tabIndex={isFocused ? 0 : -1}>
                <EditIcon fontSize="small" />
              </IconButton>
            </Tooltip>
            <Tooltip title="Move">
              <IconButton size="small" aria-label={`Move ${node.name}`} onClick={() => onMove(node)} tabIndex={isFocused ? 0 : -1}>
                <DriveFileMoveIcon fontSize="small" />
              </IconButton>
            </Tooltip>
            <Tooltip title="Delete">
              <IconButton size="small" aria-label={`Delete ${node.name}`} onClick={() => onDelete(node)} tabIndex={isFocused ? 0 : -1}>
                <DeleteOutlineIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          </Box>
        );
      })}
    </Box>
  );
}
