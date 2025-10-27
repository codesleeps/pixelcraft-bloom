import { Link } from 'react-router-dom';
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { useToast } from "@/hooks/use-toast";
import SEOHead from "@/components/SEOHead";
import { BackToTopButton } from "@/components/BackToTopButton";
import { useState } from 'react';
import { 
  CheckCircle, 
  ArrowLeft,
  Users,
  TrendingUp,
  Award,
  Globe,
  Handshake,
  DollarSign,
  Target,
  Zap,
  Shield,
  Rocket
} from "lucide-react";

const Partnership = () => {
  const [formData, setFormData] = useState({
    companyName: '',
    contactName: '',
    email: '',
    phone: '',
    website: '',
    industry: '',
    partnershipType: '',
    currentClients: '',
    monthlyRevenue: '',
    message: ''
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { toast } = useToast();

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    
    setTimeout(() => {
      toast({
        title: "Partnership Application Submitted!",
        description: "Our partnership team will review your application and contact you within 48 hours.",
      });
      setIsSubmitting(false);
      setFormData({
        companyName: '',
        contactName: '',
        email: '',
        phone: '',
        website: '',
        industry: '',
        partnershipType: '',
        currentClients: '',
        monthlyRevenue: '',
        message: ''
      });
    }, 1000);
  };

  const benefits = [
    {
      icon: <DollarSign className="w-6 h-6" />,
      title: "Revenue Sharing",
      description: "Earn up to 30% recurring commission on referred clients"
    },
    {
      icon: <Target className="w-6 h-6" />,
      title: "Lead Generation",
      description: "Access our proven lead generation systems and resources"
    },
    {
      icon: <Zap className="w-6 h-6" />,
      title: "White Label Solutions",
      description: "Offer our services under your brand with full support"
    },
    {
      icon: <Shield className="w-6 h-6" />,
      title: "Training & Support",
      description: "Comprehensive training and ongoing support for your team"
    },
    {
      icon: <Rocket className="w-6 h-6" />,
      title: "Growth Acceleration",
      description: "Scale your business faster with our proven methodologies"
    },
    {
      icon: <Award className="w-6 h-6" />,
      title: "Recognition Program",
      description: "Top partners receive exclusive rewards and recognition"
    }
  ];

  const partnershipTypes = [
    {
      title: "Referral Partner",
      description: "Refer clients and earn commission on every successful conversion",
      ideal: "Consultants, agencies, freelancers"
    },
    {
      title: "Reseller Partner",
      description: "Sell our services under your brand with white-label solutions",
      ideal: "Marketing agencies, web developers"
    },
    {
      title: "Technology Partner",
      description: "Integrate your solutions with our platform for mutual benefit",
      ideal: "SaaS companies, tool providers"
    },
    {
      title: "Strategic Alliance",
      description: "Long-term partnership for co-marketing and joint ventures",
      ideal: "Established businesses, enterprise companies"
    }
  ];

  const partnershipSchema = {
    "@context": "https://schema.org",
    "@type": "Service",
    "name": "PixelCraft Partnership Program",
    "description": "Join our partnership program and grow your business with our proven digital marketing solutions",
    "provider": {
      "@type": "Organization",
      "name": "PixelCraft Digital Marketing"
    }
  };

  return (
    <>
      <SEOHead
        title="Partnership Program | Join PixelCraft Partners"
        description="Join our partnership program and earn up to 30% commission. White-label solutions, training, and support available. Apply now!"
        keywords="partnership program, affiliate marketing, white label, reseller program, marketing partnership, revenue sharing"
        canonical="https://pixelcraft.lovable.app/partnership"
        schema={partnershipSchema}
      />
      
      <div className="min-h-screen bg-gradient-subtle">
        {/* Header */}
        <header className="bg-gradient-hero text-white py-16">
          <div className="container mx-auto px-4">
            <Link 
              to="/" 
              className="inline-flex items-center gap-2 text-white/80 hover:text-white transition-colors mb-8"
            >
              <ArrowLeft className="w-4 h-4" />
              Back to Home
            </Link>
            <div className="max-w-4xl">
              <Badge variant="secondary" className="mb-6 bg-white/10 text-white border-white/20">
                <Handshake className="w-4 h-4 mr-2" />
                Partnership Opportunities
              </Badge>
              <h1 className="text-4xl md:text-6xl font-bold mb-6 leading-tight">
                Partner With
                <span className="block bg-gradient-to-r from-white to-purple-200 bg-clip-text text-transparent">
                  PixelCraft
                </span>
              </h1>
              <p className="text-xl text-gray-200 mb-8 leading-relaxed max-w-3xl">
                Join our growing network of partners and unlock new revenue streams. 
                Whether you're an agency, consultant, or technology provider, we have the perfect partnership model for you.
              </p>
              <div className="flex items-center gap-6 text-sm">
                <div className="flex items-center gap-2">
                  <Users className="w-4 h-4" />
                  <span>500+ Active Partners</span>
                </div>
                <div className="flex items-center gap-2">
                  <TrendingUp className="w-4 h-4" />
                  <span>30% Commission Rate</span>
                </div>
                <div className="flex items-center gap-2">
                  <Globe className="w-4 h-4" />
                  <span>Global Opportunities</span>
                </div>
              </div>
            </div>
          </div>
        </header>

        <main className="container mx-auto px-4 py-16">
          {/* Benefits Section */}
          <section className="mb-20">
            <div className="text-center mb-12">
              <h2 className="text-3xl md:text-4xl font-bold mb-4">Why Partner With Us?</h2>
              <p className="text-xl text-gray-600 max-w-3xl mx-auto">
                Join a proven partnership program that helps you grow your business while providing exceptional value to your clients.
              </p>
            </div>
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
              {benefits.map((benefit, index) => (
                <Card key={index} className="p-6 hover:shadow-card transition-all duration-300">
                  <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mb-4">
                    {benefit.icon}
                  </div>
                  <h3 className="text-xl font-semibold mb-2">{benefit.title}</h3>
                  <p className="text-gray-600">{benefit.description}</p>
                </Card>
              ))}
            </div>
          </section>

          <Separator className="my-16" />

          {/* Partnership Types */}
          <section className="mb-20">
            <div className="text-center mb-12">
              <h2 className="text-3xl md:text-4xl font-bold mb-4">Partnership Options</h2>
              <p className="text-xl text-gray-600 max-w-3xl mx-auto">
                Choose the partnership model that best fits your business goals and capabilities.
              </p>
            </div>
            <div className="grid md:grid-cols-2 gap-8">
              {partnershipTypes.map((type, index) => (
                <Card key={index} className="p-8 hover:shadow-card transition-all duration-300">
                  <h3 className="text-xl font-bold mb-3">{type.title}</h3>
                  <p className="text-gray-600 mb-4">{type.description}</p>
                  <div className="text-sm text-primary font-medium">
                    Ideal for: {type.ideal}
                  </div>
                </Card>
              ))}
            </div>
          </section>

          <Separator className="my-16" />

          {/* Application Form */}
          <section>
            <div className="max-w-4xl mx-auto">
              <div className="text-center mb-12">
                <h2 className="text-3xl md:text-4xl font-bold mb-4">Apply for Partnership</h2>
                <p className="text-xl text-gray-600">
                  Fill out the application below and our partnership team will review your submission.
                </p>
              </div>

              <Card className="shadow-glow">
                <CardHeader>
                  <CardTitle className="text-2xl font-bold text-center">
                    Partnership Application
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <form onSubmit={handleSubmit} className="space-y-6">
                    <div className="grid md:grid-cols-2 gap-6">
                      <div>
                        <label className="text-sm font-medium mb-2 block">Company Name *</label>
                        <Input
                          name="companyName"
                          placeholder="Your Company Name"
                          value={formData.companyName}
                          onChange={handleInputChange}
                          required
                        />
                      </div>
                      <div>
                        <label className="text-sm font-medium mb-2 block">Contact Name *</label>
                        <Input
                          name="contactName"
                          placeholder="Your Full Name"
                          value={formData.contactName}
                          onChange={handleInputChange}
                          required
                        />
                      </div>
                    </div>

                    <div className="grid md:grid-cols-2 gap-6">
                      <div>
                        <label className="text-sm font-medium mb-2 block">Email Address *</label>
                        <Input
                          name="email"
                          type="email"
                          placeholder="your@email.com"
                          value={formData.email}
                          onChange={handleInputChange}
                          required
                        />
                      </div>
                      <div>
                        <label className="text-sm font-medium mb-2 block">Phone Number *</label>
                        <Input
                          name="phone"
                          placeholder="Your Phone Number"
                          value={formData.phone}
                          onChange={handleInputChange}
                          required
                        />
                      </div>
                    </div>

                    <div className="grid md:grid-cols-2 gap-6">
                      <div>
                        <label className="text-sm font-medium mb-2 block">Website</label>
                        <Input
                          name="website"
                          placeholder="https://yourwebsite.com"
                          value={formData.website}
                          onChange={handleInputChange}
                        />
                      </div>
                      <div>
                        <label className="text-sm font-medium mb-2 block">Industry *</label>
                        <select
                          name="industry"
                          value={formData.industry}
                          onChange={handleInputChange}
                          className="w-full p-3 border border-gray-200 rounded-md"
                          required
                        >
                          <option value="">Select Industry</option>
                          <option value="marketing-agency">Marketing Agency</option>
                          <option value="web-development">Web Development</option>
                          <option value="consulting">Consulting</option>
                          <option value="technology">Technology/SaaS</option>
                          <option value="freelance">Freelance</option>
                          <option value="other">Other</option>
                        </select>
                      </div>
                    </div>

                    <div className="grid md:grid-cols-2 gap-6">
                      <div>
                        <label className="text-sm font-medium mb-2 block">Partnership Type *</label>
                        <select
                          name="partnershipType"
                          value={formData.partnershipType}
                          onChange={handleInputChange}
                          className="w-full p-3 border border-gray-200 rounded-md"
                          required
                        >
                          <option value="">Select Partnership Type</option>
                          <option value="referral">Referral Partner</option>
                          <option value="reseller">Reseller Partner</option>
                          <option value="technology">Technology Partner</option>
                          <option value="strategic">Strategic Alliance</option>
                        </select>
                      </div>
                      <div>
                        <label className="text-sm font-medium mb-2 block">Current Client Base</label>
                        <select
                          name="currentClients"
                          value={formData.currentClients}
                          onChange={handleInputChange}
                          className="w-full p-3 border border-gray-200 rounded-md"
                        >
                          <option value="">Select Range</option>
                          <option value="0-10">0-10 clients</option>
                          <option value="11-50">11-50 clients</option>
                          <option value="51-100">51-100 clients</option>
                          <option value="100+">100+ clients</option>
                        </select>
                      </div>
                    </div>

                    <div>
                      <label className="text-sm font-medium mb-2 block">Monthly Revenue Range</label>
                      <select
                        name="monthlyRevenue"
                        value={formData.monthlyRevenue}
                        onChange={handleInputChange}
                        className="w-full p-3 border border-gray-200 rounded-md"
                      >
                        <option value="">Select Range (Optional)</option>
                        <option value="under-10k">Under £10K</option>
                        <option value="10k-50k">£10K - £50K</option>
                        <option value="50k-100k">£50K - £100K</option>
                        <option value="100k-500k">£100K - £500K</option>
                        <option value="500k+">£500K+</option>
                      </select>
                    </div>

                    <div>
                      <label className="text-sm font-medium mb-2 block">Tell Us About Your Goals *</label>
                      <Textarea
                        name="message"
                        placeholder="Tell us about your business, your goals for this partnership, and how you plan to promote our services..."
                        value={formData.message}
                        onChange={handleInputChange}
                        className="min-h-[120px]"
                        required
                      />
                    </div>

                    <Button 
                      type="submit" 
                      variant="premium" 
                      size="lg" 
                      className="w-full text-lg py-6 h-auto"
                      disabled={isSubmitting}
                    >
                      {isSubmitting ? "Submitting Application..." : "Submit Partnership Application"}
                    </Button>

                    <p className="text-xs text-center text-gray-500">
                      <CheckCircle className="w-4 h-4 inline mr-1 text-green-500" />
                      Our partnership team will review your application within 48 hours
                    </p>
                  </form>
                </CardContent>
              </Card>
            </div>
          </section>
        </main>
        <BackToTopButton />
      </div>
    </>
  );
};

export default Partnership;