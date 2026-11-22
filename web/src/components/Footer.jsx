import ShinyText from '../reactbits/ShinyText.jsx';

export default function Footer({ go }) {
  return (
    <footer className="wrap night grain footer">
      <div className="row" style={{ justifyContent: 'space-between', alignItems: 'end', position: 'relative', zIndex: 2 }}>
        <div>
          <ShinyText text="KAVACH · कवच · SHIELD" className="eyebrow" color="#8f8d88" shineColor="#e9e5dc" speed={3} />
          <h2 style={{ marginTop: 14, color: '#fff' }}>Stop. Check. <span className="serif" style={{ color: 'var(--glow-money)' }}>Then trust.</span></h2>
          <p className="muted" style={{ marginTop: 10, maxWidth: 520 }}>
            Lost money to a scam? Call <b style={{ color: '#fff' }}>1930</b> immediately and report at <b style={{ color: '#fff' }}>cybercrime.gov.in</b>.
          </p>
        </div>
        <div className="stack" style={{ gap: 8, alignItems: 'flex-end' }}>
          <button className="btn ghost" onClick={() => go('check')}>Check a message</button>
          <span className="small muted">Runs offline · nothing leaves this laptop</span>
        </div>
      </div>
    </footer>
  );
}
