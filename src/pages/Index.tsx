import Navigation from "@/components/Navigation";
import HeroSection from "@/components/HeroSection";
import ServicesSection from "@/components/ServicesSection";
import TestimonialsSection from "@/components/TestimonialsSection";
import TrustSection from "@/components/TrustSection";
import FAQSection from "@/components/FAQSection";
import ROICalculator from "@/components/ROICalculator";
import DemoPreview from "@/components/DemoPreview";
import PricingSection from "@/components/PricingSection";
import AboutSection from "@/components/AboutSection";
import ContactSection from "@/components/ContactSection";
import Footer from "@/components/Footer";
import SEOHead from "@/components/SEOHead";
import PerformanceOptimizer from "@/components/PerformanceOptimizer";
import { BackToTopButton } from "@/components/BackToTopButton";
import { ChatWidget } from "@/components/ChatWidget";

const Index = () => {
  const organizationSchema = {
    "@context": "https://schema.org",
    "@type": "WebPage",
    "name": "PixelCraft - Digital Marketing Agency",
    "description": "Award-winning digital marketing agency helping businesses scale with SEO, social media, web design, and data-driven strategies.",
    "url": "https://pixelcraft.lovable.app",
    "mainEntity": {
      "@type": "Organization",
      "name": "PixelCraft Digital Marketing",
      "url": "https://pixelcraft.lovable.app",
      "description": "Professional digital marketing services including SEO, social media marketing, web design, and PPC advertising.",
      "aggregateRating": {
        "@type": "AggregateRating",
        "ratingValue": "4.9",
        "reviewCount": "500",
        "bestRating": "5"
      },
      "offers": {
        "@type": "Service",
        "name": "Digital Marketing Services",
        "description": "Comprehensive digital marketing solutions for business growth"
      }
    }
  };

  return (
    <>
      <SEOHead
        title="PixelCraft - Digital Marketing Agency | Transform Your Business"
        description="Award-winning digital marketing agency helping businesses scale with SEO, social media, web design, and data-driven strategies. 300% average ROI guaranteed."
        keywords="digital marketing, SEO, social media marketing, web design, PPC, content marketing, marketing strategy, business growth, PixelCraft"
        canonical="https://pixelcraft.lovable.app"
        schema={organizationSchema}
      />
      <PerformanceOptimizer />
      <Navigation />
      <main className="min-h-screen">
        <HeroSection />
        <ServicesSection />
        <TestimonialsSection />
        <TrustSection />
        <FAQSection />
        <ROICalculator />
        <DemoPreview />
        <PricingSection />
        <AboutSection />
        <ContactSection />
      </main>
      <Footer />
      <BackToTopButton />
      <ChatWidget />
    </>
  );
};

export default Index;
