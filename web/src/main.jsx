import React from 'react';
import { createRoot } from 'react-dom/client';

// Fonts are bundled from npm (@fontsource), so nothing is fetched from Google Fonts: the site works offline.
import '@fontsource/bricolage-grotesque/500.css';
import '@fontsource/bricolage-grotesque/700.css';
import '@fontsource/bricolage-grotesque/800.css';
import '@fontsource/manrope/400.css';
import '@fontsource/manrope/500.css';
import '@fontsource/manrope/600.css';
import '@fontsource/manrope/700.css';
import '@fontsource/manrope/800.css';
import '@fontsource/instrument-serif/400.css';
import '@fontsource/instrument-serif/400-italic.css';
import '@fontsource/noto-sans-devanagari/400.css';
import '@fontsource/noto-sans-devanagari/600.css';
import 'lenis/dist/lenis.css';
import './styles.css';

import App from './App.jsx';

createRoot(document.getElementById('root')).render(<App />);
