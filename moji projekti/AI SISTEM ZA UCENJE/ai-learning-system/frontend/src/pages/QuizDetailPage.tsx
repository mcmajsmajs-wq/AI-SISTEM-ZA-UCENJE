import { useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { quizApi } from '@/services/api'
import {
  Trophy,
  Clock,
  Target,
  Play,
  Edit,
  Trash2,
  ChevronLeft,
  Loader2,
  BookOpen,
  CheckCircle,
  XCircle,
  HelpCircle,
  Calendar,
  Award
} from 'lucide-react'
import clsx from 'clsx'

export default function QuizDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)

  const { data: quiz, isLoading: quizLoading } = useQuery({
    queryKey: ['quiz', id],
    queryFn: () => quizApi.get(id!),
    enabled: !!id,
  })

  const { data: questions, isLoading: questionsLoading } = useQuery({
    queryKey: ['quiz-questions', id],
    queryFn: () => quizApi.getQuestions(id!),
    enabled: !!id,
  })

  const { data: attempts, isLoading: attemptsLoading } = useQuery({
    queryKey: ['quiz-attempts', id],
    queryFn: () => quizApi.listAttempts(id!),
    enabled: !!id,
  })

  const deleteMutation = useMutation({
    mutationFn: () => quizApi.delete(id!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['quizzes'] })
      toast.success('Kviz je obrisan')
      navigate('/quizzes')
    },
    onError: () => toast.error('Greška pri brisanju'),
  })

  const publishMutation = useMutation({
    mutationFn: () => quizApi.update(id!, { status: 'published' }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['quiz', id] })
      queryClient.invalidateQueries({ queryKey: ['quizzes'] })
      toast.success('Kviz je objavljen')
    },
    onError: () => toast.error('Greška pri objavljivanju'),
  })

  const getDifficultyBadge = (difficulty: string) => {
    const styles: Record<string, string> = {
      easy: 'badge-success',
      medium: 'badge-warning',
      hard: 'badge-error',
      mixed: 'badge-primary',
    }
    const labels: Record<string, string> = {
      easy: 'Lako',
      medium: 'Srednje',
      hard: 'Teško',
      mixed: 'Mešano',
    }
    return (
      <span className={clsx('badge', styles[difficulty] || 'badge-gray')}>
        {labels[difficulty] || difficulty}
      </span>
    )
  }

  const getStatusBadge = (status: string) => {
    const styles: Record<string, string> = {
      draft: 'badge-gray',
      published: 'badge-success',
      archived: 'badge-warning',
    }
    const labels: Record<string, string> = {
      draft: 'U pripremi',
      published: 'Objavljen',
      archived: 'Arhiviran',
    }
    return (
      <span className={clsx('badge', styles[status] || 'badge-gray')}>
        {labels[status] || status}
      </span>
    )
  }

  const getQuestionTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      multiple_choice: 'Višestruki izbor',
      checkbox: 'Više tačnih',
      true_false: 'Tačno/Netačno',
      short_answer: 'Kratak odgovor',
    }
    return labels[type] || type
  }

  if (quizLoading || questionsLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="w-8 h-8 text-primary-500 animate-spin" />
      </div>
    )
  }

  const quizData = quiz?.data
  const questionsData = questions?.data || []
  const attemptsData = attempts?.data?.attempts || []

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center gap-4">
        <Link to="/quizzes" className="text-gray-500 hover:text-gray-700">
          <ChevronLeft className="w-5 h-5" />
        </Link>
        <div className="flex-1">
          <div className="flex items-center gap-3">
            <h1 className="text-3xl font-bold text-gray-900">{quizData?.title}</h1>
            {getStatusBadge(quizData?.status)}
            {getDifficultyBadge(quizData?.difficulty)}
          </div>
          <p className="text-gray-500 mt-1">{quizData?.description || 'Bez opisa'}</p>
        </div>
        <div className="flex items-center gap-2">
          {quizData?.status === 'draft' && (
            <>
              <button
                onClick={() => publishMutation.mutate()}
                disabled={publishMutation.isPending}
                className="btn-primary"
              >
                <CheckCircle className="w-5 h-5" />
                Objavi
              </button>
              <button
                onClick={() => setShowDeleteConfirm(true)}
                className="btn-ghost text-red-600 hover:bg-red-50"
              >
                <Trash2 className="w-5 h-5" />
              </button>
            </>
          )}
          {quizData?.status === 'published' && (
            <Link to={`/quizzes/${id}/play`} className="btn-primary">
              <Play className="w-5 h-5" />
              Započni kviz
            </Link>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="card p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-primary-100 flex items-center justify-center">
              <Target className="w-5 h-5 text-primary-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Pitanja</p>
              <p className="text-xl font-bold">{quizData?.total_questions || 0}</p>
            </div>
          </div>
        </div>
        <div className="card p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-amber-100 flex items-center justify-center">
              <Clock className="w-5 h-5 text-amber-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Vremensko ograničenje</p>
              <p className="text-xl font-bold">{quizData?.time_limit || 0} min</p>
            </div>
          </div>
        </div>
        <div className="card p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-green-100 flex items-center justify-center">
              <Award className="w-5 h-5 text-green-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Prolazni rezultat</p>
              <p className="text-xl font-bold">{quizData?.passing_score || 0}%</p>
            </div>
          </div>
        </div>
        <div className="card p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-blue-100 flex items-center justify-center">
              <BookOpen className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Pokušaji</p>
              <p className="text-xl font-bold">{quizData?.attempts_count || 0}</p>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <div className="p-4 border-b border-gray-100">
            <h2 className="font-semibold text-gray-900">Pitanja ({questionsData.length})</h2>
          </div>
          <div className="divide-y divide-gray-100 max-h-[400px] overflow-y-auto">
            {questionsData.length === 0 ? (
              <div className="p-8 text-center text-gray-500">
                <HelpCircle className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p>Nema pitanja</p>
              </div>
            ) : (
              questionsData.map((question: any, index: number) => (
                <div key={question.id} className="p-4">
                  <div className="flex items-start gap-3">
                    <span className="w-6 h-6 rounded-full bg-primary-100 text-primary-600 flex items-center justify-center text-sm font-medium flex-shrink-0">
                      {index + 1}
                    </span>
                    <div className="flex-1 min-w-0">
                      <p className="text-gray-900 font-medium">{question.question_text}</p>
                      <div className="flex items-center gap-2 mt-2">
                        <span className="badge badge-gray text-xs">
                          {getQuestionTypeLabel(question.question_type)}
                        </span>
                        <span className="badge badge-primary text-xs">
                          {question.points} poena
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        <div className="card">
          <div className="p-4 border-b border-gray-100">
            <h2 className="font-semibold text-gray-900">Poslednji pokušaji</h2>
          </div>
          <div className="divide-y divide-gray-100 max-h-[400px] overflow-y-auto">
            {attemptsData.length === 0 ? (
              <div className="p-8 text-center text-gray-500">
                <Trophy className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p>Nema pokušaja</p>
              </div>
            ) : (
              attemptsData.slice(0, 10).map((attempt: any) => (
                <div key={attempt.id} className="p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className={clsx(
                        "w-10 h-10 rounded-full flex items-center justify-center",
                        attempt.passed ? "bg-green-100" : "bg-red-100"
                      )}>
                        {attempt.passed ? (
                          <CheckCircle className="w-5 h-5 text-green-600" />
                        ) : (
                          <XCircle className="w-5 h-5 text-red-600" />
                        )}
                      </div>
                      <div>
                        <p className="font-medium text-gray-900">
                          {attempt.percentage.toFixed(1)}%
                        </p>
                        <p className="text-sm text-gray-500">
                          {attempt.correct_answers}/{attempt.correct_answers + attempt.wrong_answers} tačnih
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-sm text-gray-500">
                        {attempt.time_spent ? `${Math.round(attempt.time_spent / 60)} min` : '-'}
                      </p>
                      <p className="text-xs text-gray-400">
                        {new Date(attempt.started_at).toLocaleDateString('sr-RS')}
                      </p>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {showDeleteConfirm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl p-6 max-w-md w-full mx-4 shadow-xl">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Obriši kviz?</h3>
            <p className="text-gray-500 mb-4">
              Da li ste sigurni da želite da obrišete ovaj kviz? Ova akcija se ne može poništiti.
            </p>
            <div className="flex justify-end gap-3">
              <button
                onClick={() => setShowDeleteConfirm(false)}
                className="btn-secondary"
              >
                Otkaži
              </button>
              <button
                onClick={() => deleteMutation.mutate()}
                disabled={deleteMutation.isPending}
                className="btn-primary bg-red-600 hover:bg-red-700"
              >
                {deleteMutation.isPending ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  'Obriši'
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
