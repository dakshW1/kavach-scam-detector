import { useEffect, useRef, useState } from 'react';
import { AnimatePresence, motion } from 'motion/react';
import { PAGES } from '../App.jsx';

export function Logo() {
  return (
    <svg viewBox="0 0 64 64" aria-hidden="true">
      <path d="M32 4 8 13v17c0 15 10 26 24 30 14-4 24-15 24-30V13L32 4z" fill="#141414" />
      <path d="M22 32l7 7 13-14" stroke="#8fcba8" strokeWidth="5" fill="none" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export default function Nav({ page, go, privacy }) {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);
  useEffect(() => {
    const close = e => { if (ref.current && !ref.current.contains(e.target)) setOpen(false); };
    document.addEventListener('pointerdown', close);
    return () => document.removeEventListener('pointerdown', close);
  }, []);
  const blocked = privacy?.guard;

  return (
    <nav className="nav">
      <a className="brand" href="#/check" onClick={e => { e.preventDefault(); go('check'); }}>
        <Logo /> Kavach
      </a>
      <div className="nav-links">
        {PAGES.map(p => (
          <button key={p.id} className={`nav-link ${page === p.id ? 'active' : ''}`} onClick={() => go(p.id)}>
            {page === p.id && <motion.span layoutId="nav-pill" className="pill-bg" transition={{ type: 'spring', stiffness: 420, damping: 34 }} />}
            {p.label}
          </button>
        ))}
      </div>
      <div ref={ref} style={{ position: 'relative' }}>
        <button className="privacy-pill" onClick={() => setOpen(o => !o)} aria-expanded={open}>
          <span className={`dot ${blocked === false ? 'off' : ''}`} />
          {blocked === false ? 'Guard off' : 'Offline · internet blocked'}
        </button>
        <AnimatePresence>
          {open && (
            <motion.div className="privacy-pop" initial={{ opacity: 0, y: -6, scale: 0.97 }} animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -6, scale: 0.97 }} transition={{ duration: 0.2 }}>
              <div className="item"><span>{blocked ? '🟢' : '🔴'}</span><div><b>Internet {blocked ? 'blocked' : 'NOT blocked'}</b>
                <small>Live check just now · {privacy?.blocked ?? 0} attempt(s) blocked this session</small></div></div>
              <div className="item"><span>{privacy?.diary ? '🟡' : '⚪'}</span><div><b>Scam Diary {privacy?.diary ? 'on' : 'off'}</b>
                <small>{privacy?.diary ? 'Masked entries, only on this computer' : 'Nothing is saved'}</small></div></div>
              <div className="item"><span>{privacy?.intel_used ? '🟡' : '⚪'}</span><div><b>News search {privacy?.intel_used ? 'used' : 'not used'}</b>
                <small>{privacy?.intel_used ? 'Only scam type + brand were sent' : 'Runs only when you click it'}</small></div></div>
              <div className="item"><span>💻</span><div><b>Messages never leave this laptop</b><small>Model, fonts and code are all local files</small></div></div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </nav>
  );
}
