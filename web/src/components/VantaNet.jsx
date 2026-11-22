import { useEffect, useRef } from 'react';
import * as THREE from 'three';
import NET from 'vanta/dist/vanta.net.min';

// Animated 3D network (Vanta.js + three.js, bundled locally). A web of connected points: the scam
// networks Kavach untangles. Disabled for people who prefer reduced motion.
export default function VantaNet({ color = 0x8fcba8, className = 'hero-bg' }) {
  const ref = useRef(null);
  useEffect(() => {
    if (!ref.current || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return undefined;
    let effect;
    try {
      effect = NET({
        el: ref.current, THREE, mouseControls: true, touchControls: true, gyroControls: false,
        minHeight: 200, minWidth: 200, scale: 1, scaleMobile: 1,
        color, backgroundColor: 0x0d0d0e, points: 11, maxDistance: 21, spacing: 17, showDots: true,
      });
    } catch { /* WebGL not available: the dark background still looks fine */ }
    return () => effect?.destroy();
  }, [color]);
  return <div ref={ref} className={className} aria-hidden="true" />;
}
