import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { useToast } from "@/hooks/use-toast";
import SEOHead from "@/components/SEOHead";
import { 
  CheckCircle, 
  Calendar, 
  Clock, 
  Users, 
  TrendingUp, 
  ArrowLeft,
  Star,
  Phone,
  Video,
  MessageSquare
} from "lucide-react";

const StrategySession = () => {
  const [formData, setFormData] = useState({
    firstName: '',
    lastName: '',
    email: '',
    company: '',
    phone: '',
    website: '',
    currentMarketing: '',
    goals: '',
    budget: '',
    timeline: '',
    preferredContact: 'phone'
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
    
    // Simulate form submission
    setTimeout(() => {
      toast({
        title: "Strategy Session Requested!",
        description: "We'll contact you within 24 hours to schedule your free consultation.",
      });
      setIsSubmitting(false);
      // Reset form
      setFormData({
        firstName: '',
        lastName: '',
        email: '',
        company: '',
        phone: '',
        website: '',
        currentMarketing: '',
        goals: '',
        budget: '',
        timeline: '',
        preferredContact: 'phone'
      });
    }, 1000);
  };

  const benefits = [
    "Comprehensive digital marketing audit",
    "Custom growth strategy roadmap",
    "ROI projections and timeline",
    "Competitive analysis insights",
    "Technology stack recommendations",
    "Team and budget optimization tips"
  ];

  const processSteps = [
    {
      icon: <MessageSquare className="w-6 h-6" />,
      title: "Discovery Call",
      description: "We'll discuss your business goals, challenges, and current marketing efforts"
    },
    {
      icon: <TrendingUp className="w-6 h-6" />,
      title: "Strategy Development",
      description: "Our experts create a customized growth strategy tailored to your business"
    },
    {
      icon: <CheckCircle className="w-6 h-6" />,
      title: "Action Plan",
      description: "Receive a detailed roadmap with prioritized recommendations and next steps"
    }
  ];

  const testimonials = [
    {
      name: "Sarah Johnson",
      company: "TechStart Inc.",
      text: "The strategy session gave us clarity on our marketing direction. We saw 150% growth in just 6 months!",
      rating: 5
    },
    {
      name: "Mike Chen",
      company: "GrowthCorp",
      text: "Best investment we made. The insights from the session transformed our entire approach to digital marketing.",
      rating: 5
    }
  ];

  const strategySchema = {
    "@context": "https://schema.org",
    "@type": "Service",
    "name": "Free Digital Marketing Strategy Session",
    "description": "Comprehensive digital marketing consultation to develop custom growth strategies for businesses",
    "provider": {
      "@type": "Organization",
      "name": "PixelCraft Digital Marketing"
    },
    "offers": {
      "@type": "Offer",
      "price": "0",
      "priceCurrency": "USD",
      "description": "Free 60-minute strategy consultation"
    },
    "aggregateRating": {
      "@type": "AggregateRating",
      "ratingValue": "5.0",
      "reviewCount": "200"
    }
  };

  return (
    <>
      <SEOHead
        title="Free Digital Marketing Strategy Session | PixelCraft"
        description="Get a free 60-minute digital marketing strategy session. Discover growth opportunities, receive custom recommendations, and create your roadmap to success."
        keywords="free marketing consultation, strategy session, digital marketing audit, marketing strategy, business growth consultation"
        canonical="https://pixelcraft.lovable.app/strategy-session"
        schema={strategySchema}
      />
      
      <div className="min-h-screen bg-gradient-subtle">
        {/* Header */}
        <header className="bg-gradient-hero text-white py-8">
          <div className="container mx-auto px-4">
            <Link 
              to="/" 
              className="inline-flex items-center gap-2 text-white/80 hover:text-white transition-colors mb-4"
            >
              <ArrowLeft className="w-4 h-4" />
              Back to Home
            </Link>
            <div className="max-w-4xl">
              <Badge variant="secondary" className="mb-4 bg-white/10 text-white border-white/20">
                Limited Time Offer
              </Badge>
              <h1 className="text-4xl md:text-6xl font-bold mb-6 leading-tight">
                Get Your Free
                <span className="block bg-gradient-to-r from-white to-purple-200 bg-clip-text text-transparent">
                  Strategy Session
                </span>
              </h1>
              <p className="text-xl text-gray-200 mb-8 leading-relaxed max-w-3xl">
                Discover untapped growth opportunities with a personalized 60-minute consultation. 
                Our experts will analyze your business and create a custom roadmap for success.
              </p>
              <div className="flex items-center gap-6 text-sm">
                <div className="flex items-center gap-2">
                  <Clock className="w-4 h-4" />
                  <span>60 Minutes</span>
                </div>
                <div className="flex items-center gap-2">
                  <Users className="w-4 h-4" />
                  <span>1-on-1 Expert Consultation</span>
                </div>
                <div className="flex items-center gap-2">
                  <TrendingUp className="w-4 h-4" />
                  <span>Custom Growth Strategy</span>
                </div>
              </div>
            </div>
          </div>
        </header>

        <main className="container mx-auto px-4 py-16">
          <div className="grid lg:grid-cols-2 gap-16">
            {/* Left Column - Information */}
            <div className="space-y-12">
              {/* What You'll Get */}
              <section>
                <h2 className="text-3xl font-bold mb-6">What You'll Receive</h2>
                <div className="grid gap-4">
                  {benefits.map((benefit, index) => (
                    <div key={index} className="flex items-start gap-3">
                      <CheckCircle className="w-5 h-5 text-green-500 mt-1 flex-shrink-0" />
                      <span className="text-gray-700">{benefit}</span>
                    </div>
                  ))}
                </div>
              </section>

              <Separator />

              {/* Process */}
              <section>
                <h2 className="text-3xl font-bold mb-6">Our Process</h2>
                <div className="space-y-6">
                  {processSteps.map((step, index) => (
                    <div key={index} className="flex gap-4">
                      <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center flex-shrink-0">
                        {step.icon}
                      </div>
                      <div>
                        <h3 className="font-semibold text-lg mb-1">{step.title}</h3>
                        <p className="text-gray-600">{step.description}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </section>

              <Separator />

              {/* Testimonials */}
              <section>
                <h2 className="text-3xl font-bold mb-6">What Others Say</h2>
                <div className="space-y-6">
                  {testimonials.map((testimonial, index) => (
                    <Card key={index} className="p-6">
                      <div className="flex items-center gap-1 mb-3">
                        {[...Array(testimonial.rating)].map((_, i) => (
                          <Star key={i} className="w-4 h-4 fill-yellow-400 text-yellow-400" />
                        ))}
                      </div>
                      <p className="text-gray-700 mb-4 italic">"{testimonial.text}"</p>
                      <div>
                        <div className="font-semibold">{testimonial.name}</div>
                        <div className="text-sm text-gray-500">{testimonial.company}</div>
                      </div>
                    </Card>
                  ))}
                </div>
              </section>
            </div>

            {/* Right Column - Form */}
            <div className="lg:sticky lg:top-8">
              <Card className="shadow-glow">
                <CardHeader>
                  <CardTitle className="text-2xl font-bold text-center">
                    Book Your Free Session
                  </CardTitle>
                  <p className="text-center text-gray-600">
                    Fill out the form below and we'll contact you within 24 hours
                  </p>
                </CardHeader>
                <CardContent>
                  <form onSubmit={handleSubmit} className="space-y-6">
                    <div className="grid grid-cols-2 gap-4">
                      <Input
                        name="firstName"
                        placeholder="First Name"
                        value={formData.firstName}
                        onChange={handleInputChange}
                        required
                      />
                      <Input
                        name="lastName"
                        placeholder="Last Name"
                        value={formData.lastName}
                        onChange={handleInputChange}
                        required
                      />
                    </div>
                    
                    <Input
                      name="email"
                      type="email"
                      placeholder="Email Address"
                      value={formData.email}
                      onChange={handleInputChange}
                      required
                    />
                    
                    <Input
                      name="company"
                      placeholder="Company Name"
                      value={formData.company}
                      onChange={handleInputChange}
                      required
                    />
                    
                    <Input
                      name="phone"
                      placeholder="Phone Number"
                      value={formData.phone}
                      onChange={handleInputChange}
                      required
                    />
                    
                    <Input
                      name="website"
                      placeholder="Website URL (if applicable)"
                      value={formData.website}
                      onChange={handleInputChange}
                    />

                    <div>
                      <label className="text-sm font-medium mb-2 block">Current Marketing Efforts</label>
                      <Textarea
                        name="currentMarketing"
                        placeholder="Tell us about your current marketing activities..."
                        value={formData.currentMarketing}
                        onChange={handleInputChange}
                        className="min-h-[80px]"
                      />
                    </div>

                    <div>
                      <label className="text-sm font-medium mb-2 block">Primary Goals</label>
                      <Textarea
                        name="goals"
                        placeholder="What are your main business goals for the next 12 months?"
                        value={formData.goals}
                        onChange={handleInputChange}
                        className="min-h-[80px]"
                        required
                      />
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="text-sm font-medium mb-2 block">Monthly Budget Range</label>
                        <select
                          name="budget"
                          value={formData.budget}
                          onChange={handleInputChange}
                          className="w-full p-3 border border-gray-200 rounded-md"
                          required
                        >
                          <option value="">Select Range</option>
                          <option value="under-1k">Under $1,000</option>
                          <option value="1k-5k">$1,000 - $5,000</option>
                          <option value="5k-10k">$5,000 - $10,000</option>
                          <option value="10k-25k">$10,000 - $25,000</option>
                          <option value="25k-plus">$25,000+</option>
                        </select>
                      </div>
                      
                      <div>
                        <label className="text-sm font-medium mb-2 block">Timeline</label>
                        <select
                          name="timeline"
                          value={formData.timeline}
                          onChange={handleInputChange}
                          className="w-full p-3 border border-gray-200 rounded-md"
                          required
                        >
                          <option value="">Select Timeline</option>
                          <option value="asap">ASAP</option>
                          <option value="1-month">Within 1 month</option>
                          <option value="3-months">Within 3 months</option>
                          <option value="6-months">Within 6 months</option>
                        </select>
                      </div>
                    </div>

                    <div>
                      <label className="text-sm font-medium mb-3 block">Preferred Contact Method</label>
                      <div className="grid grid-cols-3 gap-2">
                        {[
                          { value: 'phone', icon: <Phone className="w-4 h-4" />, label: 'Phone' },
                          { value: 'video', icon: <Video className="w-4 h-4" />, label: 'Video Call' },
                          { value: 'email', icon: <MessageSquare className="w-4 h-4" />, label: 'Email' }
                        ].map((method) => (
                          <label key={method.value} className="flex items-center gap-2 p-3 border rounded-lg cursor-pointer hover:bg-gray-50">
                            <input
                              type="radio"
                              name="preferredContact"
                              value={method.value}
                              checked={formData.preferredContact === method.value}
                              onChange={handleInputChange}
                              className="sr-only"
                            />
                            <div className={`w-4 h-4 rounded-full border-2 ${formData.preferredContact === method.value ? 'bg-primary border-primary' : 'border-gray-300'}`} />
                            {method.icon}
                            <span className="text-sm">{method.label}</span>
                          </label>
                        ))}
                      </div>
                    </div>

                    <Button 
                      type="submit" 
                      variant="premium" 
                      size="lg" 
                      className="w-full text-lg py-6 h-auto"
                      disabled={isSubmitting}
                    >
                      {isSubmitting ? "Scheduling..." : "Get My Free Strategy Session"}
                    </Button>

                    <p className="text-xs text-center text-gray-500">
                      <CheckCircle className="w-4 h-4 inline mr-1 text-green-500" />
                      100% Free • No Obligation • Expert Analysis Included
                    </p>
                  </form>
                </CardContent>
              </Card>
            </div>
          </div>
        </main>
      </div>
    </>
  );
};

export default StrategySession;