import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Calculator, TrendingUp, DollarSign, Users, Target } from 'lucide-react';

interface ROIData {
  monthlyRevenue: number;
  monthlyLeads: number;
  conversionRate: number;
  industry: string;
  currentSpend: number;
}

const industryMultipliers = {
  'ecommerce': 2.5,
  'saas': 3.2,
  'professional-services': 2.8,
  'healthcare': 2.1,
  'technology': 3.5,
  'retail': 2.3,
  'other': 2.0
};

const ROICalculator = () => {
  const [roiData, setRoiData] = useState<ROIData>({
    monthlyRevenue: 10000,
    monthlyLeads: 100,
    conversionRate: 3,
    industry: 'saas',
    currentSpend: 2000
  });

  const [results, setResults] = useState<any>(null);

  const calculateROI = () => {
    const { monthlyRevenue, monthlyLeads, conversionRate, industry, currentSpend } = roiData;

    // Calculate current metrics
    const currentCustomers = monthlyLeads * (conversionRate / 100);
    const currentMonthlyRevenue = currentCustomers * (monthlyRevenue / monthlyLeads);

    // Calculate potential improvements with PixelCraft
    const multiplier = industryMultipliers[industry as keyof typeof industryMultipliers] || 2.0;

    const improvedLeads = monthlyLeads * multiplier;
    const improvedConversionRate = Math.min(conversionRate * 1.8, 15); // Cap at 15%
    const improvedCustomers = improvedLeads * (improvedConversionRate / 100);
    const improvedMonthlyRevenue = improvedCustomers * (monthlyRevenue / monthlyLeads);

    const revenueIncrease = improvedMonthlyRevenue - currentMonthlyRevenue;
    const newSpend = currentSpend * 1.5; // Assume 50% increase in spend
    const netProfit = revenueIncrease - newSpend;
    const roiPercentage = newSpend > 0 ? (netProfit / newSpend) * 100 : 0;

    setResults({
      current: {
        leads: monthlyLeads,
        conversionRate,
        customers: Math.round(currentCustomers),
        revenue: Math.round(currentMonthlyRevenue)
      },
      improved: {
        leads: Math.round(improvedLeads),
        conversionRate: Math.round(improvedConversionRate * 100) / 100,
        customers: Math.round(improvedCustomers),
        revenue: Math.round(improvedMonthlyRevenue)
      },
      metrics: {
        revenueIncrease: Math.round(revenueIncrease),
        newSpend: Math.round(newSpend),
        netProfit: Math.round(netProfit),
        roiPercentage: Math.round(roiPercentage)
      }
    });
  };

  const updateData = (field: keyof ROIData, value: any) => {
    setRoiData(prev => ({
      ...prev,
      [field]: field === 'industry' ? value : Number(value)
    }));
  };

  return (
    <section className="py-24 bg-white">
      <div className="container mx-auto px-4">
        {/* Header */}
        <div className="text-center mb-16">
          <div className="inline-flex items-center gap-2 bg-green-100 border border-green-200 rounded-full px-6 py-2 mb-6">
            <Calculator className="w-4 h-4 text-green-600" />
            <span className="text-sm font-medium text-green-800">ROI Calculator</span>
          </div>
          <h2 className="text-4xl md:text-5xl font-bold mb-6 text-foreground">
            Calculate Your <span className="bg-gradient-primary bg-clip-text text-transparent">Potential ROI</span>
          </h2>
          <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
            See how much PixelCraft's AI-powered strategies could increase your revenue.
            Based on real results from 500+ clients.
          </p>
        </div>

        <div className="max-w-6xl mx-auto">
          <div className="grid lg:grid-cols-2 gap-8">
            {/* Input Form */}
            <Card className="border-0 bg-gray-50/50">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Calculator className="w-5 h-5" />
                  Your Business Metrics
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="revenue">Monthly Revenue (£)</Label>
                    <Input
                      id="revenue"
                      type="number"
                      value={roiData.monthlyRevenue}
                      onChange={(e) => updateData('monthlyRevenue', e.target.value)}
                      placeholder="10000"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="leads">Monthly Leads</Label>
                    <Input
                      id="leads"
                      type="number"
                      value={roiData.monthlyLeads}
                      onChange={(e) => updateData('monthlyLeads', e.target.value)}
                      placeholder="100"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="conversion">Conversion Rate (%)</Label>
                  <Input
                    id="conversion"
                    type="number"
                    step="0.1"
                    value={roiData.conversionRate}
                    onChange={(e) => updateData('conversionRate', e.target.value)}
                    placeholder="3"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="industry">Industry</Label>
                  <Select value={roiData.industry} onValueChange={(value) => updateData('industry', value)}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select your industry" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="ecommerce">E-commerce</SelectItem>
                      <SelectItem value="saas">SaaS</SelectItem>
                      <SelectItem value="professional-services">Professional Services</SelectItem>
                      <SelectItem value="healthcare">Healthcare</SelectItem>
                      <SelectItem value="technology">Technology</SelectItem>
                      <SelectItem value="retail">Retail</SelectItem>
                      <SelectItem value="other">Other</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="spend">Current Monthly Marketing Spend (£)</Label>
                  <Input
                    id="spend"
                    type="number"
                    value={roiData.currentSpend}
                    onChange={(e) => updateData('currentSpend', e.target.value)}
                    placeholder="2000"
                  />
                </div>

                <Button onClick={calculateROI} className="w-full">
                  Calculate My ROI
                </Button>
              </CardContent>
            </Card>

            {/* Results */}
            <div className="space-y-6">
              {results ? (
                <>
                  {/* Results Cards */}
                  <div className="grid md:grid-cols-2 gap-4">
                    <Card className="border-0 bg-red-50">
                      <CardContent className="p-6 text-center">
                        <div className="text-2xl font-bold text-red-600 mb-2">
                          {results.current.revenue.toLocaleString()}
                        </div>
                        <div className="text-sm text-red-800">Current Monthly Revenue</div>
                      </CardContent>
                    </Card>

                    <Card className="border-0 bg-green-50">
                      <CardContent className="p-6 text-center">
                        <div className="text-2xl font-bold text-green-600 mb-2">
                          {results.improved.revenue.toLocaleString()}
                        </div>
                        <div className="text-sm text-green-800">Potential Monthly Revenue</div>
                      </CardContent>
                    </Card>
                  </div>

                  {/* ROI Metrics */}
                  <Card className="border-0 bg-gradient-primary/5">
                    <CardContent className="p-6 space-y-4">
                      <div className="flex items-center gap-2 mb-4">
                        <TrendingUp className="w-5 h-5 text-green-600" />
                        <span className="font-semibold text-lg">Your Potential Results</span>
                      </div>

                      <div className="grid md:grid-cols-2 gap-4">
                        <div className="text-center">
                          <div className="text-2xl font-bold text-green-600">
                            +£{results.metrics.revenueIncrease.toLocaleString()}
                          </div>
                          <div className="text-sm text-muted-foreground">Monthly Revenue Increase</div>
                        </div>
                        <div className="text-center">
                          <div className="text-2xl font-bold text-blue-600">
                            {results.metrics.roiPercentage}%
                          </div>
                          <div className="text-sm text-muted-foreground">ROI on Investment</div>
                        </div>
                      </div>

                      <div className="pt-4 border-t border-gray-200">
                        <div className="flex justify-between items-center mb-2">
                          <span className="text-sm">New Monthly Investment:</span>
                          <span className="font-medium">£{results.metrics.newSpend.toLocaleString()}</span>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-sm">Net Monthly Profit:</span>
                          <span className="font-medium text-green-600">+£{results.metrics.netProfit.toLocaleString()}</span>
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  {/* Call to Action */}
                  <Card className="border-0 bg-gradient-primary text-white">
                    <CardContent className="p-6 text-center space-y-4">
                      <DollarSign className="w-12 h-12 mx-auto text-white/80" />
                      <div>
                        <h3 className="text-xl font-bold mb-2">Ready to Achieve These Results?</h3>
                        <p className="text-white/90 mb-4">
                          Based on our average client performance, you could see similar growth within 90 days.
                        </p>
                        <div className="flex flex-col sm:flex-row gap-3 justify-center">
                          <a href="/strategy-session" className="inline-flex items-center justify-center px-6 py-3 bg-white text-primary rounded-lg hover:bg-gray-100 transition-colors font-medium">
                            Get Free Strategy Session
                          </a>
                          <a href="#contact" className="inline-flex items-center justify-center px-6 py-3 border border-white/30 text-white rounded-lg hover:bg-white/10 transition-colors font-medium">
                            Learn More
                          </a>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </>
              ) : (
                <Card className="border-0 bg-gray-50/50">
                  <CardContent className="p-8 text-center space-y-4">
                    <Calculator className="w-16 h-16 mx-auto text-gray-400" />
                    <h3 className="text-xl font-semibold">Calculate Your ROI</h3>
                    <p className="text-muted-foreground">
                      Enter your business metrics above to see your potential growth with PixelCraft.
                    </p>
                    <div className="grid md:grid-cols-2 gap-4 mt-6">
                      <div className="text-center">
                        <div className="text-2xl font-bold text-primary">300%</div>
                        <div className="text-sm text-muted-foreground">Average ROI</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-primary">90 Days</div>
                        <div className="text-sm text-muted-foreground">To See Results</div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default ROICalculator;