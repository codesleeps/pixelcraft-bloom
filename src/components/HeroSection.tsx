import { Button } from "@/components/ui/button";
import heroImage from "@/assets/hero-marketing.jpg";
import { ArrowRight, Play, LogIn } from "lucide-react";
import { Link } from "react-router-dom";
import { useAuth } from "@/hooks/useAuth";
import LazyImage from "@/components/LazyImage";

const HeroSection = () => {
  const { user, signOut } = useAuth();

  return (
    <header className="relative min-h-screen bg-gradient-hero overflow-hidden">
      {/* Background Elements */}
      <div className="absolute inset-0 bg-gradient-hero opacity-90" />
      <div className="absolute inset-0 opacity-20">
        <LazyImage
          src={heroImage}
          alt="Digital marketing team collaborating on business growth strategies"
          className="w-full h-full object-cover"
          loading="eager"
        />
      </div>
      
      {/* Auth Navigation */}
      <div className="absolute top-6 right-6 z-20">
        {user ? (
          <div className="flex items-center gap-4">
            <span className="text-white text-sm">
              Welcome, {user.email}!
            </span>
            <Button 
              variant="ghost" 
              size="sm" 
              onClick={() => signOut()}
              className="text-white hover:bg-white/10"
            >
              Sign Out
            </Button>
          </div>
        ) : (
          <Link to="/auth">
            <Button variant="ghost" size="sm" className="text-white hover:bg-white/10">
              <LogIn className="mr-2 h-4 w-4" />
              Sign In
            </Button>
          </Link>
        )}
      </div>

      {/* Content */}
      <div className="relative z-10 container mx-auto px-4 pt-20 pb-32">
        <div className="max-w-4xl mx-auto text-center text-white">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 bg-white/10 backdrop-blur-sm border border-white/20 rounded-full px-6 py-2 mb-8">
            <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
            <span className="text-sm font-medium">Growing 500+ businesses worldwide</span>
          </div>
          
          {/* Main Headline */}
          <h1 className="text-5xl md:text-7xl font-bold mb-6 leading-tight">
            Transform Your Digital Marketing
            <span className="block bg-gradient-to-r from-white to-purple-200 bg-clip-text text-transparent">
              Business Growth
            </span>
          </h1>
          
          {/* Subheadline */}
          <p className="text-xl md:text-2xl mb-12 text-gray-200 max-w-3xl mx-auto leading-relaxed">
            Award-winning digital marketing agency helping ambitious businesses scale faster with data-driven SEO, 
            social media marketing, web design, and proven growth systems.
          </p>
          
          {/* CTA Buttons */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-16">
            <Link to="/strategy-session">
              <Button 
                variant="glass" 
                size="lg" 
                className="text-lg px-8 py-6 h-auto"
                aria-label="Start your digital marketing journey with PixelCraft"
                onClick={() => console.log('Hero CTA button clicked')}
              >
                Start Your Growth Journey
                <ArrowRight className="ml-2" aria-hidden="true" />
              </Button>
            </Link>
            <Button 
              variant="ghost" 
              size="lg" 
              className="text-lg px-8 py-6 h-auto text-white hover:bg-white/10"
              aria-label="Watch client success stories and case studies"
            >
              <Play className="mr-2" aria-hidden="true" />
              Watch Success Stories
            </Button>
          </div>
          
          {/* Social Proof */}
          <section className="grid grid-cols-2 md:grid-cols-4 gap-8 text-center" aria-label="Company achievements and statistics">
            <div>
              <div className="text-3xl font-bold text-white">500+</div>
              <div className="text-sm text-gray-300">Happy Clients</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-white">$50M+</div>
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
      <div className="absolute top-20 left-10 w-20 h-20 bg-white/5 rounded-full animate-pulse" aria-hidden="true" />
      <div className="absolute bottom-40 right-10 w-32 h-32 bg-purple-400/10 rounded-full animate-pulse delay-300" aria-hidden="true" />
      <div className="absolute top-1/2 left-20 w-16 h-16 bg-blue-400/10 rounded-full animate-pulse delay-700" aria-hidden="true" />
    </header>
  );
};

export default HeroSection;