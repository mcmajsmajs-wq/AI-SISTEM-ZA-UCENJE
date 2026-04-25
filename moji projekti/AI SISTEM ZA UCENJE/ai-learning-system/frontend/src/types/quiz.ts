export interface Quiz {
  id: string
  document_id: string | null
  user_id: string
  title: string
  description: string | null
  total_questions: number
  time_limit: number
  passing_score: number
  max_attempts: number
  difficulty: 'easy' | 'medium' | 'hard' | 'mixed'
  question_types: string[]
  status: 'draft' | 'published' | 'archived'
  attempts_count: number
  created_at: string
  updated_at: string | null
  published_at: string | null
}

export interface Question {
  id: string
  quiz_id: string
  question_text: string
  question_type: 'multiple_choice' | 'checkbox' | 'true_false' | 'short_answer'
  options: string[] | null
  correct_answer: string
  correct_answers: string[] | null
  explanation: string | null
  hint: string | null
  points: number
  order: number
  difficulty: 'easy' | 'medium' | 'hard'
  created_at: string
}

export interface QuestionForAttempt {
  id: string
  question_text: string
  question_type: 'multiple_choice' | 'checkbox' | 'true_false' | 'short_answer'
  options: string[] | null
  points: number
  order: number
}

export interface QuizAttempt {
  id: string
  quiz_id: string
  user_id: string
  score: number
  total_points: number
  percentage: number
  passed: boolean
  correct_answers: number
  wrong_answers: number
  skipped_answers: number
  time_spent: number
  status: 'in_progress' | 'completed' | 'abandoned'
  started_at: string
  completed_at: string | null
}

export interface Answer {
  id: string
  attempt_id: string
  question_id: string
  selected_answer: string | null
  selected_answers: string[] | null
  text_answer: string | null
  is_correct: boolean
  points_earned: number
  time_spent: number
}

export interface SubmitAnswerRequest {
  question_id: string
  selected_answer?: string
  selected_answers?: string[]
  text_answer?: string
  time_spent: number
}

export interface SubmitAnswerResponse {
  is_correct: boolean
  points_earned: number
  correct_answer?: string
  explanation?: string
}

export interface QuizStats {
  total_quizzes: number
  total_attempts: number
  average_score: number
  pass_rate: number
  total_questions_answered: number
}

export interface QuizGenerateRequest {
  document_id: string
  title?: string
  num_questions: number
  question_types?: string[]
  difficulty: 'easy' | 'medium' | 'hard' | 'mixed'
  time_limit: number
  passing_score: number
}
