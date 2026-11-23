import { useEffect, useMemo, useState } from 'react';
import { AnimatePresence, motion } from 'motion/react';
import SpotlightCard from '../reactbits/SpotlightCard.jsx';
import Reveal from '../components/Reveal.jsx';
import { md } from '../components/ResultTabs.jsx';
import { api } from '../api.js';

const ORDER = ['KYC/Bank', 'Lottery/Prize', 'Loan/Credit', 'Job/Investment', 'Other'];

export default function Library() {
  const [lib, setLib] = useState(null);
  const [q, setQ] = useState('');
  const [open, setOpen] = useState(null);
  useEffect(() => { api.library().then(setLib); }, []);
  const fams = useMemo(() => {
    if (!lib) return [];
    const ql = q.toLowerCase();
    return Object.entries(lib.families).filter(([k, f]) => k !== 'unknown' &&
      (!ql || (f.title + f.how.join(' ') + f.signs.join(' ') + f.protect.join(' ')).toLowerCase().includes(ql)))
      .sort((a, b) => ORDER.indexOf(a[1].category) - ORDER.indexOf(b[1].category));
  }, [lib, q]);
  if (!lib) return null;
  const sel = open && lib.families[open];

  return (
    <div className="wrap">
      <div className="page-title">
        <div className="kicker">Works with no internet</div>
        <h1>The Scam Library</h1>
        <p>How the common scams in India work, the warning signs, and what to do – from public advice by RBI, cybercrime.gov.in and Sanchar Saathi.</p>
      </div>

      <Reveal>
        <div className="grid-2" style={{ marginTop: 20 }}>
          <div className="night grain" style={{ padding: 28, borderRadius: 24 }}>
            <div style={{ position: 'relative', zIndex: 2 }}>
              <div className="kicker" style={{ color: 'var(--glow-bad)' }}>Lost money? Act in the golden hour</div>
              <ol className="steps" dangerouslySetInnerHTML={{ __html: lib.recovery.map(s => `<li>${md(s)}</li>`).join('') }} />
            </div>
          </div>
          <div className="card">
            <div className="kicker">Got a scam message but didn't pay?</div>
            <ul className="clean" dangerouslySetInnerHTML={{ __html: lib.report_only.map(s => `<li>${md(s)}</li>`).join('') }} />
          </div>
        </div>
      </Reveal>

      <div className="row" style={{ margin: '36px 0 16px', justifyContent: 'space-between' }}>
        <h2 style={{ fontSize: '1.9rem' }}>{fams.length} scam types</h2>
        <input className="input" style={{ width: 'min(340px, 100%)' }} placeholder="Search: electricity, loan, OTP…" value={q} onChange={e => setQ(e.target.value)} />
      </div>
      <div className="grid-3">
        {fams.map(([k, f], i) => (
          <motion.div key={k} layout initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: Math.min(i * 0.04, 0.4) }}>
            <SpotlightCard className="spot card feature" theme="light" spotlightColor="rgba(143, 203, 168, 0.28)">
              <button className="card-btn" onClick={() => setOpen(k)}>
                <div className="row" style={{ justifyContent: 'space-between' }}><div className="icon">{f.icon}</div><span className="tag neutral">{f.category}</span></div>
                <h3>{f.title}</h3>
                <p>{f.how[0]}</p>
                <p className="small" style={{ marginTop: 12, fontWeight: 700, color: 'var(--ink)' }}>Read the guide →</p>
              </button>
            </SpotlightCard>
          </motion.div>
        ))}
      </div>

      <AnimatePresence>
        {sel && (
          <motion.div onClick={() => setOpen(null)} initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            style={{ position: 'fixed', inset: 0, background: 'rgba(13,13,14,.55)', backdropFilter: 'blur(6px)', zIndex: 80, display: 'grid', placeItems: 'center', padding: 16 }}
            data-lenis-prevent>
            <motion.div className="card" onClick={e => e.stopPropagation()} initial={{ y: 40, scale: 0.96 }} animate={{ y: 0, scale: 1 }} exit={{ y: 30, opacity: 0 }}
              transition={{ type: 'spring', stiffness: 300, damping: 30 }} style={{ maxWidth: 860, width: '100%', maxHeight: '86vh', overflow: 'auto', padding: 32 }}>
              <div className="row" style={{ justifyContent: 'space-between' }}>
                <span className="tag neutral">{sel.category}</span>
                <button className="btn small ghost" onClick={() => setOpen(null)}>Close ✕</button>
              </div>
              <h2 style={{ fontSize: '2.2rem', margin: '14px 0 20px' }}>{sel.icon} {sel.title}</h2>
              <div className="grid-3">
                <div><div className="kicker">How it works</div><ol className="steps">{sel.how.map((s, i) => <li key={i}>{s}</li>)}</ol></div>
                <div><div className="kicker">Warning signs</div><ul className="clean">{sel.signs.map((s, i) => <li key={i}>{s}</li>)}</ul></div>
                <div><div className="kicker">Protect yourself</div><ul className="clean">{sel.protect.map((s, i) => <li key={i}>{s}</li>)}</ul></div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
