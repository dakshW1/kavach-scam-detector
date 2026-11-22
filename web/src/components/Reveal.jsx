import FadeContent from '../reactbits/FadeContent.jsx';

// Scroll-triggered reveal (React Bits FadeContent, GSAP ScrollTrigger, synced with Lenis).
export default function Reveal({ children, delay = 0, className = '', style }) {
  return (
    <FadeContent blur duration={0.9} delay={delay} threshold={0.12} initialOpacity={0} className={className} style={style}>
      {children}
    </FadeContent>
  );
}
