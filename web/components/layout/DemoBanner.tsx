"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

export function DemoBanner() {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    setVisible(document.cookie.includes("ribet-demo-org="));
  }, []);

  if (!visible) return null;

  return (
    <div className="border-b border-ribet-green/30 bg-ribet-green/10 px-6 py-2 text-center text-sm text-ribet-text">
      Demo workspace — data resets automatically.{" "}
      <Link href="/sign-up" className="font-medium text-ribet-green hover:underline">
        Sign up
      </Link>{" "}
      to keep your data.
    </div>
  );
}
