import { Navbar } from "@/components/layout/Navbar";
import { Footer } from "@/components/layout/Footer";
import { Hero } from "@/components/sections/Hero";
import { TrustBar } from "@/components/sections/TrustBar";
import { UploadSection } from "@/components/sections/UploadSection";
import { WhatRivetDoes } from "@/components/sections/WhatRivetDoes";
import { ProductPreview } from "@/components/sections/ProductPreview";
import { HowItWorks } from "@/components/sections/HowItWorks";
import { FinalCta } from "@/components/sections/FinalCta";

export default function HomePage() {
  return (
    <>
      <Navbar />
      <main>
        <Hero />
        <UploadSection />
        <WhatRivetDoes />
        <TrustBar />
        <ProductPreview />
        <HowItWorks />
        <FinalCta />
      </main>
      <Footer />
    </>
  );
}
