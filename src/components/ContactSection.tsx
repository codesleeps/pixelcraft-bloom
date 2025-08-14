import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Mail, Phone, MapPin, Clock } from "lucide-react";
import { Link } from "react-router-dom";

const ContactSection = () => {
  return (
    <section className="py-24 bg-gradient-hero relative overflow-hidden">
      {/* Background Elements */}
      <div className="absolute inset-0 bg-gradient-hero opacity-95" />
      <div className="absolute top-10 right-10 w-64 h-64 bg-white/5 rounded-full blur-3xl" />
      <div className="absolute bottom-10 left-10 w-48 h-48 bg-purple-400/10 rounded-full blur-2xl" />
      
      <div className="relative z-10 container mx-auto px-4">
        <div className="grid lg:grid-cols-2 gap-16 items-start">
          {/* Left Content */}
          <div className="text-white">
            <Badge variant="secondary" className="mb-4 bg-white/10 text-white border-white/20">
              Get Started Today
            </Badge>
            <h2 className="text-4xl md:text-5xl font-bold mb-6">
              Ready to Accelerate
              <span className="block text-purple-200">Your Growth?</span>
            </h2>
            <p className="text-xl text-gray-200 mb-12 leading-relaxed">
              Let's discuss how we can transform your digital presence and drive 
              measurable results for your business. Get a free consultation today.
            </p>
            
            {/* Contact Info */}
            <div className="space-y-6">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-white/10 rounded-lg flex items-center justify-center">
                  <Mail className="w-6 h-6" />
                </div>
                <div>
                  <div className="font-semibold">Email Us</div>
                  <div className="text-gray-300">hello@digitalmarketingco.com</div>
                </div>
              </div>
              
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-white/10 rounded-lg flex items-center justify-center">
                  <Phone className="w-6 h-6" />
                </div>
                <div>
                  <div className="font-semibold">Call Us</div>
                  <div className="text-gray-300">+1 (555) 123-4567</div>
                </div>
              </div>
              
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-white/10 rounded-lg flex items-center justify-center">
                  <MapPin className="w-6 h-6" />
                </div>
                <div>
                  <div className="font-semibold">Visit Us</div>
                  <div className="text-gray-300">123 Business District, NYC</div>
                </div>
              </div>
              
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-white/10 rounded-lg flex items-center justify-center">
                  <Clock className="w-6 h-6" />
                </div>
                <div>
                  <div className="font-semibold">Business Hours</div>
                  <div className="text-gray-300">Mon-Fri: 9AM-6PM EST</div>
                </div>
              </div>
            </div>
          </div>
          
          {/* Right Content - Contact Form */}
          <Card className="bg-white/95 backdrop-blur-sm border-0 shadow-glow">
            <CardHeader>
              <CardTitle className="text-2xl font-bold text-center">
                Get Your Free Consultation
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-2 gap-4">
                <Input placeholder="First Name" className="border-gray-200" />
                <Input placeholder="Last Name" className="border-gray-200" />
              </div>
              <Input placeholder="Email Address" type="email" className="border-gray-200" />
              <Input placeholder="Company Name" className="border-gray-200" />
              <Input placeholder="Phone Number" className="border-gray-200" />
              <Textarea 
                placeholder="Tell us about your marketing goals and challenges..." 
                className="min-h-[120px] border-gray-200" 
              />
              
              {/* Services Interest */}
              <div>
                <label className="text-sm font-medium mb-3 block">Services of Interest:</label>
                <div className="grid grid-cols-2 gap-2">
                  {["SEO", "Social Media", "Web Design", "PPC", "Analytics", "Content"].map((service) => (
                    <label key={service} className="flex items-center gap-2 text-sm">
                      <input type="checkbox" className="rounded border-gray-300" />
                      {service}
                    </label>
                  ))}
                </div>
              </div>
              
              <Link to="/strategy-session">
                <Button variant="premium" size="lg" className="w-full text-lg py-6 h-auto">
                  Get My Free Strategy Session
                </Button>
              </Link>
              
              <p className="text-xs text-center text-gray-500">
                No spam, ever. We respect your privacy and will only send you relevant updates.
              </p>
            </CardContent>
          </Card>
        </div>
      </div>
    </section>
  );
};

export default ContactSection;