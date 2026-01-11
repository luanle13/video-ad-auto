export interface User {
  user_id: string;
  email: string;
  created_at: string;
}

export interface Product {
  product_id: string;
  user_id: string;
  title: string;
  description: string;
  price: number;
  image_keys: string[];
  image_urls: string[];
  created_at: string;
  updated_at: string;
}

export enum JobStatus {
  PENDING = 'PENDING',
  PROCESSING = 'PROCESSING',
  ANALYZING = 'ANALYZING',
  SCRIPTING = 'SCRIPTING',
  GENERATING_TTS = 'GENERATING_TTS',
  GENERATING_VIDEO = 'GENERATING_VIDEO',
  COMPLETE = 'COMPLETE',
  FAILED = 'FAILED'
}

export interface JobAdjustments {
  background_style?: string;
  tone?: string;
  emphasis?: string;
  duration_preference?: number;
  additional_instructions?: string;
}

export interface Job {
  job_id: string;
  user_id: string;
  product_id: string;
  status: JobStatus;
  adjustments: JobAdjustments;
  step_outputs: Record<string, any>;
  video_url?: string;
  audio_url?: string;
  error_message?: string;
  created_at: string;
  updated_at: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface ErrorResponse {
  error: string;
  code: string;
  details?: any;
}