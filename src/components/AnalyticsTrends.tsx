import React, { useState, useEffect } from 'react';
import { supabase } from '@/integrations/supabase/client';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  BarChart,
  Bar
} from 'recharts';
import { Loader2, AlertCircle } from 'lucide-react';

interface TimeSeriesDataPoint {
  date: string;
  value: number;
}

interface SubscriptionTrendPoint {
  period: string;
  new_subscriptions: number;
  cancelled_subscriptions: number;
  net_change: number;
  cumulative_active: number;
}

interface RevenueByPackage {
  package_id: string;
  package_name: string;
  subscription_count: number;
  total_revenue: number;
  avg_revenue_per_subscription: number;
}

const AnalyticsTrends: React.FC = () => {
  const [timeRange, setTimeRange] = useState('30d');
  const [leadTrends, setLeadTrends] = useState<TimeSeriesDataPoint[]>([]);
  const [conversationTrends, setConversationTrends] = useState<TimeSeriesDataPoint[]>([]);
  const [subscriptionTrends, setSubscriptionTrends] = useState<SubscriptionTrendPoint[]>([]);
  const [revenueByPackage, setRevenueByPackage] = useState<RevenueByPackage[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';

  const getAuthHeaders = async () => {
    const { data: { session } } = await supabase.auth.getSession();
    return {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${session?.access_token || ''}`,
    };
  };

  const apiCall = async (endpoint: string, options: RequestInit = {}) => {
    const url = `${baseUrl}${endpoint}`;
    const headers = await getAuthHeaders();
    const config: RequestInit = {
      ...options,
      headers: { ...headers, ...options.headers },
    };

    const response = await fetch(url, config);
    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`API error: ${response.status} ${response.statusText} - ${errorText}`);
    }
    return await response.json();
  };

  useEffect(() => {
    fetchData();
  }, [timeRange]);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Calculate date range based on selection
      const now = new Date();
      let startDate = new Date();
      switch (timeRange) {
        case '7d':
          startDate.setDate(startDate.getDate() - 7);
          break;
        case '30d':
          startDate.setDate(startDate.getDate() - 30);
          break;
        case '90d':
          startDate.setDate(startDate.getDate() - 90);
          break;
        default:
          startDate.setDate(startDate.getDate() - 30);
      }

      const startDateStr = startDate.toISOString().split('T')[0];
      const endDateStr = now.toISOString().split('T')[0];

      // Fetch all analytics data in parallel
      const [
        leadTrendsData,
        conversationTrendsData,
        subscriptionTrendsData,
        revenueByPackageData
      ] = await Promise.all([
        apiCall(`/api/analytics/leads/trends?start_date=${startDateStr}&end_date=${endDateStr}&aggregation=daily`),
        apiCall(`/api/analytics/conversations/trends?start_date=${startDateStr}&end_date=${endDateStr}&aggregation=daily`),
        apiCall(`/api/analytics/revenue/subscription-trends?start_date=${startDateStr}&end_date=${endDateStr}&aggregation=daily`),
        apiCall(`/api/analytics/revenue/by-package?start_date=${startDateStr}&end_date=${endDateStr}`)
      ]);

      setLeadTrends(leadTrendsData.data || []);
      setConversationTrends(conversationTrendsData.data || []);
      setSubscriptionTrends(subscriptionTrendsData.data || []);
      setRevenueByPackage(revenueByPackageData || []);
    } catch (error: any) {
      console.error('Error fetching analytics data:', error);
      setError(error.message || 'Failed to load analytics data. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (error) {
    return (
      <Card className="border-destructive">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertCircle className="h-5 w-5 text-destructive" />
            Error Loading Analytics
          </CardTitle>
          <CardDescription>{error}</CardDescription>
        </CardHeader>
        <CardContent>
          <button 
            onClick={fetchData}
            className="px-4 py-2 bg-primary text-primary-foreground rounded hover:opacity-90"
          >
            Retry
          </button>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold">Analytics Trends</h2>
        <Select value={timeRange} onValueChange={setTimeRange}>
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Select time range" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="7d">Last 7 Days</SelectItem>
            <SelectItem value="30d">Last 30 Days</SelectItem>
            <SelectItem value="90d">Last 90 Days</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Lead Trends Chart */}
      <Card>
        <CardHeader>
          <CardTitle>Lead Creation Trends</CardTitle>
          <CardDescription>Daily lead creation over time</CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={leadTrends}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="date" 
                tickFormatter={(value) => new Date(value).toLocaleDateString()}
              />
              <YAxis />
              <Tooltip 
                labelFormatter={(value) => new Date(value).toLocaleDateString()}
                formatter={(value) => [value, 'Leads']}
              />
              <Legend />
              <Line 
                type="monotone" 
                dataKey="value" 
                name="Leads Created" 
                stroke="#8884d8" 
                activeDot={{ r: 8 }} 
              />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Conversation Trends Chart */}
      <Card>
        <CardHeader>
          <CardTitle>Conversation Trends</CardTitle>
          <CardDescription>Daily conversation activity over time</CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={conversationTrends}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="date" 
                tickFormatter={(value) => new Date(value).toLocaleDateString()}
              />
              <YAxis />
              <Tooltip 
                labelFormatter={(value) => new Date(value).toLocaleDateString()}
                formatter={(value) => [value, 'Conversations']}
              />
              <Legend />
              <Line 
                type="monotone" 
                dataKey="value" 
                name="Conversations" 
                stroke="#82ca9d" 
                activeDot={{ r: 8 }} 
              />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Subscription Trends Chart */}
      <Card>
        <CardHeader>
          <CardTitle>Subscription Trends</CardTitle>
          <CardDescription>Subscription metrics over time</CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={subscriptionTrends}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="period" 
                tickFormatter={(value) => new Date(value).toLocaleDateString()}
              />
              <YAxis />
              <Tooltip 
                labelFormatter={(value) => new Date(value).toLocaleDateString()}
              />
              <Legend />
              <Bar dataKey="new_subscriptions" name="New Subscriptions" fill="#413ea0" />
              <Bar dataKey="cancelled_subscriptions" name="Cancelled Subscriptions" fill="#ff7300" />
              <Bar dataKey="net_change" name="Net Change" fill="#00b300" />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Revenue by Package Chart */}
      <Card>
        <CardHeader>
          <CardTitle>Revenue by Package</CardTitle>
          <CardDescription>Revenue distribution across packages</CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={revenueByPackage}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="package_name" />
              <YAxis />
              <Tooltip 
                formatter={(value, name) => {
                  if (name === 'total_revenue' || name === 'avg_revenue_per_subscription') {
                    return [`$${value}`, name === 'total_revenue' ? 'Total Revenue' : 'Avg Revenue'];
                  }
                  return [value, name === 'subscription_count' ? 'Subscriptions' : name];
                }}
              />
              <Legend />
              <Bar dataKey="total_revenue" name="Total Revenue" fill="#0088fe" />
              <Bar dataKey="subscription_count" name="Subscriptions" fill="#00c49f" />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  );
};

export default AnalyticsTrends;