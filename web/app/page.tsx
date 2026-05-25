import { Navbar } from "@/components/layout/Navbar";
import { Footer } from "@/components/layout/Footer";
import { Hero } from "@/components/sections/Hero";
import { TrustBar } from "@/components/sections/TrustBar";
import { UploadSection } from "@/components/sections/UploadSection";
import { WhatRibetDoes } from "@/components/sections/WhatRibetDoes";
import { HowItWorks } from "@/components/sections/HowItWorks";
import { FinalCta } from "@/components/sections/FinalCta";

export default function HomePage() {
  return (
    <>
      <Navbar />
      <main>
        <Hero />
        <UploadSection />
        <WhatRibetDoes />
        <TrustBar />
        <HowItWorks />
        <FinalCta />
      </main>
      <Footer />
    </>
  );
}
