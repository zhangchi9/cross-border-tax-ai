export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
}

export interface UserProfile {
  countries_involved: string[];
  tax_residency_status?: string;
  visa_immigration_status?: string;
  filing_status?: string;
  tax_year?: number;
  sources_of_income: string[];
  foreign_assets: string[];
  credits_deductions: string[];
}

export interface CaseFile {
  session_id: string;
  user_profile: UserProfile;
  jurisdictions: string[];
  income_types: string[];
  assigned_tags: string[];  // Added for tag logging
  potential_issues: string[];
  unanswered_questions: string[];
  citations: string[];
  conversation_phase: 'intake' | 'clarifications' | 'final_suggestions';
  messages: ChatMessage[];
  created_at: string;
  updated_at: string;
}

export interface StreamingResponse {
  content: string;
  is_final: boolean;
  case_file?: CaseFile;
}

export interface SessionResponse {
  session_id: string;
  case_file: CaseFile;
}