import { useEffect, useState } from 'react';
import SpotlightCard from '../reactbits/SpotlightCard.jsx';
import Reveal from '../components/Reveal.jsx';
import Reliability from '../components/Reliability.jsx';
import { api } from '../api.js';

const p = x => (x == null ? '–' : `${(x * 100).toFixed(1)}%`);
const NAMES = { final_v2: 'Final test v2 – hand-written, untouched', final: 'Final test v1 – hand-written', tester: 'Messages typed by 5 testers', challenge: 'Challenge set – hand-written', test: 'Held-out templates + UCI messages' };

export default function Results() {
  const [m, setM] = useState(null);
  const [priv, setPriv] = useState(null);
  const [showMistakes, setShowMistakes] = useState(false);
  const [showTable, setShowTable] = useState(false);
  useEffect(() => { api.metrics().then(setM); api.privacy().then(setPriv); }, []);
  if (!m) return null;
  const f = m.final_v2 || m.final;
  const rob = m.robustness;

  return (
    <div className="wrap">
      <div className="page-title">
        <div className="kicker">Honest numbers</div>
        <h1>Results & privacy</h1>
        <p>Every number is on messages the model never saw during training. Final test v2 was written before the latest fixes and never used to improve the model; the tester and challenge sets were used to find mistakes, so they are less strict.</p>
      </div>

      {(() => {
        // one honest headline: all hand-written / real-user sets together, plus the large held-out set
        const hand = ['final_v2', 'final', 'challenge', 'tester'].filter(k => m[k]).map(k => m[k]);
        const sum = fn => hand.reduce((a, s) => a + fn(s), 0);
        const scams = sum(s => s.n_scam), caught = sum(s => s.verdicts.scam.SCAM + s.verdicts.scam.SUSPICIOUS);
        const genuine = sum(s => s.n_safe), wrong = sum(s => s.verdicts.safe.SCAM);
        const t = m.test;
        return (
          <div className="headline-claim">
            On <b>{scams + genuine} hand-written and real-user messages</b> Kavach caught <b>{caught} of {scams} scams</b> and wrongly called{' '}
            <b>{wrong} of {genuine} genuine messages</b> a scam. On <b>{t.n.toLocaleString('en-IN')} held-out generated messages</b> it caught{' '}
            <b>{Math.round(t.caught_scam_or_suspicious * 100)}%</b> of scams and wrongly flagged <b>{(t.safe_marked_scam * 100).toFixed(1)}%</b> of genuine ones.
            <div className="small muted" style={{ marginTop: 6 }}>No set contains real users' private messages; most were written by the team, so real-world accuracy will be lower.</div>
          </div>
        );
      })()}

      <div className="grid-4" style={{ marginTop: 16 }}>
        <div className="stat"><div className="v">{Math.round(f.caught_scam_or_suspicious * 100)}%</div><div className="l">scams caught in the untouched final test ({f.n_scam} scams)</div></div>
        <div className="stat"><div className="v">{f.verdicts.safe.SCAM}/{f.n_safe}</div><div className="l">genuine messages wrongly called a scam there</div></div>
        <div className="stat"><div className="v">{Math.round(m.test.ms_per_message)} ms</div><div className="l">to check one message on a laptop CPU</div></div>
        <div className="stat"><div className="v">{(Math.round(m.calibration_all.ece * 1000) / 1000).toFixed(3)}</div><div className="l">calibration error (0 = perfectly honest confidence)</div></div>
      </div>

      <button className="btn ghost" style={{ marginTop: 16 }} onClick={() => setShowTable(v => !v)}>{showTable ? 'Hide' : 'Show'} every test set</button>
      {showTable && (
        <div className="card table-wrap" style={{ marginTop: 12 }}>
          <table className="t">
            <thead><tr><th>Test set</th><th>Msgs</th><th>Accuracy</th><th>Scams caught</th><th>Precision</th><th>Recall</th><th>Genuine → SCAM</th><th>Genuine → suspicious</th><th>Category acc.</th></tr></thead>
            <tbody>{['final_v2', 'final', 'tester', 'challenge', 'test'].filter(k => m[k]).map(k => (
              <tr key={k}><td><b>{NAMES[k]}</b></td><td className="num">{m[k].n}</td><td className="num">{p(m[k].accuracy)}</td><td className="num">{p(m[k].caught_scam_or_suspicious)}</td>
                <td className="num">{p(m[k].precision)}</td><td className="num">{p(m[k].recall)}</td><td className="num">{p(m[k].safe_marked_scam)}</td>
                <td className="num">{p(m[k].safe_marked_suspicious)}</td><td className="num">{p(m[k].category_accuracy)}</td></tr>))}
            </tbody>
          </table>
        </div>
      )}

      <div className="grid-2" style={{ marginTop: 16 }}>
        <Reveal><div className="card">
          <div className="kicker">Can you trust the confidence %?</div>
          <Reliability bins={m.calibration_all.bins} />
          <p className="small muted">Messages grouped by the confidence Kavach gave. A point on the dashed line means “when it says 80%, it is right about 80% of the time”.
            Brier score {m.calibration_all.brier.toFixed(3)}.</p>
        </div></Reveal>
        <div className="stack">
          <Reveal><div className="card">
            <div className="kicker">Final test – scams caught by language</div>
            <div className="grid-2" style={{ gridTemplateColumns: '1fr 1fr', gap: 10 }}>
              {Object.entries(f.caught_by_kind || {}).map(([k, v]) => (
                <div key={k} className="card soft" style={{ padding: 16 }}><div className="num" style={{ fontSize: '1.8rem', fontWeight: 700 }}>{Math.round(v.caught * v.n)}/{v.n}</div><div className="small muted">{k}</div></div>))}
            </div>
          </div></Reveal>
          <Reveal><div className="card">
            <div className="kicker">Disguised messages</div>
            <p>Test scams caught: <b>{p(rob.caught_original)}</b> as written → <b>{p(rob.caught_disguised)}</b> after random disguise tricks ({rob.n} messages).</p>
            {rob.without_cleaner && <p style={{ marginTop: 6 }}>The same model <b>without</b> the text cleaner: <b>{p(rob.without_cleaner.caught_disguised)}</b> on the disguised copies.</p>}
          </div></Reveal>
          <Reveal><div className="card">
            <div className="kicker">Real bank alerts, OTPs, deliveries (final test)</div>
            {Object.entries(f.false_alarms_by_kind || {}).map(([k, v]) => (
              <p key={k} className="row" style={{ justifyContent: 'space-between' }}><span>{k.replace('_', ' ')} ({v.n})</span>
                <span className="small"><span className="tag ok">{p(v.marked_scam)} marked SCAM</span> <span className="tag warn">{p(v.marked_suspicious)} suspicious</span></span></p>))}
          </div></Reveal>
        </div>
      </div>

      <div className="card" style={{ marginTop: 16 }}>
        <button className="btn ghost" onClick={() => setShowMistakes(s => !s)}>{showMistakes ? 'Hide' : 'Show'} where it still goes wrong</button>
        {showMistakes && (
          <ul className="clean small" style={{ marginTop: 14 }}>
            {['final_v2', 'final', 'tester', 'challenge'].filter(k => m[k]).flatMap(k => (m[k].mistakes || []).map((x, i) => (
              <li key={k + i}><span className="tag neutral">{k}</span> true <b>{x.label}</b>{x.category && ` (${x.category})`} → said <b>{x.verdict}</b>{x.pred_category && ` (${x.pred_category})`}, p={x.p_scam}: {x.text}</li>)))}
          </ul>
        )}
      </div>

      <section className="section">
        <Reveal>
          <div className="night grain" style={{ padding: 40 }}>
            <div style={{ position: 'relative', zIndex: 2 }}>
              <div className="row" style={{ justifyContent: 'space-between', marginBottom: 24 }}>
                <div><div className="kicker" style={{ color: 'var(--night-muted)' }}>Privacy proof</div>
                  <h2 style={{ color: '#fff', fontSize: '2.4rem' }}>How to verify <span className="serif" style={{ color: 'var(--glow-money)' }}>it is offline.</span></h2></div>
                <span className="tag night-tag" style={{ fontSize: '.9rem', padding: '10px 16px' }}>
                  <span className={`dot ${priv?.guard ? '' : 'off'}`} /> Live check: internet {priv?.guard ? 'BLOCKED' : 'not blocked'}
                </span>
              </div>
              <div className="grid-3">
                {[
                  ['📴', 'Turn off Wi-Fi', 'Every feature keeps working except the optional news search.'],
                  ['🧱', 'Network guard in code', 'kavach/netguard.py replaces Python’s socket functions at start-up; any non-local connection raises an error.'],
                  ['🧪', 'Automated proof', 'pytest tests/test_privacy.py asserts zero outgoing connections and that the diary holds no numbers, OTPs or links.'],
                  ['🏠', 'Local only', 'The server listens on 127.0.0.1 only; fonts, three.js and every script are bundled – the browser fetches nothing from the internet.'],
                  ['🧠', 'No cloud AI', 'The model is a 1.4 MB local file. No API keys, no accounts.'],
                  ['🌐', 'One opt-in exception', 'The news search shows its exact words first, sends only scam type + brand, and can reach a single host.'],
                ].map(([i, h, t]) => (
                  <SpotlightCard key={h} className="spot" theme="dark" spotlightColor="rgba(143, 203, 168, 0.22)" style={{ padding: 22, background: 'rgba(255,255,255,.04)' }}>
                    <div style={{ fontSize: '1.6rem' }}>{i}</div><h3 style={{ color: '#fff', margin: '10px 0 6px', fontSize: '1.15rem' }}>{h}</h3><p className="muted small">{t}</p>
                  </SpotlightCard>
                ))}
              </div>
            </div>
          </div>
        </Reveal>
      </section>

      <div className="grid-2 section">
        <Reveal><div className="card">
          <div className="kicker">Data used</div>
          <ul className="clean">
            <li><b>UCI SMS Spam Collection</b> (CC BY 4.0): 2,500 genuine personal messages; prize/claim spam as Lottery/Prize scams.</li>
            <li><b>Indian messages from 376 hand-written templates</b> (175 scam, 201 genuine) in English, Hinglish and Hindi – synthetic, split by template. The third batch was written to cover gaps found by five testers.</li>
            <li><b>Four hand-written / real-user test sets</b> (final v2: 68, final v1: 72, tester messages: 137, challenge: 101), never used for training.</li>
          </ul>
        </div></Reveal>
        <Reveal><div className="card">
          <div className="kicker">Limitations</div>
          <ul className="clean">
            <li>Template-generated training data: real-world accuracy will probably be lower than these numbers.</li>
            <li>Text only – no voice calls, images or screenshots.</li>
            <li>New scam styles may come out as SUSPICIOUS or “Other” – by design.</li>
            <li>Cannot see where a short link leads (that would mean opening it).</li>
          </ul>
        </div></Reveal>
      </div>
    </div>
  );
}
