import { useEffect, useRef, useState } from 'react';
import { AnimatePresence, motion } from 'motion/react';
import { PAGES } from '../App.jsx';
import ThemeToggle from './ThemeToggle.jsx';
import { useLang } from '../i18n.js';

export function Logo() {
  return (
    <svg viewBox="0 0 64 64" aria-hidden="true">
      <path d="M32 4 8 13v17c0 15 10 26 24 30 14-4 24-15 24-30V13L32 4z" fill="currentColor" />
      <path d="M22 32l7 7 13-14" stroke="#8fcba8" strokeWidth="5" fill="none" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function useClickOutside(ref, close) {
  useEffect(() => {
    const h = e => { if (ref.current && !ref.current.contains(e.target)) close(); };
    document.addEventListener('pointerdown', h);
    return () => document.removeEventListener('pointerdown', h);
  }, [ref, close]);
}

export default function Nav({ page, go, privacy }) {
  const [open, setOpen] = useState(false);
  const [more, setMore] = useState(false);
  const ref = useRef(null);
  const moreRef = useRef(null);
  useClickOutside(ref, () => setOpen(false));
  useClickOutside(moreRef, () => setMore(false));
  const blocked = privacy?.guard;
  const { lang, setLang } = useLang();
  const main = PAGES.filter(p => p.main);
  const extra = PAGES.filter(p => !p.main);
  const inExtra = extra.some(p => p.id === page);

  return (
    <nav className="nav">
      <a className="brand" href="#/check" onClick={e => { e.preventDefault(); go('check'); }}>
        <Logo /> Kavach
      </a>
      <div className="nav-links">
        {main.map(p => (
          <button key={p.id} className={`nav-link ${page === p.id ? 'active' : ''}`} onClick={() => go(p.id)}>
            {page === p.id && <motion.span layoutId="nav-pill" className="pill-bg" transition={{ type: 'spring', stiffness: 420, damping: 34 }} />}
            {p.label}
          </button>
        ))}
        <div ref={moreRef} style={{ position: 'relative' }}>
          <button className={`nav-link ${inExtra ? 'active' : ''}`} onClick={() => setMore(m => !m)} aria-expanded={more}>
            {inExtra && <motion.span layoutId="nav-pill" className="pill-bg" transition={{ type: 'spring', stiffness: 420, damping: 34 }} />}
            {inExtra ? extra.find(p => p.id === page).label : 'More'} <span className={`caret ${more ? 'open' : ''}`} aria-hidden="true">▾</span>
          </button>
          <AnimatePresence>
            {more && (
              <motion.div className="more-menu" initial={{ opacity: 0, y: -6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -6 }} transition={{ duration: 0.18 }}>
                {extra.map(p => (
                  <button key={p.id} onClick={() => { setMore(false); go(p.id); }} className={page === p.id ? 'on' : ''}>
                    <b>{p.label}</b><small>{p.hint}</small>
                  </button>
                ))}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
      <button className="lang-toggle" aria-pressed={lang === 'hi'} onClick={() => setLang(lang === 'hi' ? 'en' : 'hi')} aria-label={lang === 'hi' ? 'Switch to English' : 'हिंदी में देखें'}>
        {lang === 'hi' ? 'English' : 'हिंदी'}
      </button>
      <ThemeToggle />
      <div ref={ref} style={{ position: 'relative' }}>
        <button className="privacy-pill" onClick={() => setOpen(o => !o)} aria-expanded={open}>
          <span className={`dot ${blocked === false ? 'off' : ''}`} />
          {blocked === false ? 'Guard off' : 'Offline'}
        </button>
        <AnimatePresence>
          {open && (
            <motion.div className="privacy-pop" initial={{ opacity: 0, y: -6, scale: 0.97 }} animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -6, scale: 0.97 }} transition={{ duration: 0.2 }}>
              <div className="item"><span>{blocked ? '🟢' : '🔴'}</span><div><b>Internet {blocked ? 'blocked for checking' : 'NOT blocked'}</b>
                <small>Live check just now · {privacy?.blocked ?? 0} attempt(s) blocked this session</small></div></div>
              <div className="item"><span>{privacy?.diary ? '🟡' : '⚪'}</span><div><b>Scam Diary {privacy?.diary ? 'on' : 'off'}</b>
                <small>{privacy?.diary ? 'Masked entries, only on this computer' : 'Nothing is saved'}</small></div></div>
              <div className="item"><span>{privacy?.intel_used ? '🟡' : '⚪'}</span><div><b>Optional news search {privacy?.intel_used ? 'was used' : 'not used'}</b>
                <small>{privacy?.intel_used ? 'Only the scam type + brand were sent, never your message' : 'Runs only if you click it'}</small></div></div>
              <div className="item"><span>💻</span><div><b>Messages never leave this laptop</b><small>Model, fonts and code are all local files</small></div></div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </nav>
  );
}
