import { useState } from 'react';
import { download } from '../api.js';
import { useLang, useT } from '../i18n.js';

// "Share result": a short warning (text + image card) that you send to family yourself, e.g. on WhatsApp.
// Made in the browser – the message itself is not included, only the verdict, the scam type and the main reason.
function shareText(r, lang) {
  const top = r.flags.find(f => f.severity === 'high') || r.flags.find(f => f.severity !== 'good');
  const good = r.flags.find(f => f.severity === 'good');
  if (lang === 'hi') {
    if (r.verdict === 'SAFE') return `✅ Kavach जाँच: यह मैसेज असली लगता है (${r.confidence_band})।${good ? ` कारण: ${good.label}.` : ''}\nफिर भी OTP या PIN किसी को न बताएँ।`;
    return `⚠️ Kavach जाँच: ${r.verdict === 'SCAM' ? 'यह मैसेज धोखा है' : 'इस मैसेज से सावधान रहें'} (${r.confidence_band}).${r.family_info ? `\nप्रकार: ${r.family_info.title}` : ''}${top ? `\nमुख्य कारण: ${top.label}` : ''}\nलिंक न दबाएँ, पैसे न भेजें, OTP न बताएँ। पैसे गए हों तो तुरंत 1930 पर कॉल करें।`;
  }
  if (r.verdict === 'SAFE') return `✅ Kavach check: this message looks genuine (${r.confidence_band}).${good ? ` Reason: ${good.label}.` : ''}\nStill, never share an OTP or PIN.`;
  return `⚠️ Kavach check: ${r.verdict === 'SCAM' ? 'this message is a SCAM' : 'be careful with this message'} (${r.confidence_band}).${r.family_info ? `\nType: ${r.family_info.title}` : ''}${top ? `\nMain reason: ${top.label}` : ''}\nDon't click, pay or share any code. Lost money? Call 1930 now.`;
}

function cardBlob(text, verdict) {
  const c = document.createElement('canvas');
  const W = 900, pad = 56;
  const ctx = c.getContext('2d');
  ctx.font = '500 30px Manrope, "Noto Sans Devanagari", sans-serif';
  const lines = [];
  text.split('\n').forEach(para => {
    let line = '';
    para.split(' ').forEach(w => {
      const test = line ? `${line} ${w}` : w;
      if (ctx.measureText(test).width > W - pad * 2) { lines.push(line); line = w; } else line = test;
    });
    lines.push(line);
  });
  c.width = W; c.height = 200 + lines.length * 46;
  const color = verdict === 'SCAM' ? '#9a2e3a' : verdict === 'SUSPICIOUS' ? '#a8771e' : '#2f6b4f';
  ctx.fillStyle = '#f4f3ef'; ctx.fillRect(0, 0, W, c.height);
  ctx.fillStyle = color; ctx.fillRect(0, 0, W, 110);
  ctx.fillStyle = '#fff'; ctx.font = '800 46px "Bricolage Grotesque", sans-serif';
  ctx.fillText(verdict === 'SCAM' ? 'SCAM ALERT' : verdict === 'SUSPICIOUS' ? 'BE CAREFUL' : 'LOOKS GENUINE', pad, 72);
  ctx.fillStyle = '#141414'; ctx.font = '500 30px Manrope, "Noto Sans Devanagari", sans-serif';
  lines.forEach((ln, i) => ctx.fillText(ln, pad, 170 + i * 46));
  ctx.fillStyle = '#6e6c67'; ctx.font = '500 20px Manrope, sans-serif';
  ctx.fillText('Checked offline with Kavach', pad, c.height - 28);
  return new Promise(res => c.toBlob(res, 'image/png'));
}

export default function ShareCard({ r }) {
  const { lang } = useLang();
  const t = useT();
  const [msg, setMsg] = useState('');
  const [busy, setBusy] = useState(false);
  const text = shareText(r, lang);
  const flash = m => { setMsg(m); setTimeout(() => setMsg(''), 1800); };

  const share = async () => {
    if (busy) return;
    setBusy(true);
    try { await doShare(); } finally { setBusy(false); }
  };
  const doShare = async () => {
    const blob = await cardBlob(text, r.verdict);
    const file = new File([blob], 'kavach-result.png', { type: 'image/png' });
    try {
      if (navigator.canShare && navigator.canShare({ files: [file] })) { await navigator.share({ files: [file], text }); return; }
    } catch { /* user cancelled or not supported */ }
    download(blob, 'kavach-result.png');
    try { await navigator.clipboard.writeText(text); flash(lang === 'hi' ? 'तस्वीर सेव हुई, टेक्स्ट कॉपी हुआ' : 'Image saved · text copied'); }
    catch { flash(lang === 'hi' ? 'तस्वीर सेव हुई' : 'Image saved'); }
  };

  return (
    <span className="row" style={{ gap: 8 }}>
      <button className="btn ghost" onClick={share} disabled={busy}>{msg ? `✓ ${t('Share result')}` : t('Share result')}</button>
      {msg && <span className="small muted" role="status">{msg}</span>}
    </span>
  );
}
