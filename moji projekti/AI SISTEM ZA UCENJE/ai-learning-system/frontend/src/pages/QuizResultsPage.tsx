import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { quizApi } from '@/services/api'
import {
  Trophy,
  Clock,
  Target,
  CheckCircle,
  XCircle,
  ChevronLeft,
  Loader2,
  Award,
  BarChart3,
  HelpCircle
} from 'lucide-react'
import clsx from 'clsx'

export default function QuizResultsPage() {
  const { id, attemptId } = useParams<{ id: string; attemptId: string }>()

  const { data: quiz, isLoading: quizLoading } = useQuery({
    queryKey: ['quiz', id],
    queryFn: () => quizApi.get(id!),
    enabled: !!id,
  })

  const { data: attempt, isLoading: attemptLoading } = useQuery({
    queryKey: ['quiz-attempt', attemptId],
    queryFn: () => quizApi.getAttempt(attemptId!),
    enabled: !!attemptId,
  })

  const { data: questions, isLoading: questionsLoading } = useQuery({
    queryKey: ['quiz-questions', id],
    queryFn: () => quizApi.getQuestions(id!),
    enabled: !!id,
  })

  if (quizLoading || attemptLoading || questionsLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="w-8 h-8 text-primary-500 animate-spin" />
      </div>
    )
  }

  const quizData = quiz?.data
  const attemptData = attempt?.data
  const questionsData = questions?.data || []

  const passed = attemptData?.passed
  const percentage = attemptData?.percentage || 0
  const score = attemptData?.score || 0
  const totalPoints = attemptData?.total_points || 0
  const timeSpent = attemptData?.time_spent || 0

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-fade-in">
      <div className="flex items-center gap-4">
        <Link to="/quizzes" className="text-gray-500 hover:text-gray-700">
          <ChevronLeft className="w-5 h-5" />
        </Link>
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Rezultati kviza</h1>
          <p className="text-gray-500 mt-1">{quizData?.title}</p>
        </div>
      </div>

      <div className={clsx(
        "card p-8 text-center",
        passed ? "bg-gradient-to-br from-green-50 to-emerald-50" : "bg-gradient-to-br from-red-50 to-rose-50"
      )}>
        <div className={clsx(
          "w-24 h-24 rounded-full mx-auto flex items-center justify-center mb-4",
          passed ? "bg-green-100" : "bg-red-100"
        )}>
          {passed ? (
            <Trophy className="w-12 h-12 text-green-600" />
          ) : (
            <XCircle className="w-12 h-12 text-red-600" />
          )}
        </div>
        <h2 className={clsx(
          "text-3xl font-bold mb-2",
          passed ? "text-green-700" : "text-red-700"
        )}>
          {passed ? 'Čestitamo!' : 'Nažalost...'}
        </h2>
        <p className={clsx(
          "text-lg mb-6",
          passed ? "text-green-600" : "text-red-600"
        )}>
          {passed
            ? `Položili ste kviz sa ${percentage.toFixed(1)}%`
            : `Niste položili kviz. Potrebno je ${quizData?.passing_score}% za prolaz.`
          }
        </p>

        <div className="grid grid-cols-4 gap-4 max-w-2xl mx-auto">
          <div className="bg-white rounded-xl p-4 shadow-sm">
            <div className="text-3xl font-bold text-gray-900">{percentage.toFixed(0)}%</div>
            <div className="text-sm text-gray-500">Rezultat</div>
          </div>
          <div className="bg-white rounded-xl p-4 shadow-sm">
            <div className="text-3xl font-bold text-gray-900">{score}/{totalPoints}</div>
            <div className="text-sm text-gray-500">Poeni</div>
          </div>
          <div className="bg-white rounded-xl p-4 shadow-sm">
            <div className="text-3xl font-bold text-gray-900">
              {attemptData?.correct_answers || 0}
            </div>
            <div className="text-sm text-gray-500">Tačnih</div>
          </div>
          <div className="bg-white rounded-xl p-4 shadow-sm">
            <div className="text-3xl font-bold text-gray-900">
              {Math.round(timeSpent / 60)}
            </div>
            <div className="text-sm text-gray-500">Minuta</div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="card p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-green-100 flex items-center justify-center">
              <CheckCircle className="w-5 h-5 text-green-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900">
                {attemptData?.correct_answers || 0}
              </p>
              <p className="text-sm text-gray-500">Tačnih odgovora</p>
            </div>
          </div>
        </div>
        <div className="card p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-red-100 flex items-center justify-center">
              <XCircle className="w-5 h-5 text-red-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900">
                {attemptData?.wrong_answers || 0}
              </p>
              <p className="text-sm text-gray-500">Pogrešnih odgovora</p>
            </div>
          </div>
        </div>
        <div className="card p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gray-100 flex items-center justify-center">
              <HelpCircle className="w-5 h-5 text-gray-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900">
                {attemptData?.skipped_answers || 0}
              </p>
              <p className="text-sm text-gray-500">Preskočenih</p>
            </div>
          </div>
        </div>
      </div>

      <div className="card">
        <div className="p-4 border-b border-gray-100">
          <h2 className="font-semibold text-gray-900">Pregled pitanja</h2>
        </div>
        <div className="divide-y divide-gray-100 max-h-[500px] overflow-y-auto">
          {questionsData.map((question: any, index: number) => {
            const userAnswer = attemptData?.answers?.find((a: any) => a.question_id === question.id)
            const isCorrect = userAnswer?.is_correct

            return (
              <div key={question.id} className="p-4">
                <div className="flex items-start gap-3">
                  <div className={clsx(
                    "w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0",
                    isCorrect ? "bg-green-100" : "bg-red-100"
                  )}>
                    {isCorrect ? (
                      <CheckCircle className="w-4 h-4 text-green-600" />
                    ) : (
                      <XCircle className="w-4 h-4 text-red-600" />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-sm font-medium text-gray-500">
                        Pitanje {index + 1}
                      </span>
                      <span className="badge badge-gray text-xs">
                        {question.points} poena
                      </span>
                    </div>
                    <p className="text-gray-900 font-medium mb-2">
                      {question.question_text}
                    </p>
                    
                    {question.options && (
                      <div className="space-y-1 mt-2">
                        {question.options.map((option: string, i: number) => {
                          const isUserAnswer = userAnswer?.selected_answer === option
                          const isCorrectAnswer = question.correct_answer === option
                          
                          return (
                            <div
                              key={i}
                              className={clsx(
                                "text-sm px-3 py-1.5 rounded-lg",
                                isCorrectAnswer && "bg-green-100 text-green-800",
                                isUserAnswer && !isCorrectAnswer && "bg-red-100 text-red-800",
                                !isCorrectAnswer && !isUserAnswer && "text-gray-600"
                              )}
                            >
                              <span className="font-medium mr-2">
                                {String.fromCharCode(65 + i)}.
                              </span>
                              {option}
                              {isCorrectAnswer && " ✓"}
                              {isUserAnswer && !isCorrectAnswer && " ✗"}
                            </div>
                          )
                        })}
                      </div>
                    )}

                    {question.explanation && (
                      <div className="mt-3 p-3 bg-gray-50 rounded-lg text-sm text-gray-700">
                        <span className="font-medium">Objašnjenje:</span> {question.explanation}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      </div>

      <div className="flex justify-center gap-4">
        <Link to="/quizzes" className="btn-secondary">
          Svi kvizovi
        </Link>
        <Link to={`/quizzes/${id}/play`} className="btn-primary">
          Pokušaj ponovo
        </Link>
      </div>
    </div>
  )
}
