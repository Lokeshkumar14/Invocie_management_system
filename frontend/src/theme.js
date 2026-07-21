import { createTheme } from '@mui/material/styles';

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#2563eb', // Modern Electric Indigo
      light: '#60a5fa',
      dark: '#1d4ed8',
      contrastText: '#ffffff',
    },
    secondary: {
      main: '#0d9488', // Premium Teal
      light: '#2dd4bf',
      dark: '#0f766e',
      contrastText: '#ffffff',
    },
    background: {
      default: '#f8fafc', // Slate background for neat SaaS dashboard
      paper: '#ffffff',
    },
    text: {
      primary: '#0f172a', // Slate 900
      secondary: '#475569', // Slate 600
    },
    divider: '#e2e8f0',
  },
  typography: {
    fontFamily: '"Inter", "Helvetica", "Arial", sans-serif',
    h1: {
      fontFamily: '"Outfit", "Inter", sans-serif',
      fontWeight: 700,
    },
    h2: {
      fontFamily: '"Outfit", "Inter", sans-serif',
      fontWeight: 700,
    },
    h3: {
      fontFamily: '"Outfit", "Inter", sans-serif',
      fontWeight: 600,
    },
    h4: {
      fontFamily: '"Outfit", "Inter", sans-serif',
      fontWeight: 600,
    },
    h5: {
      fontFamily: '"Outfit", "Inter", sans-serif',
      fontWeight: 600,
    },
    h6: {
      fontFamily: '"Outfit", "Inter", sans-serif',
      fontWeight: 600,
      fontSize: '1.1rem',
    },
    subtitle1: {
      fontFamily: '"Outfit", "Inter", sans-serif',
      fontWeight: 500,
    },
    button: {
      textTransform: 'none', // No all-caps buttons for modern look
      fontWeight: 600,
    },
  },
  shape: {
    borderRadius: 12, // Smooth, modern cards and inputs
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          padding: '8px 16px',
          boxShadow: 'none',
          '&:hover': {
            boxShadow: '0px 4px 12px rgba(37, 99, 235, 0.15)',
          },
        },
        containedSecondary: {
          '&:hover': {
            boxShadow: '0px 4px 12px rgba(13, 148, 136, 0.15)',
          },
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 16,
          boxShadow: '0px 1px 3px rgba(15, 23, 42, 0.03), 0px 4px 16px rgba(15, 23, 42, 0.05)',
          border: '1px solid #f1f5f9',
        },
      },
    },
    MuiTextField: {
      defaultProps: {
        size: 'small',
      },
    },
    MuiSelect: {
      defaultProps: {
        size: 'small',
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundColor: 'rgba(255, 255, 255, 0.8)',
          color: '#0f172a',
          backdropFilter: 'blur(8px)',
          borderBottom: '1px solid #e2e8f0',
          boxShadow: 'none',
        },
      },
    },
    MuiTableContainer: {
      styleOverrides: {
        root: {
          maxWidth: '100%',
          overflowX: 'auto',
          WebkitOverflowScrolling: 'touch',
        },
      },
    },
    MuiDialog: {
      styleOverrides: {
        paper: {
          margin: 12,
          width: 'calc(100% - 24px)',
        },
      },
    },
  },
});

export default theme;
