'use client';
import { motion, useReducedMotion } from 'framer-motion';
import { cn } from '@/lib/utils';

export type ShreyaState = 'idle' | 'listening' | 'speaking' | 'thinking';
export type ShreyaSize = 'sm' | 'md' | 'lg';

const PX: Record<ShreyaSize, number> = { sm: 40, md: 52, lg: 128 };

// Concentric resting rings on a 100×100 viewBox (centre 50,50), decreasing
// opacity outward. This is Shreya's identity at rest.
const RINGS = [
  { r: 46, o: 0.14 },
  { r: 36, o: 0.24 },
  { r: 26, o: 0.4 },
];

// SVG transforms default to the user-space origin; pin scale/rotate to each
// element's own centre so rings breathe in place instead of drifting.
const SPIN_ORIGIN = { transformBox: 'fill-box', transformOrigin: 'center' } as const;

/**
 * Shreya's signature mark: monochrome concentric line-rings that react to her
 * voice state. Colour is inherited via `currentColor`, so the parent chooses it
 * (green on light surfaces, mint/white on the dark chat header). No letterform —
 * that is the deliberate contrast with the user's initialled avatar.
 */
export default function ShreyaAvatar({
  state = 'idle',
  size = 'md',
  className,
  'aria-label': ariaLabel,
}: {
  state?: ShreyaState;
  size?: ShreyaSize;
  className?: string;
  'aria-label'?: string;
}) {
  const reduce = useReducedMotion();
  const px = PX[size];
  const animated = !reduce && state !== 'idle';
  const isSonar = state === 'listening' || state === 'speaking';

  return (
    <svg
      width={px}
      height={px}
      viewBox="0 0 100 100"
      fill="none"
      role="img"
      aria-label={ariaLabel ?? 'Shreya'}
      className={cn('text-idbi-green', className)}
    >
      {RINGS.map(ring => (
        <circle
          key={ring.r}
          cx="50"
          cy="50"
          r={ring.r}
          stroke="currentColor"
          strokeOpacity={ring.o}
          strokeWidth="2"
        />
      ))}

      {/* Listening (calm) / speaking (quick) — staggered sonar rings */}
      {animated && isSonar &&
        [0, 1, 2].map(i => (
          <motion.circle
            key={i}
            cx="50"
            cy="50"
            r="26"
            stroke="currentColor"
            strokeWidth="2"
            initial={{ scale: 0.7, opacity: 0.5 }}
            animate={{ scale: 1.7, opacity: 0 }}
            transition={{
              duration: state === 'speaking' ? 1 : 1.6,
              repeat: Infinity,
              ease: 'easeOut',
              delay: i * (state === 'speaking' ? 0.33 : 0.53),
            }}
            style={SPIN_ORIGIN}
          />
        ))}

      {/* Thinking — a single dashed ring turning slowly */}
      {animated && state === 'thinking' && (
        <motion.circle
          cx="50"
          cy="50"
          r="40"
          stroke="currentColor"
          strokeOpacity="0.5"
          strokeWidth="2"
          strokeDasharray="6 10"
          strokeLinecap="round"
          animate={{ rotate: 360 }}
          transition={{ duration: 6, repeat: Infinity, ease: 'linear' }}
          style={SPIN_ORIGIN}
        />
      )}

      {/* Core disc — breathes gently at rest, harder while speaking */}
      <motion.circle
        cx="50"
        cy="50"
        r="16"
        fill="currentColor"
        animate={reduce ? undefined : { scale: state === 'speaking' ? [1, 1.14, 1] : [1, 1.06, 1] }}
        transition={{ duration: state === 'speaking' ? 0.9 : 3, repeat: Infinity, ease: 'easeInOut' }}
        style={SPIN_ORIGIN}
      />
    </svg>
  );
}
