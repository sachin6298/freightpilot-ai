import { SwitchMode } from './SwitchMode';

export function ThemeToggleButton({ compact = false }: { compact?: boolean }) {
  return (
    <div className={`fpw-theme-toggle${compact ? ' is-compact' : ''}`} aria-label="Appearance settings">
      <SwitchMode width={compact ? 68 : 84} height={compact ? 32 : 38} compact={compact} />
      {!compact && <span>Appearance</span>}
    </div>
  );
}
