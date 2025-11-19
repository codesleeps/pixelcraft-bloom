import { supabase } from '@/integrations/supabase/client';

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

interface ModelGenerateResponse {
  response: string;
  model_used: string;
  latency: number;
}

interface ModelChatResponse {
  response: string;
  model_used: string;
  latency: number;
}

export class ModelManager {
  private static instance: ModelManager;
  private models: Record<string, ModelInfo> = {};
  private baseUrl: string;

  private constructor() {
    this.baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  }

  public static getInstance(): ModelManager {
    if (!ModelManager.instance) {
      ModelManager.instance = new ModelManager();
    }
    return ModelManager.instance;
  }

  private async getAuthHeaders(): Promise<Record<string, string>> {
    const { data: { session } } = await supabase.auth.getSession();
    return {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${session?.access_token || ''}`,
    };
  }

  private async apiCall(endpoint: string, options: RequestInit = {}): Promise<any> {
    const url = `${this.baseUrl}${endpoint}`;
    const headers = await this.getAuthHeaders();
    const config: RequestInit = {
      ...options,
      headers: { ...headers, ...options.headers },
    };

    let retries = 3;
    while (retries > 0) {
      try {
        const response = await fetch(url, config);
        if (!response.ok) {
          throw new Error(`API error: ${response.status} ${response.statusText}`);
        }
        return await response.json();
      } catch (error) {
        retries--;
        if (retries === 0) throw error;
        await new Promise(resolve => setTimeout(resolve, 1000 * (4 - retries))); // Exponential backoff
      }
    }
  }

  public async fetchModels(): Promise<void> {
    try {
      const data = await this.apiCall('/api/models');
      this.models = {};
      data.models.forEach((model: ModelInfo) => {
        this.models[model.name] = model;
      });
    } catch (error) {
      console.error('Failed to fetch models:', error);
      throw error;
    }
  }

  public getModels(): Record<string, ModelInfo> {
    return this.models;
  }

  public async getModelHealth(): Promise<ModelHealthResponse> {
    return await this.apiCall('/api/models/health');
  }

  private async trackModelUsage(
    modelName: string,
    taskType: string,
    success: boolean,
    responseTime: number,
    tokensUsed: number,
    cacheHit: boolean,
    errorMessage?: string
  ) {
    try {
      await supabase.rpc('update_model_metrics', {
        p_model_name: modelName,
        p_task_type: taskType,
        p_success: success,
        p_response_time: responseTime,
        p_tokens_used: tokensUsed,
        p_cache_hit: cacheHit,
        p_error_message: errorMessage
      });
    } catch (error) {
      console.error('Failed to track model usage:', error);
    }
  }

  private async checkCache(modelName: string, prompt: string, taskType: string): Promise<string | null> {
    try {
      const { data, error } = await supabase
        .from('model_response_cache')
        .select('response')
        .eq('model_name', modelName)
        .eq('task_type', taskType)
        .eq('prompt_hash', await this.hashPrompt(prompt))
        .single();

      if (error) throw error;
      return data?.response || null;
    } catch (error) {
      console.error('Cache check failed:', error);
      return null;
    }
  }

  private async cacheResponse(
    modelName: string,
    prompt: string,
    response: string,
    tokensUsed: number,
    taskType: string
  ) {
    try {
      const expiryTime = new Date();
      expiryTime.setHours(expiryTime.getHours() + 24); // Cache for 24 hours

      await supabase.from('model_response_cache').insert({
        model_name: modelName,
        task_type: taskType,
        prompt_hash: await this.hashPrompt(prompt),
        prompt,
        response,
        tokens_used: tokensUsed,
        expires_at: expiryTime.toISOString()
      });
    } catch (error) {
      console.error('Failed to cache response:', error);
    }
  }

  private async hashPrompt(prompt: string): Promise<string> {
    const encoder = new TextEncoder();
    const data = encoder.encode(prompt);
    const hashBuffer = await crypto.subtle.digest('SHA-256', data);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
  }

  public async generateCompletion(
    modelName: string,
    prompt: string,
    options: {
      temperature?: number;
      maxTokens?: number;
      stream?: boolean;
      taskType?: string;
      systemPrompt?: string;
    } = {}
  ): Promise<string | ReadableStream> {
    const startTime = Date.now();
    let success = false;
    let tokensUsed = 0;
    let cacheHit = false;
    let response: string | null = null;
    let actualModelUsed = modelName;

    try {
      // Check cache first
      response = await this.checkCache(modelName, prompt, options.taskType || 'completion');

      if (response) {
        cacheHit = true;
        success = true;
        tokensUsed = Math.ceil(response.length / 4);
      } else {
        // Call backend API
        const requestBody = {
          model_name: modelName,
          prompt,
          task_type: options.taskType || 'completion',
          system_prompt: options.systemPrompt,
          temperature: options.temperature,
          max_tokens: options.maxTokens,
        };

        const data: ModelGenerateResponse = await this.apiCall('/api/models/generate', {
          method: 'POST',
          body: JSON.stringify(requestBody),
        });

        response = data.response;
        tokensUsed = Math.ceil(response.length / 4); // Estimate tokens
        success = true;
        actualModelUsed = data.model_used;

        // Cache successful response using the actual model used
        await this.cacheResponse(actualModelUsed, prompt, response, tokensUsed, options.taskType || 'completion');
      }

      // Track usage with the actual model used
      const responseTime = Date.now() - startTime;
      await this.trackModelUsage(
        actualModelUsed,
        options.taskType || 'completion',
        success,
        responseTime,
        tokensUsed,
        cacheHit
      );

      return response;

    } catch (error) {
      const responseTime = Date.now() - startTime;
      await this.trackModelUsage(
        actualModelUsed,
        options.taskType || 'completion',
        false,
        responseTime,
        0,
        false,
        error instanceof Error ? error.message : 'Unknown error'
      );
      throw error;
    }
  }

  public async generateChat(
    modelName: string,
    messages: Array<{ role: 'system' | 'user' | 'assistant'; content: string }>,
    options: {
      temperature?: number;
      maxTokens?: number;
      stream?: boolean;
      taskType?: string;
      systemPrompt?: string;
    } = {}
  ): Promise<string | ReadableStream> {
    const startTime = Date.now();
    let success = false;
    let tokensUsed = 0;
    let response: string | null = null;
    let actualModelUsed = modelName;

    try {
      // Format messages for prompt-based caching
      const prompt = messages.map(msg => `${msg.role}: ${msg.content}`).join('\n');

      // Check cache for exact conversation
      response = await this.checkCache(modelName, prompt, options.taskType || 'chat');

      if (response) {
        success = true;
        tokensUsed = Math.ceil(response.length / 4);

        // Track cached response usage
        const responseTime = Date.now() - startTime;
        await this.trackModelUsage(
          actualModelUsed,
          options.taskType || 'chat',
          true,
          responseTime,
          tokensUsed,
          true
        );

        return response;
      }

      // Call backend API
      const requestBody = {
        model_name: modelName,
        messages,
        task_type: options.taskType || 'chat',
        system_prompt: options.systemPrompt,
        temperature: options.temperature,
        max_tokens: options.maxTokens,
      };

      const data: ModelChatResponse = await this.apiCall('/api/models/chat', {
        method: 'POST',
        body: JSON.stringify(requestBody),
      });

      response = data.response;
      tokensUsed = Math.ceil(response.length / 4); // Estimate tokens
      success = true;
      actualModelUsed = data.model_used;

      // Cache successful response using the actual model used
      await this.cacheResponse(actualModelUsed, prompt, response, tokensUsed, options.taskType || 'chat');

      // Track usage with the actual model used
      const responseTime = Date.now() - startTime;
      await this.trackModelUsage(
        actualModelUsed,
        options.taskType || 'chat',
        success,
        responseTime,
        tokensUsed,
        false
      );

      return response;

    } catch (error) {
      const responseTime = Date.now() - startTime;
      await this.trackModelUsage(
        actualModelUsed,
        options.taskType || 'chat',
        false,
        responseTime,
        0,
        false,
        error instanceof Error ? error.message : 'Unknown error'
      );
      throw error;
    }
  }

  // Placeholder for WebSocket streaming - to be implemented when backend supports it
  public async generateChatStream(
    modelName: string,
    messages: Array<{ role: 'system' | 'user' | 'assistant'; content: string }>,
    options: {
      temperature?: number;
      maxTokens?: number;
      taskType?: string;
      systemPrompt?: string;
    } = {}
  ): Promise<ReadableStream> {
    // TODO: Implement WebSocket connection to backend for streaming
    throw new Error('Streaming not yet implemented');
  }
}
