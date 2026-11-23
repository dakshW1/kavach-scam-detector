import { createContext, useContext } from 'react';

// Website text in English and Hindi. Result text (signs, reasons, checks, advice) is translated by the server.
const HI = {
  'On-device · offline · private': 'आपके कंप्यूटर पर · बिना इंटरनेट · निजी',
  'Is this message a scam?': 'क्या यह मैसेज धोखा है?',
  'Paste any SMS or WhatsApp message.': 'कोई भी SMS या WhatsApp मैसेज यहाँ डालें।',
  'Kavach checks it on this laptop': 'Kavach इसे इसी कंप्यूटर पर जाँचता है',
  '– nothing ever leaves the device.': '– कुछ भी बाहर नहीं जाता।',
  'Paste the message here…': 'मैसेज यहाँ पेस्ट करें…',
  'Sender (optional) e.g. AX-SBIINB-S or 98765 43210': 'भेजने वाला (वैकल्पिक) जैसे AX-SBIINB-S या 98765 43210',
  'Check message →': 'मैसेज जाँचें →', Checking: 'जाँच हो रही है', 'Try:': 'आज़माएँ:', Paste: 'पेस्ट करें', Pasted: 'पेस्ट हुआ', 'Undoing disguise…': 'छिपावट हटा रहे हैं…', 'Spotting tactics…': 'चालें पहचान रहे हैं…', 'Inspecting links…': 'लिंक जाँच रहे हैं…', 'Weighing it all…': 'सब तौल रहे हैं…',
  'Paste a message first.': 'पहले मैसेज डालें।',
  'or try an example:': 'या कोई उदाहरण आज़माएँ:', 'Obvious scams': 'साफ़ धोखे', 'Subtle scams': 'छिपे हुए धोखे', Genuine: 'असली मैसेज',
  Scam: 'धोखा', 'Be careful': 'सावधान', 'Looks safe': 'सुरक्षित लगता है',
  'Clear signs of fraud. Do not click, call back, pay or share anything.': 'धोखे के साफ़ संकेत। लिंक न दबाएँ, वापस फ़ोन न करें, पैसे या कुछ भी न भेजें।',
  'Some warning signs. Check with the organisation through its official number or app before you act.': 'कुछ चेतावनी संकेत हैं। कुछ करने से पहले संस्था के आधिकारिक नंबर या ऐप से पक्का करें।',
  'No warning signs found. Still, never share an OTP or PIN with anyone who asks for it.': 'कोई चेतावनी संकेत नहीं। फिर भी OTP या PIN माँगने वाले को कभी न बताएँ।',
  'How sure Kavach is': 'Kavach कितना पक्का है',
  'Checked on this computer – nothing was sent anywhere': 'इसी कंप्यूटर पर जाँचा गया – कुछ भी बाहर नहीं भेजा गया',
  'model score': 'मॉडल स्कोर',
  'Already paid or shared a code?': 'पैसे दे दिए या कोड बता दिया?',
  'now – the first hours matter most. Then call your bank.': 'पर अभी कॉल करें – पहले कुछ घंटे सबसे ज़रूरी हैं। फिर बैंक को फ़ोन करें।',
  Call: ' ', 'Make a report': 'रिपोर्ट बनाएँ', 'Check another message': 'दूसरा मैसेज जाँचें', 'Share result': 'नतीजा शेयर करें',
  'You have checked this exact message before': 'यही मैसेज आप पहले जाँच चुके हैं',
  'similar to a message you checked before': 'पहले जाँचे गए मैसेज जैसा है',
  SCAM: 'धोखा', SUSPICIOUS: 'सावधान', SAFE: 'सुरक्षित',
  'times in total – your diary keeps one entry and counts the repeats.': 'बार – डायरी में एक ही एंट्री है, दोहराव गिने जाते हैं।',
  Seen: 'कुल', 'Remembered for this session only (diary is off).': 'सिर्फ़ इस सत्र के लिए याद रखा गया (डायरी बंद है)।',
  'First checked': 'पहली बार जाँचा', 'it was marked': 'तब नतीजा था', 'the same as now.': 'अभी भी वही।', 'now:': 'अब:',
  'The message · tap a highlight to see why': 'मैसेज · कारण देखने के लिए रंगीन हिस्से पर दबाएँ',
  'danger sign': 'ख़तरे का संकेत', 'be careful': 'सावधानी', 'good sign': 'अच्छा संकेत',
  'warning sign': 'चेतावनी संकेत', 'warning signs': 'चेतावनी संकेत', 'good signs': 'अच्छे संकेत',
  'Show fewer': 'कम दिखाएँ', more: 'और', 'Links – checked, never opened': 'लिंक – जाँचे गए, खोले नहीं गए',
  'Why it is a threat': 'यह ख़तरा क्यों है', 'Why it is reassuring': 'यह भरोसे का संकेत क्यों है',
  'What a genuine message does instead': 'असली मैसेज इसकी जगह क्या करता है', 'In plain words': 'आसान शब्दों में',
  '← Previous': '← पिछला', 'Next →': 'अगला →', Done: 'ठीक है',
  'Why it looks genuine': 'यह असली क्यों लगता है', 'Scam checks it passed': 'धोखे की जाँचें जो पास हुईं',
  'What looks normal': 'क्या सामान्य लगता है', 'Still, stay careful': 'फिर भी सावधान रहें',
  'What to do': 'क्या करें', 'Report this scam': 'शिकायत करें', 'How this scam works': 'यह धोखा कैसे होता है', 'For experts': 'विशेषज्ञों के लिए',
  'If you have NOT paid or shared anything': 'अगर आपने पैसे नहीं दिए या कुछ नहीं बताया',
  'Already paid, clicked or shared a code?': 'पैसे दे दिए, लिंक दबाया या कोड बता दिया?',
  'Protect yourself from this type': 'इस तरह के धोखे से कैसे बचें',
};

export const LangContext = createContext({ lang: 'en', setLang: () => {} });
export const useLang = () => useContext(LangContext);
export function useT() {
  const { lang } = useLang();
  return s => (lang === 'hi' && HI[s]) || s;
}
