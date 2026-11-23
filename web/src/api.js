// Talks only to the local Kavach server on this computer (127.0.0.1).
async function call(method, path, body) {
  const res = await fetch(path, {
    method,
    headers: body ? { 'Content-Type': 'application/json' } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) {
    let msg = res.statusText;
    try { msg = (await res.json()).detail || msg; } catch { /* not json */ }
    throw new Error(typeof msg === 'string' ? msg : 'Request failed');
  }
  return res;
}

export const api = {
  analyze: (text, sender, save = true, lang = 'en') => call('POST', '/api/analyze', { text, sender, save, lang }).then(r => r.json()),
  privacy: () => call('GET', '/api/privacy').then(r => r.json()),
  library: () => call('GET', '/api/library').then(r => r.json()),
  metrics: () => call('GET', '/api/metrics').then(r => r.json()),
  diary: () => call('GET', '/api/diary').then(r => r.json()),
  diarySettings: s => call('POST', '/api/diary/settings', s).then(r => r.json()),
  diaryDelete: id => call('DELETE', `/api/diary/${id}`).then(r => r.json()),
  diaryDeleteAll: () => call('DELETE', '/api/diary').then(r => r.json()),
  alert: days => call('GET', `/api/diary/alert?days=${days}`).then(r => r.json()),
  intelPreview: (text, sender) => call('POST', '/api/intel/preview', { text, sender, save: false }).then(r => r.json()),
  intelSearch: (text, sender) => call('POST', '/api/intel/search', { text, sender, save: false }).then(r => r.json()),
  batch: messages => call('POST', '/api/batch', { messages }).then(r => r.json()),
  tricks: () => call('GET', '/api/tricks').then(r => r.json()),
  disguise: (text, tricks, seed) => call('POST', '/api/disguise', { text, tricks, seed }).then(r => r.json()),
  reportSummary: body => call('POST', '/api/report', { ...body, format: 'summary', save: false }).then(r => r.json()),
  reportFile: async (body, format) => {
    const res = await call('POST', '/api/report', { ...body, format, save: false });
    const name = (res.headers.get('Content-Disposition') || '').match(/filename="(.+)"/)?.[1] || `kavach-report.${format}`;
    download(await res.blob(), name);
  },
};

export function download(blob, name) {
  const url = URL.createObjectURL(blob);
  const a = Object.assign(document.createElement('a'), { href: url, download: name });
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 2000);
}

export const pct = p => (p >= 0.995 ? '>99%' : p < 0.005 ? '<1%' : `${Math.round(p * 100)}%`);
