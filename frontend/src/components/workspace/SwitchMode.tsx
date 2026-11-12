import { useEffect, useState, type FC } from 'react';
import { motion } from 'motion/react';
import { IoMoonOutline, IoSunnyOutline } from 'react-icons/io5';
import { useTheme } from './ThemeProvider';

export interface SwitchModeProps {
  width?: number;
  height?: number;
  darkColor?: string;
  lightColor?: string;
  knobDarkColor?: string;
  knobLightColor?: string;
  borderDarkColor?: string;
  borderLightColor?: string;
  compact?: boolean;
}

export const SwitchMode: FC<SwitchModeProps> = ({
  width = 84,
  height = 38,
  darkColor = '#18343A',
  lightColor = '#E8F2F1',
  knobDarkColor = '#31565B',
  knobLightColor = '#FFFFFF',
  borderDarkColor = '#45666B',
  borderLightColor = '#BFD4D3',
  compact = false,
}) => {
  const [mounted, setMounted] = useState(false);
  const { resolvedTheme, setTheme } = useTheme();
  const isDark = resolvedTheme === 'dark';
  const knobSize = Math.max(22, height - 8);
  const travel = width - height;

  useEffect(() => setMounted(true), []);

  if (!mounted) {
    return <span className="fp-mode-switch-placeholder" style={{ width, height }} aria-hidden="true" />;
  }

  return (
    <motion.button
      type="button"
      className={`fp-mode-switch${compact ? ' is-compact' : ''}`}
      style={{ width, height, borderColor: isDark ? borderDarkColor : borderLightColor, backgroundColor: isDark ? darkColor : lightColor }}
      onClick={() => setTheme(isDark ? 'light' : 'dark')}
      whileTap={{ scale: 0.94 }}
      aria-label={`Switch to ${isDark ? 'light' : 'dark'} mode`}
      aria-pressed={isDark}
      title={`Switch to ${isDark ? 'light' : 'dark'} mode`}
    >
      <span className={`fp-mode-switch-icon sun${!isDark ? ' active' : ''}`} style={{ width: height, height }}>
        <IoSunnyOutline size={Math.round(height * 0.43)} />
      </span>
      <span className={`fp-mode-switch-icon moon${isDark ? ' active' : ''}`} style={{ width: height, height }}>
        <IoMoonOutline size={Math.round(height * 0.43)} />
      </span>
      <motion.span
        className="fp-mode-switch-knob"
        style={{ width: knobSize, height: knobSize, backgroundColor: isDark ? knobDarkColor : knobLightColor, borderColor: isDark ? borderDarkColor : borderLightColor }}
        animate={{ x: isDark ? travel : 0 }}
        transition={{ type: 'spring', stiffness: 320, damping: 25 }}
      />
    </motion.button>
  );
};
