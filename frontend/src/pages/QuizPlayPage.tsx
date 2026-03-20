import { useState, useEffect, useCallback, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation } from '@tanstack/react-query'
import { quizzesApi } from '@/services/api'
import { QuizWithQuestions, Question } from '@/types'
import { Clock, ChevronRight, CheckSquare, AlertCircle, Loader2, CheckCircle2, XCircle, BookOpen, MessageCircle, Send, LogOut, Play, Save, X, ZoomIn } from 'lucide-react'
import toast from 'react-hot-toast'
import clsx from 'clsx'

type Answer = { question_id: string; user_answer: string }

interface SavedProgress {
  attemptId: string
  answers: Record<string, string>
  currentIdx: number
  confirmed: string[]
  savedAt: string
}

const STORAGE_KEY = (quizId: string) => `quiz_progress_${quizId}`

function loadProgress(quizId: string): SavedProgress | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY(quizId))
    if (!raw) return null
    const data: SavedProgress = JSON.parse(raw)
    // Odbaci staro stanje starije od 7 dana
    if (Date.now() - new Date(data.savedAt).getTime() > 7 * 86400_000) {
      localStorage.removeItem(STORAGE_KEY(quizId))
      return null
    }
    return data
  } catch { return null }
}

function saveProgress(quizId: string, data: Omit<SavedProgress, 'savedAt'>) {
  try {
    localStorage.setItem(STORAGE_KEY(quizId), JSON.stringify({ ...data, savedAt: new Date().toISOString() }))
  } catch {}
}

function clearProgress(quizId: string) {
  localStorage.removeItem(STORAGE_KEY(quizId))
}

export default function QuizPlayPage() {
  const { quizId } = useParams<{ quizId: string }>()
  const navigate = useNavigate()

  const [attemptId, setAttemptId] = useState<string | null>(null)
  const [currentIdx, setCurrentIdx] = useState(0)
  const [answers, setAnswers] = useState<Record<string, string>>({})
  const [confirmed, setConfirmed] = useState<Set<string>>(new Set()) // potvrđena pitanja
  const [timeLeft, setTimeLeft] = useState<number | null>(null)
  const [started, setStarted] = useState(false)
  const [showQuitConfirm, setShowQuitConfirm] = useState(false)
  const [savedProgress, setSavedProgress] = useState<SavedProgress | null>(null)
  const [zoomImage, setZoomImage] = useState<{url: string; caption?: string} | null>(null)

  // Učitaj sačuvani napredak pri montiranju
  useEffect(() => {
    if (quizId) setSavedProgress(loadProgress(quizId))
  }, [quizId])

  // Auto-generated AI explanations per question
  const [autoExplanations, setAutoExplanations] = useState<Record<string, string>>({})
  const [loadingExplanation, setLoadingExplanation] = useState<Record<string, boolean>>({})

  // Chat state per question
  const [chatHistories, setChatHistories] = useState<Record<string, { role: string; content: string }[]>>({})
  const [chatInput, setChatInput] = useState('')
  const [chatLoading, setChatLoading] = useState(false)
  const [chatProvider, setChatProvider] = useState('auto')
  const chatBottomRef = useRef<HTMLDivElement>(null)

  const CHAT_PROVIDERS = [
    { id: 'auto',    label: 'Auto',    emoji: '🤖' },
    { id: 'gemini',  label: 'Gemini',  emoji: '✨' },
    { id: 'groq',    label: 'Groq',    emoji: '⚡' },
    { id: 'openai',  label: 'OpenAI',  emoji: '🔵' },
    { id: 'ollama',  label: 'Ollama',  emoji: '🖥️' },
    { id: 'claude',  label: 'Claude',  emoji: '🟠' },
    { id: 'mistral', label: 'Mistral', emoji: '🌊' },
  ]

  const { data: quizData, isLoading } = useQuery({
    queryKey: ['quiz', quizId],
    queryFn: () => quizzesApi.get(quizId!),
    enabled: !!quizId,
  })

  const quiz: QuizWithQuestions | null = (quizData as any)?.data ?? null
  const questions: Question[] = quiz?.questions ?? []
  const currentQ = questions[currentIdx]

  // Start attempt (novi)
  const startMutation = useMutation({
    mutationFn: () => quizzesApi.startAttempt(quizId!),
    onSuccess: (res) => {
      setAttemptId((res as any).data.id)
      setStarted(true)
      if (quiz?.time_limit) setTimeLeft(quiz.time_limit)
    },
    onError: () => toast.error('Greška pri pokretanju kviza'),
  })

  // Nastavi sačuvani pokušaj
  const handleResume = () => {
    if (!savedProgress) return
    setAttemptId(savedProgress.attemptId)
    setAnswers(savedProgress.answers)
    setCurrentIdx(savedProgress.currentIdx)
    setConfirmed(new Set(savedProgress.confirmed))
    setStarted(true)
    setSavedProgress(null)
  }

  // Submit (kraj ili delimičan)
  const submitMutation = useMutation({
    mutationFn: (ans: Answer[]) => quizzesApi.submitAttempt(quizId!, attemptId!, ans),
    onSuccess: (res) => {
      clearProgress(quizId!)
      const result = (res as any).data
      navigate(`/quizzes/${quizId}/results/${attemptId}`, { state: { result } })
    },
    onError: () => toast.error('Greška pri submitovanju'),
  })

  // Sačuvaj i izađi
  const handleSaveAndExit = () => {
    if (quizId && attemptId) {
      saveProgress(quizId, {
        attemptId,
        answers,
        currentIdx,
        confirmed: Array.from(confirmed),
      })
      toast.success('Napredak sačuvan — možeš nastaviti kasnije')
    }
    setShowQuitConfirm(false)
    navigate('/quizzes')
  }

  // Predaj delimično i izađi
  const handleSubmitAndExit = () => {
    setShowQuitConfirm(false)
    const ans: Answer[] = questions.map((q) => ({
      question_id: q.id,
      user_answer: answers[q.id] ?? '',
    }))
    submitMutation.mutate(ans)
  }

  // Timer
  useEffect(() => {
    if (!started || timeLeft === null) return
    if (timeLeft <= 0) { handleSubmit(); return }
    const t = setTimeout(() => setTimeLeft((p) => (p ?? 1) - 1), 1000)
    return () => clearTimeout(t)
  }, [started, timeLeft])

  const handleAnswer = (questionId: string, value: string, type: string, checked?: boolean) => {
    if (confirmed.has(questionId)) return // ne menjaj posle potvrde
    if (type === 'checkbox') {
      const current = answers[questionId] ? answers[questionId].split(',') : []
      const updated = checked
        ? [...current, value]
        : current.filter((v) => v !== value)
      setAnswers((prev) => ({ ...prev, [questionId]: updated.join(',') }))
    } else {
      setAnswers((prev) => ({ ...prev, [questionId]: value }))
    }
  }

  // Provjera tačnosti odgovora
  const isAnswerCorrect = (q: Question, userAnswer: string): boolean => {
    if (!userAnswer) return false
    const correct = (q.correct_answer ?? '').trim()
    const user = userAnswer.trim()
    
    if (q.question_type === 'calculation' || q.question_type === 'step_by_step') {
      const numCorrect = parseFloat(correct.replace(',', '.'))
      const numUser = parseFloat(user.replace(',', '.'))
      if (isNaN(numCorrect) || isNaN(numUser)) return false
      return Math.abs(numCorrect - numUser) < 0.001
    }
    
    if (q.question_type === 'fill_blank') {
      if (q.case_insensitive) {
        return correct.toLowerCase() === user.toLowerCase()
      }
      return correct === user
    }
    
    if (q.question_type === 'chemical_equation') {
      const normalizeEq = (eq: string) => eq.toLowerCase()
        .replace(/→/g, '->')
        .replace(/\s+/g, '')
        .replace(/[-=]+>/g, '->')
      return normalizeEq(correct) === normalizeEq(user)
    }
    
    if (q.question_type === 'checkbox') {
      const correctSet = new Set(correct.split(',').map(s => s.trim().toLowerCase()))
      const userSet = new Set(user.split(',').map(s => s.trim().toLowerCase()))
      return correctSet.size === userSet.size && [...correctSet].every(v => userSet.has(v))
    }
    
    return correct.toLowerCase() === user.toLowerCase()
  }

  const FALLBACK_EXPLANATION = 'Ova tvrdnja je direktno navedena u tekstu.'

  const handleConfirm = (questionId: string) => {
    const q = questions.find(q => q.id === questionId)
    const isTextInput = q?.question_type === 'calculation' || q?.question_type === 'fill_blank' || q?.question_type === 'step_by_step' || q?.question_type === 'chemical_equation'
    if (!answers[questionId] && !isTextInput) {
      toast.error('Izaberi odgovor pre potvrde')
      return
    }
    if (isTextInput && !answers[questionId]?.trim()) {
      toast.error('Unesi odgovor pre potvrde')
      return
    }
    const newConfirmed = new Set([...confirmed, questionId])
    setConfirmed(newConfirmed)

    // Auto-save napredak posle svake potvrde
    if (quizId && attemptId) {
      saveProgress(quizId, {
        attemptId,
        answers,
        currentIdx,
        confirmed: Array.from(newConfirmed),
      })
    }

    // Auto-generate AI explanation if the stored one is missing or is the generic fallback
    if (!q) return
    const hasGoodExplanation = q.explanation && q.explanation.trim() !== FALLBACK_EXPLANATION
    if (hasGoodExplanation || autoExplanations[questionId]) return

    const userAnswer = answers[questionId] ?? ''
    const isCorrect = isAnswerCorrect(q, userAnswer)
    const msg = `Pitanje: "${q.question_text}"\nMoj odgovor: "${userAnswer}" (${isCorrect ? 'TAČNO ✓' : 'NETAČNO ✗'})\nTačan odgovor: "${q.correct_answer}"\n\nObjasni kratko (2-4 rečenice) zašto je "${q.correct_answer}" tačan odgovor i šta je ključna informacija koju treba zapamtiti.`

    setLoadingExplanation(prev => ({ ...prev, [questionId]: true }))
    quizzesApi.chat(quizId!, {
      message: msg,
      question_id: questionId,
      user_answer: userAnswer,
      history: [],
    }).then(res => {
      const reply = (res as any).data?.reply ?? ''
      if (reply) setAutoExplanations(prev => ({ ...prev, [questionId]: reply }))
    }).catch(() => {/* silently fail */}).finally(() => {
      setLoadingExplanation(prev => ({ ...prev, [questionId]: false }))
    })
  }

  const sendChatMessage = async () => {
    if (!chatInput.trim() || !currentQ || !quizId || chatLoading) return
    const questionId = currentQ.id
    const userMsg = { role: 'user', content: chatInput.trim() }
    const currentHistory = chatHistories[questionId] ?? []
    const newHistory = [...currentHistory, userMsg]

    setChatHistories(prev => ({ ...prev, [questionId]: newHistory }))
    setChatInput('')
    setChatLoading(true)

    try {
      const res = await quizzesApi.chat(quizId, {
        message: userMsg.content,
        question_id: questionId,
        user_answer: answers[questionId] ?? '',
        history: currentHistory,
        provider: chatProvider === 'auto' ? undefined : chatProvider,
      })
      const reply = { role: 'assistant', content: (res as any).data.reply }
      setChatHistories(prev => ({ ...prev, [questionId]: [...newHistory, reply] }))
      setTimeout(() => chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' }), 50)
    } catch {
      setChatHistories(prev => ({
        ...prev,
        [questionId]: [...newHistory, { role: 'assistant', content: 'Greška pri komunikaciji sa AI-jem. Pokušaj ponovo.' }]
      }))
    } finally {
      setChatLoading(false)
    }
  }

  const handleSubmit = useCallback(() => {
    const ans: Answer[] = questions.map((q) => ({
      question_id: q.id,
      user_answer: answers[q.id] ?? '',
    }))
    clearProgress(quizId!)
    submitMutation.mutate(ans)
  }, [questions, answers, submitMutation, quizId])

  const formatTime = (s: number) => `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`
  const progress = questions.length > 0 ? ((currentIdx + 1) / questions.length) * 100 : 0


  if (isLoading) {
    return (
      <div className="flex justify-center items-center py-32">
        <Loader2 className="w-8 h-8 animate-spin text-indigo-400" />
      </div>
    )
  }

  if (!quiz) {
    return (
      <div className="text-center py-16 text-gray-500">
        <AlertCircle className="w-10 h-10 mx-auto mb-3 text-gray-300" />
        <p>Kviz nije pronađen</p>
      </div>
    )
  }

  // Intro screen
  if (!started) {
    return (
      <div className="max-w-xl mx-auto">
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8 text-center space-y-5">
          <div className="w-16 h-16 rounded-2xl mx-auto flex items-center justify-center"
            style={{ background: 'linear-gradient(135deg, #e0e7ff, #ede9fe)' }}>
            <CheckSquare className="w-8 h-8 text-indigo-600" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-gray-900">{quiz.title}</h1>
            {quiz.description && <p className="text-gray-500 text-sm mt-1">{quiz.description}</p>}
          </div>
          <div className="flex justify-center gap-6 text-sm text-gray-600">
            <div className="text-center">
              <p className="text-2xl font-bold text-indigo-600">{quiz.total_questions}</p>
              <p className="text-xs text-gray-400">Pitanja</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-indigo-600">{quiz.passing_score}%</p>
              <p className="text-xs text-gray-400">Za prolaz</p>
            </div>
            {quiz.time_limit && (
              <div className="text-center">
                <p className="text-2xl font-bold text-indigo-600">{Math.floor(quiz.time_limit / 60)}</p>
                <p className="text-xs text-gray-400">Minuta</p>
              </div>
            )}
          </div>

          {/* Nastavi sačuvani pokušaj */}
          {savedProgress && (
            <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 text-left space-y-3">
              <p className="text-sm font-semibold text-amber-800">
                📌 Imaš sačuvan napredak — pitanje {savedProgress.currentIdx + 1} od {quiz.total_questions}
              </p>
              <p className="text-xs text-amber-600">
                Sačuvano: {new Date(savedProgress.savedAt).toLocaleString('sr-RS')}
              </p>
              <button
                onClick={handleResume}
                className="w-full py-2.5 rounded-xl text-white font-semibold flex items-center justify-center gap-2"
                style={{ background: 'linear-gradient(135deg, #f59e0b, #d97706)' }}
              >
                <Play className="w-4 h-4" />
                Nastavi od pitanja {savedProgress.currentIdx + 1}
              </button>
            </div>
          )}

          <button
            onClick={() => startMutation.mutate()}
            disabled={startMutation.isPending}
            className="w-full py-3 rounded-xl text-white font-semibold flex items-center justify-center gap-2"
            style={{ background: 'linear-gradient(135deg, #6366f1, #8b5cf6)' }}
          >
            {startMutation.isPending ? <Loader2 className="w-5 h-5 animate-spin" /> : (savedProgress ? 'Počni ispočetka' : 'Počni kviz')}
          </button>
        </div>
      </div>
    )
  }

  if (!currentQ) return null

  const selectedAnswer = answers[currentQ.id] ?? ''
  const selectedCheckboxes = selectedAnswer ? selectedAnswer.split(',') : []
  const isConfirmed = confirmed.has(currentQ.id)
  const userCorrect = isConfirmed && isAnswerCorrect(currentQ, selectedAnswer)

  return (
    <div className="max-w-2xl mx-auto space-y-4 pb-20">
      {/* Confirm quit modal */}
      {showQuitConfirm && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-2xl p-6 max-w-sm w-full space-y-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-red-50 flex items-center justify-center">
                <LogOut className="w-5 h-5 text-red-500" />
              </div>
              <div>
                <h3 className="font-bold text-gray-900">Izlaz iz kviza</h3>
                <p className="text-sm text-gray-500">Pitanje {currentIdx + 1} od {questions.length}</p>
              </div>
            </div>
            <p className="text-sm text-gray-600">
              Odgovoreno je na <strong>{confirmed.size} od {questions.length}</strong> pitanja. Šta želiš da uradiš?
            </p>
            <div className="space-y-2">
              <button
                onClick={handleSaveAndExit}
                className="w-full py-2.5 rounded-xl border-2 border-amber-400 bg-amber-50 text-amber-800 font-semibold text-sm flex items-center justify-center gap-2 hover:bg-amber-100 transition-colors"
              >
                <Save className="w-4 h-4" />
                Sačuvaj i izađi — nastavi kasnije
              </button>
              <button
                onClick={handleSubmitAndExit}
                disabled={submitMutation.isPending}
                className="w-full py-2.5 rounded-xl border-2 border-red-300 bg-red-50 text-red-700 font-semibold text-sm flex items-center justify-center gap-2 hover:bg-red-100 transition-colors"
              >
                {submitMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <XCircle className="w-4 h-4" />}
                Predaj delimično i pogledaj rezultate
              </button>
              <button
                onClick={() => setShowQuitConfirm(false)}
                className="w-full py-2.5 rounded-xl bg-indigo-600 text-white font-semibold text-sm flex items-center justify-center gap-2 hover:bg-indigo-700 transition-colors"
              >
                <Play className="w-4 h-4" />
                Nastavi kviz
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Progress bar */}
      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm px-5 py-3 flex items-center gap-4">
        <span className="text-sm font-medium text-gray-500 whitespace-nowrap">
          {currentIdx + 1} / {questions.length}
        </span>
        <div className="flex-1 bg-gray-100 rounded-full h-2">
          <div
            className="h-2 rounded-full transition-all duration-300"
            style={{ width: `${progress}%`, background: 'linear-gradient(90deg, #6366f1, #8b5cf6)' }}
          />
        </div>
        {timeLeft !== null && (
          <span className={clsx(
            "text-sm font-bold tabular-nums",
            timeLeft < 30 ? "text-red-500" : "text-indigo-600"
          )}>
            <Clock className="w-3.5 h-3.5 inline mr-1" />
            {formatTime(timeLeft)}
          </span>
        )}
        <button
          onClick={() => setShowQuitConfirm(true)}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-red-500 border border-red-200 hover:bg-red-50 transition-colors"
          title="Odustani od kviza"
        >
          <LogOut className="w-3.5 h-3.5" />
          Odustani
        </button>
      </div>

      {/* Question card */}
      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 space-y-5">
        {currentQ.image_url && (
          <div className="space-y-2">
            <div 
              className="relative group cursor-zoom-in rounded-lg border border-gray-200 bg-gray-50 overflow-y-auto"
              style={{ maxHeight: '600px' }}
              onClick={() => setZoomImage({url: currentQ.image_url || '', caption: currentQ.image_caption || undefined})}
            >
              <img 
                src={currentQ.image_url} 
                alt={currentQ.image_caption || "Quiz image"}
                className="w-full h-auto rounded"
                style={{ maxHeight: '600px' }}
              />
              <div className="absolute top-2 right-2 p-1.5 bg-black/50 rounded-full opacity-0 group-hover:opacity-100 transition-opacity">
                <ZoomIn className="w-4 h-4 text-white" />
              </div>
            </div>
            {currentQ.image_caption && (
              <p className="text-sm text-gray-500 italic text-center">{currentQ.image_caption}</p>
            )}
          </div>
        )}
        <div>
          <span className="text-xs font-semibold text-indigo-500 uppercase tracking-wider">
            {currentQ.question_type === 'multiple_choice' ? 'Jedan tačan odgovor' :
             currentQ.question_type === 'checkbox' ? 'Više tačnih odgovora' :
             currentQ.question_type === 'true_false' ? 'Tačno / Netačno' :
             currentQ.question_type === 'calculation' ? 'Računski zadatak' :
             currentQ.question_type === 'fill_blank' ? 'Popuni prazninu' :
             currentQ.question_type === 'step_by_step' ? 'Korak po korak' :
             currentQ.question_type === 'chemical_equation' ? 'Hemijska jednačina' : 'Pitanje'}
          </span>
          <p className="text-lg font-semibold text-gray-900 mt-2 leading-snug">{currentQ.question_text}</p>
        </div>

        <div className="space-y-2">
          {currentQ.question_type === 'calculation' || currentQ.question_type === 'step_by_step' ? (
            <div className="space-y-3">
              {currentQ.formula && (
                <div className="bg-gray-50 border border-gray-200 rounded-lg p-3 text-sm text-gray-600">
                  <span className="font-medium">Formula:</span> {currentQ.formula}
                </div>
              )}
              <input
                type="text"
                value={selectedAnswer}
                onChange={(e) => handleAnswer(currentQ.id, e.target.value, currentQ.question_type)}
                disabled={isConfirmed}
                placeholder="Unesi odgovor (npr: H=6)..."
                className={clsx(
                  "w-full px-4 py-3 rounded-xl border text-lg",
                  isConfirmed ? "bg-gray-50 cursor-default" : "",
                  isConfirmed && userCorrect
                    ? "border-green-400 bg-green-50"
                    : isConfirmed && !userCorrect
                    ? "border-red-400 bg-red-50"
                    : "border-gray-200 focus:outline-none focus:ring-2 focus:ring-indigo-300"
                )}
              />
              {isConfirmed && currentQ.steps && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 text-sm text-gray-700">
                  <span className="font-medium text-blue-700">Rešenje korak po korak:</span>
                  <div className="mt-2 whitespace-pre-wrap">{currentQ.steps}</div>
                </div>
              )}
            </div>
          ) : currentQ.question_type === 'fill_blank' ? (
            <div className="space-y-3">
              <input
                type="text"
                value={selectedAnswer}
                onChange={(e) => handleAnswer(currentQ.id, e.target.value, currentQ.question_type)}
                disabled={isConfirmed}
                placeholder="Unesi tačan odgovor..."
                className={clsx(
                  "w-full px-4 py-3 rounded-xl border text-lg",
                  isConfirmed ? "bg-gray-50 cursor-default" : "",
                  isConfirmed && userCorrect
                    ? "border-green-400 bg-green-50"
                    : isConfirmed && !userCorrect
                    ? "border-red-400 bg-red-50"
                    : "border-gray-200 focus:outline-none focus:ring-2 focus:ring-indigo-300"
                )}
              />
              {currentQ.exact_word && (
                <p className="text-xs text-gray-400">
                  {currentQ.case_insensitive ? 'Odgovor nije osetljiv na velika/mala slova' : 'Odgovor je osetljiv na velika/mala slova'}
                </p>
              )}
            </div>
          ) : currentQ.question_type === 'chemical_equation' ? (
            <div className="space-y-3">
              <input
                type="text"
                value={selectedAnswer}
                onChange={(e) => handleAnswer(currentQ.id, e.target.value, currentQ.question_type)}
                disabled={isConfirmed}
                placeholder="Npr: 2H2 + O2 -> 2H2O"
                className={clsx(
                  "w-full px-4 py-3 rounded-xl border text-lg font-mono",
                  isConfirmed ? "bg-gray-50 cursor-default" : "",
                  isConfirmed && userCorrect
                    ? "border-green-400 bg-green-50"
                    : isConfirmed && !userCorrect
                    ? "border-red-400 bg-red-50"
                    : "border-gray-200 focus:outline-none focus:ring-2 focus:ring-indigo-300"
                )}
              />
              <p className="text-xs text-gray-400">
                Koristi standardnu hemijsku notaciju (npr: -&gt; za strelicu)
              </p>
            </div>
          ) : (
            currentQ.options.map((option) => {
              const isSelected = currentQ.question_type === 'checkbox'
                ? selectedCheckboxes.includes(option)
                : selectedAnswer === option

              const isCorrectOption = isConfirmed && (() => {
                const correct = (currentQ.correct_answer ?? '').trim()
                if (currentQ.question_type === 'checkbox') {
                  return correct.split(',').map(s => s.trim()).includes(option.trim())
                }
                return correct === option
              })()

              return (
                <label
                  key={option}
                  className={clsx(
                    "flex items-center gap-3 p-3.5 rounded-xl border transition-all",
                    isConfirmed ? "cursor-default" : "cursor-pointer",
                    isConfirmed && isCorrectOption
                      ? "border-green-400 bg-green-50"
                      : isConfirmed && isSelected && !isCorrectOption
                      ? "border-red-400 bg-red-50"
                      : isSelected
                      ? "border-indigo-400 bg-indigo-50"
                      : isConfirmed
                      ? "border-gray-100 bg-gray-50 opacity-60"
                      : "border-gray-200 hover:border-indigo-200 hover:bg-gray-50"
                  )}
                >
                  {currentQ.question_type === 'checkbox' ? (
                    <input
                      type="checkbox"
                      checked={isSelected}
                      onChange={(e) => handleAnswer(currentQ.id, option, 'checkbox', e.target.checked)}
                      disabled={isConfirmed}
                      className="w-4 h-4 accent-indigo-600"
                    />
                  ) : (
                    <input
                      type="radio"
                      checked={isSelected}
                      onChange={() => handleAnswer(currentQ.id, option, currentQ.question_type)}
                      disabled={isConfirmed}
                      className="w-4 h-4 accent-indigo-600"
                    />
                  )}
                  <span className="text-sm font-medium text-gray-800 flex-1">{option}</span>
                  {isConfirmed && isCorrectOption && <CheckCircle2 className="w-4 h-4 text-green-500 flex-shrink-0" />}
                  {isConfirmed && isSelected && !isCorrectOption && <XCircle className="w-4 h-4 text-red-500 flex-shrink-0" />}
                </label>
              )
            })
          )}
        </div>

        {/* Feedback panel — prikazuje se posle potvrde */}
        {isConfirmed && (
          <div className={clsx(
            "rounded-xl p-4 border mt-2",
            userCorrect ? "bg-green-50 border-green-200" : "bg-amber-50 border-amber-200"
          )}>
            <div className="flex items-center gap-2 mb-2">
              {userCorrect
                ? <CheckCircle2 className="w-4 h-4 text-green-600 flex-shrink-0" />
                : <XCircle className="w-4 h-4 text-amber-600 flex-shrink-0" />}
              <span className={clsx("text-sm font-semibold", userCorrect ? "text-green-800" : "text-amber-800")}>
                {userCorrect 
                  ? 'Tačno! ✓' 
                  : `Netačno. ${(currentQ.question_type === 'calculation' || currentQ.question_type === 'fill_blank' || currentQ.question_type === 'step_by_step') ? `Tvoj odgovor: "${selectedAnswer}" — Tačan: ` : ''}${currentQ.correct_answer}`}
              </span>
            </div>
            {/* Show stored explanation if it's a good one */}
            {currentQ.explanation && currentQ.explanation !== FALLBACK_EXPLANATION && (
              <div className="flex gap-2 mt-2">
                <BookOpen className="w-4 h-4 text-indigo-400 flex-shrink-0 mt-0.5" />
                <p className="text-sm text-gray-700 leading-relaxed">{currentQ.explanation}</p>
              </div>
            )}
            {/* Auto-generated AI explanation */}
            {loadingExplanation[currentQ.id] && (
              <div className="flex items-center gap-2 mt-3 text-xs text-indigo-500">
                <Loader2 className="w-3 h-3 animate-spin" />
                <span>AI generiše objašnjenje...</span>
              </div>
            )}
            {autoExplanations[currentQ.id] && (
              <div className="mt-3 pt-3 border-t border-current/10">
                <div className="flex gap-2">
                  <BookOpen className="w-4 h-4 text-indigo-500 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="text-xs font-semibold text-indigo-600 mb-1">AI Objašnjenje</p>
                    <p className="text-sm text-gray-700 leading-relaxed">{autoExplanations[currentQ.id]}</p>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* AI Chat - otključan posle potvrde odgovora */}
        {isConfirmed && (
          <div className="mt-4 rounded-xl border border-indigo-100 bg-indigo-50/40 overflow-hidden">
            {/* Header */}
            <div className="flex items-center gap-2 px-4 py-2.5 border-b border-indigo-100 bg-white/60">
              <MessageCircle className="w-4 h-4 text-indigo-500" />
              <span className="text-sm font-semibold text-indigo-700">Pitaj AI za pojašnjenje</span>
              <span className="ml-auto text-xs text-gray-400">Postavi dodatna pitanja o ovoj temi</span>
            </div>

            {/* Messages */}
            <div className="max-h-56 overflow-y-auto px-4 py-3 flex flex-col gap-3">
              {(chatHistories[currentQ.id] ?? []).length === 0 && (
                <p className="text-xs text-gray-400 text-center py-2">
                  Nema poruka. Postavi pitanje AI tutoru.
                </p>
              )}
              {(chatHistories[currentQ.id] ?? []).map((msg, i) => (
                <div key={i} className={clsx('flex', msg.role === 'user' ? 'justify-end' : 'justify-start')}>
                  <div className={clsx(
                    'max-w-[85%] rounded-xl px-3 py-2 text-sm leading-relaxed',
                    msg.role === 'user'
                      ? 'bg-indigo-600 text-white rounded-br-sm'
                      : 'bg-white border border-gray-200 text-gray-700 rounded-bl-sm'
                  )}>
                    {msg.content}
                  </div>
                </div>
              ))}
              {chatLoading && (
                <div className="flex justify-start">
                  <div className="bg-white border border-gray-200 rounded-xl rounded-bl-sm px-3 py-2">
                    <Loader2 className="w-4 h-4 animate-spin text-indigo-400" />
                  </div>
                </div>
              )}
              <div ref={chatBottomRef} />
            </div>

            {/* Provider selector + input */}
            <div className="px-4 py-3 border-t border-indigo-100 bg-white/60 space-y-2">
              <div className="flex items-center gap-1 flex-wrap">
                <span className="text-xs text-gray-400 mr-1">AI:</span>
                {CHAT_PROVIDERS.map(p => (
                  <button
                    key={p.id}
                    onClick={() => setChatProvider(p.id)}
                    className={clsx(
                      'px-2 py-0.5 rounded-full text-xs font-medium border transition-all',
                      chatProvider === p.id
                        ? 'bg-indigo-600 text-white border-indigo-600'
                        : 'bg-white text-gray-500 border-gray-200 hover:border-indigo-300 hover:text-indigo-600'
                    )}
                  >
                    {p.emoji} {p.label}
                  </button>
                ))}
              </div>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={chatInput}
                  onChange={e => setChatInput(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && !e.shiftKey && sendChatMessage()}
                  placeholder="Postavi pitanje AI tutoru..."
                  className="flex-1 text-sm px-3 py-2 rounded-lg border border-gray-200 focus:outline-none focus:ring-2 focus:ring-indigo-300 bg-white"
                  disabled={chatLoading}
                />
                <button
                  onClick={sendChatMessage}
                  disabled={!chatInput.trim() || chatLoading}
                  className="px-3 py-2 rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-40 transition-colors"
                >
                  <Send className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Navigation */}
      <div className="flex gap-3">
        <button
          onClick={() => { setCurrentIdx((i) => Math.max(0, i - 1)) }}
          disabled={currentIdx === 0}
          className="px-5 py-2.5 rounded-xl border border-gray-200 text-sm font-medium text-gray-600 hover:bg-gray-50 disabled:opacity-30"
        >
          Nazad
        </button>

        {/* Potvrdi odgovor (pre potvrde) */}
        {!isConfirmed && (
          <button
            onClick={() => handleConfirm(currentQ.id)}
            disabled={!selectedAnswer}
            className="flex-1 flex items-center justify-center gap-2 py-2.5 rounded-xl text-white text-sm font-semibold disabled:opacity-40"
            style={{ background: 'linear-gradient(135deg, #6366f1, #8b5cf6)' }}
          >
            <CheckCircle2 className="w-4 h-4" />
            Potvrdi odgovor
          </button>
        )}

        {/* Sledeće / Završi (posle potvrde) */}
        {isConfirmed && (
          currentIdx < questions.length - 1 ? (
            <button
              onClick={() => setCurrentIdx((i) => i + 1)}
              className="flex-1 flex items-center justify-center gap-2 py-2.5 rounded-xl text-white text-sm font-semibold"
              style={{ background: 'linear-gradient(135deg, #6366f1, #8b5cf6)' }}
            >
              Sledeće
              <ChevronRight className="w-4 h-4" />
            </button>
          ) : (
            <button
              onClick={handleSubmit}
              disabled={submitMutation.isPending}
              className="flex-1 flex items-center justify-center gap-2 py-2.5 rounded-xl text-white text-sm font-semibold"
              style={{ background: 'linear-gradient(135deg, #10b981, #059669)' }}
            >
              {submitMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Završi kviz'}
            </button>
          )
        )}
      </div>

      {/* Lightbox Modal for Image Zoom */}
      {zoomImage && (
        <div 
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/90 overflow-auto"
          onClick={() => setZoomImage(null)}
        >
          <button
            className="fixed top-4 right-4 p-2 rounded-full bg-white/10 hover:bg-white/20 text-white transition-colors z-50"
            onClick={() => setZoomImage(null)}
          >
            <X className="w-6 h-6" />
          </button>
          <div 
            className="relative max-w-[95vw] my-8"
            onClick={(e) => e.stopPropagation()}
          >
            <img 
              src={zoomImage.url} 
              alt={zoomImage.caption || "Uvećana slika"}
              className="w-full h-auto rounded-lg"
            />
            {zoomImage.caption && (
              <p className="mt-3 text-center text-white/80 text-sm">{zoomImage.caption}</p>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
