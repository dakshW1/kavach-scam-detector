import { useCallback, useEffect, useRef, useState } from 'react';
import { AnimatePresence, MotionConfig, motion } from 'motion/react';
import Lenis from 'lenis';
import { gsap } from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';

import Nav from './components/Nav.jsx';
import Footer from './components/Footer.jsx';
import Check from './pages/Check.jsx';
import Diary from './pages/Diary.jsx';
import Library from './pages/Library.jsx';
import Fool from './pages/Fool.jsx';
import Batch from './pages/Batch.jsx';
import Results from './pages/Results.jsx';
import { api } from './api.js';
import { LangContext } from './i18n.js';

gsap.registerPlugin(ScrollTrigger);

// main = always visible in the nav; the rest sit under "More"
export const PAGES = [
  { id: 'check', label: 'Check', comp: Check, main: true },
  { id: 'library', label: 'Scam Library', comp: Library, main: true },
  { id: 'diary', label: 'My Scam Diary', comp: Diary, main: true },
  { id: 'fool', label: 'Try to fool it', comp: Fool, hint: 'See how disguised scams are still caught' },
  { id: 'batch', label: 'Check many messages', comp: Batch, hint: 'Upload a list or SMS backup' },
  { id: 'results', label: 'How accurate is it?', comp: Results, hint: 'Test results and privacy proof' },
];

const pageFromHash = () => {
  const id = window.location.hash.replace('#/', '');
  return PAGES.some(p => p.id === id) ? id : 'check';
};

export let lenis = null;

export default function App() {
  const [page, setPage] = useState(pageFromHash);
  const [privacy, setPrivacy] = useState(null);
  const [lang, setLangState] = useState(() => { try { return localStorage.getItem('kavach-lang') || 'en'; } catch { return 'en'; } });
  useEffect(() => { document.documentElement.lang = lang === 'hi' ? 'hi' : 'en'; }, [lang]);
  const setLang = l => { setLangState(l); try { localStorage.setItem('kavach-lang', l); } catch { /* ok */ } document.documentElement.lang = l === 'hi' ? 'hi' : 'en'; };
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
    };
    window.addEventListener('hashchange', onHash);
    return () => window.removeEventListener('hashchange', onHash);
  }, []);

  const go = id => {
    if (id === page) return;
    window.location.hash = `#/${id}`;
  };

  // jump to the top only once the old page has faded out (no visible jump), then re-measure scroll reveals
  const onPageSwap = () => {
    if (lenisRef.current) lenisRef.current.scrollTo(0, { immediate: true }); else window.scrollTo(0, 0);
    ScrollTrigger.refresh();
  };

  const Page = PAGES.find(p => p.id === page).comp;
  return (
    <LangContext.Provider value={{ lang, setLang }}>
     <MotionConfig reducedMotion="user">
      <Nav page={page} go={go} privacy={privacy} />
      <AnimatePresence mode="wait" onExitComplete={onPageSwap}>
        <motion.main
          key={page}
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0, transitionEnd: { transform: 'none' } }}
          exit={{ opacity: 0, transition: { duration: 0.18, ease: [0.4, 0, 1, 1] } }}
          transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
        >
          <Page go={go} onChange={refreshPrivacy} />
        </motion.main>
      </AnimatePresence>
      <Footer go={go} />
     </MotionConfig>
    </LangContext.Provider>
  );
}
