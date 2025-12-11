import React from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Star, Quote, ArrowRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Link, useNavigate } from 'react-router-dom';
import { createCheckoutSession } from '@/lib/payments';

const testimonials = [
  {
    name: 'Sarah Johnson',
    company: 'TechStart Inc.',
    role: 'CEO',
    avatar: 'https://images.unsplash.com/photo-1494790108755-2616b612b47c?ixlib=rb-4.0.3&auto=format&fit=crop&w=150&q=80',
    rating: 5,
    testimonial: 'AgentsFlowAI transformed our online presence completely. Our leads increased by 300% and we saw a 150% improvement in conversion rates within just 3 months.',
    results: ['300% Lead Increase', '150% Conversion Boost', '3 Months ROI']
  },
  {
    name: 'Michael Chen',
    company: 'GrowthCorp',
    role: 'Marketing Director',
    avatar: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?ixlib=rb-4.0.3&auto=format&fit=crop&w=150&q=80',
    rating: 5,
    testimonial: 'The AI-powered insights and automated campaigns have been game-changing. We saved 20 hours per week while improving our campaign performance by 40%.',
    results: ['40% Performance Increase', '20 Hours Saved/Week', 'Automated Campaigns']
  },
  {
    name: 'Emily Rodriguez',
    company: 'Creative Solutions',
    role: 'Founder',
    avatar: 'https://images.unsplash.com/photo-1438761681033-6461ffad8d80?ixlib=rb-4.0.3&auto=format&fit=crop&w=150&q=80',
    rating: 5,
    testimonial: 'Working with AgentsFlowAI was the best decision we made this year. Their strategic approach and attention to detail delivered results beyond our expectations.',
    results: ['Exceeded Expectations', 'Strategic Approach', 'Detailed Execution']
  },
  {
    name: 'David Thompson',
    company: 'ScaleUp Ventures',
    role: 'CTO',
    avatar: 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?ixlib=rb-4.0.3&auto=format&fit=crop&w=150&q=80',
    rating: 5,
    testimonial: 'The technical expertise and innovative solutions provided by AgentsFlowAI helped us scale our digital infrastructure seamlessly. Outstanding service!',
    results: ['Technical Expertise', 'Infrastructure Scaling', 'Innovative Solutions']
  },
  {
    name: 'Lisa Park',
    company: 'Digital Dynamics',
    role: 'VP of Marketing',
    avatar: 'https://images.unsplash.com/photo-1544005313-94ddf0286df2?ixlib=rb-4.0.3&auto=format&fit=crop&w=150&q=80',
    rating: 5,
    testimonial: 'From day one, AgentsFlowAI understood our vision and delivered exceptional results. Their team is professional, responsive, and truly cares about our success.',
    results: ['Professional Team', 'Responsive Service', 'Vision Alignment']
  },
  {
    name: 'James Wilson',
    company: 'InnovateTech',
    role: 'Product Manager',
    avatar: 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?ixlib=rb-4.0.3&auto=format&fit=crop&w=150&q=80',
    rating: 5,
    testimonial: 'The ROI we achieved with AgentsFlowAI exceeded all our projections. Their data-driven approach and creative strategies are second to none.',
    results: ['Exceeded ROI Goals', 'Data-Driven Approach', 'Creative Strategies']
  }
];

const TestimonialsSection = () => {
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

  const handleCaseStudiesClick = () => {
    const contactSection = document.getElementById('contact');
    if (contactSection) {
      contactSection.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <section id="testimonials" className="py-24 bg-gray-50">
      <div className="container mx-auto px-4">
        {/* Header */}
        <div className="text-center mb-16">
          <div className="inline-flex items-center gap-2 bg-gradient-primary/10 border border-gradient-primary/20 rounded-full px-6 py-2 mb-6">
            <Star className="w-4 h-4 text-yellow-500 fill-current" />
            <span className="text-sm font-medium text-primary">4.9/5 Average Rating</span>
          </div>
          <h2 className="text-4xl md:text-5xl font-bold mb-6 text-foreground">
            Trusted by <span className="bg-gradient-primary bg-clip-text text-transparent">500+ Businesses</span>
          </h2>
          <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
            Don't just take our word for it. See what our clients say about working with AgentsFlowAI.
          </p>
        </div>

        {/* Testimonials Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
          {testimonials.map((testimonial, index) => (
            <Card key={index} className="group hover:shadow-card transition-all duration-300 border-0 bg-white relative overflow-hidden">
              {/* Quote Icon */}
              <div className="absolute top-4 right-4 opacity-10 group-hover:opacity-20 transition-opacity">
                <Quote className="w-12 h-12 text-primary" />
              </div>

              <CardContent className="p-6 space-y-4">
                {/* Rating */}
                <div className="flex items-center space-x-1">
                  {[...Array(testimonial.rating)].map((_, i) => (
                    <Star key={i} className="w-4 h-4 text-yellow-400 fill-current" />
                  ))}
                </div>

                {/* Testimonial Text */}
                <p className="text-gray-700 leading-relaxed">
                  "{testimonial.testimonial}"
                </p>

                {/* Results */}
                <div className="flex flex-wrap gap-2">
                  {testimonial.results.map((result, idx) => (
                    <Badge key={idx} variant="secondary" className="text-xs">
                      {result}
                    </Badge>
                  ))}
                </div>

                {/* Author */}
                <div className="flex items-center space-x-3 pt-4 border-t border-gray-100">
                  <img
                    src={testimonial.avatar}
                    alt={testimonial.name}
                    className="w-12 h-12 rounded-full object-cover"
                    loading="lazy"
                    onError={(e) => {
                      // Fallback to a placeholder if image fails to load
                      e.currentTarget.src = `https://ui-avatars.com/api/?name=${encodeURIComponent(testimonial.name)}&background=random`;
                    }}
                  />
                  <div>
                    <div className="font-semibold text-sm">{testimonial.name}</div>
                    <div className="text-xs text-muted-foreground">
                      {testimonial.role} at {testimonial.company}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Bottom CTA */}
        <div className="text-center mt-16">
          <div className="bg-gradient-primary/5 border border-gradient-primary/20 rounded-lg p-8 max-w-4xl mx-auto">
            <h3 className="text-2xl font-bold mb-4">Ready to Join Our Success Stories?</h3>
            <p className="text-muted-foreground mb-6 max-w-2xl mx-auto">
              Join 500+ businesses that have transformed their digital presence with AgentsFlowAI.
              Start your growth journey today.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button variant="default" size="lg" onClick={handleStrategyClick}>
                Get Your Free Strategy Session
              </Button>
              <Button variant="outline" size="lg" onClick={handleCaseStudiesClick}>
                View More Case Studies
              </Button>
              <Button variant="hero" size="lg" onClick={handleSubscribe}>
                Subscribe
                <ArrowRight className="ml-2" />
              </Button>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default TestimonialsSection;
