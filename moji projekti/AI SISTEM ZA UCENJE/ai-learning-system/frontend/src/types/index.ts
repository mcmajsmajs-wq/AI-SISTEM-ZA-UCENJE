export interface User {
  id: number
  email: string
  full_name: string | null
  is_active: boolean
  is_superuser: boolean
  timezone: string
  language: string
  created_at: string
  updated_at: string
}

export interface UserStats {
  total_documents: number
  total_chunks: number
  translated_chunks: number
  total_quizzes: number
  average_score: number
  study_streak: number
}

export interface Token {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface LoginCredentials {
  username: string
  password: string
}

export interface RegisterData {
  email: string
  password: string
  full_name?: string
}

export interface FileUploadResponse {
  id: number
  filename: string
  original_filename: string
  file_size: number
  mime_type: string
  checksum: string
  status: string
  created_at: string
}

export interface FileListResponse {
  files: FileUploadResponse[]
  total: number
  page: number
  size: number
  pages: number
}

export interface Document {
  id: number
  file_id: number
  title: string
  author: string | null
  total_pages: number
  total_chunks: number
  source_language: string
  target_language: string
  status: DocumentStatus
  processing_progress: number
  created_at: string
  updated_at: string
}

export type DocumentStatus = 
  | 'pending'
  | 'processing'
  | 'processed'
  | 'translating'
  | 'translated'
  | 'error'

export interface Chunk {
  id: number
  document_id: number
  chunk_index: number
  original_text: string
  translated_text: string | null
  status: ChunkStatus
  page_number: number | null
  heading: string | null
  is_edited: boolean
  created_at: string
  updated_at: string
}

export type ChunkStatus = 
  | 'pending'
  | 'processed'
  | 'translated'
  | 'approved'
  | 'edited'

export interface ChunkUpdate {
  translated_text: string
  status?: ChunkStatus
}

export interface TranslationProgress {
  document_id: number
  total_chunks: number
  translated_chunks: number
  current_chunk: number
  status: string
  progress_percent: number
}

export interface Quiz {
  id: number
  document_id: number
  title: string
  description: string | null
  total_questions: number
  time_limit: number | null
  passing_score: number
  created_at: string
}

export interface Question {
  id: number
  quiz_id: number
  question_text: string
  question_type: QuestionType
  options: string[]
  correct_answer: string
  explanation: string | null
  points: number
}

export type QuestionType = 'multiple_choice' | 'checkbox' | 'true_false'

export interface QuizAttempt {
  id: number
  quiz_id: number
  user_id: number
  score: number
  total_points: number
  percentage: number
  passed: boolean
  started_at: string
  completed_at: string | null
}

export interface ApiError {
  detail: string
  status_code: number
}

export interface CostEstimate {
  provider: string
  estimated_cost: number
  currency: string
  character_count: number
}
