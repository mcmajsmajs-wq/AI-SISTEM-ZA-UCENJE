import { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { quizApi } from '@/services/api'
import { 
  Trophy,
  Clock,
  ChevronLeft,
  ChevronRight,
  CheckCircle,
  XCircle,
  Loader2,
  AlertCircle,
  HelpCircle
} from 'lucide-react'
import clsx from 'clsx'

export default function QuizPlayPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  
  const [currentQuestion, setCurrentQuestion] = useState(0)
  const [answers, setAnswers] = useState<Record<string, { answer: string | string[]; time: number }>>({})
  const [questionStartTime, setQuestionStartTime] = useState(Date.now())
  const [showExplanation, setShowExplanation] = useState(false)
  const [lastAnswer, setLastAnswer] = useState<{ isCorrect: boolean; explanation?: string } | null>(null)
  const [isCompleted, setIsCompleted] = useState(false)
  const [attemptId, setAttemptId] = useState<string | null>(null)

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

  const startAttemptMutation = useMutation({
    mutationFn: () => quizApi.startAttempt(id!),
    onSuccess: (data) => {
      setAttemptId(data.data.id)
    },
    onError: () => {
      toast.error('Greška pri pokretanju kviza')
      navigate('/quizzes')
    },
  })

  const submitAnswerMutation = useMutation({
    mutationFn: (data: {
      question_id: string
      selected_answer?: string
      selected_answers?: string[]
      time_spent: number
    }) => quizApi.submitAnswer(attemptId!, data),
    onSuccess: (data) => {
      const result = data.data
      setLastAnswer({
        isCorrect: result.is_correct,
        explanation: result.explanation,
      })
      setShowExplanation(true)
    },
  })

  const completeAttemptMutation = useMutation({
    mutationFn: () => quizApi.completeAttempt(attemptId!),
    onSuccess: (data) => {
      setIsCompleted(true)
      queryClient.invalidateQueries({ queryKey: ['quizzes'] })
    },
  })

  useEffect(() => {
    if (quiz?.data && !attemptId) {
      startAttemptMutation.mutate()
    }
  }, [quiz, attemptId])

  useEffect(() => {
    setQuestionStartTime(Date.now())
    setShowExplanation(false)
    setLastAnswer(null)
  }, [currentQuestion])

  const handleAnswer = useCallback((answer: string | string[]) => {
    if (!questions?.data?.[currentQuestion] || showExplanation) return
    
    const question = questions.data[currentQuestion]
    const timeSpent = Math.round((Date.now() - questionStartTime) / 1000)
    
    setAnswers(prev => ({
      ...prev,
      [question.id]: { answer, time: timeSpent },
    }))

    if (question.question_type === 'checkbox' && Array.isArray(answer)) {
      submitAnswerMutation.mutate({
        question_id: question.id,
        selected_answers: answer,
        time_spent: timeSpent,
      })
    } else {
      submitAnswerMutation.mutate({
        question_id: question.id,
        selected_answer: answer as string,
        time_spent: timeSpent,
      })
    }
  }, [questions, currentQuestion, showExplanation, questionStartTime])

  const handleNext = () => {
    if (questions?.data && currentQuestion < questions.data.length - 1) {
      setCurrentQuestion(prev => prev + 1)
    }
  }

  const handlePrevious = () => {
    if (currentQuestion > 0) {
      setCurrentQuestion(prev => prev - 1)
    }
  }

  const handleComplete = () => {
    completeAttemptMutation.mutate()
  }

  if (quizLoading || questionsLoading || !attemptId) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="w-8 h-8 text-primary-500 animate-spin" />
      </div>
    )
  }

  if (isCompleted) {
    return (
      <div className="max-w-2xl mx-auto text-center py-12 animate-fade-in">
        <div className="w-24 h-24 rounded-full bg-gradient-to-br from-green-400 to-green-600 flex items-center justify-center mx-auto mb-6">
          <CheckCircle className="w-12 h-12 text-white" />
        </div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Kviz završen!</h1>
        <p className="text-gray-500 mb-6">Rezultati se obrađuju...</p>
        <div className="flex justify-center gap-4">
          <Link to="/quizzes" className="btn-secondary">
            Nazad na kvizove
          </Link>
          <Link to="/" className="btn-primary">
            Dashboard
          </Link>
        </div>
      </div>
    )
  }

  const question = questions?.data?.[currentQuestion]
  const totalQuestions = questions?.data?.length || 0
  const progress = ((currentQuestion + 1) / totalQuestions) * 100

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <Link to="/quizzes" className="text-gray-500 hover:text-gray-700 flex items-center gap-2">
          <ChevronLeft className="w-5 h-5" />
          Nazad
        </Link>
        <div className="flex items-center gap-4">
          <span className="text-sm text-gray-500">
            Pitanje {currentQuestion + 1} od {totalQuestions}
          </span>
        </div>
      </div>

      <div className="card p-6">
        <div className="mb-4">
          <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
            <div 
              className="h-full bg-gradient-to-r from-primary-500 to-accent-500 transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        {question && (
          <>
            <div className="mb-6">
              <div className="flex items-center gap-2 mb-2">
                <span className="badge badge-primary">
                  {question.points} {question.points === 1 ? 'poen' : 'poena'}
                </span>
                <span className="badge badge-gray">
                  {question.question_type === 'multiple_choice' && 'Višestruki izbor'}
                  {question.question_type === 'checkbox' && 'Više tačnih'}
                  {question.question_type === 'true_false' && 'Tačno/Netačno'}
                  {question.question_type === 'short_answer' && 'Kratak odgovor'}
                </span>
              </div>
              <h2 className="text-xl font-semibold text-gray-900">
                {question.question_text}
              </h2>
            </div>

            {question.question_type === 'multiple_choice' && question.options && (
              <div className="space-y-3">
                {question.options.map((option: string, index: number) => {
                  const isSelected = answers[question.id]?.answer === option
                  const isCorrect = showExplanation && option === question.correct_answer
                  
                  return (
                    <button
                      key={index}
                      onClick={() => handleAnswer(option)}
                      disabled={showExplanation}
                      className={clsx(
                        "w-full text-left p-4 rounded-xl border-2 transition-all",
                        showExplanation
                          ? isCorrect
                            ? "border-green-500 bg-green-50"
                            : isSelected
                              ? "border-red-500 bg-red-50"
                              : "border-gray-200"
                          : isSelected
                            ? "border-primary-500 bg-primary-50"
                            : "border-gray-200 hover:border-primary-300 hover:bg-gray-50"
                      )}
                    >
                      <div className="flex items-center gap-3">
                        <span className="w-8 h-8 rounded-lg bg-gray-100 flex items-center justify-center font-medium">
                          {String.fromCharCode(65 + index)}
                        </span>
                        <span>{option}</span>
                        {showExplanation && isCorrect && (
                          <CheckCircle className="w-5 h-5 text-green-500 ml-auto" />
                        )}
                        {showExplanation && isSelected && !isCorrect && (
                          <XCircle className="w-5 h-5 text-red-500 ml-auto" />
                        )}
                      </div>
                    </button>
                  )
                })}
              </div>
            )}

            {question.question_type === 'true_false' && (
              <div className="grid grid-cols-2 gap-4">
                {['Tačno', 'Netačno'].map((option) => {
                  const isSelected = answers[question.id]?.answer === option
                  const isCorrect = showExplanation && option === question.correct_answer
                  
                  return (
                    <button
                      key={option}
                      onClick={() => handleAnswer(option)}
                      disabled={showExplanation}
                      className={clsx(
                        "p-6 rounded-xl border-2 text-center transition-all",
                        showExplanation
                          ? isCorrect
                            ? "border-green-500 bg-green-50"
                            : isSelected
                              ? "border-red-500 bg-red-50"
                              : "border-gray-200"
                          : isSelected
                            ? "border-primary-500 bg-primary-50"
                            : "border-gray-200 hover:border-primary-300"
                      )}
                    >
                      <span className="text-lg font-medium">{option}</span>
                    </button>
                  )
                })}
              </div>
            )}

            {showExplanation && lastAnswer && (
              <div className={clsx(
                "mt-6 p-4 rounded-xl",
                lastAnswer.isCorrect ? "bg-green-50 border border-green-200" : "bg-amber-50 border border-amber-200"
              )}>
                <div className="flex items-center gap-2 mb-2">
                  {lastAnswer.isCorrect ? (
                    <>
                      <CheckCircle className="w-5 h-5 text-green-600" />
                      <span className="font-medium text-green-700">Tačno!</span>
                    </>
                  ) : (
                    <>
                      <AlertCircle className="w-5 h-5 text-amber-600" />
                      <span className="font-medium text-amber-700">Netačno</span>
                    </>
                  )}
                </div>
                {lastAnswer.explanation && (
                  <p className="text-gray-700">{lastAnswer.explanation}</p>
                )}
              </div>
            )}
          </>
        )}

        <div className="flex items-center justify-between mt-6 pt-6 border-t border-gray-100">
          <button
            onClick={handlePrevious}
            disabled={currentQuestion === 0}
            className="btn-secondary"
          >
            <ChevronLeft className="w-5 h-5" />
            Prethodno
          </button>

          {currentQuestion === totalQuestions - 1 ? (
            <button
              onClick={handleComplete}
              disabled={Object.keys(answers).length < totalQuestions}
              className="btn-primary"
            >
              Završi kviz
            </button>
          ) : (
            <button
              onClick={handleNext}
              className="btn-primary"
            >
              Sledeće
              <ChevronRight className="w-5 h-5" />
            </button>
          )}
        </div>
      </div>

      <div className="flex justify-center gap-2">
        {questions?.data?.map((q: any, i: number) => (
          <button
            key={q.id}
            onClick={() => setCurrentQuestion(i)}
            className={clsx(
              "w-10 h-10 rounded-lg text-sm font-medium transition-all",
              i === currentQuestion
                ? "bg-primary-500 text-white"
                : answers[q.id]
                  ? "bg-green-100 text-green-700"
                  : "bg-gray-100 text-gray-600 hover:bg-gray-200"
            )}
          >
            {i + 1}
          </button>
        ))}
      </div>
    </div>
  )
}
