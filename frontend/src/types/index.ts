export interface User {
  id: string
  email: string
  full_name: string | null
  is_active: boolean
  is_verified: boolean
  is_superuser?: boolean
  timezone?: string
  language?: string
  created_at: string
  updated_at?: string
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
  id: string
  original_filename: string
  file_size: number
  mime_type: string
  checksum: string
  status: string
  created_at: string
}

export interface FileListResponse {
  items: FileUploadResponse[]
  total: number
  skip: number
  limit: number
}

export interface Document {
  id: string
  file_id: string | null
  user_id: string | null
  title: string
  description: string | null
  total_pages: number | null
  total_chunks: number
  source_language: string
  target_language: string
  status: DocumentStatus
  metadata: Record<string, unknown>
  created_at: string
  updated_at: string | null
}

export type DocumentStatus =
  | 'pending'
  | 'processing'
  | 'translating'
  | 'completed'
  | 'error'

export interface Chunk {
  id: string
  document_id: string
  sequence_number: number
  content: string
  translated_content: string | null
  token_count: number | null
  heading_level: number
  parent_heading: string | null
  is_translated: boolean
  is_reviewed: boolean
  created_at: string
  updated_at: string | null
}

export interface ChunkUpdate {
  translated_content?: string
  is_reviewed?: boolean
}

export interface TranslationProgress {
  document_id: string
  total_chunks: number
  translated_chunks: number
  current_chunk: number
  status: string
  progress_percent: number
}

export interface Quiz {
  id: string
  document_id: string
  title: string
  description: string | null
  total_questions: number
  target_questions: number
  time_limit: number | null
  passing_score: number
  status: string
  created_at: string
}

export interface Question {
  id: string
  quiz_id: string
  question_text: string
  question_type: QuestionType
  options: string[]
  correct_answer: string
  explanation: string | null
  points: number
  image_url?: string | null
  image_caption?: string | null
  exact_word?: string | null
  alternative_words?: string | null
  case_insensitive?: boolean
  formula?: string | null
  steps?: string | null
  extra_data?: {
    categories?: string[]
  }
}

export type QuestionType = 'multiple_choice' | 'checkbox' | 'true_false' | 'calculation' | 'fill_blank' | 'step_by_step' | 'chemical_equation' | 'sequencing' | 'matching' | 'categorization' | 'text_input'

export interface QuizAttempt {
  id: string
  quiz_id: string
  user_id: string
  score: number
  total_points: number
  percentage: number
  passed: boolean
  started_at: string
  completed_at: string | null
}

export interface QuizWithQuestions extends Quiz {
  questions: Question[]
}

export interface AnswerResult {
  question_id: string
  user_answer: string
  correct_answer: string
  is_correct: boolean
  points_earned: number
  explanation: string | null
}

export interface AttemptResult extends QuizAttempt {
  answers: AnswerResult[]
}

export interface ApiError {
  detail: string
  status_code: number
}

export interface StudyPlan {
  id: string
  user_id: string
  daily_quiz_goal: number
  weekly_quiz_goal: number
  session_duration_min: number
  study_days: number[]
  reminder_enabled: boolean
  reminder_time: string | null
  notes: string | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface StudyPlanItem {
  id: string
  plan_id: string
  quiz_id: string
  quiz?: { id: string; title: string }
  scheduled_for: string
  completed_at: string | null
  is_completed: boolean
  priority: number
  notes: string | null
}

export interface StudyPlanProgress {
  plan: StudyPlan
  current_streak: number
  week_completed: number
  week_goal: number
  week_pct: number
  today_completed: number
  today_goal: number
  today_items: StudyPlanItem[]
  upcoming_items: StudyPlanItem[]
}

export interface CostEstimate {
  provider: string
  estimated_cost: number
  currency: string
  character_count: number
}
