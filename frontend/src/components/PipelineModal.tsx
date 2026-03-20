import { useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { documentsApi } from '@/services/api'
import { X, Zap, Loader2, CheckCircle, ChevronRight, Activity } from 'lucide-react'
import toast from 'react-hot-toast'
import clsx from 'clsx'

interface Props {
  documentId: string
  documentTitle: string
  onClose: () => void
  onStarted?: (taskId: string) => void
}

const TRANSLATION_PROVIDERS = [
  { id: null, label: 'Auto (fallback lanac)' },
  { id: 'ollama', label: 'Ollama (lokalni)' },
  { id: 'openai', label: 'OpenAI GPT' },
  { id: 'deepl', label: 'DeepL' },
  { id: 'google', label: 'Google Translate' },
  { id: 'claude', label: 'Claude (Anthropic)' },
  { id: 'gemini', label: 'Google Gemini' },
  { id: 'groq', label: 'Groq' },
  { id: 'mistral', label: 'Mistral' },
]

const QUIZ_PROVIDERS = [
  { id: null, label: 'Auto (fallback lanac)' },
  { id: 'ollama', label: 'Ollama (lokalni)' },
  { id: 'openai', label: 'OpenAI GPT' },
  { id: 'claude', label: 'Claude (Anthropic)' },
  { id: 'gemini', label: 'Google Gemini' },
  { id: 'groq', label: 'Groq' },
  { id: 'mistral', label: 'Mistral' },
]

const LANGUAGES = [
  { code: 'en', label: 'Engleski' },
  { code: 'sr', label: 'Srpski' },
  { code: 'de', label: 'Nemački' },
  { code: 'fr', label: 'Francuski' },
  { code: 'es', label: 'Španski' },
  { code: 'ru', label: 'Ruski' },
]

export default function PipelineModal({ documentId, documentTitle, onClose, onStarted }: Props) {
  const [sourceLang, setSourceLang] = useState('en')
  const [targetLang, setTargetLang] = useState('sr')
  const [translationProvider, setTranslationProvider] = useState<string | null>(null)
  const [quizProvider, setQuizProvider] = useState<string | null>(null)
  const [numQuestions, setNumQuestions] = useState(0)
  const [skipTranslation, setSkipTranslation] = useState(false)
  const [passingScore, setPassingScore] = useState(60)
  const [started, setStarted] = useState(false)
  const [taskResult, setTaskResult] = useState<any>(null)

  const { data: progressData } = useQuery({
    queryKey: ['document-progress', documentId],
    queryFn: () => documentsApi.getProgress(documentId),
    enabled: started,
    refetchInterval: 3000,
  })

  const { data: providersData } = useQuery({
    queryKey: ['pipeline-providers'],
    queryFn: () => documentsApi.getPipelineProviders(),
  })

  const providers = (providersData as any)?.data
  const quizProviderStatuses: Record<string, boolean> = {}
  const transProviderStatuses: Record<string, boolean> = {}
  providers?.quiz_providers?.forEach((p: any) => { quizProviderStatuses[p.id] = p.available })
  providers?.translation_providers?.forEach((p: any) => { transProviderStatuses[p.id] = p.available })

  const pipelineMutation = useMutation({
    mutationFn: () => documentsApi.startPipeline(documentId, {
      source_language: sourceLang,
      target_language: targetLang,
      translation_provider: skipTranslation ? null : translationProvider,
      quiz_provider: quizProvider,
      num_questions: numQuestions,
      skip_translation: skipTranslation,
      passing_score: passingScore,
    }),
    onSuccess: (res) => {
      const data = (res as any).data
      setTaskResult(data)
      setStarted(true)
      onStarted?.(data.task_id)
      toast.success('Pipeline pokrenut! Obrada tece u pozadini.')
    },
    onError: (err: any) => {
      toast.error(err?.response?.data?.detail || 'Greška pri pokretanju pipeline-a')
    },
  })

  const stages = [
    { label: 'PDF Processing', active: true },
    { label: `Prevod ${sourceLang} → ${targetLang}`, active: !skipTranslation && sourceLang !== targetLang },
    { label: `AI kviz (${numQuestions === 0 ? 'auto' : numQuestions} pitanja)`, active: true },
  ]

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg flex items-center justify-center"
              style={{ background: 'linear-gradient(135deg, #6366f1, #8b5cf6)' }}>
              <Zap className="w-4 h-4 text-white" />
            </div>
            <div>
              <h2 className="font-bold text-gray-900 text-base">Auto Pipeline</h2>
              <p className="text-xs text-gray-500 truncate max-w-[250px]">{documentTitle}</p>
            </div>
          </div>
          <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-gray-100 text-gray-500">
            <X className="w-5 h-5" />
          </button>
        </div>

        {!started ? (
          <div className="p-6 space-y-5">
            {/* Pipeline vizualizacija */}
            <div className="flex items-center gap-1 bg-gray-50 rounded-xl p-3">
              {stages.map((stage, i) => (
                <div key={i} className="flex items-center gap-1 flex-1 min-w-0">
                  <div className={clsx(
                    'flex-1 text-center px-2 py-1.5 rounded-lg text-xs font-medium truncate',
                    stage.active
                      ? 'bg-indigo-100 text-indigo-700'
                      : 'bg-gray-100 text-gray-400 line-through'
                  )}>
                    {stage.label}
                  </div>
                  {i < stages.length - 1 && (
                    <ChevronRight className={clsx('w-3 h-3 flex-shrink-0', stage.active ? 'text-indigo-400' : 'text-gray-300')} />
                  )}
                </div>
              ))}
            </div>

            {/* Jezik */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-semibold text-gray-600 mb-1 block">Izvorni jezik</label>
                <select value={sourceLang} onChange={e => setSourceLang(e.target.value)}
                  className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300">
                  {LANGUAGES.map(l => <option key={l.code} value={l.code}>{l.label}</option>)}
                </select>
              </div>
              <div>
                <label className="text-xs font-semibold text-gray-600 mb-1 block">Ciljni jezik</label>
                <select value={targetLang} onChange={e => setTargetLang(e.target.value)}
                  className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300">
                  {LANGUAGES.map(l => <option key={l.code} value={l.code}>{l.label}</option>)}
                </select>
              </div>
            </div>

            {/* Skip translation */}
            <label className="flex items-center gap-3 cursor-pointer">
              <div className="relative">
                <input type="checkbox" checked={skipTranslation}
                  onChange={e => setSkipTranslation(e.target.checked)} className="sr-only" />
                <div className={clsx(
                  'w-10 h-5 rounded-full transition-colors',
                  skipTranslation ? 'bg-indigo-500' : 'bg-gray-200'
                )}>
                  <div className={clsx(
                    'w-4 h-4 bg-white rounded-full shadow transition-transform mt-0.5',
                    skipTranslation ? 'translate-x-5 ml-0.5' : 'translate-x-0.5'
                  )} />
                </div>
              </div>
              <span className="text-sm font-medium text-gray-700">Preskoči prevod</span>
            </label>

            {/* Provajder za prevod */}
            {!skipTranslation && (
              <div>
                <label className="text-xs font-semibold text-gray-600 mb-1 block">AI za prevod</label>
                <div className="grid grid-cols-2 gap-2">
                  {TRANSLATION_PROVIDERS.map(p => {
                    const available = p.id === null || transProviderStatuses[p.id] !== false
                    return (
                      <button key={String(p.id)} onClick={() => setTranslationProvider(p.id)}
                        className={clsx(
                          'px-3 py-2 rounded-xl border text-xs font-medium text-left transition-all',
                          translationProvider === p.id
                            ? 'border-indigo-400 bg-indigo-50 text-indigo-700'
                            : 'border-gray-200 text-gray-600 hover:border-indigo-200',
                          !available && 'opacity-40 cursor-not-allowed'
                        )}>
                        {p.label}
                        {p.id && (
                          <span className={clsx('block text-[10px] mt-0.5',
                            available ? 'text-green-600' : 'text-red-400')}>
                            {available ? '● dostupan' : '● nedostupan'}
                          </span>
                        )}
                      </button>
                    )
                  })}
                </div>
              </div>
            )}

            {/* Provajder za kviz */}
            <div>
              <label className="text-xs font-semibold text-gray-600 mb-1 block">AI za kviz</label>
              <div className="grid grid-cols-2 gap-2">
                {QUIZ_PROVIDERS.map(p => {
                  const available = p.id === null || quizProviderStatuses[p.id] !== false
                  return (
                    <button key={String(p.id)} onClick={() => setQuizProvider(p.id)}
                      className={clsx(
                        'px-3 py-2 rounded-xl border text-xs font-medium text-left transition-all',
                        quizProvider === p.id
                          ? 'border-indigo-400 bg-indigo-50 text-indigo-700'
                          : 'border-gray-200 text-gray-600 hover:border-indigo-200',
                        !available && 'opacity-40 cursor-not-allowed'
                      )}>
                      {p.label}
                      {p.id && (
                        <span className={clsx('block text-[10px] mt-0.5',
                          available ? 'text-green-600' : 'text-red-400')}>
                          {available ? '● dostupan' : '● nedostupan'}
                        </span>
                      )}
                    </button>
                  )
                })}
              </div>
            </div>

            {/* Broj pitanja i prolaznost */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-semibold text-gray-600 mb-1 block">
                  Pitanja: <span className="text-indigo-600">{numQuestions === 0 ? 'Auto' : numQuestions}</span>
                </label>
                <input type="range" min={0} max={50} value={numQuestions}
                  onChange={e => setNumQuestions(Number(e.target.value))}
                  className="w-full accent-indigo-600" />
              </div>
              <div>
                <label className="text-xs font-semibold text-gray-600 mb-1 block">
                  Za prolaz: <span className="text-indigo-600">{passingScore}%</span>
                </label>
                <input type="range" min={40} max={100} step={5} value={passingScore}
                  onChange={e => setPassingScore(Number(e.target.value))}
                  className="w-full accent-indigo-600" />
              </div>
            </div>

            {/* Start button */}
            <button
              onClick={() => pipelineMutation.mutate()}
              disabled={pipelineMutation.isPending}
              className="w-full flex items-center justify-center gap-2 py-3 rounded-xl text-white font-semibold"
              style={{ background: 'linear-gradient(135deg, #6366f1, #8b5cf6)' }}
            >
              {pipelineMutation.isPending
                ? <><Loader2 className="w-5 h-5 animate-spin" /> Pokretanje...</>
                : <><Zap className="w-5 h-5" /> Pokreni Auto Pipeline</>
              }
            </button>
          </div>
        ) : (
          /* After start — status with progress */
          <div className="p-6 space-y-5">
            {/* Progress indicator */}
            {progressData && (() => {
              const data = (progressData as any).data
              const progressPct = data.progress_percentage || 0
              const phase = data.phase_label || 'Obrada u toku...'
              const translated = data.translated_chunks || 0
              const total = data.total_chunks || 0
              
              return (
                <div className="space-y-4">
                  <div className="text-center space-y-2">
                    <div className="w-16 h-16 rounded-2xl mx-auto flex items-center justify-center relative">
                      <div className="absolute inset-0 rounded-2xl border-4 border-indigo-100"></div>
                      <Loader2 className="w-8 h-8 text-indigo-600 animate-spin" />
                    </div>
                    <div>
                      <h3 className="font-bold text-gray-900">{phase}</h3>
                      <p className="text-gray-500 text-sm mt-1">
                        {progressPct}% završeno
                      </p>
                    </div>
                  </div>
                  
                  {/* Progress bar */}
                  <div className="bg-gray-100 rounded-full h-2 overflow-hidden">
                    <div 
                      className="h-full bg-gradient-to-r from-indigo-500 to-violet-500 transition-all duration-500"
                      style={{ width: `${progressPct}%` }}
                    />
                  </div>
                  
                  {/* Details */}
                  {(translated > 0 || total > 0) && (
                    <div className="bg-gray-50 rounded-xl p-3 text-sm text-gray-600 flex items-center justify-center gap-2">
                      <Activity className="w-4 h-4" />
                      <span>Prevedeno: {translated} / {total} odlomaka</span>
                    </div>
                  )}
                  
                  {/* Current phase details */}
                  {data.status === 'translating' && (
                    <div className="bg-violet-50 rounded-xl p-3 text-sm text-violet-700">
                      Prevod u toku...
                    </div>
                  )}
                  
                  {data.status === 'processing' && (
                    <div className="bg-blue-50 rounded-xl p-3 text-sm text-blue-700">
                      Obrada dokumenta u toku...
                    </div>
                  )}
                  
                  {data.status === 'completed' && (
                    <div className="text-center space-y-3">
                      <div className="w-16 h-16 rounded-2xl mx-auto flex items-center justify-center"
                        style={{ background: 'linear-gradient(135deg, #d1fae5, #a7f3d0)' }}>
                        <CheckCircle className="w-8 h-8 text-green-600" />
                      </div>
                      <div>
                        <h3 className="font-bold text-gray-900">Obrada završena!</h3>
                        <p className="text-gray-500 text-sm mt-1">
                          Sve je spremno.
                        </p>
                      </div>
                    </div>
                  )}
                </div>
              )
            })()}

            {!progressData && started && (
              <div className="text-center space-y-3">
                <div className="w-16 h-16 rounded-2xl mx-auto flex items-center justify-center"
                  style={{ background: 'linear-gradient(135deg, #d1fae5, #a7f3d0)' }}>
                  <CheckCircle className="w-8 h-8 text-green-600" />
                </div>
                <div>
                  <h3 className="font-bold text-gray-900">Pipeline je pokrenut!</h3>
                  <p className="text-gray-500 text-sm mt-1">
                    Obrada tece u pozadini. Kviz će biti spreman za nekoliko minuta.
                  </p>
                </div>
              </div>
            )}

            {taskResult && (
              <div className="bg-gray-50 rounded-xl p-4 space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">AI za prevod:</span>
                  <span className="font-medium text-gray-700">{taskResult.providers?.translation || 'auto'}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">AI za kviz:</span>
                  <span className="font-medium text-gray-700">{taskResult.providers?.quiz || 'auto'}</span>
                </div>
              </div>
            )}

            <div className="flex gap-3">
              <button onClick={onClose}
                className="flex-1 py-2.5 rounded-xl border border-gray-200 text-sm font-medium text-gray-600 hover:bg-gray-50">
                Zatvori
              </button>
              <a href="/quizzes"
                className="flex-1 py-2.5 rounded-xl text-white text-sm font-semibold text-center"
                style={{ background: 'linear-gradient(135deg, #6366f1, #8b5cf6)' }}>
                Idi na Kvizove
              </a>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
