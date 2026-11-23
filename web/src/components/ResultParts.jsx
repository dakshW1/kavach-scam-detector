import { useEffect, useRef, useState } from 'react';
import { AnimatePresence, motion } from 'motion/react';
import { SEVERITY, TIPS } from './signTips.js';
import { lenis } from '../App.jsx';
import DecryptedText from '../reactbits/DecryptedText.jsx';
import { pct } from '../api.js';

const VERDICT = {
  SCAM: { word: 'Scam', sub: 'Clear signs of fraud. Do not click, call back, pay or share anything.' },
  SUSPICIOUS: { word: 'Be careful', sub: 'Some warning signs. Check with the organisation through its official number or app before you act.' },
  SAFE: { word: 'Looks safe', sub: 'No warning signs found. Still, never share an OTP or PIN with anyone who asks for it.' },
};

// Merge signs that highlight the same words (keep the most serious one, mention the other names).
export function mergeFlags(flags) {
  const out = [];
  for (const f of flags) {
    const overlap = o => Math.min(o.end, f.end) - Math.max(o.start, f.start);
    const same = out.find(o => o.end > o.start && f.end > f.start && o.severity !== 'good' && f.severity !== 'good'
      && overlap(o) >= 0.7 * Math.min(o.end - o.start, f.end - f.start));
    if (same) { same.also = [...(same.also || []), f.label]; continue; }
    out.push({ ...f });
  }
  return out;
}

export function VerdictCard({ r, onReport }) {
  const v = VERDICT[r.verdict];
  const type = r.verdict !== 'SAFE' && r.family_info && r.family !== 'unknown'
    ? `${r.family_info.icon} ${r.family_info.title}` : r.verdict !== 'SAFE' ? (r.category === 'Other' ? 'New or unusual type of scam' : r.category) : null;
  return (
    <>
      <motion.div className={`verdict night grain ${r.verdict}`} initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}>
        <div className="glow" />
        <div className="verdict-grid">
          <div>
            {type && <div className="row" style={{ marginBottom: 14 }}><span className="tag night-tag">{type}</span></div>}
            <div className="verdict-word">{v.word}</div>
            <p className="sub">{v.sub}</p>
            {r.safety_net && <p className="small" style={{ marginTop: 10, color: 'var(--glow-warn)' }}>{r.safety_net}</p>}
          </div>
          <div className="conf">
            <div className="muted small" style={{ fontWeight: 700, letterSpacing: '.08em', textTransform: 'uppercase' }}>How sure Kavach is</div>
            <div className="big">{pct(r.confidence)}</div>
            <div className="small muted" style={{ marginTop: 6 }}>Checked on this computer – nothing was sent anywhere</div>
          </div>
        </div>
      </motion.div>
      {r.verdict !== 'SAFE' && (
        <motion.div className="help-strip" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.25 }}>
          <span><b>Already paid or shared a code?</b> Call <b className="num">1930</b> now – the first hours matter most. Then call your bank.</span>
          <button className="btn small" onClick={onReport}>Make a report</button>
        </motion.div>
      )}
    </>
  );
}

// Each highlight is a button: clicking it puts that sign in focus (see FlagList and .focusing in styles.css).
export function HighlightedMessage({ r, focus = null, onPick }) {
  const spans = [];
  r.flags.forEach((f, i) => { if (f.end > f.start) spans.push({ ...f, idx: i }); });
  const chosen = [];
  for (const s of spans) if (chosen.every(c => s.end <= c.start || s.start >= c.end)) chosen.push(s);
  chosen.sort((a, b) => a.start - b.start);
  const parts = [];
  let pos = 0;
  chosen.forEach((s, k) => {
    if (s.start > pos) parts.push(<span key={`t${k}`}>{r.text.slice(pos, s.start)}</span>);
    const on = focus === s.idx;
    parts.push(
      <motion.mark key={`m${k}`} className={`${s.severity} ${onPick ? 'pickable' : ''} ${on ? 'is-focus' : ''}`}
        title={onPick ? `${s.label} – click for details` : s.reason}
        role={onPick ? 'button' : undefined} tabIndex={onPick ? 0 : undefined}
        onClick={onPick ? e => { e.stopPropagation(); onPick(on ? null : s.idx); } : undefined}
        onKeyDown={onPick ? e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onPick(on ? null : s.idx); } } : undefined}
        initial={{ opacity: 0.4 }} animate={{ opacity: focus != null && !on ? 0.3 : 1, scale: on ? 1.06 : 1 }}
        transition={{ delay: on ? 0 : 0.25 + k * 0.12, duration: 0.35, type: on ? 'spring' : 'tween', stiffness: 400, damping: 18 }}>
        {r.text.slice(s.start, s.end)}
      </motion.mark>,
      <sup key={`s${k}`}>{s.idx + 1}</sup>,
    );
    pos = s.end;
  });
  parts.push(<span key="end">{r.text.slice(pos)}</span>);
  return <div className="msg">{parts}</div>;
}

export function Legend() {
  return (
    <div className="legend">
      <span><i style={{ background: 'var(--bad-soft)', boxShadow: 'inset 0 -2px 0 var(--bad)' }} />! danger sign</span>
      <span><i style={{ background: 'var(--warn-soft)', boxShadow: 'inset 0 -2px 0 var(--warn)' }} />? be careful</span>
      <span><i style={{ background: 'var(--ok-soft)', boxShadow: 'inset 0 -2px 0 var(--ok)' }} />✓ good sign</span>
    </div>
  );
}

export function FlagList({ r, focus = null, onPick }) {
  const refs = useRef([]);
  // when a sign comes into focus, glide its card into the middle of the screen
  useEffect(() => {
    const el = focus != null && refs.current[focus];
    if (!el) return;
    const t = setTimeout(() => {
      const offset = -(window.innerHeight / 2) + el.offsetHeight / 2;
      if (lenis) lenis.scrollTo(el, { offset, duration: 0.9 });
      else el.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }, 60);
    return () => clearTimeout(t);
  }, [focus]);

  const [all, setAll] = useState(false);
  if (!r.flags.length) return r.verdict === 'SAFE' ? null : <p className="muted">No specific warning signs; the verdict comes from the model's reading of the wording.</p>;
  const n = r.flags.length;
  const LIMIT = 4;
  const shown = all || (focus != null && focus >= LIMIT) ? r.flags : r.flags.slice(0, LIMIT);
  const firstSentence = s => (s.match(/^.*?[.!?](\s|$)/) || [s])[0].trim();
  return (
    <div className="stack" style={{ gap: 10 }}>
      {shown.map((f, i) => {
        const on = focus === i;
        const sev = SEVERITY[f.severity];
        return (
          <motion.div key={i} ref={el => { refs.current[i] = el; }} layout
            className={`flag ${f.severity} ${onPick ? 'pickable' : ''} ${on ? 'is-focus' : ''}`}
            onClick={onPick ? e => { e.stopPropagation(); if (!on) onPick(i); } : undefined}
            role={onPick ? 'button' : undefined} tabIndex={onPick && !on ? 0 : undefined}
            onKeyDown={onPick ? e => { if (!on && (e.key === 'Enter' || e.key === ' ')) { e.preventDefault(); onPick(i); } } : undefined}
            initial={{ opacity: 0, x: 24 }} animate={{ opacity: 1, x: 0 }}
            transition={{ delay: focus == null ? 0.15 + i * 0.07 : 0, duration: 0.45, ease: [0.22, 1, 0.36, 1], layout: { duration: 0.35 } }}>
            <span className="n">{i + 1}</span>
            <div style={{ flex: 1, minWidth: 0 }}>
              <b>{f.label} {!on && f.text.trim() && <q>{f.text.slice(0, 70)}</q>}</b>
              <AnimatePresence initial={false}>
                {on ? (
                  <motion.div key="detail" initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }}
                    transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }} style={{ overflow: 'hidden' }}>
                    <span className={`tag ${sev.tone}`} style={{ marginTop: 10 }}>{f.severity === 'good' ? '✓' : '!'} {sev.label}</span>
                    {f.text.trim() && <div className="focus-quote">“{f.text}”</div>}
                    <div className="focus-row">
                      <div className="focus-k">{f.severity === 'good' ? 'Why it is reassuring' : 'Why it is a threat'}</div>
                      <p>{f.reason}</p>
                    </div>
                    {TIPS[f.rule] && f.severity !== 'good' && (
                      <div className="focus-row genuine">
                        <div className="focus-k">What a genuine message does instead</div>
                        <p>{TIPS[f.rule]}</p>
                      </div>
                    )}
                    {TIPS[f.rule] && f.severity === 'good' && (
                      <div className="focus-row genuine"><div className="focus-k">In plain words</div><p>{TIPS[f.rule]}</p></div>
                    )}
                    <div className="row" style={{ marginTop: 14, gap: 8 }}>
                      <button className="btn small ghost" onClick={e => { e.stopPropagation(); onPick((i - 1 + n) % n); }}>← Previous</button>
                      <button className="btn small ghost" onClick={e => { e.stopPropagation(); onPick((i + 1) % n); }}>Next →</button>
                      <button className="btn small" onClick={e => { e.stopPropagation(); onPick(null); }}>Done</button>
                      <span className="small muted">{i + 1} of {n} · ← → keys · Esc</span>
                    </div>
                  </motion.div>
                ) : (
                  <motion.p key="short" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                    {firstSentence(f.reason)}{f.also ? <span className="muted"> (also: {f.also.join(', ').toLowerCase()})</span> : null}
                  </motion.p>
                )}
              </AnimatePresence>
            </div>
          </motion.div>
        );
      })}
      {n > LIMIT && !(focus != null && focus >= LIMIT) && (
        <button className="btn small ghost" style={{ alignSelf: 'flex-start' }} onClick={() => setAll(a => !a)}>
          {all ? 'Show fewer' : `Show ${n - LIMIT} more sign${n - LIMIT > 1 ? 's' : ''}`}
        </button>
      )}
    </div>
  );
}

const LINK_TAG = { dangerous: 'bad', suspicious: 'warn', official: 'ok', unknown: 'neutral' };

export function LinkCards({ r }) {
  return r.links.map((l, i) => (
    <motion.div key={i} className="link-card" initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 + i * 0.1 }}>
      <div className="row" style={{ gap: 10 }}>
        <span className={`tag ${LINK_TAG[l.verdict]}`}>{l.verdict.toUpperCase()}</span>
        <code>{l.defanged}</code>
      </div>
      <div className="small muted" style={{ marginTop: 6 }}>Real website (decided by the end of the address): <b style={{ color: 'var(--ink)' }}>{l.registered}</b></div>
      <ul>{[...l.issues, ...l.notes].map((x, j) => <li key={j}>{x}</li>)}</ul>
    </motion.div>
  ));
}

export function Decoded({ r }) {
  const tricks = Object.entries(r.tricks).filter(([k]) => k !== 'stretched letters' || Object.keys(r.tricks).length === 1);
  if (!tricks.length) return null;
  return (
    <div style={{ marginTop: 18 }}>
      <div className="kicker">🕵️ Disguise undone – what Kavach actually read</div>
      <div className="decoded">
        <DecryptedText key={r.text} text={r.cleaned} animateOn="view" sequential speed={18} revealDirection="start"
          useOriginalCharsOnly={false} encryptedClassName="encrypted" />
      </div>
      <div className="row" style={{ marginTop: 8, gap: 6 }}>
        {tricks.map(([k, v]) => <span key={k} className="tag neutral">{k} ×{v}</span>)}
      </div>
    </div>
  );
}
