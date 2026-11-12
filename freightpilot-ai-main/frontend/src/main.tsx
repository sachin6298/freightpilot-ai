import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import './index.css';
import './ui.css';
import './components/workspace/freight-workspace.css';
import './components/workspace/freightpilot-refinement.css';
import App from './App';
import { ThemeProvider } from './components/workspace/ThemeProvider';

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <ThemeProvider defaultTheme="light">
      <App />
    </ThemeProvider>
  </StrictMode>,
);
