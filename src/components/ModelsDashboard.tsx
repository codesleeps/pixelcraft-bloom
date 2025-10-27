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
  Table,
  TableBody,
  TableCaption,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';

interface ModelMetrics {
  model_name: string;
  task_type: string;
  success_rate: number;
  avg_response_time: number;
  cache_hit_rate: number;
  total_requests: number;
  total_tokens: number;
}

export default function ModelsDashboard() {
  const [metrics, setMetrics] = useState<ModelMetrics[]>([]);
  const [timeRange, setTimeRange] = useState('24h');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchMetrics();
  }, [timeRange]);

  const fetchMetrics = async () => {
    try {
      setLoading(true);
      
      // Calculate date range based on selection
      const now = new Date();
      let startDate = new Date();
      switch (timeRange) {
        case '24h':
          startDate.setHours(startDate.getHours() - 24);
          break;
        case '7d':
          startDate.setDate(startDate.getDate() - 7);
          break;
        case '30d':
          startDate.setDate(startDate.getDate() - 30);
          break;
      }

      const { data, error } = await supabase.rpc('get_model_performance_metrics', {
        start_date: startDate.toISOString(),
        end_date: now.toISOString()
      });

      if (error) throw error;
      setMetrics(data);
    } catch (error) {
      console.error('Error fetching metrics:', error);
    } finally {
      setLoading(false);
    }
  };

  const chartData = metrics.map(m => ({
    name: m.model_name,
    successRate: Number(m.success_rate.toFixed(1)),
    cacheHitRate: Number(m.cache_hit_rate.toFixed(1)),
  }));

  return (
    <div className="space-y-6 p-6">
      <div className="flex justify-between items-center">
        <h2 className="text-3xl font-bold tracking-tight">Model Performance Dashboard</h2>
        <Select value={timeRange} onValueChange={setTimeRange}>
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Select time range" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="24h">Last 24 Hours</SelectItem>
            <SelectItem value="7d">Last 7 Days</SelectItem>
            <SelectItem value="30d">Last 30 Days</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader>
            <CardTitle>Total Requests</CardTitle>
            <CardDescription>Across all models</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">
              {metrics.reduce((sum, m) => sum + m.total_requests, 0).toLocaleString()}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Average Success Rate</CardTitle>
            <CardDescription>All models combined</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">
              {(metrics.reduce((sum, m) => sum + m.success_rate, 0) / metrics.length || 0).toFixed(1)}%
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Cache Hit Rate</CardTitle>
            <CardDescription>Response caching efficiency</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">
              {(metrics.reduce((sum, m) => sum + m.cache_hit_rate, 0) / metrics.length || 0).toFixed(1)}%
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Total Tokens</CardTitle>
            <CardDescription>Token usage across models</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">
              {metrics.reduce((sum, m) => sum + m.total_tokens, 0).toLocaleString()}
            </p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Performance Metrics</CardTitle>
          <CardDescription>Success rate and cache efficiency by model</CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis domain={[0, 100]} />
              <Tooltip />
              <Legend />
              <Bar dataKey="successRate" name="Success Rate (%)" fill="#22c55e" />
              <Bar dataKey="cacheHitRate" name="Cache Hit Rate (%)" fill="#3b82f6" />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Detailed Metrics</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableCaption>A detailed view of model performance metrics</TableCaption>
            <TableHeader>
              <TableRow>
                <TableHead>Model</TableHead>
                <TableHead>Task Type</TableHead>
                <TableHead>Success Rate</TableHead>
                <TableHead>Avg Response Time</TableHead>
                <TableHead>Cache Hit Rate</TableHead>
                <TableHead>Total Requests</TableHead>
                <TableHead>Total Tokens</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {metrics.map((metric, i) => (
                <TableRow key={i}>
                  <TableCell className="font-medium">{metric.model_name}</TableCell>
                  <TableCell>{metric.task_type}</TableCell>
                  <TableCell>{metric.success_rate.toFixed(1)}%</TableCell>
                  <TableCell>{metric.avg_response_time.toFixed(0)}ms</TableCell>
                  <TableCell>{metric.cache_hit_rate.toFixed(1)}%</TableCell>
                  <TableCell>{metric.total_requests.toLocaleString()}</TableCell>
                  <TableCell>{metric.total_tokens.toLocaleString()}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}