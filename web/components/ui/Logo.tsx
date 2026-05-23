import Link from "next/link";

function FrogMark({ className = "" }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 32 32"
      fill="none"
      className={className}
      aria-hidden
    >
      <ellipse cx="16" cy="18" rx="12" ry="10" fill="#A3C957" />
      <circle cx="10" cy="12" r="5" fill="#8BB84A" />
      <circle cx="22" cy="12" r="5" fill="#8BB84A" />
      <circle cx="10" cy="12" r="2.5" fill="#111111" />
      <circle cx="22" cy="12" r="2.5" fill="#111111" />
      <circle cx="11" cy="11" r="0.8" fill="#ffffff" />
      <circle cx="23" cy="11" r="0.8" fill="#ffffff" />
      <ellipse cx="16" cy="20" rx="2" ry="1" fill="#6B9E3A" />
    </svg>
  );
}

type LogoProps = {
  href?: string;
};

export function Logo({ href = "/" }: LogoProps) {
  return (
    <Link href={href} className="flex items-center gap-2">
      <FrogMark className="h-8 w-8" />
      <span className="text-lg font-semibold tracking-tight text-rivet-text">
        ribet
      </span>
    </Link>
  );
}
