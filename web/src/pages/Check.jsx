import { useEffect, useRef, useState } from 'react';
import { AnimatePresence, motion } from 'motion/react';

import BlurText from '../reactbits/BlurText.jsx';
import ShinyText from '../reactbits/ShinyText.jsx';
import StarBorder from '../reactbits/StarBorder.jsx';
import SpotlightCard from '../reactbits/SpotlightCard.jsx';
import CountUp from '../reactbits/CountUp.jsx';
import VantaNet from '../components/VantaNet.jsx';
import Reveal from '../components/Reveal.jsx';
import Tabs from '../components/Tabs.jsx';
import { Decoded, FlagList, HighlightedMessage, Legend, LinkCards, VerdictCard } from '../components/ResultParts.jsx';
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

const TRICKS = ['KYC by SMS link', 'L0TT3RY', 'digital arrest', 'bit.ly/…', 'sbi-kyc-update.xyz', 'processing fee', 'K.Y.C',
  'bijli kat jayega', 'part-time task job', 'Hi Mum, new number', 'enter PIN to receive', 'AnyDesk', 'hdfcbnak.com', 'loan without CIBIL',
  'parcel held at customs', 'इनाम जीता है'];

const RESULT_TABS = [
  { id: 'todo', label: 'What to do' }, { id: 'report', label: 'Report this scam' }, { id: 'guide', label: 'How this scam works' },
  { id: 'intel', label: 'Happening to others?' }, { id: 'hood', label: 'Under the hood' },
];

export default function Check({ onChange }) {
  const [text, setText] = useState('');
  const [sender, setSender] = useState('');
  const [channel, setChannel] = useState('SMS');
  const [r, setR] = useState(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState('');
  const [tab, setTab] = useState('todo');
  const [metrics, setMetrics] = useState(null);
  const resultRef = useRef(null);

  useEffect(() => { api.metrics().then(setMetrics).catch(() => {}); }, []);

  const check = async () => {
    if (!text.trim()) { setErr('Paste a message first.'); return; }
    setBusy(true); setErr('');
    try {
      const res = await api.analyze(text, sender);
      setR(res); setTab('todo'); onChange?.();
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
  const fin = metrics?.final;

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

      <div className="marquee-wrap" aria-hidden="true">
        <div className="marquee">
          {[...TRICKS, ...TRICKS].map((t, i) => <span key={i}><b>✕</b> {t}</span>)}
        </div>
      </div>

      <div ref={resultRef} />
      <AnimatePresence mode="wait">
        {r && (
          <motion.section key={r.text + r.verdict} className="wrap" style={{ paddingTop: 28 }} initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            <VerdictCard r={r} />
            {r.saved_to_diary && <p className="small muted" style={{ margin: '10px 4px 0' }}>📔 Saved to your Scam Diary (masked: no numbers, codes or clickable links).</p>}
            <div className="grid-2" style={{ marginTop: 20 }}>
              <div className="card">
                <div className="kicker">The message, with suspicious parts marked</div>
                <HighlightedMessage r={r} />
                <Legend />
                <Decoded r={r} />
                {r.links.length > 0 && (<div style={{ marginTop: 22 }}><div className="kicker">🔗 Links – inspected, never opened</div><LinkCards r={r} /></div>)}
              </div>
              <div>
                <div className="kicker" style={{ margin: '6px 4px 12px' }}>
                  Why? {r.flags.filter(f => f.severity !== 'good').length} warning signs · {r.flags.filter(f => f.severity === 'good').length} reassuring
                </div>
                <FlagList r={r} />
                {r.sender_note && <p className="small muted" style={{ marginTop: 10 }}>Sender: {r.sender_note}</p>}
              </div>
            </div>
            <div style={{ marginTop: 28 }}>
              <Tabs tabs={RESULT_TABS} active={tab} onChange={setTab} id="result" />
              <AnimatePresence mode="wait">
                <motion.div key={tab} className="card" style={{ marginTop: 14 }} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -6 }} transition={{ duration: 0.25 }}>
                  {tab === 'todo' && <TodoTab r={r} />}
                  {tab === 'report' && <ReportTab r={r} sender={sender} channel={channel} />}
                  {tab === 'guide' && <GuideTab r={r} />}
                  {tab === 'intel' && <IntelTab r={r} sender={sender} onChange={onChange} />}
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
            ['02', '🚩', 'Spot the tactics', '20 red-flag rules for OTP requests, threats, urgency, prizes, fees, fake jobs and “digital arrest” – in English, Hinglish and Hindi.'],
            ['03', '🔗', 'Inspect every link', 'Compared with official domains of 41 banks, brands and government sites. Never opened.'],
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
              <div className="stat"><div className="v"><CountUp to={0} from={9} duration={1.2} /></div><div className="l">network calls while checking (tested)</div></div>
              <div className="stat"><div className="v"><CountUp to={fin ? Math.round(fin.ms_per_message) : 20} duration={1.2} /> ms</div><div className="l">to check a message on a laptop CPU</div></div>
              <div className="stat"><div className="v"><CountUp to={fin ? Math.round(fin.caught_scam_or_suspicious * 100) : 100} duration={1.4} />%</div><div className="l">of scams caught in the untouched final test</div></div>
              <div className="stat"><div className="v"><CountUp to={metrics ? metrics.model.size_mb : 1.2} decimals={1} duration={1.2} /> MB</div><div className="l">model size – no cloud AI, no API keys</div></div>
            </div>
          </div>
        </Reveal>
      </section>
    </>
  );
}
