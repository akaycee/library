import { createTheme, type Theme } from '@mui/material/styles';

// A refined, accessible Material Design theme with light and dark modes. Uses a
// local system font stack (no external font downloads — the app stays fully
// offline/local) and a calm, high-contrast palette suited to a small library
// used by non-technical staff.
const FONT_STACK = [
  '"Segoe UI"',
  '-apple-system',
  'BlinkMacSystemFont',
  'Roboto',
  '"Helvetica Neue"',
  'Arial',
  'sans-serif',
].join(',');

const PRIMARY = '#1d4ed8'; // indigo
const SECONDARY = '#0f766e'; // teal

export type ColorMode = 'light' | 'dark';

export function makeTheme(mode: ColorMode): Theme {
  const isDark = mode === 'dark';
  return createTheme({
    palette: {
      mode,
      primary: { main: isDark ? '#60a5fa' : PRIMARY },
      secondary: { main: isDark ? '#2dd4bf' : SECONDARY },
      background: {
        default: isDark ? '#0f1420' : '#f4f6fb',
        paper: isDark ? '#161d2b' : '#ffffff',
      },
      success: { main: isDark ? '#4ade80' : '#15803d' },
      text: isDark
        ? { primary: '#e6ebf5', secondary: '#9aa5b8' }
        : { primary: '#1a2233', secondary: '#5b6472' },
    },
    shape: { borderRadius: 12 },
    typography: {
      fontFamily: FONT_STACK,
      fontSize: 15,
      h1: { fontWeight: 700 },
      h4: { fontWeight: 700, letterSpacing: '-0.5px' },
      h5: { fontWeight: 700, letterSpacing: '-0.3px' },
      h6: { fontWeight: 600 },
      button: { textTransform: 'none', fontWeight: 600 },
    },
    components: {
      MuiButton: {
        defaultProps: { disableElevation: true },
        styleOverrides: {
          root: { borderRadius: 10, paddingInline: 18 },
          sizeLarge: { paddingBlock: 10 },
        },
      },
      MuiPaper: {
        styleOverrides: {
          rounded: { borderRadius: 16 },
        },
      },
      MuiAppBar: {
        styleOverrides: {
          root: {
            // Solid dark bar (no gradient) so white nav text is deterministically
            // AA-contrast and axe can evaluate it reliably.
            backgroundColor: '#143a9e',
            backgroundImage: 'none',
          },
        },
      },
      MuiCard: {
        styleOverrides: {
          root: {
            borderRadius: 16,
            border: `1px solid ${isDark ? '#243044' : '#e6e9f0'}`,
          },
        },
      },
      MuiTableHead: {
        styleOverrides: {
          root: { backgroundColor: isDark ? '#1b2536' : '#f7f9fc' },
        },
      },
    },
  });
}

// Default light theme (kept for any direct import).
export const theme = makeTheme('light');
