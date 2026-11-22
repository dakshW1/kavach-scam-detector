import { useState } from 'react';
import { motion } from 'motion/react';
import BlurText from '../reactbits/BlurText.jsx';
import CountUp from '../reactbits/CountUp.jsx';
import { api, download, pct } from '../api.js';

function parse(name, raw) {
  const lines = raw.split(/\r?\n/).filter(l => l.trim());
  if (!name.toLowerCase().endsWith('.csv') || !lines.length) return lines;
  const head = lines[0].split(',').map(h => h.trim().toLowerCase().replace(/"/g, ''));
  const col = head.findIndex(h => ['text', 'message', 'sms', 'body'].includes(h));
  const rows = lines.slice(1);
  if (col < 0) return rows;
  // simple CSV: take the column, honouring quotes
  return rows.map(r => {
    const cells = r.match(/("([^"]|"")*"|[^,]*)(,|$)/g)?.map(c => c.replace(/,$/, '').replace(/^"|"$/g, '').replace(/""/g, '"')) || [];
    return cells[col] || '';
  }).filter(Boolean);
}

const TAG = { SCAM: 'bad', SUSPICIOUS: 'warn', SAFE: 'ok' };

export default function Batch() {
  const [text, setText] = useState('');
  const [rows, setRows] = useState(null);
  const [busy, setBusy] = useState(false);
  const msgs = text.split(/\r?\n/).filter(l => l.trim());

  const onFile = async e => {
    const f = e.target.files?.[0];
    if (!f) return;
    setText(parse(f.name, await f.text()).join('\n'));
  };
  const run = async () => { setBusy(true); const r = await api.batch(msgs.slice(0, 2000)); setRows(r.rows); setBusy(false); };
  const csv = () => {
    const esc = s => `"${String(s).replace(/"/g, '""')}"`;
    const out = ['verdict,confidence,category,top warning signs,message', ...rows.map(r => [r.verdict, r.confidence.toFixed(3), r.category, r.signs.join('; '), r.message].map(esc).join(','))];
    download(new Blob([out.join('\n')], { type: 'text/csv' }), 'kavach_results.csv');
  };
  const count = v => rows?.filter(r => r.verdict === v).length || 0;
  const order = { SCAM: 0, SUSPICIOUS: 1, SAFE: 2 };

  return (
    <div className="wrap">
      <div className="page-title">
        <div className="kicker">Many messages at once</div>
        <h1><BlurText text="Batch check" delay={80} /></h1>
        <p>Check an exported SMS backup or a list of messages. Files are read in your browser and checked on this computer.</p>
      </div>
      <div className="card stack" style={{ marginTop: 20 }}>
        <div className="row"><label className="btn ghost" style={{ cursor: 'pointer' }}>📄 Choose .txt or .csv<input type="file" accept=".txt,.csv" hidden onChange={onFile} /></label>
          <span className="small muted">.txt = one message per line · .csv = a column named text or message</span></div>
        <textarea className="textarea" style={{ minHeight: 160 }} placeholder="…or paste messages, one per line" value={text} onChange={e => setText(e.target.value)} />
        <div><button className="btn" disabled={!msgs.length || busy} onClick={run}>{busy ? 'Checking…' : `Check ${msgs.length} message${msgs.length === 1 ? '' : 's'}`}</button></div>
      </div>
      {rows && (
        <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}>
          <div className="grid-3" style={{ marginTop: 16 }}>
            <div className="stat"><div className="v" style={{ color: 'var(--bad)' }}><CountUp to={count('SCAM')} duration={1} /></div><div className="l">SCAM</div></div>
            <div className="stat"><div className="v" style={{ color: 'var(--warn)' }}><CountUp to={count('SUSPICIOUS')} duration={1} /></div><div className="l">SUSPICIOUS</div></div>
            <div className="stat"><div className="v" style={{ color: 'var(--ok)' }}><CountUp to={count('SAFE')} duration={1} /></div><div className="l">SAFE</div></div>
          </div>
          <div className="card table-wrap" style={{ marginTop: 16 }}>
            <table className="t"><thead><tr><th>Verdict</th><th>Confidence</th><th>Category</th><th>Top warning signs</th><th>Message</th></tr></thead>
              <tbody>{[...rows].sort((x, y) => order[x.verdict] - order[y.verdict]).map((r, i) => (
                <tr key={i}><td><span className={`tag ${TAG[r.verdict]}`}>{r.verdict}</span></td><td className="num">{pct(r.confidence)}</td>
                  <td>{r.category}</td><td className="small">{r.signs.join(', ')}</td><td className="small">{r.message}</td></tr>))}
              </tbody></table>
          </div>
          <button className="btn ghost" style={{ marginTop: 14 }} onClick={csv}>⬇ Download results (CSV)</button>
        </motion.div>
      )}
    </div>
  );
}
