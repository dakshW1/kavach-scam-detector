import { useEffect, useState } from 'react';
import { AnimatePresence, motion } from 'motion/react';
import Reveal from '../components/Reveal.jsx';
import { api, pct } from '../api.js';

function Bars({ title, data, color = 'var(--ink)' }) {
  const items = Object.entries(data || {}).slice(0, 7);
  const max = Math.max(1, ...items.map(([, v]) => v));
  return (
    <div className="card">
      <div className="kicker">{title}</div>
      {items.length === 0 ? <p className="muted small">–</p> : (
        <div className="bars">{items.map(([k, v], i) => (
          <div key={k} className="bar-row"><span title={k} style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{k}</span>
            <div className="bar-track"><motion.div className="bar-fill" style={{ background: color }} initial={{ width: 0 }}
              whileInView={{ width: `${(v / max) * 100}%` }} viewport={{ once: true }} transition={{ delay: i * 0.07, duration: 0.9, ease: [0.22, 1, 0.36, 1] }} /></div>
            <span className="num">{v}</span></div>))}
        </div>)}
    </div>
  );
}

function Copy({ text }) {
  const [d, setD] = useState(false);
  return <button className="btn small ghost copy" onClick={() => { navigator.clipboard?.writeText(text); setD(true); setTimeout(() => setD(false), 1400); }}>{d ? 'Copied ✓' : 'Copy'}</button>;
}

export default function Diary({ onChange }) {
  const [d, setD] = useState(null);
  const [days, setDays] = useState(7);
  const [alert, setAlert] = useState(null);
  const [sure, setSure] = useState(false);
  const load = () => api.diary().then(setD);
  useEffect(() => { load(); }, []);
  useEffect(() => { api.alert(days).then(setAlert); }, [days, d?.entries?.length]);
  if (!d) return null;
  const on = d.settings.diary_enabled;
  const st = d.stats;

  const toggle = async () => { await api.diarySettings({ diary_enabled: !on }); await load(); onChange?.(); };
  const setAuto = async v => { await api.diarySettings({ auto_delete_days: Number(v) }); load(); };
  const del = async id => { await api.diaryDelete(id); load(); };
  const delAll = async () => { await api.diaryDeleteAll(); setSure(false); load(); };
  const topType = Object.keys(st.by_category || {})[0] || '–';

  return (
    <div className="wrap">
      <div className="page-title">
        <div className="kicker">Optional · only on this computer</div>
        <h1>Your Scam Diary</h1>
        <p>See which scams were aimed at you, and warn your family. Private details are masked before anything is saved.</p>
      </div>

      <div className="card row" style={{ justifyContent: 'space-between', marginTop: 20 }}>
        <div className="row" style={{ gap: 14 }}>
          <button className={`switch ${on ? 'on' : ''}`} onClick={toggle} aria-pressed={on} aria-label="Keep a scam diary">
            <motion.span layout transition={{ type: 'spring', stiffness: 500, damping: 30 }} style={{ left: on ? 25 : 3 }} />
          </button>
          <div><b>Keep a scam diary on this computer</b><div className="small muted">{on ? 'On – each SCAM/SUSPICIOUS result is saved in masked form' : 'Off – nothing is saved'}</div></div>
        </div>
        <label className="row small" style={{ gap: 8 }}>Auto-delete after
          <select className="select" value={d.settings.auto_delete_days} onChange={e => setAuto(e.target.value)}>
            {[0, 7, 30, 90].map(v => <option key={v} value={v}>{v ? `${v} days` : 'never'}</option>)}
          </select>
        </label>
      </div>
      <p className="small muted" style={{ margin: '10px 6px 0' }}><b>Saved:</b> date, verdict, category, warning-sign names, brands, link domains and a masked snippet.
        <b> Never saved:</b> the full message, phone numbers, OTPs, account/card numbers, UPI IDs, names or clickable links.</p>

      {d.entries.length === 0 ? (
        <div className="card soft" style={{ marginTop: 24, textAlign: 'center', padding: 48 }}>
          <div style={{ fontSize: '2.4rem' }}>📔</div><h3 style={{ marginTop: 8 }}>Your diary is empty</h3>
          <p className="muted">{on ? 'Check messages on the Check page – scams will appear here.' : 'Switch it on above, then check messages.'}</p>
        </div>
      ) : (
        <>
          <div className="grid-4" style={{ marginTop: 24 }}>
            <div className="stat"><div className="v">{st.total}</div><div className="l">different scam messages{st.received > st.total ? ` (received ${st.received} times)` : ''}</div></div>
            <div className="stat"><div className="v" style={{ color: 'var(--bad)' }}>{st.scam}</div><div className="l">marked SCAM</div></div>
            <div className="stat"><div className="v" style={{ color: 'var(--warn)' }}>{st.suspicious}</div><div className="l">marked suspicious</div></div>
            <div className="stat"><div className="v" style={{ fontSize: '1.6rem', paddingTop: 10 }}>{topType}</div><div className="l">most common type</div></div>
          </div>
          <div className="grid-2" style={{ marginTop: 16 }}>
            <Bars title="Scams aimed at you, by type" data={st.by_category} color="var(--bad)" />
            <Bars title="Tricks used on you most" data={st.by_flag} color="var(--warn)" />
            <Bars title="Brands / authorities impersonated" data={st.by_brand} color="var(--info)" />
            <Bars title="Scam messages per week (week starting)" data={st.by_week} color="var(--ink)" />
          </div>

          <Reveal>
            <div className="night grain" style={{ padding: 32, marginTop: 28 }}>
              <div style={{ position: 'relative', zIndex: 2 }}>
                <div className="section-head">
                  <div><div className="kicker" style={{ color: 'var(--night-muted)' }}>Warn your family and friends</div>
                    <h2 style={{ color: '#fff', fontSize: '2.2rem' }}>One tap, <span className="serif" style={{ color: 'var(--glow-money)' }}>two languages.</span></h2></div>
                  <div className="row">{[[7, '7 days'], [30, '30 days'], [3650, 'everything']].map(([v, l]) => (
                    <button key={v} className="chip" style={days === v ? { background: '#fff', color: '#141414' } : {}} onClick={() => setDays(v)}>{l}</button>))}</div>
                </div>
                <p className="muted small" style={{ marginBottom: 14 }}>Scam patterns only – no personal details. Kavach never sends it: you copy or download it and share it yourself.</p>
                {alert && (
                  <div className="grid-2">
                    <div className="codebox" style={{ background: 'rgba(255,255,255,.06)', color: 'var(--night-text)' }}><Copy text={alert.en} />{alert.en}</div>
                    <div className="codebox" style={{ background: 'rgba(255,255,255,.06)', color: 'var(--night-text)' }}><Copy text={alert.hi} />{alert.hi}</div>
                  </div>
                )}
                <div className="row" style={{ marginTop: 14 }}>
                  <a className="btn ghost" href={`/api/diary/alert.png?days=${days}`} download="scam_alert.png">⬇ Alert card (image)</a>
                </div>
              </div>
            </div>
          </Reveal>

          <h2 style={{ margin: '40px 0 14px', fontSize: '1.8rem' }}>Entries</h2>
          <div className="stack" style={{ gap: 10 }}>
            <AnimatePresence>
              {d.entries.map(e => (
                <motion.div key={e.id} className="card row" layout initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, x: -40 }}
                  style={{ justifyContent: 'space-between', flexWrap: 'nowrap', alignItems: 'flex-start', padding: 18 }}>
                  <div>
                    <div className="row" style={{ gap: 8 }}>
                      <span className={`tag ${e.verdict === 'SCAM' ? 'bad' : 'warn'}`}>{e.verdict}</span>
                      <b>{e.category || 'Other'}</b><span className="small muted">{e.ts.replace('T', ' ')} · scam probability {pct(e.confidence)}</span>
                      {(e.times_seen || 1) > 1 && <span className="tag info">received ×{e.times_seen} · last {(e.last_seen || e.ts).replace('T', ' ').slice(0, 16)}</span>}
                    </div>
                    <p className="small" style={{ marginTop: 8, color: 'var(--ink-2)' }}>{e.snippet}</p>
                    {e.flags.length > 0 && <p className="small muted" style={{ marginTop: 4 }}>Signs: {e.flags.join(', ')}</p>}
                  </div>
                  <button className="btn small ghost" onClick={() => del(e.id)}>Delete</button>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
          <div className="card soft" style={{ marginTop: 18 }}>
            <label className="check"><input type="checkbox" checked={sure} onChange={e => setSure(e.target.checked)} /> Yes, permanently delete all diary entries from this computer</label>
            <button className="btn danger" style={{ marginTop: 12 }} disabled={!sure} onClick={delAll}>Delete everything</button>
          </div>
        </>
      )}
    </div>
  );
}
