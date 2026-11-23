import { useEffect, useState } from 'react';
import { motion } from 'motion/react';
import { api } from '../api.js';

function Copy({ text }) {
  const [done, setDone] = useState(false);
  return (
    <button className="btn small ghost copy" onClick={() => { navigator.clipboard?.writeText(text); setDone(true); setTimeout(() => setDone(false), 1500); }}>
      {done ? 'Copied ✓' : 'Copy'}
    </button>
  );
}

export function TodoTab({ r }) {
  if (r.verdict === 'SAFE') return (
    <div className="stack">
      <p><b>{r.genuine?.summary}</b></p>
      <ul className="clean">{(r.genuine?.cautions || []).map(c => <li key={c}>{c}</li>)}</ul>
    </div>
  );
  return (
    <div className="grid-2">
      <div>
        <h3>If you have NOT paid or shared anything</h3>
        <ul className="clean" dangerouslySetInnerHTML={{ __html: r.report_only.map(s => `<li>${md(s)}</li>`).join('') }} />
        <h3 style={{ marginTop: 22 }}>Protect yourself from this type</h3>
        <ul className="clean">{(r.advice.protect || []).map((s, i) => <li key={i}>{s}</li>)}</ul>
      </div>
      <div className="night grain" style={{ padding: 24, borderRadius: 20 }}>
        <div style={{ position: 'relative', zIndex: 2 }}>
          <h3 style={{ color: '#fff' }}>Already paid, clicked or shared a code?</h3>
          <ol className="steps" dangerouslySetInnerHTML={{ __html: r.recovery.map(s => `<li>${md(s)}</li>`).join('') }} />
        </div>
      </div>
    </div>
  );
}

// tiny **bold** renderer for trusted, built-in advice strings (escapes HTML first)
export function md(s) {
  const esc = s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  return esc.replace(/\*\*(.+?)\*\*/g, '<b>$1</b>');
}

export function ReportTab({ r, sender, channel }) {
  const [f, setF] = useState({ sender, received: '', channel, lost_money: false, amount_lost: '', transaction_ref: '',
    debit_time: '', victim_bank: '', beneficiary: '', notes: '' });
  const [summary, setSummary] = useState(null);
  const [busy, setBusy] = useState('');
  const set = (k, v) => setF(p => ({ ...p, [k]: v }));
  const body = { text: r.text, ...f };

  const make = async () => { setBusy('summary'); setSummary(await api.reportSummary(body)); setBusy(''); };
  const file = async fmt => { setBusy(fmt); await api.reportFile(body, fmt); setBusy(''); };

  return (
    <div className="stack">
      <p className="muted">Make an <b style={{ color: 'var(--ink)' }}>evidence report</b> for a complaint (cybercrime.gov.in, your bank, Chakshu). It lists the money trail
        investigators need. Made on this computer and saved only if you download it. <b style={{ color: 'var(--ink)' }}>Do not delete the original message.</b></p>
      <div className="grid-3">
        <label className="field">Sender number / ID<input className="input" value={f.sender} onChange={e => set('sender', e.target.value)} /></label>
        <label className="field">Received on (date &amp; time)<input className="input" value={f.received} placeholder="e.g. 23 Nov 2026, 10:15 AM" onChange={e => set('received', e.target.value)} /></label>
        <label className="field">Channel<select className="select" value={f.channel} onChange={e => set('channel', e.target.value)}>{['SMS', 'WhatsApp', 'Email', 'Other'].map(c => <option key={c}>{c}</option>)}</select></label>
      </div>
      <label className="check"><input type="checkbox" checked={f.lost_money} onChange={e => set('lost_money', e.target.checked)} /> I lost money because of this message</label>
      {f.lost_money && (
        <motion.div className="grid-3" initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }}>
          <label className="field">Amount lost<input className="input" placeholder="e.g. Rs 15,000" value={f.amount_lost} onChange={e => set('amount_lost', e.target.value)} /></label>
          <label className="field">Transaction ref. (UTR / UPI ref)<input className="input" placeholder="12-digit number in your bank SMS" value={f.transaction_ref} onChange={e => set('transaction_ref', e.target.value)} /></label>
          <label className="field">When was it debited?<input className="input" placeholder="e.g. 23 Nov, 4:10 PM" value={f.debit_time} onChange={e => set('debit_time', e.target.value)} /></label>
          <label className="field">Your bank / app<input className="input" placeholder="e.g. SBI, PhonePe" value={f.victim_bank} onChange={e => set('victim_bank', e.target.value)} /></label>
          <label className="field">Paid to (UPI ID / account)<input className="input" placeholder="if you know it" value={f.beneficiary} onChange={e => set('beneficiary', e.target.value)} /></label>
        </motion.div>
      )}
      <label className="field">Anything else (what happened, when you noticed)<textarea className="textarea" value={f.notes} onChange={e => set('notes', e.target.value)} /></label>
      {f.lost_money && <div className="tag bad" style={{ padding: '10px 14px', fontSize: '.9rem' }}>💸 Money lost: call 1930 now – the first hours matter most.</div>}
      <div className="row">
        <button className="btn" onClick={() => file('pdf')} disabled={!!busy}>{busy === 'pdf' ? 'Preparing…' : '⬇ Download PDF report'}</button>
        <button className="btn ghost" onClick={() => file('txt')} disabled={!!busy}>⬇ Text report</button>
        <button className="btn ghost" onClick={make} disabled={!!busy}>Show complaint text</button>
      </div>
      {summary && (
        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
          {summary.trail && (summary.trail.upi_ids.length + summary.trail.accounts.length + summary.trail.phones.length + summary.trail.links.length > 0) && (
            <div className="trail">
              <div className="focus-k">Money trail found in the message – investigators trace these</div>
              {summary.trail.upi_ids.length > 0 && <div>UPI ID: <b>{summary.trail.upi_ids.join(', ')}</b></div>}
              {summary.trail.accounts.length > 0 && <div>Account: <b>{summary.trail.accounts.join(', ')}</b>{summary.trail.ifsc.length > 0 && <> · IFSC <b>{summary.trail.ifsc.join(', ')}</b></>}</div>}
              {summary.trail.phones.length > 0 && <div>Phone: <b>{summary.trail.phones.map(([n, k]) => `${n} (${k})`).join(', ')}</b></div>}
              {summary.trail.links.length > 0 && <div>Link: <b>{summary.trail.links.map(l => l[0]).join(', ')}</b></div>}
            </div>
          )}
          <div className="kicker" style={{ marginTop: 14 }}>Copy into the complaint form's “incident details” box</div>
          <div className="codebox"><Copy text={summary.summary} />{summary.summary}</div>
        </motion.div>
      )}
    </div>
  );
}

export function GuideTab({ r }) {
  const fam = r.family_info;
  if (r.verdict === 'SAFE' || !fam) return <p className="muted">No scam detected. Browse every scam type in the Library.</p>;
  return (
    <div className="stack">
      <h3 style={{ fontSize: '1.6rem' }}>{fam.icon} {fam.title}</h3>
      <div className="grid-3">
        <div><div className="kicker">How it works</div><ol className="steps">{fam.how.map((s, i) => <li key={i}>{s}</li>)}</ol></div>
        <div><div className="kicker">Warning signs</div><ul className="clean">{fam.signs.map((s, i) => <li key={i}>{s}</li>)}</ul></div>
        <div><div className="kicker">Protect yourself</div><ul className="clean">{fam.protect.map((s, i) => <li key={i}>{s}</li>)}</ul></div>
      </div>
      <p className="small muted">From the offline Scam Library – works without internet.</p>
    </div>
  );
}

export function IntelTab({ r, sender, onChange }) {
  const [q, setQ] = useState(null);
  const [ok, setOk] = useState(false);
  const [res, setRes] = useState(null);
  const [busy, setBusy] = useState(false);
  useEffect(() => { api.intelPreview(r.text, sender).then(setQ).catch(() => {}); }, [r.text, sender]);
  const [open, setOpen] = useState(false);
  if (r.verdict === 'SAFE') return null;
  if (!open) return (
    <div className="optional-box">
      <div><b>Optional: is this scam in the news?</b><div className="small muted">Uses the internet once, and only sends the scam type – never your message.</div></div>
      <button className="btn small ghost" onClick={() => setOpen(true)}>Show</button>
    </div>
  );
  const go = async () => { setBusy(true); try { setRes(await api.intelSearch(r.text, sender)); } catch (e) { setRes({ error: e.message }); } setBusy(false); onChange?.(); };
  return (
    <div className="stack optional-box open">
      <p><b>Optional.</b> Search recent news to see whether this type of scam is being reported. This is the <b>only</b> feature that uses the internet, and only when you click the button.</p>
      <div className="night" style={{ padding: '18px 20px', borderRadius: 18 }}>
        <div className="small muted">Only these words will be sent to news.google.com:</div>
        <div className="num" style={{ fontSize: '1.5rem', color: '#fff', marginTop: 4 }}>“{q?.query ?? '…'}”</div>
        <div className="small" style={{ color: 'var(--glow-bad)', marginTop: 6 }}>✕ Not sent: your message, phone numbers, links, names or anything about you.</div>
      </div>
      <label className="check"><input type="checkbox" checked={ok} onChange={e => setOk(e.target.checked)} /> I understand – send only these words</label>
      <div><button className="btn" disabled={!ok || busy} onClick={go}>{busy ? 'Searching…' : '🌐 Send this search'}</button></div>
      {res?.error && <p className="tag warn" style={{ padding: '10px 14px' }}>{res.error}</p>}
      {res && !res.error && (
        <motion.div className="stack" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
          <div className="grid-3">
            <div className="stat"><div className="v">{res.total}</div><div className="l">news reports (last 120 days)</div></div>
            <div className="stat"><div className="v">{res.last_30}</div><div className="l">in the last 30 days</div></div>
            <div className="stat"><div className="v">{res.cities.length}</div><div className="l">cities mentioned</div></div>
          </div>
          {res.cities.length > 0 && <p><b>Where it was reported:</b> {res.cities.map(([c, n]) => `${c} (${n})`).join(', ')}</p>}
          {res.amounts.length > 0 && <p><b>Amounts in headlines:</b> {res.amounts.join(', ')}</p>}
          <div>{res.articles.map((a, i) => (
            <div key={i} className="row" style={{ padding: '10px 0', borderBottom: '1px solid var(--line)', justifyContent: 'space-between', flexWrap: 'nowrap' }}>
              <span>{a.title}</span><span className="small muted" style={{ whiteSpace: 'nowrap' }}>{a.source} · {a.date}</span>
            </div>))}
          </div>
          <p className="small muted">Fetched {res.fetched_at}. Headlines shown as text (links not opened). Summarised on this computer – no AI service used.</p>
        </motion.div>
      )}
    </div>
  );
}

export function HoodTab({ r }) {
  const probs = Object.entries(r.category_probs).sort((a, b) => b[1] - a[1]);
  return (
    <div className="grid-2">
      <div className="stack">
        <div><div className="kicker">Category probabilities</div>
          <div className="bars">{probs.map(([c, p], i) => (
            <div key={c} className="bar-row"><span>{c}</span>
              <div className="bar-track"><motion.div className="bar-fill" initial={{ width: 0 }} animate={{ width: `${p * 100}%` }} transition={{ delay: i * 0.06, duration: 0.8 }} /></div>
              <span className="small">{Math.round(p * 100)}%</span></div>))}
          </div>
        </div>
        <p className="small muted">Calibrated scam probability {r.p_scam.toFixed(3)} · checked in {Math.round(r.ms)} ms, fully offline.
          Thresholds: ≥ 0.70 SCAM, &lt; 0.35 SAFE, in between SUSPICIOUS.</p>
      </div>
      <div className="stack">
        <div><div className="kicker">Words that pushed the model (learned weights)</div>
          <p className="small muted" style={{ marginBottom: 8 }}>Single words show what the statistical model leaned on; it reads patterns, not meaning, so small words can appear here.</p>
          <div className="row" style={{ gap: 8 }}>{r.top_words.map((w, i) => (
            <span key={i} className={`tag ${w.weight > 0 ? 'bad' : 'ok'}`}>{w.word} {w.weight > 0 ? '▲' : '▼'} {w.weight.toFixed(2)}</span>))}
            {!r.top_words.length && <span className="muted small">–</span>}
          </div>
        </div>
        <div><div className="kicker">Text after cleaning</div><div className="codebox mono">{r.cleaned}</div></div>
      </div>
    </div>
  );
}
