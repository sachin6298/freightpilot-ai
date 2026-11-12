import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';

export type Theme = 'light' | 'dark';
type ThemeContextValue = {
  theme: Theme;
  resolvedTheme: Theme;
  setTheme: (theme: Theme) => void;
};

const ThemeContext = createContext<ThemeContextValue | null>(null);
const STORAGE_KEY = 'freightpilot-theme';

function readInitialTheme(defaultTheme: Theme): Theme {
  if (typeof window === 'undefined') return defaultTheme;
  try {
    const stored = window.localStorage.getItem(STORAGE_KEY);
    return stored === 'dark' ? 'dark' : stored === 'light' ? 'light' : defaultTheme;
  } catch {
    return defaultTheme;
  }
}

/** Theme defaults to light; the header/sidebar switch can opt into dark mode. */
export function ThemeProvider({ children, defaultTheme = 'light' }: { children: ReactNode; defaultTheme?: Theme }) {
  const [theme, setThemeState] = useState<Theme>(() => readInitialTheme(defaultTheme));
  const setTheme = useCallback((nextTheme: Theme) => setThemeState(nextTheme), []);

  useEffect(() => {
    const root = document.documentElement;
    root.classList.toggle('dark', theme === 'dark');
    root.classList.toggle('light', theme === 'light');
    root.dataset.theme = theme;
    root.style.colorScheme = theme;
    try { window.localStorage.setItem(STORAGE_KEY, theme); } catch { /* storage may be unavailable */ }
  }, [theme]);

  const value = useMemo(() => ({ theme, resolvedTheme: theme, setTheme }), [theme, setTheme]);
  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) throw new Error('useTheme must be used inside ThemeProvider');
  return context;
}
