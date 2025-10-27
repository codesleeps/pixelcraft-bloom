import React, { useState } from 'react';
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

export default function ModelTester() {
  const [selectedModel, setSelectedModel] = useState('llama2');
  const [prompt, setPrompt] = useState('');
  const [response, setResponse] = useState('');
  const [loading, setLoading] = useState(false);

  const modelManager = ModelManager.getInstance();

  const handleGenerate = async () => {
    try {
      setLoading(true);
      const result = await modelManager.generateCompletion(selectedModel, prompt);
      setResponse(result || 'No response generated');
    } catch (error) {
      setResponse(`Error: ${error instanceof Error ? error.message : 'Unknown error occurred'}`);
    } finally {
      setLoading(false);
    }
  };

  const handleChat = async () => {
    try {
      setLoading(true);
      const result = await modelManager.generateChat(selectedModel, [
        {
          role: 'system',
          content: 'You are a helpful AI assistant.'
        },
        {
          role: 'user',
          content: prompt
        }
      ]);
      setResponse(result || 'No response generated');
    } catch (error) {
      setResponse(`Error: ${error instanceof Error ? error.message : 'Unknown error occurred'}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Model Tester</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center space-x-4">
            <Select
              value={selectedModel}
              onValueChange={setSelectedModel}
            >
              <SelectTrigger className="w-[200px]">
                <SelectValue placeholder="Select a model" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="llama2">Llama 2</SelectItem>
                <SelectItem value="llama3">Llama 3</SelectItem>
                <SelectItem value="codellama">CodeLlama</SelectItem>
                <SelectItem value="mistral">Mistral</SelectItem>
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
            <Button 
              onClick={handleGenerate}
              disabled={loading || !prompt}
            >
              {loading ? 'Generating...' : 'Generate Completion'}
            </Button>
            <Button 
              onClick={handleChat}
              disabled={loading || !prompt}
              variant="secondary"
            >
              {loading ? 'Processing...' : 'Chat'}
            </Button>
          </div>

          <div className="mt-6">
            <h3 className="text-lg font-semibold mb-2">Response:</h3>
            <div className="bg-muted p-4 rounded-lg min-h-[100px] whitespace-pre-wrap">
              {response}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}