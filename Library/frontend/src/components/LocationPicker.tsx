import { useEffect, useState } from 'react';
import { MenuItem, TextField } from '@mui/material';
import { api, type LocationNode } from '../services/api';

interface Option {
  id: string;
  label: string;
}

function flatten(nodes: LocationNode[], level = 0, out: Option[] = []): Option[] {
  for (const n of nodes) {
    out.push({ id: n.id, label: `${'\u00A0\u00A0'.repeat(level)}${n.name}` });
    flatten(n.children, level + 1, out);
  }
  return out;
}

/** A select populated from the location tree (flattened with indentation). */
export default function LocationPicker({
  value,
  onChange,
  label = 'Location',
  required,
}: {
  value: string;
  onChange: (id: string) => void;
  label?: string;
  required?: boolean;
}) {
  const [options, setOptions] = useState<Option[]>([]);

  useEffect(() => {
    api.listLocations().then((tree) => setOptions(flatten(tree)));
  }, []);

  return (
    <TextField
      select
      label={label}
      fullWidth
      required={required}
      margin="normal"
      value={value}
      onChange={(e) => onChange(e.target.value)}
      helperText={options.length === 0 ? 'Create a location first (Locations page).' : undefined}
    >
      {options.map((o) => (
        <MenuItem key={o.id} value={o.id}>
          {o.label}
        </MenuItem>
      ))}
    </TextField>
  );
}
