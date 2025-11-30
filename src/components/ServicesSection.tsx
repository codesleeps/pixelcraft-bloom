import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Link, useNavigate } from "react-router-dom";
import { createCheckoutSession } from "@/lib/payments";
import {
  Search,
  Megaphone,
  Palette,
  BarChart3,
  Smartphone,
  MessageSquare,
  ArrowRight
} from "lucide-react";

const services = [
  {
    icon: Search,
    title: "SEO & Search Marketing",
    description: "Dominate search results with our proven SEO strategies and paid search campaigns that drive qualified traffic.",
    features: ["Keyword Research", "Technical SEO", "Link Building", "PPC Management"]
  },
  {
    icon: Megaphone,
    title: "Social Media Marketing",
    description: "Build engaged communities and drive conversions through strategic social media campaigns across all platforms.",
    features: ["Content Strategy", "Community Management", "Paid Social", "Influencer Marketing"]
  },
  {
    icon: Palette,
    title: "Web Design & Development",
    description: "Create stunning, high-converting websites that reflect your brand and drive business growth.",
    features: ["UI/UX Design", "Responsive Development", "E-commerce", "Performance Optimization"]
  },
  {
    icon: BarChart3,
    title: "Analytics & Insights",
    description: "Make data-driven decisions with comprehensive tracking, reporting, and actionable insights.",
    features: ["Google Analytics", "Conversion Tracking", "Custom Dashboards", "ROI Reporting"]
  },
  {
    icon: Smartphone,
    title: "Mobile Marketing",
    description: "Reach customers on-the-go with mobile-first strategies that maximize engagement and conversions.",
    features: ["App Store Optimization", "Mobile Ads", "SMS Marketing", "Location-Based Marketing"]
  },
  {
    icon: MessageSquare,
    title: "Content Marketing",
    description: "Engage your audience with compelling content that builds trust, authority, and drives organic growth.",
    features: ["Content Strategy", "Blog Writing", "Video Production", "Email Marketing"]
  }
];

const ServicesSection = () => {
  const navigate = useNavigate();

  const handleSubscribe = async () => {
    try {
      const origin = window.location.origin;
      const success_url = `${origin}/#/payments/success`;
      const cancel_url = `${origin}/#/payments/cancel`;
      const { url } = await createCheckoutSession({ mode: 'subscription', success_url, cancel_url });
      window.location.href = url;
    } catch (err) {
      console.error('Checkout error', err);
    }
  };

  const handleStrategyClick = () => {
    navigate('/strategy-session');
    setTimeout(() => window.scrollTo({ top: 0, behavior: 'smooth' }), 100);
  };

  return (
    <section id="services" className="py-24 bg-gradient-subtle">
      <div className="container mx-auto px-4">
        {/* Header */}
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-bold mb-6 text-foreground">
            Complete Digital Marketing
            <span className="block bg-gradient-primary bg-clip-text text-transparent">Solutions</span>
          </h2>
          <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
            From strategy to execution, we provide end-to-end digital marketing services
            that drive measurable results for your business.
          </p>
        </div>

        {/* Services Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8 mb-16">
          {services.map((service, index) => {
            const IconComponent = service.icon;
            return (
              <Card key={index} className="group hover:shadow-card transition-all duration-300 border-0 bg-card/50 backdrop-blur-sm">
                <CardHeader>
                  <div className="w-12 h-12 bg-gradient-primary rounded-lg flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-300">
                    <IconComponent className="w-6 h-6 text-white" />
                  </div>
                  <CardTitle className="text-xl font-semibold">{service.title}</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-muted-foreground mb-4">{service.description}</p>
                  <ul className="space-y-2">
                    {service.features.map((feature, idx) => (
                      <li key={idx} className="flex items-center text-sm">
                        <div className="w-1.5 h-1.5 bg-primary rounded-full mr-3" />
                        {feature}
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            );
          })}
        </div>

        {/* CTA */}
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Button variant="hero" size="lg" className="text-lg px-8 py-6 h-auto" onClick={handleStrategyClick}>
            Get Custom Strategy
            <ArrowRight className="ml-2" />
          </Button>
          <Button variant="hero" size="lg" className="text-lg px-8 py-6 h-auto" onClick={handleSubscribe}>
            Subscribe
            <ArrowRight className="ml-2" />
          </Button>
        </div>
      </div>
    </section>
  );
};

export default ServicesSection;
