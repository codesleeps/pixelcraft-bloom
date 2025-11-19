import React, { useState, useEffect } from 'react';
import { ModelManager } from '@/lib/ModelManager';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2 } from 'lucide-react';
  
interface ModelTestResult {
  model_name: string;
  response: string;
  latency: number;
  tokens_used: number;
  success: boolean;
  error?: string;
}
  
export default function ModelTester() {
  const [selectedModel, setSelectedModel] = useState('');
  const [taskType, setTaskType] = useState('completion');
  const [prompt, setPrompt] = useState('');
  const [testResult, setTestResult] = useState<ModelTestResult | null>(null);
  const [comparisonResults, setComparisonResults] = useState<ModelTestResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [comparisonLoading, setComparisonLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [models, setModels] = useState<Record<string, any>>({});
  
  const modelManager = ModelManager.getInstance();
  
  useEffect(() => {
    const loadModels = async () => {
      try {
        await modelManager.fetchModels();
        const fetchedModels = modelManager.getModels();
        setModels(fetchedModels);
        // Set default model if available
        const modelNames = Object.keys(fetchedModels);
        if (modelNames.length > 0 && !selectedModel) {
          setSelectedModel(modelNames[0]);
        }
      } catch (err) {
        setError('Failed to load models from backend');
      }
    };
    loadModels();
  }, []);
  
  const apiCall = async (endpoint: string, options: RequestInit = {}): Promise<any> => {
    const url = `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}${endpoint}`;
    const { data: { session } } = await import('@/integrations/supabase/client').then(m => m.supabase.auth.getSession());
    const headers = {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${session?.access_token || ''}`,
      ...options.headers,
    };
    const config: RequestInit = { ...options, headers };
  
    const response = await fetch(url, config);
    if (!response.ok) {
      throw new Error(`API error: ${response.status} ${response.statusText}`);
    }
    return response.json();
  };
  
  const handleTest = async () => {
    if (!selectedModel || !prompt) return;
  
    setLoading(true);
    setError(null);
    setTestResult(null);
  
    try {
      const result: ModelTestResult = await apiCall('/api/models/test', {
        method: 'POST',
        body: JSON.stringify({
          model_name: selectedModel,
          prompt,
          task_type: taskType,
        }),
      });
      setTestResult(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Test failed');
    } finally {
      setLoading(false);
    }
  };
  
  const handleTestAll = async () => {
    if (!prompt) return;
  
    setComparisonLoading(true);
    setError(null);
    setComparisonResults([]);
  
    const modelNames = Object.keys(models);
    const results: ModelTestResult[] = [];
  
    for (const modelName of modelNames) {
      try {
        const result: ModelTestResult = await apiCall('/api/models/test', {
          method: 'POST',
          body: JSON.stringify({
            model_name: modelName,
            prompt,
            task_type: taskType,
          }),
        });
        results.push(result);
      } catch (err) {
        results.push({
          model_name: modelName,
          response: '',
          latency: 0,
          tokens_used: 0,
          success: false,
          error: err instanceof Error ? err.message : 'Test failed',
        });
      }
    }
  
    setComparisonResults(results);
    setComparisonLoading(false);
  };
  
  return (
    <div className="container mx-auto p-6 space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Model Tester</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center space-x-4">
            <Select value={selectedModel} onValueChange={setSelectedModel}>
              <SelectTrigger className="w-[200px]">
                <SelectValue placeholder="Select a model" />
              </SelectTrigger>
              <SelectContent>
                {Object.keys(models).map((modelName) => (
                  <SelectItem key={modelName} value={modelName}>
                    {modelName}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={taskType} onValueChange={setTaskType}>
              <SelectTrigger className="w-[150px]">
                <SelectValue placeholder="Task type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="completion">Completion</SelectItem>
                <SelectItem value="chat">Chat</SelectItem>
                <SelectItem value="code">Code</SelectItem>
                <SelectItem value="analysis">Analysis</SelectItem>
              </SelectContent>
            </Select>
          </div>
  
          <Textarea
            placeholder="Enter your prompt here..."
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            className="min-h-[100px]"
          />
  
          <div className="flex space-x-4">
            <Button onClick={handleTest} disabled={loading || !prompt || !selectedModel}>
              {loading ? <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Testing...</> : 'Test Model'}
            </Button>
            <Button onClick={handleTestAll} disabled={comparisonLoading || !prompt} variant="outline">
              {comparisonLoading ? <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Testing All...</> : 'Test All Models'}
            </Button>
          </div>
  
          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
  
          {testResult && (
            <div className="mt-6">
              <h3 className="text-lg font-semibold mb-2">Test Result:</h3>
              <div className="bg-muted p-4 rounded-lg space-y-2">
                <div className="flex justify-between">
                  <span><strong>Model:</strong> {testResult.model_name}</span>
                  <Badge variant={testResult.success ? 'default' : 'destructive'}>
                    {testResult.success ? 'Success' : 'Failed'}
                  </Badge>
                </div>
                <div><strong>Latency:</strong> {testResult.latency}ms</div>
                <div><strong>Tokens Used:</strong> {testResult.tokens_used}</div>
                {testResult.error && <div><strong>Error:</strong> {testResult.error}</div>}
                <div><strong>Response:</strong></div>
                <div className="whitespace-pre-wrap bg-background p-2 rounded mt-2">
                  {testResult.response || 'No response'}
                </div>
              </div>
            </div>
          )}
  
          {comparisonResults.length > 0 && (
            <div className="mt-6">
              <h3 className="text-lg font-semibold mb-2">Model Comparison:</h3>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Model</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Latency (ms)</TableHead>
                    <TableHead>Tokens</TableHead>
                    <TableHead>Response Preview</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {comparisonResults.map((result) => (
                    <TableRow key={result.model_name}>
                      <TableCell>{result.model_name}</TableCell>
                      <TableCell>
                        <Badge variant={result.success ? 'default' : 'destructive'}>
                          {result.success ? 'Success' : 'Failed'}
                        </Badge>
                      </TableCell>
                      <TableCell>{result.latency}</TableCell>
                      <TableCell>{result.tokens_used}</TableCell>
                      <TableCell className="max-w-xs truncate">
                        {result.response.substring(0, 50)}...
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
  
          {/* Placeholder for streaming visualization - to be implemented when backend supports streaming */}
          <div className="mt-6 p-4 bg-muted rounded-lg">
            <h4 className="font-semibold">Streaming Response</h4>
            <p className="text-sm text-muted-foreground">Streaming visualization will be available once backend streaming is implemented.</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
