/** Observant frog peeking over a surface — calm, not cartoonish */
export function FrogHero() {
  return (
    <div className="animate-breathe relative mx-auto w-full max-w-md">
      <svg
        viewBox="0 0 400 320"
        fill="none"
        className="h-auto w-full drop-shadow-lg"
        aria-hidden
      >
        {/* Body */}
        <ellipse cx="200" cy="240" rx="130" ry="90" fill="#7CB342" />
        <ellipse cx="200" cy="250" rx="110" ry="70" fill="#8BC34A" />
        {/* Head */}
        <ellipse cx="200" cy="160" rx="100" ry="85" fill="#9CCC65" />
        {/* Eyes */}
        <ellipse cx="140" cy="130" rx="42" ry="48" fill="#AED581" />
        <ellipse cx="260" cy="130" rx="42" ry="48" fill="#AED581" />
        <circle cx="140" cy="135" r="22" fill="#1B1B1B" />
        <circle cx="260" cy="135" r="22" fill="#1B1B1B" />
        <circle cx="148" cy="125" r="7" fill="#ffffff" opacity="0.9" />
        <circle cx="268" cy="125" r="7" fill="#ffffff" opacity="0.9" />
        {/* Mouth */}
        <path
          d="M175 185 Q200 195 225 185"
          stroke="#558B2F"
          strokeWidth="3"
          fill="none"
          strokeLinecap="round"
        />
        {/* Front legs on ledge */}
        <ellipse cx="120" cy="295" rx="35" ry="18" fill="#689F38" />
        <ellipse cx="280" cy="295" rx="35" ry="18" fill="#689F38" />
        {/* Spots */}
        <circle cx="170" cy="200" r="8" fill="#7CB342" opacity="0.6" />
        <circle cx="230" cy="210" r="6" fill="#7CB342" opacity="0.5" />
        <circle cx="200" cy="230" r="10" fill="#7CB342" opacity="0.4" />
      </svg>
    </div>
  );
}
