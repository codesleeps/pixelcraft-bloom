import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { supabase } from '@/integrations/supabase/client';
import { Check, X } from 'lucide-react';

interface PricingPackage {
  id: string;
  name: string;
  description: string | null;
  price_monthly: number | null;
  price_yearly: number | null;
  features: any; // Json from Supabase
  max_projects: number | null;
  max_team_members: number | null;
  priority: number;
  is_active: boolean;
}

interface PricingCampaign {
  id: string;
  name: string;
  code: string | null;
  discount_type: string;
  discount_value: number;
  max_uses: number | null;
  used_count: number;
  start_date: string | null;
  end_date: string | null;
  applicable_packages: string[] | null;
  is_active: boolean;
}

interface DiscountCalculation {
  original_price: number;
  discount_amount: number;
  final_price: number;
  discount_percentage: number | null;
  campaign_name: string | null;
}

const PricingSection = () => {
  const [packages, setPackages] = useState<PricingPackage[]>([]);
  const [loading, setLoading] = useState(true);
  const [billingCycle, setBillingCycle] = useState<'monthly' | 'yearly'>('monthly');
  const [discountCode, setDiscountCode] = useState('');
  const [discountCalc, setDiscountCalc] = useState<DiscountCalculation | null>(null);
  const [validatingCode, setValidatingCode] = useState(false);

  useEffect(() => {
    fetchPackages();
  }, []);

  const fetchPackages = async () => {
    try {
      const { data, error } = await supabase
        .from('pricing_packages')
        .select('*')
        .eq('is_active', true)
        .order('priority');

      if (error) throw error;

      // If no data, use fallback data
      if (!data || data.length === 0) {
        console.log('No pricing data found, using fallback data');
        const fallbackPackages: PricingPackage[] = [
          {
            id: '1',
            name: 'Starter',
            description: 'Perfect for small businesses and startups',
            price_monthly: 99,
            price_yearly: 990,
            features: [
              { name: '1 Project', included: true },
              { name: '5 Team Members', included: true },
              { name: 'Basic AI Agents', included: true },
              { name: 'Email Support', included: true },
              { name: 'Analytics Dashboard', included: true },
              { name: 'API Access', included: false },
              { name: 'Custom Integrations', included: false }
            ],
            max_projects: 1,
            max_team_members: 5,
            priority: 1,
            is_active: true
          },
          {
            id: '2',
            name: 'Professional',
            description: 'Ideal for growing businesses',
            price_monthly: 299,
            price_yearly: 2990,
            features: [
              { name: '5 Projects', included: true },
              { name: '20 Team Members', included: true },
              { name: 'Advanced AI Agents', included: true },
              { name: 'Priority Support', included: true },
              { name: 'Advanced Analytics', included: true },
              { name: 'API Access', included: true },
              { name: 'Custom Integrations', included: false }
            ],
            max_projects: 5,
            max_team_members: 20,
            priority: 2,
            is_active: true
          },
          {
            id: '3',
            name: 'Enterprise',
            description: 'For large organizations and enterprises',
            price_monthly: 599,
            price_yearly: 5990,
            features: [
              { name: 'Unlimited Projects', included: true },
              { name: 'Unlimited Team Members', included: true },
              { name: 'Custom AI Models', included: true },
              { name: 'Dedicated Support', included: true },
              { name: 'Enterprise Analytics', included: true },
              { name: 'API Access', included: true },
              { name: 'Custom Integrations', included: true }
            ],
            max_projects: null,
            max_team_members: null,
            priority: 3,
            is_active: true
          }
        ];
        setPackages(fallbackPackages);
      } else {
        setPackages(data);
      }
    } catch (error) {
      console.error('Error fetching packages:', error);
      // Use fallback data on error
      const fallbackPackages: PricingPackage[] = [
        {
          id: '1',
          name: 'Starter',
          description: 'Perfect for small businesses and startups',
          price_monthly: 99,
          price_yearly: 990,
          features: [
            { name: '1 Project', included: true },
            { name: '5 Team Members', included: true },
            { name: 'Basic AI Agents', included: true },
            { name: 'Email Support', included: true },
            { name: 'Analytics Dashboard', included: true },
            { name: 'API Access', included: false },
            { name: 'Custom Integrations', included: false }
          ],
          max_projects: 1,
          max_team_members: 5,
          priority: 1,
          is_active: true
        },
        {
          id: '2',
          name: 'Professional',
          description: 'Ideal for growing businesses',
          price_monthly: 299,
          price_yearly: 2990,
          features: [
            { name: '5 Projects', included: true },
            { name: '20 Team Members', included: true },
            { name: 'Advanced AI Agents', included: true },
            { name: 'Priority Support', included: true },
            { name: 'Advanced Analytics', included: true },
            { name: 'API Access', included: true },
            { name: 'Custom Integrations', included: false }
          ],
          max_projects: 5,
          max_team_members: 20,
          priority: 2,
          is_active: true
        },
        {
          id: '3',
          name: 'Enterprise',
          description: 'For large organizations and enterprises',
          price_monthly: 599,
          price_yearly: 5990,
          features: [
            { name: 'Unlimited Projects', included: true },
            { name: 'Unlimited Team Members', included: true },
            { name: 'Custom AI Models', included: true },
            { name: 'Dedicated Support', included: true },
            { name: 'Enterprise Analytics', included: true },
            { name: 'API Access', included: true },
            { name: 'Custom Integrations', included: true }
          ],
          max_projects: null,
          max_team_members: null,
          priority: 3,
          is_active: true
        }
      ];
      setPackages(fallbackPackages);
    } finally {
      setLoading(false);
    }
  };

  const validateDiscountCode = async (packageId: string) => {
    if (!discountCode) {
      setDiscountCalc(null);
      return;
    }

    setValidatingCode(true);
    try {
      const { data, error } = await supabase
        .from('pricing_campaigns')
        .select('*')
        .eq('code', discountCode)
        .eq('is_active', true)
        .single();

      if (error || !data) {
        setDiscountCalc(null);
        return;
      }

      const campaign = data as PricingCampaign;
      const now = new Date();

      if (campaign.start_date && new Date(campaign.start_date) > now) {
        setDiscountCalc(null);
        return;
      }

      if (campaign.end_date && new Date(campaign.end_date) < now) {
        setDiscountCalc(null);
        return;
      }

      if (campaign.max_uses && campaign.used_count >= campaign.max_uses) {
        setDiscountCalc(null);
        return;
      }

      if (campaign.applicable_packages && !campaign.applicable_packages.includes(packageId)) {
        setDiscountCalc(null);
        return;
      }

      // Calculate discount
      const packageData = packages.find(p => p.id === packageId);
      if (!packageData) return;

      const originalPrice = billingCycle === 'yearly' ? (packageData.price_yearly || 0) : (packageData.price_monthly || 0);

      let discountAmount = 0;
      if (campaign.discount_type === 'percentage') {
        discountAmount = (originalPrice * campaign.discount_value) / 100;
      } else {
        discountAmount = campaign.discount_value;
      }

      const finalPrice = originalPrice - discountAmount;

      setDiscountCalc({
        original_price: originalPrice,
        discount_amount: discountAmount,
        final_price: finalPrice,
        discount_percentage: campaign.discount_type === 'percentage' ? campaign.discount_value : null,
        campaign_name: campaign.name
      });
    } catch (error) {
      console.error('Error validating discount code:', error);
      setDiscountCalc(null);
    } finally {
      setValidatingCode(false);
    }
  };

  const handleSubscribe = (packageId: string) => {
    // TODO: Implement subscription flow
    console.log('Subscribe to package:', packageId, 'with discount:', discountCode);
  };

  if (loading) {
    return (
      <section className="py-24 bg-gradient-subtle">
        <div className="container mx-auto px-4">
          <div className="text-center">
            <div className="animate-pulse">
              <div className="h-8 bg-gray-300 rounded w-1/3 mx-auto mb-4"></div>
              <div className="h-4 bg-gray-300 rounded w-1/2 mx-auto"></div>
            </div>
          </div>
        </div>
      </section>
    );
  }

  return (
    <section className="py-24 bg-gradient-subtle">
      <div className="container mx-auto px-4">
        {/* Header */}
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-bold mb-6 text-foreground">
            Choose Your Plan
            <span className="block bg-gradient-primary bg-clip-text text-transparent">Scale with Confidence</span>
          </h2>
          <p className="text-xl text-muted-foreground max-w-3xl mx-auto mb-8">
            Start free and scale as you grow. All plans include our core AI features with varying limits.
          </p>

          {/* Billing Toggle */}
          <div className="flex items-center justify-center space-x-4 mb-8">
            <Label htmlFor="billing-toggle" className="text-sm font-medium">
              Monthly
            </Label>
            <Select value={billingCycle} onValueChange={(value: 'monthly' | 'yearly') => setBillingCycle(value)}>
              <SelectTrigger className="w-32" id="billing-toggle">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="monthly">Monthly</SelectItem>
                <SelectItem value="yearly">Yearly</SelectItem>
              </SelectContent>
            </Select>
            <Label htmlFor="billing-toggle" className="text-sm font-medium">
              Yearly
            </Label>
            <Badge variant="secondary" className="ml-2">Save 20%</Badge>
          </div>

          {/* Discount Code Input */}
          <div className="flex items-center justify-center space-x-4 max-w-md mx-auto">
            <Input
              placeholder="Discount code"
              value={discountCode}
              onChange={(e) => setDiscountCode(e.target.value)}
              className="flex-1"
            />
            <Button
              variant="outline"
              onClick={() => validateDiscountCode(packages[0]?.id || '')}
              disabled={validatingCode || !discountCode}
            >
              Apply
            </Button>
          </div>

          {discountCalc && (
            <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg max-w-md mx-auto">
              <p className="text-green-800 font-medium">
                {discountCalc.campaign_name} Applied!
              </p>
              <p className="text-green-600 text-sm">
                {discountCalc.discount_percentage}% discount - Save £{discountCalc.discount_amount}
              </p>
            </div>
          )}
        </div>

        {/* Pricing Cards */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8 max-w-7xl mx-auto">
          {packages.map((pkg) => {
            const originalPrice = billingCycle === 'yearly' ? pkg.price_yearly : pkg.price_monthly;
            const finalPrice = discountCalc ? discountCalc.final_price : originalPrice;

            return (
              <Card key={pkg.id} className="relative group hover:shadow-card transition-all duration-300 border-0 bg-card/50 backdrop-blur-sm">
                {pkg.name === 'Professional' && (
                  <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                    <Badge className="bg-gradient-primary text-white">Most Popular</Badge>
                  </div>
                )}

                <CardHeader className="text-center pb-8">
                  <CardTitle className="text-2xl font-bold">{pkg.name}</CardTitle>
                  {pkg.description && (
                    <p className="text-muted-foreground mt-2">{pkg.description}</p>
                  )}

                  <div className="mt-6">
                    <div className="flex items-baseline justify-center">
                      <span className="text-4xl font-bold">
                        £{finalPrice || 0}
                      </span>
                      <span className="text-muted-foreground ml-1">
                        /{billingCycle === 'yearly' ? 'year' : 'month'}
                      </span>
                    </div>

                    {discountCalc && originalPrice !== finalPrice && (
                      <div className="text-sm text-muted-foreground line-through">
                        £{originalPrice}
                      </div>
                    )}

                    {billingCycle === 'yearly' && (
                      <p className="text-green-600 text-sm mt-1">Save 20% annually</p>
                    )}
                  </div>
                </CardHeader>

                <CardContent className="space-y-6">
                  {/* Features */}
                  <div className="space-y-3">
                    {Array.isArray(pkg.features) && pkg.features.map((feature, idx) => (
                      <div key={idx} className="flex items-center">
                        {feature.included ? (
                          <Check className="w-5 h-5 text-green-500 mr-3" />
                        ) : (
                          <X className="w-5 h-5 text-red-500 mr-3" />
                        )}
                        <span className={feature.included ? 'text-foreground' : 'text-muted-foreground'}>
                          {feature.name}
                        </span>
                      </div>
                    ))}
                  </div>

                  {/* Limits */}
                  <div className="border-t pt-4 space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>Projects:</span>
                      <span>{pkg.max_projects ? pkg.max_projects : 'Unlimited'}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span>Team Members:</span>
                      <span>{pkg.max_team_members ? pkg.max_team_members : 'Unlimited'}</span>
                    </div>
                  </div>

                  {/* CTA Button */}
                  <Button
                    className="w-full mt-6"
                    variant={pkg.name === 'Professional' ? 'default' : 'outline'}
                    onClick={() => handleSubscribe(pkg.id)}
                  >
                    Get Started
                  </Button>
                </CardContent>
              </Card>
            );
          })}
        </div>

        {/* Campaign Banner */}
        {discountCalc && (
          <div className="mt-16 text-center">
            <div className="inline-flex items-center space-x-2 bg-gradient-primary/10 border border-gradient-primary/20 rounded-lg px-6 py-3">
              <span className="text-lg">🎉</span>
              <span className="font-medium">
                {discountCalc.campaign_name} - {discountCalc.discount_percentage}% off applied!
              </span>
            </div>
          </div>
        )}
      </div>
    </section>
  );
};

export default PricingSection;