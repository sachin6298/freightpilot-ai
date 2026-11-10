import { Moon, Sun } from 'lucide-react';
import { useTheme } from './ThemeProvider';

export function ThemeToggleButton({ compact = false }: { compact?: boolean }) {
  const { resolvedTheme, setTheme } = useTheme();
  const dark = resolvedTheme === 'dark';
  return (
    <button
      type="button"
      className={`fpw-theme-toggle${compact ? ' is-compact' : ''}`}
      onClick={() => setTheme(dark ? 'light' : 'dark')}
      aria-label={`Switch to ${dark ? 'light' : 'dark'} mode`}
      title={`Switch to ${dark ? 'light' : 'dark'} mode`}
    >
      {dark ? <Sun size={17} /> : <Moon size={17} />}
      {!compact && <span>{dark ? 'Light mode' : 'Dark mode'}</span>}
    </button>
  );
}
