import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { quizzesApi } from '@/services/api'
import type { Quiz, QuizWithQuestions, QuizAttempt, AttemptResult } from '@/types'

export const quizKeys = {
  all: ['quizzes'] as const,
  detail: (id: string) => ['quiz', id] as const,
  attempts: (quizId: string) => ['quiz-attempts', quizId] as const,
  attemptResult: (quizId: string, attemptId: string) => ['quiz-result', quizId, attemptId] as const,
}

export function useQuizzesList(limit = 50) {
  return useQuery({
    queryKey: [...quizKeys.all, limit],
    queryFn: async () => {
      const res = await quizzesApi.list(0, limit)
      return res.data as { items: Quiz[]; total: number }
    },
    refetchInterval: (query) => {
      const items: Quiz[] = query.state.data?.items ?? []
      return items.some(q => q.status === 'generating') ? 3000 : false
    },
  })
}

export function useQuizDetail(id: string) {
  return useQuery({
    queryKey: quizKeys.detail(id),
    queryFn: async () => {
      const res = await quizzesApi.get(id)
      return res.data as QuizWithQuestions
    },
    enabled: !!id,
  })
}

export function useStartAttempt() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (quizId: string) => {
      const res = await quizzesApi.startAttempt(quizId)
      return res.data as QuizAttempt & { questions: QuizWithQuestions['questions'] }
    },
    onSuccess: (_data, quizId) => {
      queryClient.invalidateQueries({ queryKey: quizKeys.attempts(quizId) })
    },
  })
}

export function useSubmitAttempt() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({
      quizId, attemptId, answers,
    }: {
      quizId: string
      attemptId: string
      answers: { question_id: string; user_answer: string }[]
    }) => {
      const res = await quizzesApi.submitAttempt(quizId, attemptId, answers)
      return res.data as AttemptResult
    },
    onSuccess: (_data, { quizId }) => {
      queryClient.invalidateQueries({ queryKey: quizKeys.detail(quizId) })
      queryClient.invalidateQueries({ queryKey: quizKeys.attempts(quizId) })
    },
  })
}

export function useAttemptResult(quizId: string, attemptId: string) {
  return useQuery({
    queryKey: quizKeys.attemptResult(quizId, attemptId),
    queryFn: async () => {
      const res = await quizzesApi.getAttemptResult(quizId, attemptId)
      return res.data as AttemptResult
    },
    enabled: !!quizId && !!attemptId,
  })
}

export function useQuizAttempts(quizId: string, limit = 10) {
  return useQuery({
    queryKey: [...quizKeys.attempts(quizId), limit],
    queryFn: async () => {
      const res = await quizzesApi.listAttempts(quizId, 0, limit)
      return res.data as { items: QuizAttempt[]; total: number }
    },
    enabled: !!quizId,
  })
}

export function useCreateQuiz() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (params: {
      documentId: string
      numQuestions?: number
      shuffleQuestions?: boolean
      sourceContent?: string
    }) => {
      const res = await quizzesApi.create(
        params.documentId,
        params.numQuestions,
        undefined,
        undefined,
        params.shuffleQuestions,
        params.sourceContent,
      )
      return res.data as Quiz
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: quizKeys.all })
    },
  })
}

export function useDeleteQuiz() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => quizzesApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: quizKeys.all })
    },
  })
}
