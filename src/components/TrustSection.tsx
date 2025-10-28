import React from 'react';
import { Link } from 'react-router-dom';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  Shield,
  Award,
  Users,
  TrendingUp,
  Clock,
  CheckCircle,
  Star,
  Globe
} from 'lucide-react';

const trustElements = [
  {
    icon: Shield,
    title: '100% Secure',
    description: 'Enterprise-grade security with SSL encryption',
    badge: 'Certified'
  },
  {
    icon: Award,
    title: 'Award Winning',
    description: 'Recognized by industry leaders and peers',
    badge: '2023 Winner'
  },
  {
    icon: Users,
    title: '500+ Clients',
    description: 'Trusted by businesses worldwide',
    badge: 'Global Reach'
  },
  {
    icon: TrendingUp,
    title: '300% Avg ROI',
    description: 'Proven results across all industries',
    badge: 'Guaranteed'
  },
  {
    icon: Clock,
    title: '24/7 Support',
    description: 'Round-the-clock expert assistance',
    badge: 'Always Available'
  },
  {
    icon: CheckCircle,
    title: '99.9% Uptime',
    description: 'Reliable service with minimal downtime',
    badge: 'SLA Guaranteed'
  }
];

const certifications = [
  { name: 'Google Partner', logo: 'https://logos-world.net/wp-content/uploads/2020/12/Google-Logo.png' },
  { name: 'Meta Business Partner', logo: 'https://upload.wikimedia.org/wikipedia/commons/thumb/0/05/Facebook_Logo_%282019%29.png/600px-Facebook_Logo_%282019%29.png' },
  { name: 'HubSpot Certified', logo: 'https://logos-world.net/wp-content/uploads/2020/12/HubSpot-Logo.png' },
  { name: 'AWS Certified', logo: 'https://logos-world.net/wp-content/uploads/2020/12/Amazon-Web-Services-AWS-Logo.png' },
  { name: 'ISO 27001', logo: 'https://www.iso.org/files/live/sites/isoorg/files/store/en/PUB100090.png' },
  { name: 'GDPR Compliant', logo: 'https://www.eugdpr.org/images/gdpr-logo.png' }
];

const TrustSection = () => {
  return (
    <section className="py-24 bg-white">
      <div className="container mx-auto px-4">
        {/* Header */}
        <div className="text-center mb-16">
          <div className="inline-flex items-center gap-2 bg-green-100 border border-green-200 rounded-full px-6 py-2 mb-6">
            <Shield className="w-4 h-4 text-green-600" />
            <span className="text-sm font-medium text-green-800">Trusted & Secure</span>
          </div>
          <h2 className="text-4xl md:text-5xl font-bold mb-6 text-foreground">
            Why Choose <span className="bg-gradient-primary bg-clip-text text-transparent">PixelCraft?</span>
          </h2>
          <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
            We're not just another agency. We're your growth partners, backed by certifications,
            awards, and proven results.
          </p>
        </div>

        {/* Trust Elements Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8 mb-16">
          {trustElements.map((element, index) => {
            const IconComponent = element.icon;
            return (
              <Card key={index} className="group hover:shadow-lg transition-all duration-300 border-0 bg-gray-50/50">
                <CardContent className="p-6 text-center space-y-4">
                  <div className="w-16 h-16 bg-gradient-primary/10 rounded-full flex items-center justify-center mx-auto group-hover:bg-gradient-primary/20 transition-colors">
                    <IconComponent className="w-8 h-8 text-primary" />
                  </div>
                  <div>
                    <Badge variant="secondary" className="mb-2 bg-primary/10 text-primary border-primary/20 hover:bg-primary/20">
                      {element.badge}
                    </Badge>
                    <h3 className="font-semibold text-lg mb-2">{element.title}</h3>
                    <p className="text-muted-foreground text-sm">{element.description}</p>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>

        {/* Certifications */}
        <div className="text-center mb-16">
          <h3 className="text-2xl font-bold mb-8">Certified & Recognized By</h3>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-8 items-center opacity-60 hover:opacity-100 transition-opacity">
            {certifications.map((cert, index) => (
              <div key={index} className="flex items-center justify-center h-16">
                <img
                  src={cert.logo}
                  alt={cert.name}
                  className="max-h-12 max-w-24 object-contain filter grayscale hover:grayscale-0 transition-all"
                />
              </div>
            ))}
          </div>
        </div>

        {/* Statistics */}
        <div className="bg-gradient-primary/5 border border-gradient-primary/10 rounded-2xl p-8">
          <div className="grid md:grid-cols-4 gap-8 text-center">
            <div>
              <div className="text-4xl font-bold text-primary mb-2">500+</div>
              <div className="text-sm text-muted-foreground">Happy Clients</div>
            </div>
            <div>
              <div className="text-4xl font-bold text-primary mb-2">£50M+</div>
              <div className="text-sm text-muted-foreground">Revenue Generated</div>
            </div>
            <div>
              <div className="text-4xl font-bold text-primary mb-2">300%</div>
              <div className="text-sm text-muted-foreground">Average ROI</div>
            </div>
            <div>
              <div className="text-4xl font-bold text-primary mb-2">4.9★</div>
              <div className="text-sm text-muted-foreground">Client Rating</div>
            </div>
          </div>
        </div>

        {/* CTA */}
        <div className="text-center mt-16">
          <div className="bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-200/50 rounded-lg p-8 max-w-4xl mx-auto">
            <Globe className="w-12 h-12 text-blue-600 mx-auto mb-4" />
            <h3 className="text-2xl font-bold mb-4">Ready to Scale Your Business?</h3>
            <p className="text-muted-foreground mb-6 max-w-2xl mx-auto">
              Join hundreds of successful businesses that trust PixelCraft with their digital growth.
              Get your free strategy session today.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link to="/strategy-session" className="inline-flex items-center justify-center px-6 py-3 bg-gradient-primary text-white rounded-lg hover:bg-gradient-primary/90 transition-colors font-medium">
                Get Free Strategy Session
              </Link>
              <Link to="/strategy-session" className="inline-flex items-center justify-center px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors font-medium">
                Schedule a Call
              </Link>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default TrustSection;