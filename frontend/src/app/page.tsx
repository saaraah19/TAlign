import { CapabilitiesSection } from "@/components/landing/capabilities-section";
import { HeroSection } from "@/components/landing/hero-section";
import { HumanInLoopSection } from "@/components/landing/human-in-loop-section";
import { JourneySection } from "@/components/landing/journey-section";
import { LandingFooter } from "@/components/landing/landing-footer";
import { LandingNav } from "@/components/landing/landing-nav";

/**
 * Public marketing landing page. Deliberately has no live backend call
 * of any kind (the old health-check widget was removed) — a visitor's
 * first impression of the product must never depend on infrastructure
 * being reachable. The actual product experience starts at /login,
 * /register/company, or /careers, all linked from here.
 */
export default function HomePage() {
  return (
    <div className="bg-paper">
      <LandingNav />
      <main>
        <HeroSection />
        <CapabilitiesSection />
        <JourneySection />
        <HumanInLoopSection />
      </main>
      <LandingFooter />
    </div>
  );
}
