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
  Button,
} from "@/components/ui/button";
import {
  Input,
} from "@/components/ui/input";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  LineChart,
  Line
} from 'recharts';
import AnalyticsTrends from '@/components/AnalyticsTrends';

interface ModelInfo {
  name: string;
  provider: string;
  health: boolean;
  metrics: Record<string, any>;
}

interface ModelHealthResponse {
  healthy: number;
  total: number;
  status: string;
}

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
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [health, setHealth] = useState<ModelHealthResponse | null>(null);
  const [metrics, setMetrics] = useState<ModelMetrics[]>([]);
  const [timeRange, setTimeRange] = useState('24h');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [testModel, setTestModel] = useState('');
  const [testPrompt, setTestPrompt] = useState('');
  const [testResult, setTestResult] = useState('');
  const [testing, setTesting] = useState(false);
  const [activeTab, setActiveTab] = useState<'models' | 'analytics'>('models');

  const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

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
      throw new Error(`API error: ${response.status} ${response.statusText}`);
    }
    return await response.json();
  };

  useEffect(() => {
    fetchData();
  }, [timeRange]);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError('');
      
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

      const [modelsData, healthData, metricsData] = await Promise.all([
        apiCall('/api/models'),
        apiCall('/api/models/health'),
        apiCall(`/api/models/metrics?start_date=${startDate.toISOString()}&end_date=${now.toISOString()}`)
      ]);

      setModels(modelsData.models || []);
      setHealth(healthData);
      setMetrics(metricsData.metrics || []);
    } catch (error) {
      console.error('Error fetching data:', error);
      setError(error instanceof Error ? error.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const handleTest = async () => {
    if (!testModel || !testPrompt) return;
    try {
      setTesting(true);
      setTestResult('');
      const result = await apiCall('/api/models/test', {
        method: 'POST',
        body: JSON.stringify({ model_name: testModel, prompt: testPrompt })
      });
      setTestResult(result.response);
    } catch (error) {
      setTestResult('Error: ' + (error instanceof Error ? error.message : 'Unknown error'));
    } finally {
      setTesting(false);
    }
  };

  const chartData = metrics.map(m => ({
    name: m.model_name,
    successRate: Number(m.success_rate.toFixed(1)),
    cacheHitRate: Number(m.cache_hit_rate.toFixed(1)),
  }));

  if (loading) {
    return <div className="p-6">Loading...</div>;
  }

  return (
    <div className="space-y-6 p-6">
      <div className="flex justify-between items-center">
        <h2 className="text-3xl font-bold tracking-tight">Model Performance Dashboard</h2>
        <div className="flex gap-2">
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
          <Button onClick={fetchData} disabled={loading}>
            Refresh
          </Button>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="flex border-b">
        <button
          className={`px-4 py-2 font-medium ${activeTab === 'models' ? 'border-b-2 border-primary text-primary' : 'text-muted-foreground'}`}
          onClick={() => setActiveTab('models')}
        >
          Model Performance
        </button>
        <button
          className={`px-4 py-2 font-medium ${activeTab === 'analytics' ? 'border-b-2 border-primary text-primary' : 'text-muted-foreground'}`}
          onClick={() => setActiveTab('analytics')}
        >
          Business Analytics
        </button>
      </div>

      {error && <p className="text-red-500">{error}</p>}

      {activeTab === 'models' ? (
        <>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Card>
              <CardHeader>
                <CardTitle>Model Health</CardTitle>
                <CardDescription>Healthy models / Total</CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-2xl font-bold">
                  {health ? `${health.healthy}/${health.total}` : 'N/A'}
                </p>
                <p className="text-sm text-muted-foreground">
                  Status: {health?.status || 'Unknown'}
                </p>
              </CardContent>
            </Card>

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
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Available Models</CardTitle>
              <CardDescription>Current model status and providers</CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableCaption>List of available models with health status</TableCaption>
                <TableHeader>
                  <TableRow>
                    <TableHead>Model Name</TableHead>
                    <TableHead>Provider</TableHead>
                    <TableHead>Health</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {models.map((model, i) => (
                    <TableRow key={i}>
                      <TableCell className="font-medium">{model.name}</TableCell>
                      <TableCell>{model.provider}</TableCell>
                      <TableCell>
                        <span className={model.health ? 'text-green-600' : 'text-red-600'}>
                          {model.health ? 'Healthy' : 'Unhealthy'}
                        </span>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Model Testing</CardTitle>
              <CardDescription>Test a model with a custom prompt</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex gap-2">
                <Select value={testModel} onValueChange={setTestModel}>
                  <SelectTrigger className="w-[200px]">
                    <SelectValue placeholder="Select model" />
                  </SelectTrigger>
                  <SelectContent>
                    {models.map((model) => (
                      <SelectItem key={model.name} value={model.name}>
                        {model.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Input
                  placeholder="Enter test prompt"
                  value={testPrompt}
                  onChange={(e) => setTestPrompt(e.target.value)}
                  className="flex-1"
                />
                <Button onClick={handleTest} disabled={testing || !testModel || !testPrompt}>
                  {testing ? 'Testing...' : 'Test'}
                </Button>
              </div>
              {testResult && (
                <div className="p-4 bg-gray-50 rounded">
                  <p className="font-medium">Result:</p>
                  <p>{testResult}</p>
                </div>
              )}
            </CardContent>
          </Card>

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
        </>
      ) : (
        <AnalyticsTrends />
      )}
    </div>
  );
}