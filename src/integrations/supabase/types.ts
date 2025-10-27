export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[]

export type Database = {
  // Allows to automatically instanciate createClient with right options
  // instead of createClient<Database, { PostgrestVersion: 'XX' }>(URL, KEY)
  __InternalSupabase: {
    PostgrestVersion: "13.0.4"
  }
  public: {
    Tables: {
      leads: {
        Row: {
          id: string
          email: string
          first_name: string | null
          last_name: string | null
          company: string | null
          phone: string | null
          website: string | null
          lead_score: number | null
          lead_status: 'new' | 'contacted' | 'qualified' | 'opportunity' | 'customer' | 'lost'
          source: string
          services_interested: string[] | null
          budget_range: string | null
          timeline: string | null
          notes: string | null
          metadata: Json
          created_at: string
          updated_at: string
          deleted_at: string | null
        }
        Insert: {
          id?: string
          email: string
          first_name?: string | null
          last_name?: string | null
          company?: string | null
          phone?: string | null
          website?: string | null
          lead_score?: number | null
          lead_status?: 'new' | 'contacted' | 'qualified' | 'opportunity' | 'customer' | 'lost'
          source: string
          services_interested?: string[] | null
          budget_range?: string | null
          timeline?: string | null
          notes?: string | null
          metadata?: Json
          created_at?: string
          updated_at?: string
          deleted_at?: string | null
        }
        Update: {
          id?: string
          email?: string
          first_name?: string | null
          last_name?: string | null
          company?: string | null
          phone?: string | null
          website?: string | null
          lead_score?: number | null
          lead_status?: 'new' | 'contacted' | 'qualified' | 'opportunity' | 'customer' | 'lost'
          source?: string
          services_interested?: string[] | null
          budget_range?: string | null
          timeline?: string | null
          notes?: string | null
          metadata?: Json
          created_at?: string
          updated_at?: string
          deleted_at?: string | null
        }
        Relationships: []
      }
      conversations: {
        Row: {
          id: string
          lead_id: string
          session_id: string
          user_id: string | null
          status: 'active' | 'paused' | 'completed' | 'archived'
          channel: 'chat' | 'email' | 'phone' | 'web' | 'other'
          metadata: Json
          created_at: string
          updated_at: string
          deleted_at: string | null
        }
        Insert: {
          id?: string
          lead_id: string
          session_id: string
          user_id?: string | null
          status?: 'active' | 'paused' | 'completed' | 'archived'
          channel: 'chat' | 'email' | 'phone' | 'web' | 'other'
          metadata?: Json
          created_at?: string
          updated_at?: string
          deleted_at?: string | null
        }
        Update: {
          id?: string
          lead_id?: string
          session_id?: string
          user_id?: string | null
          status?: 'active' | 'paused' | 'completed' | 'archived'
          channel?: 'chat' | 'email' | 'phone' | 'web' | 'other'
          metadata?: Json
          created_at?: string
          updated_at?: string
          deleted_at?: string | null
        }
        Relationships: [{ foreignKeyName: "conversations_lead_id_fkey", columns: ["lead_id"], referencedRelation: "leads", referencedColumns: ["id"] }]
      }
      messages: {
        Row: {
          id: string
          conversation_id: string
          role: 'user' | 'assistant' | 'system'
          content: string
          agent_type: string | null
          metadata: Json
          created_at: string
        }
        Insert: {
          id?: string
          conversation_id: string
          role: 'user' | 'assistant' | 'system'
          content: string
          agent_type?: string | null
          metadata?: Json
          created_at?: string
        }
        Update: {
          id?: string
          conversation_id?: string
          role?: 'user' | 'assistant' | 'system'
          content?: string
          agent_type?: string | null
          metadata?: Json
          created_at?: string
        }
        Relationships: [{ foreignKeyName: "messages_conversation_id_fkey", columns: ["conversation_id"], referencedRelation: "conversations", referencedColumns: ["id"] }]
      }
      agent_logs: {
        Row: {
          id: string
          conversation_id: string | null
          agent_type: string
          action: string
          input_data: Json
          output_data: Json
          execution_time_ms: number | null
          status: 'success' | 'error' | 'timeout'
          error_message: string | null
          created_at: string
        }
        Insert: {
          id?: string
          conversation_id?: string | null
          agent_type: string
          action: string
          input_data?: Json
          output_data?: Json
          execution_time_ms?: number | null
          status: 'success' | 'error' | 'timeout'
          error_message?: string | null
          created_at?: string
        }
        Update: {
          id?: string
          conversation_id?: string | null
          agent_type?: string
          action?: string
          input_data?: Json
          output_data?: Json
          execution_time_ms?: number | null
          status?: 'success' | 'error' | 'timeout'
          error_message?: string | null
          created_at?: string
        }
        Relationships: [{ foreignKeyName: "agent_logs_conversation_id_fkey", columns: ["conversation_id"], referencedRelation: "conversations", referencedColumns: ["id"] }]
      }
      appointments: {
        Row: {
          id: string
          lead_id: string
          conversation_id: string | null
          appointment_type: string
          scheduled_at: string
          duration_minutes: number
          status: 'scheduled' | 'confirmed' | 'completed' | 'cancelled' | 'no_show'
          meeting_link: string | null
          notes: string | null
          metadata: Json
          created_at: string
          updated_at: string
          deleted_at: string | null
        }
        Insert: {
          id?: string
          lead_id: string
          conversation_id?: string | null
          appointment_type: string
          scheduled_at: string
          duration_minutes: number
          status?: 'scheduled' | 'confirmed' | 'completed' | 'cancelled' | 'no_show'
          meeting_link?: string | null
          notes?: string | null
          metadata?: Json
          created_at?: string
          updated_at?: string
          deleted_at?: string | null
        }
        Update: {
          id?: string
          lead_id?: string
          conversation_id?: string | null
          appointment_type?: string
          scheduled_at?: string
          duration_minutes?: number
          status?: 'scheduled' | 'confirmed' | 'completed' | 'cancelled' | 'no_show'
          meeting_link?: string | null
          notes?: string | null
          metadata?: Json
          created_at?: string
          updated_at?: string
          deleted_at?: string | null
        }
        Relationships: [
          { foreignKeyName: "appointments_lead_id_fkey", columns: ["lead_id"], referencedRelation: "leads", referencedColumns: ["id"] },
          { foreignKeyName: "appointments_conversation_id_fkey", columns: ["conversation_id"], referencedRelation: "conversations", referencedColumns: ["id"] }
        ]
      }
      service_recommendations: {
        Row: {
          id: string
          lead_id: string
          conversation_id: string | null
          service_name: string
          confidence_score: number | null
          reasoning: string | null
          priority: 'high' | 'medium' | 'low' | null
          status: 'suggested' | 'accepted' | 'rejected'
          metadata: Json
          created_at: string
        }
        Insert: {
          id?: string
          lead_id: string
          conversation_id?: string | null
          service_name: string
          confidence_score?: number | null
          reasoning?: string | null
          priority?: 'high' | 'medium' | 'low' | null
          status?: 'suggested' | 'accepted' | 'rejected'
          metadata?: Json
          created_at?: string
        }
        Update: {
          id?: string
          lead_id?: string
          conversation_id?: string | null
          service_name?: string
          confidence_score?: number | null
          reasoning?: string | null
          priority?: 'high' | 'medium' | 'low' | null
          status?: 'suggested' | 'accepted' | 'rejected'
          metadata?: Json
          created_at?: string
        }
        Relationships: [
          { foreignKeyName: "service_recommendations_lead_id_fkey", columns: ["lead_id"], referencedRelation: "leads", referencedColumns: ["id"] },
          { foreignKeyName: "service_recommendations_conversation_id_fkey", columns: ["conversation_id"], referencedRelation: "conversations", referencedColumns: ["id"] }
        ]
      }
      generated_content: {
        Row: {
          id: string
          lead_id: string | null
          content_type: string
          title: string
          content: string
          agent_type: string
          status: 'draft' | 'review' | 'approved' | 'published' | 'archived'
          metadata: Json
          created_at: string
          updated_at: string
          deleted_at: string | null
        }
        Insert: {
          id?: string
          lead_id?: string | null
          content_type: string
          title: string
          content: string
          agent_type: string
          status?: 'draft' | 'review' | 'approved' | 'published' | 'archived'
          metadata?: Json
          created_at?: string
          updated_at?: string
          deleted_at?: string | null
        }
        Update: {
          id?: string
          lead_id?: string | null
          content_type?: string
          title?: string
          content?: string
          agent_type?: string
          status?: 'draft' | 'review' | 'approved' | 'published' | 'archived'
          metadata?: Json
          created_at?: string
          updated_at?: string
          deleted_at?: string | null
        }
        Relationships: [{ foreignKeyName: "generated_content_lead_id_fkey", columns: ["lead_id"], referencedRelation: "leads", referencedColumns: ["id"] }]
      }
      profiles: {
        Row: {
          avatar_url: string | null
          bio: string | null
          created_at: string
          display_name: string | null
          id: string
          updated_at: string
          user_id: string
        }
        Insert: {
          avatar_url?: string | null
          bio?: string | null
          created_at?: string
          display_name?: string | null
          id?: string
          updated_at?: string
          user_id: string
        }
        Update: {
          avatar_url?: string | null
          bio?: string | null
          created_at?: string
          display_name?: string | null
          id?: string
          updated_at?: string
          user_id?: string
        }
        Relationships: []
      }
      model_response_cache: {
        Row: {
          id: string
          model_name: string
          task_type: string
          prompt_hash: string
          prompt: string
          response: string
          tokens_used: number | null
          execution_time_ms: number | null
          created_at: string
          expires_at: string | null
        }
        Insert: {
          id?: string
          model_name: string
          task_type: string
          prompt_hash: string
          prompt: string
          response: string
          tokens_used?: number | null
          execution_time_ms?: number | null
          created_at?: string
          expires_at?: string | null
        }
        Update: {
          id?: string
          model_name?: string
          task_type?: string
          prompt_hash?: string
          prompt?: string
          response?: string
          tokens_used?: number | null
          execution_time_ms?: number | null
          created_at?: string
          expires_at?: string | null
        }
        Relationships: []
      }
      model_performance_metrics: {
        Row: {
          id: string
          model_name: string
          task_type: string
          total_requests: number
          successful_requests: number
          failed_requests: number
          total_tokens: number
          avg_response_time: number
          cache_hits: number
          cache_misses: number
          last_error: string | null
          last_error_at: string | null
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          model_name: string
          task_type: string
          total_requests?: number
          successful_requests?: number
          failed_requests?: number
          total_tokens?: number
          avg_response_time?: number
          cache_hits?: number
          cache_misses?: number
          last_error?: string | null
          last_error_at?: string | null
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          model_name?: string
          task_type?: string
          total_requests?: number
          successful_requests?: number
          failed_requests?: number
          total_tokens?: number
          avg_response_time?: number
          cache_hits?: number
          cache_misses?: number
          last_error?: string | null
          last_error_at?: string | null
          created_at?: string
          updated_at?: string
        }
        Relationships: []
      }
    }
    Views: {
      [_ in never]: never
    }
    Functions: {
      get_model_performance_metrics: {
        Args: {
          start_date?: string | null
          end_date?: string | null
        }
        Returns: {
          model_name: string
          task_type: string
          success_rate: number
          avg_response_time: number
          cache_hit_rate: number
          total_requests: number
          total_tokens: number
        }[]
      }
      update_model_metrics: {
        Args: {
          p_model_name: string
          p_task_type: string
          p_success: boolean
          p_response_time: number
          p_tokens_used: number | null
          p_cache_hit: boolean
          p_error_message?: string | null
        }
        Returns: undefined
      }
    }
    Enums: {
      [_ in never]: never
    }
    CompositeTypes: {
      [_ in never]: never
    }
  }
}

type DatabaseWithoutInternals = Omit<Database, "__InternalSupabase">

type DefaultSchema = DatabaseWithoutInternals[Extract<keyof Database, "public">]

export type Tables<
  DefaultSchemaTableNameOrOptions extends
    | keyof (DefaultSchema["Tables"] & DefaultSchema["Views"])
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof (DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"] &
        DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Views"])
    : never = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? (DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"] &
      DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Views"])[TableName] extends {
      Row: infer R
    }
    ? R
    : never
  : DefaultSchemaTableNameOrOptions extends keyof (DefaultSchema["Tables"] &
        DefaultSchema["Views"])
    ? (DefaultSchema["Tables"] &
        DefaultSchema["Views"])[DefaultSchemaTableNameOrOptions] extends {
        Row: infer R
      }
      ? R
      : never
    : never

export type TablesInsert<
  DefaultSchemaTableNameOrOptions extends
    | keyof DefaultSchema["Tables"]
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"]
    : never = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"][TableName] extends {
      Insert: infer I
    }
    ? I
    : never
  : DefaultSchemaTableNameOrOptions extends keyof DefaultSchema["Tables"]
    ? DefaultSchema["Tables"][DefaultSchemaTableNameOrOptions] extends {
        Insert: infer I
      }
      ? I
      : never
    : never

export type TablesUpdate<
  DefaultSchemaTableNameOrOptions extends
    | keyof DefaultSchema["Tables"]
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"]
    : never = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"][TableName] extends {
      Update: infer U
    }
    ? U
    : never
  : DefaultSchemaTableNameOrOptions extends keyof DefaultSchema["Tables"]
    ? DefaultSchema["Tables"][DefaultSchemaTableNameOrOptions] extends {
        Update: infer U
      }
      ? U
      : never
    : never

export type Enums<
  DefaultSchemaEnumNameOrOptions extends
    | keyof DefaultSchema["Enums"]
    | { schema: keyof DatabaseWithoutInternals },
  EnumName extends DefaultSchemaEnumNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaEnumNameOrOptions["schema"]]["Enums"]
    : never = never,
> = DefaultSchemaEnumNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaEnumNameOrOptions["schema"]]["Enums"][EnumName]
  : DefaultSchemaEnumNameOrOptions extends keyof DefaultSchema["Enums"]
    ? DefaultSchema["Enums"][DefaultSchemaEnumNameOrOptions]
    : never

export type CompositeTypes<
  PublicCompositeTypeNameOrOptions extends
    | keyof DefaultSchema["CompositeTypes"]
    | { schema: keyof DatabaseWithoutInternals },
  CompositeTypeName extends PublicCompositeTypeNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[PublicCompositeTypeNameOrOptions["schema"]]["CompositeTypes"]
    : never = never,
> = PublicCompositeTypeNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[PublicCompositeTypeNameOrOptions["schema"]]["CompositeTypes"][CompositeTypeName]
  : PublicCompositeTypeNameOrOptions extends keyof DefaultSchema["CompositeTypes"]
    ? DefaultSchema["CompositeTypes"][PublicCompositeTypeNameOrOptions]
    : never

export const Constants = {
  public: {
    Enums: {},
  },
} as const
