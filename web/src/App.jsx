import { useCallback, useEffect, useRef, useState } from 'react';
import { AnimatePresence, motion } from 'motion/react';
import Lenis from 'lenis';
import { gsap } from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';

import ClickSpark from './reactbits/ClickSpark.jsx';
import Nav from './components/Nav.jsx';
import Footer from './components/Footer.jsx';
import Check from './pages/Check.jsx';
import Diary from './pages/Diary.jsx';
import Library from './pages/Library.jsx';
import Fool from './pages/Fool.jsx';
import Batch from './pages/Batch.jsx';
import Results from './pages/Results.jsx';
import { api } from './api.js';

gsap.registerPlugin(ScrollTrigger);

export const PAGES = [
  { id: 'check', label: 'Check', comp: Check },
  { id: 'diary', label: 'Scam Diary', comp: Diary },
  { id: 'library', label: 'Library', comp: Library },
  { id: 'fool', label: 'Try to fool it', comp: Fool },
  { id: 'batch', label: 'Batch', comp: Batch },
  { id: 'results', label: 'Results & privacy', comp: Results },
];

const pageFromHash = () => {
  const id = window.location.hash.replace('#/', '');
  return PAGES.some(p => p.id === id) ? id : 'check';
};

export let lenis = null;

export default function App() {
  const [page, setPage] = useState(pageFromHash);
  const [privacy, setPrivacy] = useState(null);
  const lenisRef = useRef(null);

  // Lenis smooth scrolling, driven by GSAP's ticker so ScrollTrigger animations stay in sync.
  useEffect(() => {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return undefined;
    const l = new Lenis({ duration: 1.15, easing: t => Math.min(1, 1.001 - Math.pow(2, -10 * t)), smoothWheel: true });
    lenis = l;
    lenisRef.current = l;
    l.on('scroll', ScrollTrigger.update);
    const tick = time => l.raf(time * 1000);
    gsap.ticker.add(tick);
    gsap.ticker.lagSmoothing(0);
    return () => { gsap.ticker.remove(tick); l.destroy(); lenis = null; };
  }, []);

  const refreshPrivacy = useCallback(() => { api.privacy().then(setPrivacy).catch(() => setPrivacy(null)); }, []);
  useEffect(() => { refreshPrivacy(); const t = setInterval(refreshPrivacy, 15000); return () => clearInterval(t); }, [refreshPrivacy]);

  useEffect(() => {
    const onHash = () => {
      setPage(pageFromHash());
      if (lenisRef.current) lenisRef.current.scrollTo(0, { immediate: true });
      else window.scrollTo(0, 0);
    };
    window.addEventListener('hashchange', onHash);
    return () => window.removeEventListener('hashchange', onHash);
  }, []);

  const go = id => {
    if (id === page) return;
    window.location.hash = `#/${id}`;
    if (lenisRef.current) lenisRef.current.scrollTo(0, { immediate: true });
    else window.scrollTo(0, 0);
  };

  useEffect(() => { setTimeout(() => ScrollTrigger.refresh(), 600); }, [page]);

  const Page = PAGES.find(p => p.id === page).comp;
  return (
    <ClickSpark sparkColor="#8fcba8" sparkSize={9} sparkRadius={22} sparkCount={8} duration={420}>
      <Nav page={page} go={go} privacy={privacy} />
      <AnimatePresence mode="wait">
        <motion.main
          key={page}
          initial={{ opacity: 0, y: 24, filter: 'blur(6px)' }}
          animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
          exit={{ opacity: 0, y: -12, filter: 'blur(4px)' }}
          transition={{ duration: 0.45, ease: [0.22, 1, 0.36, 1] }}
        >
          <Page go={go} onChange={refreshPrivacy} />
        </motion.main>
      </AnimatePresence>
      <Footer go={go} />
    </ClickSpark>
  );
}
