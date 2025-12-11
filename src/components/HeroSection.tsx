import { Button } from "@/components/ui/button";
// import heroImage from "@/assets/hero-marketing.jpg";
import { ArrowRight, Play, LogIn } from "lucide-react";
import { Link } from "react-router-dom";
import { useAuth } from "@/hooks/useAuth";
import LazyImage from "@/components/LazyImage";
import { createCheckoutSession } from "@/lib/payments";
import { useState } from "react";

const HeroSection = () => {
  const { user, signOut } = useAuth();
  const [showVideoModal, setShowVideoModal] = useState(false);

  const handleSubscribe = async () => {
    try {
      console.log('Subscribe button clicked');
      const origin = window.location.origin;
      const success_url = `${origin}/#/payments/success`;
      const cancel_url = `${origin}/#/payments/cancel`;

      console.log('Creating checkout session with:', { mode: 'subscription', success_url, cancel_url });
      const { url } = await createCheckoutSession({ mode: 'subscription', success_url, cancel_url });

      console.log('Checkout session created, redirecting to:', url);
      window.location.href = url;
    } catch (err) {
      console.error('Checkout error:', err);
      alert(`Unable to start checkout: ${err instanceof Error ? err.message : 'Unknown error'}. Please ensure the backend is running.`);
    }
  };

  const handleWatchStories = () => {
    // TODO: Replace with actual video modal or redirect to success stories page
    setShowVideoModal(true);
    // Temporary: scroll to testimonials section
    const testimonialsSection = document.getElementById('testimonials');
    if (testimonialsSection) {
      testimonialsSection.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <header className="relative min-h-screen bg-gradient-hero overflow-hidden">
      {/* Background Elements */}
      <div className="absolute inset-0 bg-gradient-hero opacity-90" />

      {/* Video Background - Placeholder until real video is provided */}
      <div className="absolute inset-0 opacity-20">
        {/* TODO: Replace with actual success stories video when available */}
        {/* <video 
          autoPlay 
          loop 
          muted 
          playsInline
          className="w-full h-full object-cover"
        >
          <source src="/videos/success-stories.mp4" type="video/mp4" />
        </video> */}

        {/* Fallback to image until video is provided */}
        <LazyImage
          src="https://images.unsplash.com/photo-1600880292203-757bb62b4baf?ixlib=rb-4.0.3&auto=format&fit=crop&w=2070&q=80"
          alt="Digital marketing team collaborating on business growth strategies"
          className="w-full h-full object-cover"
          loading="eager"
        />
      </div>


      {/* Content */}
      <div className="relative z-10 container mx-auto px-4 pt-20 pb-32">
        <div className="max-w-4xl mx-auto text-center text-white">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 bg-white/10 backdrop-blur-sm border border-white/20 rounded-full px-6 py-2 mb-8">
            <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
            <span className="text-sm font-medium">
              AI-Powered Automation for 500+ Growing Businesses
            </span>
          </div>

          {/* Main Headline */}
          <h1 className="text-5xl md:text-7xl font-bold mb-6 leading-tight">
            Automate Your Business Growth
            <span className="block bg-gradient-to-r from-white to-purple-200 bg-clip-text text-transparent">
              With AI-Powered Solutions
            </span>
          </h1>

          {/* Subheadline */}
          <p className="text-xl md:text-2xl mb-12 text-gray-200 max-w-3xl mx-auto leading-relaxed">
            Transform your business with intelligent automation. Our AI agents handle lead qualification,
            customer engagement, and analytics—so you can focus on what matters most: growing your business.
          </p>

          {/* CTA Buttons */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-16">
            <Link to="/strategy-session">
              <Button
                variant="glass"
                size="lg"
                className="text-lg px-8 py-6 h-auto"
                aria-label="Start your digital marketing journey with AgentsFlowAI"
              >
                Start Your Growth Journey
                <ArrowRight className="ml-2" aria-hidden="true" />
              </Button>
            </Link>
            <Button
              variant="hero"
              size="lg"
              className="text-lg px-8 py-6 h-auto"
              aria-label="Subscribe to AgentsFlowAI"
              onClick={handleSubscribe}
            >
              Subscribe
              <ArrowRight className="ml-2" aria-hidden="true" />
            </Button>
            <Button
              variant="ghost"
              size="lg"
              className="text-lg px-8 py-6 h-auto text-white hover:bg-white/10"
              aria-label="Watch client success stories and case studies"
              onClick={handleWatchStories}
            >
              <Play className="mr-2" aria-hidden="true" />
              Watch Success Stories
            </Button>
          </div>

          {/* Social Proof */}
          <section
            className="grid grid-cols-2 md:grid-cols-4 gap-8 text-center"
            aria-label="Company achievements and statistics"
          >
            <div>
              <div className="text-3xl font-bold text-white">500+</div>
              <div className="text-sm text-gray-300">Happy Clients</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-white">£50M+</div>
              <div className="text-sm text-gray-300">Revenue Generated</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-white">300%</div>
              <div className="text-sm text-gray-300">Average ROI</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-white">24/7</div>
              <div className="text-sm text-gray-300">Expert Support</div>
            </div>
          </section>
        </div>
      </div>

      {/* Floating Elements */}
      <div
        className="absolute top-20 left-10 w-20 h-20 bg-white/5 rounded-full animate-pulse"
        aria-hidden="true"
      />
      <div
        className="absolute bottom-40 right-10 w-32 h-32 bg-purple-400/10 rounded-full animate-pulse delay-300"
        aria-hidden="true"
      />
      <div
        className="absolute top-1/2 left-20 w-16 h-16 bg-blue-400/10 rounded-full animate-pulse delay-700"
        aria-hidden="true"
      />
    </header>
  );
};

export default HeroSection;
