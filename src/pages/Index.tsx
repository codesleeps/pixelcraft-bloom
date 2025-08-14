import HeroSection from "@/components/HeroSection";
import ServicesSection from "@/components/ServicesSection";
import AboutSection from "@/components/AboutSection";
import ContactSection from "@/components/ContactSection";
import SEOHead from "@/components/SEOHead";
import PerformanceOptimizer from "@/components/PerformanceOptimizer";

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
      <main className="min-h-screen">
        <HeroSection />
        <ServicesSection />
        <AboutSection />
        <ContactSection />
      </main>
    </>
  );
};

export default Index;
