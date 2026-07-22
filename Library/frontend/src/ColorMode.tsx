import { createContext, useContext, useMemo, useState, type ReactNode } from 'react';
import { CssBaseline, ThemeProvider } from '@mui/material';
import { makeTheme, type ColorMode } from './theme';

interface ColorModeState {
  mode: ColorMode;
  toggle: () => void;
}

const ColorModeContext = createContext<ColorModeState | undefined>(undefined);

const STORAGE_KEY = 'library.colorMode';

function initialMode(): ColorMode {
  const stored = typeof localStorage !== 'undefined' ? localStorage.getItem(STORAGE_KEY) : null;
  if (stored === 'light' || stored === 'dark') return stored;
  return 'light';
}

/** Provides the light/dark theme, a toggle, and MUI's ThemeProvider + CssBaseline. */
export function ColorModeProvider({ children }: { children: ReactNode }) {
  const [mode, setMode] = useState<ColorMode>(initialMode);

  const value = useMemo<ColorModeState>(
    () => ({
      mode,
      toggle: () =>
        setMode((prev) => {
          const next = prev === 'light' ? 'dark' : 'light';
          try {
            localStorage.setItem(STORAGE_KEY, next);
          } catch {
            /* ignore persistence errors */
          }
          return next;
        }),
    }),
    [mode],
  );

  const theme = useMemo(() => makeTheme(mode), [mode]);

  return (
    <ColorModeContext.Provider value={value}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        {children}
      </ThemeProvider>
    </ColorModeContext.Provider>
  );
}

export function useColorMode(): ColorModeState {
  const ctx = useContext(ColorModeContext);
  if (!ctx) throw new Error('useColorMode must be used within ColorModeProvider');
  return ctx;
}
