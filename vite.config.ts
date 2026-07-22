import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig(({ mode }) => ({
  plugins: [react()],
  // GitHub Pages serves the site under /<repo>/; local dev stays at /.
  base: mode === 'production' ? '/word_game/' : '/',
}));
