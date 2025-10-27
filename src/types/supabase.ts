export type Database = {
  public: {
    Tables: {
      model_response_cache: {
        Row: {
          id: string;
          model_name: string;
          task_type: string;
          prompt_hash: string;
          prompt: string;
          response: string;
          tokens_used: number;
          execution_time_ms: number;
          created_at: string;
          expires_at: string;
        };
        Insert: {
          id?: string;
          model_name: string;
          task_type: string;
          prompt_hash: string;
          prompt: string;
          response: string;
          tokens_used: number;
          execution_time_ms?: number;
          created_at?: string;
          expires_at: string;
        };
        Update: {
          id?: string;
          model_name?: string;
          task_type?: string;
          prompt_hash?: string;
          prompt?: string;
          response?: string;
          tokens_used?: number;
          execution_time_ms?: number;
          created_at?: string;
          expires_at?: string;
        };
      };
      model_performance_metrics: {
        Row: {
          id: string;
          model_name: string;
          task_type: string;
          total_requests: number;
          successful_requests: number;
          failed_requests: number;
          total_tokens: number;
          avg_response_time: number;
          cache_hits: number;
          cache_misses: number;
          last_error: string | null;
          last_error_at: string | null;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id?: string;
          model_name: string;
          task_type: string;
          total_requests?: number;
          successful_requests?: number;
          failed_requests?: number;
          total_tokens?: number;
          avg_response_time?: number;
          cache_hits?: number;
          cache_misses?: number;
          last_error?: string | null;
          last_error_at?: string | null;
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          id?: string;
          model_name?: string;
          task_type?: string;
          total_requests?: number;
          successful_requests?: number;
          failed_requests?: number;
          total_tokens?: number;
          avg_response_time?: number;
          cache_hits?: number;
          cache_misses?: number;
          last_error?: string | null;
          last_error_at?: string | null;
          created_at?: string;
          updated_at?: string;
        };
      };
    };
    Functions: {
      update_model_metrics: {
        Args: {
          p_model_name: string;
          p_task_type: string;
          p_success: boolean;
          p_response_time: number;
          p_tokens_used: number;
          p_cache_hit: boolean;
          p_error_message?: string;
        };
        Returns: void;
      };
    };
  };
};