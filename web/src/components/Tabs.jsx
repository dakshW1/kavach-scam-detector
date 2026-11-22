import { motion } from 'motion/react';

export default function Tabs({ tabs, active, onChange, id = 'tabs' }) {
  return (
    <div className="tabs" role="tablist">
      {tabs.map(t => (
        <button key={t.id} role="tab" aria-selected={active === t.id} className={`tab ${active === t.id ? 'active' : ''}`} onClick={() => onChange(t.id)}>
          {active === t.id && <motion.span layoutId={`${id}-bg`} className="tab-bg" transition={{ type: 'spring', stiffness: 420, damping: 34 }} />}
          {t.label}
        </button>
      ))}
    </div>
  );
}
