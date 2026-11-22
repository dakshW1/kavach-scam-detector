import { useEffect, useMemo, useRef, useState } from 'react';
import { AnimatePresence, motion } from 'motion/react';

import BlurText from '../reactbits/BlurText.jsx';
import ShinyText from '../reactbits/ShinyText.jsx';
import StarBorder from '../reactbits/StarBorder.jsx';
import SpotlightCard from '../reactbits/SpotlightCard.jsx';
import VantaNet from '../components/VantaNet.jsx';
import Reveal from '../components/Reveal.jsx';
import Tabs from '../components/Tabs.jsx';
import { Decoded, FlagList, HighlightedMessage, Legend, LinkCards, VerdictCard, mergeFlags } from '../components/ResultParts.jsx';
import { ReportTab, GuideTab, IntelTab, HoodTab, TodoTab } from '../components/ResultTabs.jsx';
import { api } from '../api.js';
import { lenis } from '../App.jsx';

const EXAMPLES = {
  'Fake SBI KYC': ['Dear customer, your SBI account will be blocked today. Update your KYC immediately at https://onlinesbi.sbi.secure-login.top/kyc or call 9876543210.', '9876543210'],
  'Hinglish bijli scare': ['Aapka bijli connection aaj raat 9:30 baje kat jayega kyunki pichle mahine ka bill update nahi hua. Turant officer ko call karein 8123456790', ''],
  'Disguised lottery': ['C0NGR@TS!! Y0u w0n ₹25,00,000 in the K.B.C lucky dr@w. Pay ₹4,999 pr0cessing fee to claim. WhatsApp 9123456780', ''],
  'Task job': ['Part time job! Earn Rs 3000 per day by liking YouTube videos from home. Join now t.me/earnfast24', ''],
  'Hindi OTP request': ['प्रिय ग्राहक, आपका डेबिट कार्ड ब्लॉक हो गया है। अनब्लॉक करने के लिए अपना ओटीपी हमें भेजें।', ''],
  'Genuine OTP': ['482913 is your OTP for txn of Rs 2,499 at Amazon. Valid for 10 mins. Do not share it with anyone. -SBI', 'AX-SBIINB-S'],
  'Genuine debit alert': ['Rs.500.00 debited from A/c XX1234 on 22-11-26 to VPA swiggy@icici (UPI Ref No 412345678901). Not you? Call 18001234567 to block. -HDFC Bank', 'VM-HDFCBK-S'],
};

const RESULT_TABS = [
  { id: 'todo', label: 'What to do' }, { id: 'report', label: 'Report this scam' },
  { id: 'guide', label: 'How this scam works' }, { id: 'hood', label: 'For experts' },
];

export default function Check({ onChange }) {
  const [text, setText] = useState('');
  const [sender, setSender] = useState('');
  const [channel, setChannel] = useState('SMS');
  const [r, setR] = useState(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState('');
  const [tab, setTab] = useState('todo');
  const [focus, setFocus] = useState(null);   // index of the sign in focus mode (null = off)

  // keyboard: Esc leaves focus mode, ← → walk through the signs
  useEffect(() => {
    if (focus == null || !r) return undefined;
    const n = mergeFlags(r.flags).length;
    const onKey = e => {
      if (e.key === 'Escape') setFocus(null);
      else if (e.key === 'ArrowRight') { e.preventDefault(); setFocus(f => (f + 1) % n); }
      else if (e.key === 'ArrowLeft') { e.preventDefault(); setFocus(f => (f - 1 + n) % n); }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [focus, r]);
  const [metrics, setMetrics] = useState(null);
  const resultRef = useRef(null);
  const tabsRef = useRef(null);
  // signs that highlight exactly the same words are shown once (the most serious one)
  const rv = useMemo(() => (r ? { ...r, flags: mergeFlags(r.flags) } : null), [r]);
  const openReport = () => {
    setTab('report');
    setTimeout(() => { if (tabsRef.current) { if (lenis) lenis.scrollTo(tabsRef.current, { offset: -90 }); else tabsRef.current.scrollIntoView({ behavior: 'smooth' }); } }, 50);
  };

  useEffect(() => { api.metrics().then(setMetrics).catch(() => {}); }, []);

  const check = async () => {
    if (!text.trim()) { setErr('Paste a message first.'); return; }
    setBusy(true); setErr('');
    try {
      const res = await api.analyze(text, sender);
      setR(res); setTab('todo'); setFocus(null); onChange?.();
      setTimeout(() => {
        if (resultRef.current) {
          if (lenis) lenis.scrollTo(resultRef.current, { offset: -90, duration: 1.4 });
          else resultRef.current.scrollIntoView({ behavior: 'smooth' });
        }
      }, 120);
    } catch (e) { setErr(e.message); }
    setBusy(false);
  };

  const pick = name => { const [t, s] = EXAMPLES[name]; setText(t); setSender(s); setErr(''); };
  const fin = metrics?.final_v2 || metrics?.final;

  return (
    <>
      <section className="wrap night grain hero">
        <VantaNet />
        <div className="hero-inner">
          <ShinyText text="On-device · offline · private" className="eyebrow" color="#8f8d88" shineColor="#ffffff" speed={2.6} />
          <h1><BlurText text="Is this message a scam?" delay={90} animateBy="words" direction="top" className="blur-text" /></h1>
          <p className="lede">Paste any SMS or WhatsApp message. <span className="serif">Kavach checks it on this laptop</span> – nothing ever leaves the device.</p>

          <motion.div className="input-card" initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.5, duration: 0.8, ease: [0.22, 1, 0.36, 1] }}>
            <textarea value={text} onChange={e => setText(e.target.value)} placeholder="Paste the message here…"
              onKeyDown={e => { if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) check(); }} aria-label="Message to check" />
            <div className="controls">
              <input className="night-input" value={sender} onChange={e => setSender(e.target.value)} placeholder="Sender (optional) e.g. AX-SBIINB-S or 98765 43210" aria-label="Sender" />
              <select className="night-input" value={channel} onChange={e => setChannel(e.target.value)} aria-label="Channel">
                {['SMS', 'WhatsApp', 'Email', 'Other'].map(c => <option key={c}>{c}</option>)}
              </select>
              <StarBorder as="button" className="go-btn" onClick={check} color="#8fcba8" duration={5} thickness={1} radius={14} disabled={busy}>
                {busy ? <span className="row" style={{ justifyContent: 'center' }}><span className="spinner" /> Checking</span> : 'Check message →'}
              </StarBorder>
            </div>
            {err && <p className="small" style={{ color: 'var(--glow-bad)', marginTop: 10 }}>{err}</p>}
            <div className="chips">
              <span className="small muted">Try:</span>
              {Object.keys(EXAMPLES).map(n => <button key={n} className="chip" onClick={() => pick(n)}>{n}</button>)}
            </div>
          </motion.div>
        </div>
      </section>

      <div ref={resultRef} />
      <AnimatePresence mode="wait">
        {rv && (
          <motion.section key={rv.text + rv.verdict} className="wrap" style={{ paddingTop: 28 }} initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            <VerdictCard r={rv} onReport={openReport} />
            {r.saved_to_diary && <p className="small muted" style={{ margin: '10px 4px 0' }}>📔 Saved to your Scam Diary (masked: no numbers, codes or clickable links).</p>}
            <AnimatePresence>
              {focus != null && (
                <motion.div className="focus-overlay" onClick={() => setFocus(null)} initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }} transition={{ duration: 0.3 }} aria-hidden="true" />
              )}
            </AnimatePresence>
            <div className={`grid-2 result-grid ${focus != null ? 'focusing' : ''}`} style={{ marginTop: 20 }}>
              <div className="card message-card">
                <div className="kicker">The message · tap a highlight to see why</div>
                <HighlightedMessage r={rv} focus={focus} onPick={setFocus} />
                <Legend />
                <Decoded r={rv} />
                {rv.links.length > 0 && (<div style={{ marginTop: 22 }}><div className="kicker">Links – checked, never opened</div><LinkCards r={rv} /></div>)}
              </div>
              <div>
                <div className="kicker" style={{ margin: '6px 4px 12px' }}>
                  {(() => { const bad = rv.flags.filter(f => f.severity !== 'good').length; const ok = rv.flags.length - bad;
                    return [bad && `${bad} warning sign${bad > 1 ? 's' : ''}`, ok && `${ok} good sign${ok > 1 ? 's' : ''}`].filter(Boolean).join(' · ') || 'Why?'; })()}
                </div>
                <FlagList r={rv} focus={focus} onPick={setFocus} />
                {r.sender_note && <p className="small muted" style={{ marginTop: 10 }}>Sender: {r.sender_note}</p>}
              </div>
            </div>
            <div style={{ marginTop: 28 }} ref={tabsRef}>
              <Tabs tabs={RESULT_TABS} active={tab} onChange={setTab} id="result" />
              <AnimatePresence mode="wait">
                <motion.div key={tab} className="card" style={{ marginTop: 14 }} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -6 }} transition={{ duration: 0.25 }}>
                  {tab === 'todo' && <TodoTab r={r} />}
                  {tab === 'report' && <ReportTab r={r} sender={sender} channel={channel} />}
                  {tab === 'guide' && <><GuideTab r={r} /><IntelTab r={r} sender={sender} onChange={onChange} /></>}
                  {tab === 'hood' && <HoodTab r={r} />}
                </motion.div>
              </AnimatePresence>
            </div>
          </motion.section>
        )}
      </AnimatePresence>

      <section className="wrap section">
        <Reveal>
          <div className="section-head">
            <div><div className="kicker">How Kavach decides</div><h2>Four checks, <span className="serif">twenty milliseconds.</span></h2></div>
            <p>Every verdict can be explained: the rules say what they found, and the model's word weights show what pushed it.</p>
          </div>
        </Reveal>
        <div className="grid-4">
          {[
            ['01', '🕵️', 'Undo the disguise', 'L0TT3RY → lottery, K.Y.C → kyc, Cyrillic lookalikes and invisible characters removed.'],
            ['02', '🚩', 'Spot the tactics', 'Rules for OTP requests, threats, urgency, prizes, fees, fake jobs, donations and “digital arrest” – in English, Hinglish and Hindi.'],
            ['03', '🔗', 'Inspect every link', 'Compared with the official domains of banks, brands and government sites; free site builders are never trusted. Never opened.'],
            ['04', '🧠', 'Weigh it all', 'A small TF-IDF + logistic regression model gives a calibrated confidence and the scam category.'],
          ].map(([n, icon, h, p], i) => (
            <Reveal key={n} delay={i * 0.08}>
              <SpotlightCard className="spot card feature" theme="light" spotlightColor="rgba(143, 203, 168, 0.28)">
                <div className="row" style={{ justifyContent: 'space-between' }}><div className="icon">{icon}</div><span className="step-num">{n}</span></div>
                <h3>{h}</h3><p>{p}</p>
              </SpotlightCard>
            </Reveal>
          ))}
        </div>
      </section>

      <section className="wrap section">
        <Reveal>
          <div className="night grain" style={{ padding: 40 }}>
            <div className="section-head" style={{ position: 'relative', zIndex: 2 }}>
              <div><div className="kicker" style={{ color: 'var(--night-muted)' }}>Privacy by design</div>
                <h2 style={{ color: '#fff' }}>Offline by default. <span className="serif" style={{ color: 'var(--glow-money)' }}>Online only by choice.</span></h2></div>
              <p className="muted">The app blocks its own internet access at start-up. The only online feature sends just the scam type – never your message.</p>
            </div>
            <div className="grid-4" style={{ position: 'relative', zIndex: 2 }}>
              <div className="stat"><div className="v">0</div><div className="l">network calls while checking (tested)</div></div>
              <div className="stat"><div className="v">{fin ? Math.round(fin.ms_per_message) : 20} ms</div><div className="l">to check a message on a laptop CPU</div></div>
              <div className="stat"><div className="v">{fin ? `${fin.verdicts.scam.SCAM + fin.verdicts.scam.SUSPICIOUS}/${fin.n_scam}` : '–'}</div><div className="l">scams caught in the untouched final test</div></div>
              <div className="stat"><div className="v">{fin ? `${fin.verdicts.safe.SCAM}/${fin.n_safe}` : '–'}</div><div className="l">genuine messages wrongly called a scam there</div></div>
            </div>
          </div>
        </Reveal>
      </section>
    </>
  );
}
