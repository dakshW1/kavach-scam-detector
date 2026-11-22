import { motion } from 'motion/react';

// Reliability chart drawn in SVG from results/metrics.json, in the site's own style.
export default function Reliability({ bins }) {
  const W = 460, H = 330, L = 52, B = 46, T = 16, R = 16;
  const x = v => L + v * (W - L - R);
  const y = v => H - B - v * (H - B - T);
  const pts = bins.map(b => [x(b.mean_p), y(b.frac_scam), b.n]);
  const path = pts.map((p, i) => `${i ? 'L' : 'M'}${p[0]},${p[1]}`).join(' ');
  const maxN = Math.max(...bins.map(b => b.n));
  return (
    <svg viewBox={`0 0 ${W} ${H}`} style={{ width: '100%', height: 'auto' }} role="img" aria-label="Confidence reliability chart">
      {[0, 0.25, 0.5, 0.75, 1].map(t => (
        <g key={t}>
          <line x1={x(0)} x2={x(1)} y1={y(t)} y2={y(t)} stroke="var(--line)" />
          <text x={L - 10} y={y(t) + 4} textAnchor="end" fontSize="11" fill="var(--muted)">{Math.round(t * 100)}%</text>
          <text x={x(t)} y={H - B + 18} textAnchor="middle" fontSize="11" fill="var(--muted)">{Math.round(t * 100)}%</text>
        </g>
      ))}
      <line x1={x(0)} y1={y(0)} x2={x(1)} y2={y(1)} stroke="var(--line-strong)" strokeDasharray="5 5" />
      <text x={x(0.62)} y={y(0.72)} fontSize="11" fill="var(--muted)" transform={`rotate(-34 ${x(0.62)} ${y(0.72)})`}>perfectly honest</text>
      <motion.path d={path} fill="none" stroke="var(--ink)" strokeWidth="2.5" initial={{ pathLength: 0 }} whileInView={{ pathLength: 1 }}
        viewport={{ once: true }} transition={{ duration: 1.4, ease: [0.22, 1, 0.36, 1] }} />
      {pts.map(([px, py, n], i) => (
        <motion.g key={i} initial={{ opacity: 0, scale: 0 }} whileInView={{ opacity: 1, scale: 1 }} viewport={{ once: true }} transition={{ delay: 0.3 + i * 0.15 }}>
          <circle cx={px} cy={py} r={5 + 9 * Math.sqrt(n / maxN)} fill="var(--glow-money)" opacity="0.45" />
          <circle cx={px} cy={py} r="4.5" fill="var(--ink)" />
          <text x={px + 10} y={py + 16} fontSize="10.5" fill="var(--muted)">{n} msgs</text>
        </motion.g>
      ))}
      <text x={(L + W - R) / 2} y={H - 8} textAnchor="middle" fontSize="12" fill="var(--ink-2)" fontWeight="600">Confidence Kavach gave (scam probability)</text>
      <text x={14} y={(T + H - B) / 2} textAnchor="middle" fontSize="12" fill="var(--ink-2)" fontWeight="600" transform={`rotate(-90 14 ${(T + H - B) / 2})`}>How often it really was a scam</text>
    </svg>
  );
}
