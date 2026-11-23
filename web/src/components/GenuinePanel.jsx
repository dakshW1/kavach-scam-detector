import { useState } from 'react';
import { motion } from 'motion/react';
import { useT } from '../i18n.js';

// "Why it looks genuine": the explanation for SAFE results (and "what looks normal" for SUSPICIOUS ones).
export function GenuineSummary({ g }) {
  const t = useT();
  if (!g?.summary) return null;
  return (
    <motion.div className="genuine-summary" initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}>
      <div className="focus-k">{t('Why it looks genuine')}</div>
      <p>{g.summary}</p>
    </motion.div>
  );
}

export function PassedChecks({ g, compact = false }) {
  const t = useT();
  const [open, setOpen] = useState(false);
  if (!g) return null;
  return (
    <div className="passed">
      <button className="passed-head" onClick={() => setOpen(o => !o)} aria-expanded={open}>
        <span><b>{t(compact ? 'What looks normal' : 'Scam checks it passed')}</b>
          <span className="muted small"> · {g.passed.length} of {g.n_checks}</span></span>
        <span className="muted">{open ? '▴' : '▾'}</span>
      </button>
      {open && (
        <ul>
          {g.passed.map((t, i) => (
            <motion.li key={t} initial={{ opacity: 0, x: 12 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.05 * i }}>
              <span className="tick">✓</span>{t}
            </motion.li>
          ))}
        </ul>
      )}
    </div>
  );
}

export function StayCareful({ g }) {
  const t = useT();
  if (!g?.cautions?.length) return null;
  return (
    <div className="careful">
      <div className="focus-k">{t('Still, stay careful')}</div>
      <ul>{g.cautions.map(c => <li key={c}>{c}</li>)}</ul>
    </div>
  );
}
