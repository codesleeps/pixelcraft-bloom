import React, { useState } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ChevronDown, ChevronUp, HelpCircle, ArrowRight } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { createCheckoutSession } from '@/lib/payments';

const faqs = [
  {
    question: "How quickly can I expect to see results from your services?",
    answer: "Most clients see initial improvements within 30-60 days, with significant growth in 90-180 days. Our AI-powered strategies typically deliver faster results than traditional methods, with an average ROI of 300% within the first 6 months."
  },
  {
    question: "Do you work with businesses of all sizes?",
    answer: "Yes! We work with startups, small businesses, mid-market companies, and enterprise clients. Our pricing and service packages are designed to scale with your business needs, from basic SEO to comprehensive digital transformation."
  },
  {
    question: "What makes PixelCraft different from other agencies?",
    answer: "We combine AI-powered insights with human expertise to deliver results that traditional agencies can't match. Our average client sees 300% ROI, and we use data-driven strategies backed by real results from 500+ successful campaigns."
  },
  {
    question: "How do you measure and report on campaign performance?",
    answer: "We provide comprehensive analytics dashboards with real-time tracking of KPIs, conversion rates, ROI, and growth metrics. You'll get detailed monthly reports plus 24/7 access to your performance data through our client portal."
  },
  {
    question: "Can I cancel or modify my service package at any time?",
    answer: "Absolutely! We offer flexible month-to-month contracts with no long-term commitments. You can upgrade, downgrade, or cancel anytime. We're confident in our results, so we don't need to lock you in."
  },
  {
    question: "Do you guarantee results?",
    answer: "While we can't guarantee specific results (as no ethical agency can), we do guarantee our process and expertise. We offer a 90-day performance review, and if you're not satisfied, we'll work with you to improve results or provide a prorated refund."
  },
  {
    question: "How do your AI agents work?",
    answer: "Our AI agents analyze your business data, market trends, and customer behavior to create personalized strategies. They handle everything from lead qualification to content optimization, working 24/7 to improve your digital marketing performance."
  },
  {
    question: "What industries do you specialize in?",
    answer: "We work across all industries, with particular expertise in e-commerce, SaaS, professional services, healthcare, and technology. Our AI adapts to any business model and creates industry-specific strategies."
  },
  {
    question: "How much do your services cost?",
    answer: "Our pricing starts at £99/month for basic services and goes up to £599/month for enterprise solutions. We also offer custom packages and one-time projects. Check our pricing section for detailed breakdowns and current promotions."
  },
  {
    question: "Do you provide ongoing support and optimization?",
    answer: "Yes! All our plans include ongoing optimization, monthly strategy reviews, and dedicated account management. Our team actively monitors your campaigns and makes data-driven adjustments to maximize performance."
  }
];

const FAQSection = () => {
  const [openIndex, setOpenIndex] = useState<number | null>(null);
  const navigate = useNavigate();

  const toggleFAQ = (index: number) => {
    setOpenIndex(openIndex === index ? null : index);
  };

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

  const handleContactClick = () => {
    const contactSection = document.getElementById('contact');
    if (contactSection) {
      contactSection.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <section className="py-24 bg-gradient-subtle">
      <div className="container mx-auto px-4">
        {/* Header */}
        <div className="text-center mb-16">
          <div className="inline-flex items-center gap-2 bg-blue-100 border border-blue-200 rounded-full px-6 py-2 mb-6">
            <HelpCircle className="w-4 h-4 text-blue-600" />
            <span className="text-sm font-medium text-blue-800">Frequently Asked Questions</span>
          </div>
          <h2 className="text-4xl md:text-5xl font-bold mb-6 text-foreground">
            Got Questions? <span className="bg-gradient-primary bg-clip-text text-transparent">We Have Answers</span>
          </h2>
          <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
            Everything you need to know about working with PixelCraft and our AI-powered services.
          </p>
        </div>

        {/* FAQ Grid */}
        <div className="max-w-4xl mx-auto space-y-4">
          {faqs.map((faq, index) => (
            <Card key={index} className="border-0 bg-white/50 backdrop-blur-sm hover:bg-white/70 transition-all duration-300">
              <CardContent className="p-6">
                <Button
                  variant="ghost"
                  className="w-full justify-between p-0 h-auto text-left"
                  onClick={() => toggleFAQ(index)}
                >
                  <span className="font-semibold text-lg text-foreground pr-4">
                    {faq.question}
                  </span>
                  {openIndex === index ? (
                    <ChevronUp className="w-5 h-5 text-primary flex-shrink-0" />
                  ) : (
                    <ChevronDown className="w-5 h-5 text-muted-foreground flex-shrink-0" />
                  )}
                </Button>

                {openIndex === index && (
                  <div className="mt-4 pt-4 border-t border-gray-200">
                    <p className="text-muted-foreground leading-relaxed">
                      {faq.answer}
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Bottom CTA */}
        <div className="text-center mt-16">
          <div className="bg-gradient-primary/5 border border-gradient-primary/20 rounded-lg p-8 max-w-4xl mx-auto">
            <h3 className="text-2xl font-bold mb-4">Still Have Questions?</h3>
            <p className="text-muted-foreground mb-6 max-w-2xl mx-auto">
              Can't find what you're looking for? Our team is here to help you understand how
              PixelCraft can transform your business.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button variant="default" size="lg" onClick={handleStrategyClick}>
                Get Free Strategy Session
              </Button>
              <Button variant="outline" size="lg" onClick={handleContactClick}>
                Contact Our Team
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

export default FAQSection;
