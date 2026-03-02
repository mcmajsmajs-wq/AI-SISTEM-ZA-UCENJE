import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { quizzesApi, documentsApi } from '@/services/api'
import { Quiz, Document } from '@/types'
import { BookOpen, Plus, Trash2, Play, Clock, CheckCircle, AlertCircle, Loader2 } from 'lucide-react'
import toast from 'react-hot-toast'

export default function QuizzesPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [selectedDocId, setSelectedDocId] = useState<string>('')
  const [numQuestions, setNumQuestions] = useState(0)
  const [showCreateForm, setShowCreateForm] = useState(false)

  const { data: quizzesData, isLoading } = useQuery({
    queryKey: ['quizzes'],
    queryFn: () => quizzesApi.list(0, 50),
    refetchInterval: (data) => {
      const quizzes: Quiz[] = (data as any)?.data?.items ?? []
      return quizzes.some((q) => q.status === 'generating') ? 3000 : false
    },
  })

  const { data: docsData } = useQuery({
    queryKey: ['documents', 'completed'],
    queryFn: () => documentsApi.list(0, 100, 'completed'),
  })

  const createMutation = useMutation({
    mutationFn: () => quizzesApi.create(selectedDocId, numQuestions),
    onSuccess: () => {
      toast.success('Generisanje kviza pokrenuto!')
      queryClient.invalidateQueries({ queryKey: ['quizzes'] })
      setShowCreateForm(false)
      setSelectedDocId('')
    },
    onError: () => toast.error('Greška pri kreiranju kviza'),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => quizzesApi.delete(id),
    onSuccess: () => {
      toast.success('Kviz obrisan')
      queryClient.invalidateQueries({ queryKey: ['quizzes'] })
    },
    onError: () => toast.error('Greška pri brisanju'),
  })

  const quizzes: Quiz[] = (quizzesData as any)?.data?.items ?? []
  const documents: Document[] = (docsData as any)?.data?.items ?? []

  const statusIcon = (status: string) => {
    if (status === 'generating') return <Loader2 className="w-4 h-4 animate-spin text-yellow-500" />
    if (status === 'ready') return <CheckCircle className="w-4 h-4 text-green-500" />
    return <AlertCircle className="w-4 h-4 text-red-500" />
  }

  const statusLabel = (status: string) => {
    if (status === 'generating') return 'Generisanje...'
    if (status === 'ready') return 'Spreman'
    return 'Greška'
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Kvizovi</h1>
          <p className="text-gray-500 text-sm mt-0.5">Testiraj znanje iz tvojih dokumenata</p>
        </div>
        <button
          onClick={() => setShowCreateForm(!showCreateForm)}
          className="flex items-center gap-2 px-4 py-2 rounded-xl text-white text-sm font-semibold transition-all"
          style={{ background: 'linear-gradient(135deg, #6366f1, #8b5cf6)' }}
        >
          <Plus className="w-4 h-4" />
          Novi kviz
        </button>
      </div>

      {/* Create form */}
      {showCreateForm && (
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 space-y-4">
          <h2 className="font-semibold text-gray-800">Generiši novi kviz</h2>
          <div>
            <label className="text-sm font-medium text-gray-700 mb-1 block">Dokument</label>
            <select
              value={selectedDocId}
              onChange={(e) => setSelectedDocId(e.target.value)}
              className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300"
            >
              <option value="">— Izaberi dokument —</option>
              {documents.map((d) => (
                <option key={d.id} value={d.id}>{d.title}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="text-sm font-medium text-gray-700 mb-1 block">
              Broj pitanja: <span className="text-indigo-600 font-bold">{numQuestions === 0 ? 'Auto (na osnovu dokumenta)' : numQuestions}</span>
            </label>
            <input
              type="range" min={0} max={50} value={numQuestions}
              onChange={(e) => setNumQuestions(Number(e.target.value))}
              className="w-full accent-indigo-600"
            />
            <div className="flex justify-between text-xs text-gray-400 mt-0.5">
              <span>Auto</span><span>50</span>
            </div>
          </div>
          <div className="flex gap-3">
            <button
              onClick={() => createMutation.mutate()}
              disabled={!selectedDocId || createMutation.isPending}
              className="flex items-center gap-2 px-5 py-2 rounded-xl text-white text-sm font-semibold disabled:opacity-50"
              style={{ background: 'linear-gradient(135deg, #6366f1, #8b5cf6)' }}
            >
              {createMutation.isPending && <Loader2 className="w-4 h-4 animate-spin" />}
              Generiši
            </button>
            <button
              onClick={() => setShowCreateForm(false)}
              className="px-5 py-2 rounded-xl border border-gray-200 text-sm font-medium text-gray-600 hover:bg-gray-50"
            >
              Otkaži
            </button>
          </div>
        </div>
      )}

      {/* Quiz list */}
      {isLoading ? (
        <div className="flex justify-center py-16">
          <Loader2 className="w-8 h-8 animate-spin text-indigo-400" />
        </div>
      ) : quizzes.length === 0 ? (
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-16 text-center">
          <BookOpen className="w-12 h-12 text-gray-200 mx-auto mb-4" />
          <p className="text-gray-500 font-medium">Nema kvizova</p>
          <p className="text-gray-400 text-sm mt-1">Klikni "Novi kviz" da počneš</p>
        </div>
      ) : (
        <div className="space-y-3">
          {quizzes.map((quiz) => (
            <div
              key={quiz.id}
              className="bg-white rounded-2xl shadow-sm border border-gray-100 p-5 flex items-center gap-4 hover:shadow-md transition-shadow"
            >
              <div className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0"
                style={{ background: 'linear-gradient(135deg, #e0e7ff, #ede9fe)' }}>
                <BookOpen className="w-5 h-5 text-indigo-600" />
              </div>

              <div className="flex-1 min-w-0">
                <h3 className="font-semibold text-gray-900 truncate">{quiz.title}</h3>
                <div className="flex items-center gap-3 mt-1">
                  <span className="flex items-center gap-1 text-xs text-gray-500">
                    {statusIcon(quiz.status)}
                    {statusLabel(quiz.status)}
                  </span>
                  <span className="text-xs text-gray-400">·</span>
                  <span className="text-xs text-gray-500">{quiz.total_questions} pitanja</span>
                  {quiz.time_limit && (
                    <>
                      <span className="text-xs text-gray-400">·</span>
                      <span className="flex items-center gap-1 text-xs text-gray-500">
                        <Clock className="w-3 h-3" />
                        {Math.floor(quiz.time_limit / 60)} min
                      </span>
                    </>
                  )}
                </div>
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={() => navigate(`/quizzes/${quiz.id}/results`)}
                  className="px-3 py-1.5 rounded-lg text-xs font-medium text-gray-600 border border-gray-200 hover:bg-gray-50"
                >
                  Rezultati
                </button>
                <button
                  disabled={quiz.status !== 'ready'}
                  onClick={() => navigate(`/quizzes/${quiz.id}/play`)}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold text-white disabled:opacity-40"
                  style={{ background: 'linear-gradient(135deg, #6366f1, #8b5cf6)' }}
                >
                  <Play className="w-3 h-3" />
                  Igraj
                </button>
                <button
                  onClick={() => deleteMutation.mutate(quiz.id)}
                  className="p-1.5 rounded-lg text-gray-400 hover:text-red-500 hover:bg-red-50 transition-colors"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
