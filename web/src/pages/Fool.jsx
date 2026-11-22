import { useEffect, useState } from 'react';
import { motion } from 'motion/react';
import BlurText from '../reactbits/BlurText.jsx';
import DecryptedText from '../reactbits/DecryptedText.jsx';
import Magnet from '../reactbits/Magnet.jsx';
import { HighlightedMessage } from '../components/ResultParts.jsx';
import { api, pct } from '../api.js';

const BASES = [
  'Your SBI account will be blocked today. Update KYC now at sbi-kyc-update.xyz',
  'Congratulations! You won Rs 25 lakh in the KBC lottery. Pay Rs 5000 processing fee to claim.',
  'Instant loan approved, no documents needed. Pay Rs 999 file charge to receive the money.',
  'Earn Rs 3000 daily by liking YouTube videos. Join our Telegram group.',
];
const COLORS = { SCAM: 'var(--bad)', SUSPICIOUS: 'var(--warn)', SAFE: 'var(--ok)' };

function Side({ label, r }) {
  if (!r) return <div className="card" />;
  return (
    <motion.div className="card" key={r.text} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}>
      <div className="row" style={{ justifyContent: 'space-between' }}>
        <div className="kicker" style={{ margin: 0 }}>{label}</div>
        <span className="num" style={{ fontSize: '1.6rem', fontWeight: 800, color: COLORS[r.verdict] }}>{r.verdict} · {pct(r.confidence)}</span>
      </div>
      <div style={{ marginTop: 12 }}><HighlightedMessage r={r} /></div>
    </motion.div>
  );
}

export default function Fool() {
  const [tricks, setTricks] = useState({});
  const [base, setBase] = useState(BASES[0]);
  const [on, setOn] = useState(['leet', 'homoglyph']);
  const [seed, setSeed] = useState(1);
  const [fooled, setFooled] = useState('');
  const [a, setA] = useState(null);
  const [b, setB] = useState(null);

  useEffect(() => { api.tricks().then(setTricks); }, []);
  useEffect(() => { api.disguise(base, on, seed).then(d => setFooled(d.text)); }, [base, on, seed]);
  useEffect(() => { if (base.trim()) api.analyze(base, '', false).then(setA); }, [base]);
  useEffect(() => {
    if (!fooled.trim()) return undefined;
    const t = setTimeout(() => api.analyze(fooled, '', false).then(setB), 250);
    return () => clearTimeout(t);
  }, [fooled]);
  const toggle = k => setOn(o => (o.includes(k) ? o.filter(x => x !== k) : [...o, k]));

  return (
    <div className="wrap">
      <div className="page-title">
        <div className="kicker">Robustness demo</div>
        <h1><BlurText text="Try to fool it" delay={80} /></h1>
        <p>Scammers disguise words so filters miss them. Disguise a scam here – or type your own – and watch Kavach still read it.</p>
      </div>
      <div className="card stack" style={{ marginTop: 20 }}>
        <div><div className="kicker">1 · Start from a scam</div>
          <div className="row" style={{ gap: 8 }}>{BASES.map((s, i) => (
            <button key={i} className={`chip light ${base === s ? 'on' : ''}`} onClick={() => setBase(s)}>{s.split(' ').slice(0, 4).join(' ')}…</button>))}</div>
          <textarea className="textarea" style={{ width: '100%', marginTop: 10 }} value={base} onChange={e => setBase(e.target.value)} />
        </div>
        <div><div className="kicker">2 · Pick disguise tricks</div>
          <div className="row" style={{ gap: 8 }}>
            {Object.entries(tricks).map(([k, l]) => <button key={k} className={`chip light ${on.includes(k) ? 'on' : ''}`} onClick={() => toggle(k)}>{l}</button>)}
            <Magnet padding={40} magnetStrength={3}><button className="btn" onClick={() => setSeed(s => s + 1)}>🎲 Disguise differently</button></Magnet>
          </div>
        </div>
        <div><div className="kicker">3 · The disguised message (edit it further if you like)</div>
          <textarea className="textarea mono" style={{ width: '100%' }} value={fooled} onChange={e => setFooled(e.target.value)} /></div>
      </div>
      <div className="grid-2" style={{ marginTop: 16, gridTemplateColumns: '1fr 1fr' }}>
        <Side label="Original" r={a} />
        <Side label="Disguised" r={b} />
      </div>
      {b && (
        <div className="night grain" style={{ padding: 28, marginTop: 16, borderRadius: 24 }}>
          <div style={{ position: 'relative', zIndex: 2 }}>
            <div className="kicker" style={{ color: 'var(--night-muted)' }}>What Kavach read after cleaning</div>
            <div className="decoded" style={{ background: 'transparent', padding: 0, fontSize: '1.05rem' }}>
              <DecryptedText key={b.text} text={b.cleaned} animateOn="view" sequential speed={14} encryptedClassName="encrypted" />
            </div>
            <div className="row" style={{ marginTop: 12, gap: 6 }}>
              {Object.entries(b.tricks).map(([k, v]) => <span key={k} className="tag night-tag">{k} ×{v}</span>)}
            </div>
            <p className="muted small" style={{ marginTop: 14, maxWidth: 760 }}>Before checking, Kavach turns lookalike letters into normal letters, numbers inside words back into letters,
              removes dots between single letters and deletes invisible characters. The disguise itself is also a red flag: genuine companies never write like this.</p>
          </div>
        </div>
      )}
    </div>
  );
}
