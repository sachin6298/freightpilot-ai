import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';

export type Theme = 'light' | 'dark' | 'system';
type ThemeContextValue = { theme: Theme; resolvedTheme: 'light' | 'dark'; setTheme: (theme: Theme) => void };
const ThemeContext = createContext<ThemeContextValue | null>(null);
const STORAGE_KEY = 'freightpilot-theme';

/** Light theme is intentionally locked while the current UI design is being finalized. */
export function ThemeProvider({ children }: { children: ReactNode; defaultTheme?: Theme }) {
  const [theme, setThemeState] = useState<Theme>('light');
  const setTheme = useCallback((_next: Theme) => {
    window.localStorage.setItem(STORAGE_KEY, 'light');
    setThemeState('light');
  }, []);
  useEffect(() => {
    document.documentElement.classList.remove('dark', 'system');
    document.documentElement.classList.add('light');
    document.documentElement.dataset.theme = 'light';
    window.localStorage.setItem(STORAGE_KEY, 'light');
  }, []);
  const value = useMemo(() => ({ theme, resolvedTheme: 'light' as const, setTheme }), [theme, setTheme]);
  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) throw new Error('useTheme must be used inside ThemeProvider');
  return context;
}
