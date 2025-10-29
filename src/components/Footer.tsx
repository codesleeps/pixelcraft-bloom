import React from 'react';
import { HashLink as Link } from 'react-router-hash-link';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Separator } from '@/components/ui/separator';
import {
  Facebook,
  Twitter,
  Instagram,
  Linkedin,
  Mail,
  Phone,
  MapPin,
  ArrowUp
} from 'lucide-react';

const Footer = () => {
  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const currentYear = new Date().getFullYear();

  return (
    <footer className="bg-gray-900 text-white">
      {/* Main Footer Content */}
      <div className="container mx-auto px-4 py-12">
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
          {/* Company Info */}
          <div className="space-y-4">
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-gradient-primary rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-sm">PC</span>
              </div>
              <span className="text-xl font-bold">PixelCraft</span>
            </div>
            <p className="text-gray-300 text-sm">
              Award-winning digital marketing agency helping businesses scale with AI-powered strategies,
              SEO, social media, and data-driven growth solutions.
            </p>
            <div className="flex space-x-4">
              <a href="https://facebook.com" target="_blank" rel="noopener noreferrer">
                <Button variant="ghost" size="sm" className="text-gray-300 hover:text-white p-2">
                  <Facebook className="w-4 h-4" />
                </Button>
              </a>
              <a href="https://twitter.com" target="_blank" rel="noopener noreferrer">
                <Button variant="ghost" size="sm" className="text-gray-300 hover:text-white p-2">
                  <Twitter className="w-4 h-4" />
                </Button>
              </a>
              <a href="https://instagram.com" target="_blank" rel="noopener noreferrer">
                <Button variant="ghost" size="sm" className="text-gray-300 hover:text-white p-2">
                  <Instagram className="w-4 h-4" />
                </Button>
              </a>
              <a href="https://linkedin.com" target="_blank" rel="noopener noreferrer">
                <Button variant="ghost" size="sm" className="text-gray-300 hover:text-white p-2">
                  <Linkedin className="w-4 h-4" />
                </Button>
              </a>
            </div>
          </div>

          {/* Services */}
          <div className="space-y-4">
            <h3 className="font-semibold text-lg">Services</h3>
            <div className="space-y-2">
              <Link smooth to="/#services" className="block text-gray-300 hover:text-white text-sm transition-colors">
                SEO & Search Marketing
              </Link>
              <Link smooth to="/#services" className="block text-gray-300 hover:text-white text-sm transition-colors">
                Social Media Marketing
              </Link>
              <Link smooth to="/#services" className="block text-gray-300 hover:text-white text-sm transition-colors">
                Web Design & Development
              </Link>
              <Link smooth to="/#services" className="block text-gray-300 hover:text-white text-sm transition-colors">
                Analytics & Insights
              </Link>
              <Link smooth to="/#services" className="block text-gray-300 hover:text-white text-sm transition-colors">
                Content Marketing
              </Link>
            </div>
          </div>

          {/* Company */}
          <div className="space-y-4">
            <h3 className="font-semibold text-lg">Company</h3>
            <div className="space-y-2">
              <Link smooth to="/#about" className="block text-gray-300 hover:text-white text-sm transition-colors">
                About Us
              </Link>
              <Link smooth to="/#contact" className="block text-gray-300 hover:text-white text-sm transition-colors">
                Contact
              </Link>
              <Link to="/dashboard" className="block text-gray-300 hover:text-white text-sm transition-colors">
                Dashboard
              </Link>
              <Link to="/strategy-session" className="block text-gray-300 hover:text-white text-sm transition-colors">
                Strategy Session
              </Link>
              <Link smooth to="/#pricing" className="block text-gray-300 hover:text-white text-sm transition-colors">
                Pricing
              </Link>
            </div>
          </div>

          {/* Contact Info */}
          <div className="space-y-4">
            <h3 className="font-semibold text-lg">Contact Us</h3>
            <div className="space-y-3">
              <div className="flex items-center space-x-3 text-sm text-gray-300">
                <Mail className="w-4 h-4" />
                <span>hello@pixelcraft.com</span>
              </div>
              <div className="flex items-center space-x-3 text-sm text-gray-300">
                <Phone className="w-4 h-4" />
                <span>+44 1234 567890</span>
              </div>
              <div className="flex items-center space-x-3 text-sm text-gray-300">
                <MapPin className="w-4 h-4" />
                <span>West Midlands, UK</span>
              </div>
            </div>

            {/* Newsletter Signup */}
            <div className="space-y-2">
              <h4 className="font-medium text-sm">Stay Updated</h4>
              <div className="flex space-x-2">
                <Input
                  placeholder="Enter your email"
                  className="bg-gray-800 border-gray-700 text-white placeholder-gray-400"
                />
                <Button size="sm" className="bg-gradient-primary hover:bg-gradient-primary/90">
                  Subscribe
                </Button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <Separator className="bg-gray-700" />

      {/* Bottom Footer */}
      <div className="container mx-auto px-4 py-6">
        <div className="flex flex-col md:flex-row items-center justify-between space-y-4 md:space-y-0">
          <div className="flex items-center space-x-4 text-sm text-gray-400">
            <span>&copy; {currentYear} PixelCraft. All rights reserved.</span>
            <Link to="/privacy" className="hover:text-white transition-colors">
              Privacy Policy
            </Link>
            <Link to="/terms" className="hover:text-white transition-colors">
              Terms of Service
            </Link>
          </div>

          <div className="flex items-center space-x-4">
            <span className="text-sm text-gray-400">Trusted by 500+ businesses worldwide</span>
            <Button
              variant="ghost"
              size="sm"
              onClick={scrollToTop}
              className="text-gray-400 hover:text-white"
            >
              <ArrowUp className="w-4 h-4 mr-1" />
              Back to Top
            </Button>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;