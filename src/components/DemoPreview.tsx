import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Play, Eye, TrendingUp, Users, MessageSquare } from 'lucide-react';

const DemoPreview = () => {
  const [activeDemo, setActiveDemo] = useState('overview');

  const demos = [
    {
      id: 'overview',
      title: 'AI Agent Dashboard',
      description: 'See how our AI agents work in real-time',
      icon: Eye,
      preview: 'Live dashboard showing agent performance, lead scoring, and automated responses.'
    },
    {
      id: 'analytics',
      title: 'Performance Analytics',
      description: 'Real-time insights and reporting',
      icon: TrendingUp,
      preview: 'Interactive charts showing conversion rates, ROI, and campaign performance metrics.'
    },
    {
      id: 'automation',
      title: 'Lead Qualification',
      description: 'Watch AI qualify leads automatically',
      icon: Users,
      preview: 'Automated lead scoring, qualification, and routing to the right team member.'
    },
    {
      id: 'chat',
      title: 'AI Chat Assistant',
      description: 'Intelligent customer conversations',
      icon: MessageSquare,
      preview: 'AI-powered chat that handles customer inquiries, schedules appointments, and provides instant support.'
    }
  ];

  return (
    <section className="py-24 bg-gradient-subtle">
      <div className="container mx-auto px-4">
        {/* Header */}
        <div className="text-center mb-16">
          <div className="inline-flex items-center gap-2 bg-purple-100 border border-purple-200 rounded-full px-6 py-2 mb-6">
            <Play className="w-4 h-4 text-purple-600" />
            <span className="text-sm font-medium text-purple-800">Interactive Demo</span>
          </div>
          <h2 className="text-4xl md:text-5xl font-bold mb-6 text-foreground">
            See Our AI <span className="bg-gradient-primary bg-clip-text text-transparent">In Action</span>
          </h2>
          <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
            Experience how PixelCraft's AI agents can transform your digital marketing.
            Interactive demos of our most popular features.
          </p>
        </div>

        <div className="max-w-6xl mx-auto">
          <Tabs value={activeDemo} onValueChange={setActiveDemo} className="w-full">
            {/* Demo Tabs */}
            <TabsList className="grid w-full grid-cols-2 lg:grid-cols-4 mb-8">
              {demos.map((demo) => {
                const IconComponent = demo.icon;
                return (
                  <TabsTrigger
                    key={demo.id}
                    value={demo.id}
                    className="flex items-center gap-2 p-4"
                  >
                    <IconComponent className="w-4 h-4" />
                    <span className="hidden sm:inline">{demo.title}</span>
                  </TabsTrigger>
                );
              })}
            </TabsList>

            {/* Demo Content */}
            {demos.map((demo) => (
              <TabsContent key={demo.id} value={demo.id} className="space-y-6">
                <div className="grid lg:grid-cols-2 gap-8 items-center">
                  {/* Demo Description */}
                  <div className="space-y-6">
                    <div>
                      <h3 className="text-2xl font-bold mb-4">{demo.title}</h3>
                      <p className="text-muted-foreground text-lg mb-6">
                        {demo.description}
                      </p>
                      <p className="text-gray-600">
                        {demo.preview}
                      </p>
                    </div>

                    <div className="space-y-3">
                      <div className="flex items-center gap-3">
                        <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                        <span className="text-sm">Real-time processing</span>
                      </div>
                      <div className="flex items-center gap-3">
                        <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                        <span className="text-sm">Automated workflows</span>
                      </div>
                      <div className="flex items-center gap-3">
                        <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                        <span className="text-sm">Data-driven insights</span>
                      </div>
                      <div className="flex items-center gap-3">
                        <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                        <span className="text-sm">24/7 availability</span>
                      </div>
                    </div>

                    <div className="flex flex-col sm:flex-row gap-3">
                      <Button className="bg-gradient-primary hover:bg-gradient-primary/90">
                        <Play className="w-4 h-4 mr-2" />
                        Start Live Demo
                      </Button>
                      <Button variant="outline">
                        Schedule Demo Call
                      </Button>
                    </div>
                  </div>

                  {/* Demo Preview */}
                  <div className="relative">
                    <Card className="border-0 bg-gray-900 text-white overflow-hidden">
                      <div className="absolute top-4 right-4">
                        <Badge variant="secondary" className="bg-green-500/20 text-green-400 border-green-500/30">
                          Live Demo
                        </Badge>
                      </div>

                      <CardContent className="p-6">
                        <div className="space-y-4">
                          {/* Simulated Demo Interface */}
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                              <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
                              <span className="text-sm font-medium">AI Agent Active</span>
                            </div>
                            <div className="text-xs text-gray-400">
                              {new Date().toLocaleTimeString()}
                            </div>
                          </div>

                          <div className="space-y-3">
                            <div className="p-3 bg-gray-800 rounded-lg">
                              <div className="text-sm text-gray-300 mb-1">User Query:</div>
                              <div className="text-sm">"I need help with SEO for my e-commerce site"</div>
                            </div>

                            <div className="p-3 bg-blue-600/20 border border-blue-500/30 rounded-lg">
                              <div className="text-sm text-blue-300 mb-1">AI Response:</div>
                              <div className="text-sm">"I'd be happy to help! Let me analyze your site and create a custom SEO strategy..."</div>
                            </div>

                            <div className="flex items-center justify-between text-xs text-gray-400">
                              <span>Processing time: 0.3s</span>
                              <span>Confidence: 95%</span>
                            </div>
                          </div>
                        </div>
                      </CardContent>
                    </Card>

                    {/* Floating Elements */}
                    <div className="absolute -top-4 -right-4 w-8 h-8 bg-gradient-primary rounded-full animate-pulse"></div>
                    <div className="absolute -bottom-4 -left-4 w-6 h-6 bg-purple-500 rounded-full animate-pulse delay-300"></div>
                  </div>
                </div>
              </TabsContent>
            ))}
          </Tabs>
        </div>

        {/* Bottom CTA */}
        <div className="text-center mt-16">
          <div className="bg-gradient-primary/5 border border-gradient-primary/20 rounded-lg p-8 max-w-4xl mx-auto">
            <h3 className="text-2xl font-bold mb-4">Ready to Experience the Difference?</h3>
            <p className="text-muted-foreground mb-6 max-w-2xl mx-auto">
              See how PixelCraft's AI agents can transform your business operations.
              Book a personalized demo today.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button className="bg-gradient-primary hover:bg-gradient-primary/90">
                <Play className="w-4 h-4 mr-2" />
                Schedule Live Demo
              </Button>
              <Button variant="outline">
                View Case Studies
              </Button>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default DemoPreview;