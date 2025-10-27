export type ModelConfig = {
  name: string;
  provider: 'ollama' | 'huggingface';
  baseUrl?: string;
  contextWindow: number;
  capabilities: {
    chat: boolean;
    completion: boolean;
    embedding: boolean;
    codeCompletion: boolean;
  };
  parameters: {
    temperature?: number;
    topP?: number;
    maxTokens?: number;
  };
};

export const models: Record<string, ModelConfig> = {
  'llama2': {
    name: 'llama2',
    provider: 'ollama',
    contextWindow: 4096,
    capabilities: {
      chat: true,
      completion: true,
      embedding: true,
      codeCompletion: true
    },
    parameters: {
      temperature: 0.7,
      topP: 0.9,
      maxTokens: 2048
    }
  },
  'llama3': {
    name: 'llama3',
    provider: 'ollama',
    contextWindow: 8192, // Increased context window for Llama 3
    capabilities: {
      chat: true,
      completion: true,
      embedding: true,
      codeCompletion: true
    },
    parameters: {
      temperature: 0.7,
      topP: 0.9,
      maxTokens: 4096
    }
  },
  'codellama': {
    name: 'codellama',
    provider: 'ollama',
    contextWindow: 4096,
    capabilities: {
      chat: true,
      completion: true,
      embedding: true,
      codeCompletion: true
    },
    parameters: {
      temperature: 0.5, // Lower temperature for more focused code generation
      topP: 0.95,
      maxTokens: 2048
    }
  },
  'mistral': {
    name: 'mistral',
    provider: 'ollama',
    contextWindow: 8192,
    capabilities: {
      chat: true,
      completion: true,
      embedding: true,
      codeCompletion: true
    },
    parameters: {
      temperature: 0.7,
      topP: 0.9,
      maxTokens: 4096
    }
  }
};