import { models, ModelConfig } from '../config/models';
import { supabase } from '@/integrations/supabase/client';

export class ModelManager {
  private static instance: ModelManager;
  private models: Record<string, ModelConfig>;

  private constructor() {
    this.models = models;
  }

  public static getInstance(): ModelManager {
    if (!ModelManager.instance) {
      ModelManager.instance = new ModelManager();
    }
    return ModelManager.instance;
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

  private async checkCache(modelName: string, prompt: string): Promise<string | null> {
    try {
      const { data, error } = await supabase
        .from('model_response_cache')
        .select('response')
        .eq('model_name', modelName)
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
    tokensUsed: number
  ) {
    try {
      const expiryTime = new Date();
      expiryTime.setHours(expiryTime.getHours() + 24); // Cache for 24 hours

      await supabase.from('model_response_cache').insert({
        model_name: modelName,
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
    } = {}
  ) {
    const startTime = Date.now();
    let success = false;
    let tokensUsed = 0;
    let cacheHit = false;
    let response: string | null = null;

    try {
      // Check cache first
      response = await this.checkCache(modelName, prompt);
      
      if (response) {
        cacheHit = true;
        success = true;
        // Estimate tokens for cached response
        tokensUsed = Math.ceil(response.length / 4);
      } else {
        // Get model configuration
        const model = this.models[modelName];
        if (!model) throw new Error(`Model ${modelName} not found`);

        // Prepare request to Ollama
        const requestBody = {
          model: modelName,
          prompt,
          stream: options.stream || false,
          options: {
            temperature: options.temperature || model.parameters.temperature,
            num_predict: options.maxTokens || model.parameters.maxTokens,
          }
        };

        // Make request to Ollama
        const ollamaResponse = await fetch('http://localhost:11434/api/generate', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(requestBody),
        });

        if (!ollamaResponse.ok) {
          throw new Error(`Ollama API error: ${ollamaResponse.statusText}`);
        }

        if (options.stream) {
          return ollamaResponse.body;
        } else {
          const result = await ollamaResponse.json();
          response = result.response;
          tokensUsed = result.total_tokens || Math.ceil(response.length / 4);
          success = true;

          // Cache successful response
          await this.cacheResponse(modelName, prompt, response, tokensUsed);
        }
      }

      // Track usage
      const responseTime = Date.now() - startTime;
      await this.trackModelUsage(
        modelName,
        'completion',
        success,
        responseTime,
        tokensUsed,
        cacheHit
      );

      return response;

    } catch (error) {
      const responseTime = Date.now() - startTime;
      await this.trackModelUsage(
        modelName,
        'completion',
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
    } = {}
  ) {
    const startTime = Date.now();
    let success = false;
    let tokensUsed = 0;
    let response: string | null = null;

    try {
      // Get model configuration
      const model = this.models[modelName];
      if (!model) throw new Error(`Model ${modelName} not found`);

      // Format messages for Ollama
      const prompt = messages.map(msg => {
        switch (msg.role) {
          case 'system':
            return `System: ${msg.content}\n`;
          case 'user':
            return `User: ${msg.content}\n`;
          case 'assistant':
            return `Assistant: ${msg.content}\n`;
        }
      }).join('');

      // Check cache for exact conversation
      response = await this.checkCache(modelName, prompt);
      
      if (response) {
        success = true;
        tokensUsed = Math.ceil(response.length / 4);
        
        // Track cached response usage
        const responseTime = Date.now() - startTime;
        await this.trackModelUsage(
          modelName,
          'chat',
          true,
          responseTime,
          tokensUsed,
          true
        );
        
        return response;
      }

      // Prepare request to Ollama
      const requestBody = {
        model: modelName,
        messages: messages,
        stream: options.stream || false,
        options: {
          temperature: options.temperature || model.parameters.temperature,
          num_predict: options.maxTokens || model.parameters.maxTokens,
        }
      };

      // Make request to Ollama
      const ollamaResponse = await fetch('http://localhost:11434/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      });

      if (!ollamaResponse.ok) {
        throw new Error(`Ollama API error: ${ollamaResponse.statusText}`);
      }

      if (options.stream) {
        return ollamaResponse.body;
      } else {
        const result = await ollamaResponse.json();
        response = result.message.content;
        tokensUsed = result.total_tokens || Math.ceil(response.length / 4);
        success = true;

        // Cache successful response
        await this.cacheResponse(modelName, prompt, response, tokensUsed);
      }

      // Track usage
      const responseTime = Date.now() - startTime;
      await this.trackModelUsage(
        modelName,
        'chat',
        success,
        responseTime,
        tokensUsed,
        false
      );

      return response;

    } catch (error) {
      const responseTime = Date.now() - startTime;
      await this.trackModelUsage(
        modelName,
        'chat',
        false,
        responseTime,
        0,
        false,
        error instanceof Error ? error.message : 'Unknown error'
      );
      throw error;
    }
  }
}