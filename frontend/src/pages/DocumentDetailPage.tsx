/**
 * ================================================================================
 * Petar II Petrović-Njegoš
 * "Blago tome ko dovijek živi, imao se rašta i roditi"
 * ================================================================================
 * 
 * AI Learning System
 * DocumentDetailPage.tsx
 * Verzija: 1.0.0
 * Autor: Branko Suznjevic
 * Datum: 2026
 * ================================================================================
 */

import { useParams, Link, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useState, useEffect, useRef } from 'react'
import { documentsApi } from '@/services/api'
import { 
  BookOpen, 
  Languages, 
  FileText,
  Clock,
  Calendar,
  Loader2,
  ChevronRight,
  CheckCircle,
  Circle,
  Hash,
  Zap,
  Download,
  AlertTriangle,
  AlertCircle,
  Activity,
  Trash2
} from 'lucide-react'
import clsx from 'clsx'
import PipelineModal from '@/components/PipelineModal'
import toast from 'react-hot-toast'

export default function DocumentDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [showPipeline, setShowPipeline] = useState(false)
  const [downloadingPdf, setDownloadingPdf] = useState(false)
  const docId = id || ''

  const deleteMutation = useMutation({
    mutationFn: () => documentsApi.delete(docId),
    onSuccess: () => {
      toast.success('Dokument obrisan')
      queryClient.invalidateQueries({ queryKey: ['documents'] })
      navigate('/documents')
    },
    onError: () => toast.error('Greška pri brisanju dokumenta'),
  })

  const handleExportPdf = async () => {
    if (!docId) return
    setDownloadingPdf(true)
    try {
      const res = await documentsApi.exportPdf(docId)
      const url = window.URL.createObjectURL(new Blob([res.data], { type: 'application/pdf' }))
      const a = document.createElement('a')
      a.href = url
      a.download = `${doc?.title ?? 'dokument'}_prevod.pdf`
      a.click()
      window.URL.revokeObjectURL(url)
    } catch {
      toast.error('Greška pri eksportu PDF-a')
    } finally {
      setDownloadingPdf(false)
    }
  }

  const activeStatuses = ['pending', 'processing', 'translating']

  // Track seconds since last worker activity
  const [secondsSinceActivity, setSecondsSinceActivity] = useState<number | null>(null)
  const activityTimerRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const { data: docQueryData, isLoading } = useQuery({
    queryKey: ['document', docId],
    queryFn: () => documentsApi.get(docId),
    enabled: !!docId,
    // Auto-refresh every 3s while document is being processed
    refetchInterval: (query) => {
      const status = (query.state.data as any)?.data?.status
      return activeStatuses.includes(status) ? 3000 : false
    },
  })

  const { data: progressData } = useQuery({
    queryKey: ['document-progress', docId],
    queryFn: () => documentsApi.getProgress(docId),
    enabled: !!docId,
    refetchInterval: (query) => {
      const status = (query.state.data as any)?.data?.status
      return activeStatuses.includes(status) ? 2000 : false
    },
  })
  const progress = (progressData as any)?.data

  const { data: quizAvailabilityData } = useQuery({
    queryKey: ['document-quiz-availability', docId],
    queryFn: () => documentsApi.getQuizAvailability(docId),
    enabled: !!docId && docQueryData?.data?.status === 'completed',
    refetchInterval: 30000,
  })
  const quizAvailability = (quizAvailabilityData as any)?.data

  // Update "seconds since last activity" counter every second
  useEffect(() => {
    if (!progress?.last_activity_at) {
      setSecondsSinceActivity(null)
      return
    }
    const update = () => {
      const diff = Math.floor((Date.now() - new Date(progress.last_activity_at).getTime()) / 1000)
      setSecondsSinceActivity(diff)
    }
    update()
    activityTimerRef.current = setInterval(update, 1000)
    return () => { if (activityTimerRef.current) clearInterval(activityTimerRef.current) }
  }, [progress?.last_activity_at])

  const [chunkPage, setChunkPage] = useState(0)
  const CHUNKS_PER_PAGE = 20

  const { data: chunks } = useQuery({
    queryKey: ['document-chunks', docId, chunkPage],
    queryFn: () => documentsApi.getChunks(docId, chunkPage * CHUNKS_PER_PAGE, CHUNKS_PER_PAGE),
    enabled: !!docId && docQueryData?.data?.status !== 'pending',
  })

  const doc = docQueryData?.data

  const getStatusConfig = (status: string, translatedChunks: number, totalChunks: number) => {
    const configs: Record<string, { badge: string; strip: string; label: string }> = {
      pending:     { badge: 'badge-gray',    strip: 'from-gray-500 to-slate-600',     label: 'Na čekanju' },
      processing:  { badge: 'badge-primary', strip: 'from-indigo-500 to-blue-600',    label: 'Obrađuje se' },
      completed:   { badge: 'badge-success', strip: 'from-emerald-500 to-green-600',  label: totalChunks === 0 ? 'Bez odlomaka' : (translatedChunks === 0 ? 'Nije prevedeno' : 'Obrađeno') },
      translating: { badge: 'badge-primary', strip: 'from-violet-500 to-purple-600',  label: 'Prevodi se' },
      error:       { badge: 'badge-error',   strip: 'from-red-500 to-rose-600',       label: 'Greška' },
    }
    return configs[status] || configs['pending']
  }

  const getTranslationStatus = () => {
    if (!doc) return null
    const translated = doc.translated_chunks || 0
    const total = doc.total_chunks || 0
    if (total === 0) return null
    if (translated === 0 && doc.status === 'completed') {
      return { label: 'Nije prevedeno', color: 'text-orange-600 bg-orange-50' }
    }
    if (translated > 0 && translated < total) {
      return { label: `Delimično prevedeno (${translated}/${total})`, color: 'text-yellow-600 bg-yellow-50' }
    }
    if (translated === total && total > 0) {
      return { label: 'Prevedeno', color: 'text-green-600 bg-green-50' }
    }
    return null
  }

  const translationStatus = getTranslationStatus()

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="w-8 h-8 text-indigo-500 animate-spin" />
      </div>
    )
  }

  if (!doc) {
    return (
      <div className="text-center py-16">
        <div className="w-16 h-16 rounded-2xl bg-indigo-50 flex items-center justify-center mx-auto mb-4">
          <FileText className="w-8 h-8 text-indigo-400" />
        </div>
        <p className="text-gray-700 font-semibold mb-1">Dokument nije pronađen</p>
        <Link to="/documents" className="btn-primary mt-4">
          Nazad na dokumente
        </Link>
      </div>
    )
  }

  const cfg = getStatusConfig(doc.status, doc.translated_chunks || 0, doc.total_chunks || 0)
  const translatedCount = Array.isArray(chunks?.data) 
    ? chunks.data.filter((c: any) => c.translated_content).length 
    : 0

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Breadcrumb */}
      <nav className="flex items-center gap-2 text-sm text-gray-500">
        <Link to="/documents" className="hover:text-indigo-600 transition-colors font-medium">Dokumenti</Link>
        <ChevronRight className="w-4 h-4" />
        <span className="text-gray-900 font-semibold truncate max-w-xs">{doc.title}</span>
      </nav>

      {/* Hero banner */}
      <div className={clsx('rounded-3xl overflow-hidden bg-gradient-to-r relative', cfg.strip)}>
        <div className="absolute inset-0 opacity-10"
          style={{ backgroundImage: 'radial-gradient(circle at 20% 50%, white 1px, transparent 1px), radial-gradient(circle at 80% 20%, white 1px, transparent 1px)', backgroundSize: '40px 40px' }} />
        <div className="relative z-10 p-8">
          <div className="flex items-start justify-between gap-4 mb-5">
            <div className="flex items-center gap-4">
              <div className="w-14 h-14 rounded-2xl bg-white/20 backdrop-blur flex items-center justify-center">
                <BookOpen className="w-7 h-7 text-white" />
              </div>
              <div>
                <span className={clsx('badge bg-white/20 text-white backdrop-blur border-0 mb-2')}>
                  {cfg.label}
                </span>
                <h1 className="text-2xl font-extrabold text-white leading-tight">{doc.title}</h1>
                {doc.description && (
                  <p className="text-white/75 text-sm mt-1">{doc.description}</p>
                )}
              </div>
            </div>
          </div>

          {/* Stats row */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {[
              { icon: FileText, label: 'Strane', value: doc.total_pages },
              { icon: BookOpen, label: 'Odlomci', value: doc.total_chunks },
              { icon: Languages, label: 'Jezik', value: `${doc.source_language?.toUpperCase() || '?'} → ${doc.target_language?.toUpperCase() || 'SR'}` },
              { icon: Clock,    label: 'Status',  value: cfg.label },
            ].map((item, i) => (
              <div key={i} className="bg-white/15 backdrop-blur rounded-2xl px-4 py-3">
                <div className="flex items-center gap-1.5 mb-1">
                  <item.icon className="w-3.5 h-3.5 text-white/70" />
                  <span className="text-xs text-white/70">{item.label}</span>
                </div>
                <p className="text-white font-bold text-sm">{item.value}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Processing progress card - always show for all statuses */}
      {(doc.status === 'processing' || doc.status === 'pending' || doc.status === 'translating' || doc.status === 'completed') && (
        <div className={clsx(
          'rounded-2xl border overflow-hidden',
          doc.status === 'translating' ? 'border-violet-200 bg-violet-50' : 'border-indigo-200 bg-indigo-50'
        )}>
          {/* Header */}
          <div className="flex items-center gap-3 px-5 pt-4 pb-3">
            <div className={clsx(
              'w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0',
              doc.status === 'translating' ? 'bg-violet-100' : 'bg-indigo-100'
            )}>
              <Loader2 className={clsx(
                'w-5 h-5 animate-spin',
                doc.status === 'translating' ? 'text-violet-600' : 'text-indigo-600'
              )} />
            </div>
            <div className="flex-1">
              <p className={clsx(
                'font-semibold text-sm',
                doc.status === 'translating' ? 'text-violet-900' : 'text-indigo-900'
              )}>
                {doc.status === 'completed' ? 'Obrada završena' : (
                  progress?.phase_label || (
                    doc.status === 'pending' ? 'Dokument čeka na obradu...' :
                    doc.status === 'processing' ? 'Pokretanje procesora PDF-a...' :
                    'Pokretanje prevodioca...'
                  )
                )}
              </p>
              <p className={clsx('text-xs flex items-center gap-1.5', doc.status === 'translating' ? 'text-violet-500' : 'text-indigo-400')}>
                {secondsSinceActivity !== null ? (
                  secondsSinceActivity > 30 ? (
                    <span className="flex items-center gap-1 text-amber-600 font-medium">
                      <AlertTriangle className="w-3 h-3" />
                      Nema aktivnosti već {secondsSinceActivity}s — worker možda nije pokrenut
                    </span>
                  ) : (
                    <span className="flex items-center gap-1 text-emerald-600">
                      <Activity className="w-3 h-3" />
                      Aktivan · pre {secondsSinceActivity}s
                    </span>
                  )
                ) : (
                  <span>Čekanje na radnika...</span>
                )}
                {progress?.elapsed_seconds ? ` · ${Math.floor(progress.elapsed_seconds / 60)}m ${progress.elapsed_seconds % 60}s` : ''}
              </p>
            </div>
            <span className={clsx(
              'text-2xl font-extrabold tabular-nums',
              doc.status === 'translating' ? 'text-violet-700' : 
              (doc.status === 'completed' && (doc.translated_chunks || 0) === 0) ? 'text-orange-700' : 'text-indigo-700'
            )}>
              {doc.status === 'completed' 
                ? ((doc.translated_chunks || 0) === 0 && (doc.total_chunks || 0) > 0 ? '0' : '100')
                : (progress?.progress_percentage ?? 0)}%
            </span>
          </div>

          {/* Progress bar */}
          <div className="px-5 pb-2">
            <div className="h-2.5 bg-white/60 rounded-full overflow-hidden">
              <div
                className={clsx(
                  'h-full rounded-full transition-all duration-700',
                  doc.status === 'translating'
                    ? 'bg-gradient-to-r from-violet-500 to-purple-500'
                    : doc.status === 'completed' && (doc.translated_chunks || 0) === 0
                      ? 'bg-gradient-to-r from-orange-500 to-red-500'
                      : 'bg-gradient-to-r from-indigo-500 to-blue-500'
                )}
                style={{ width: `${doc.status === 'completed' 
                  ? ((doc.translated_chunks || 0) === 0 && (doc.total_chunks || 0) > 0 ? 0 : 100)
                  : (progress?.progress_percentage ?? (doc.status === 'pending' ? 0 : 10))}%` }}
              />
            </div>
          </div>

          {/* Stats row - always show for all statuses */}
          {progress && (
            <div className="grid grid-cols-3 gap-px bg-white/30 border-t border-white/40 mt-1">
              {(doc.status === 'processing' ? [
                { label: 'Strana obrađeno', value: progress.pages_done > 0 ? `${progress.pages_done} / ${progress.pages_total || '?'}` : '...' },
                { label: 'Odlomaka kreirano', value: progress.chunks_so_far > 0 ? progress.chunks_so_far : '...' },
                { label: 'Ukupno strana', value: progress.pages_total || doc.total_pages || '...' },
              ] : doc.status === 'completed' ? [
                { label: 'Odlomaka ukupno', value: progress.total_chunks },
                { label: 'Prevedeno', value: progress.translated_chunks },
                { label: 'Neprevedeno', value: progress.total_chunks - progress.translated_chunks },
              ] : [
                { label: 'Prevedeno', value: `${progress.translated_chunks} / ${progress.total_chunks}` },
                { label: 'Odlomaka ukupno', value: progress.total_chunks },
                { label: 'Neprevedeno', value: progress.total_chunks - progress.translated_chunks },
              ]).map((s, i) => (
                <div key={i} className="px-4 py-2.5 bg-white/40">
                  <p className="text-xs text-gray-500">{s.label}</p>
                  <p className="text-sm font-bold text-gray-800">{s.value}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Quiz availability status - show when document is completed */}
      {docQueryData?.data?.status === 'completed' && quizAvailability && (
        <div className="card bg-gradient-to-r from-amber-50 to-orange-50 border-amber-200">
          <div className="px-5 py-3 flex items-center justify-between border-b border-amber-100">
            <div className="flex items-center gap-2">
              <Activity className="w-4 h-4 text-amber-600" />
              <span className="font-semibold text-amber-900">Kviz pitanja</span>
            </div>
            {quizAvailability.available === 0 && quizAvailability.total > 0 ? (
              <span className="text-xs font-medium text-red-600 bg-red-50 px-2 py-1 rounded">
                Sva pitanja su iskorišćena u kvizovima
              </span>
            ) : quizAvailability.total === 0 ? (
              <span className="text-xs font-medium text-gray-500 bg-gray-100 px-2 py-1 rounded">
                Nema generisanih pitanja
              </span>
            ) : null}
          </div>
          {quizAvailability.total > 0 && (
            <>
              <div className="px-5 py-2">
                <div className="h-2.5 bg-amber-100 rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-amber-500 to-orange-500 transition-all duration-700"
                    style={{ width: `${((quizAvailability.total - quizAvailability.available) / quizAvailability.total) * 100}%` }}
                  />
                </div>
              </div>
              <div className="grid grid-cols-3 gap-px bg-amber-100/50 border-t border-amber-100">
                <div className="px-4 py-2.5 bg-white/60">
                  <p className="text-xs text-gray-500">Ukupno pitanja</p>
                  <p className="text-sm font-bold text-gray-800">{quizAvailability.total}</p>
                </div>
                <div className="px-4 py-2.5 bg-white/60">
                  <p className="text-xs text-gray-500">Iskorišćeno</p>
                  <p className="text-sm font-bold text-amber-700">{quizAvailability.used}</p>
                </div>
                <div className="px-4 py-2.5 bg-white/60">
                  <p className="text-xs text-gray-500">Dostupno</p>
                  <p className="text-sm font-bold text-green-700">{quizAvailability.available}</p>
                </div>
              </div>
            </>
          )}
        </div>
      )}

      {/* Action buttons */}
      <div className="flex flex-wrap gap-3">
        {doc.status === 'error' && (
          <div className="w-full bg-red-50 border border-red-200 rounded-lg p-4 mb-2">
            <div className="flex items-center gap-2 text-red-700 font-medium mb-2">
              <AlertTriangle className="w-5 h-5" />
              Greška pri obradi dokumenta
            </div>
            <p className="text-red-600 text-sm mb-3">
              {doc.metadata?.processing_error || doc.metadata?.translation?.errors?.[0] || doc.description || 'Nepoznata greška'}
            </p>
            {(doc.metadata?.processing_error || doc.metadata?.translation?.errors?.[0]) && (
              <p className="text-gray-600 text-xs">
                Tehnički detalji: {doc.metadata.processing_error || doc.metadata.translation?.errors?.[0]}
              </p>
            )}
          </div>
        )}
        {doc.status === 'error' && (
          <button
            onClick={() => {
              if (confirm('Da li želite da obrisete ovaj dokument?')) {
                deleteMutation.mutate()
              }
            }}
            disabled={deleteMutation.isPending}
            className="btn-primary bg-red-600 hover:bg-red-700 disabled:opacity-50"
          >
            <Trash2 className="w-4 h-4" />
            {deleteMutation.isPending ? 'Brisanje...' : 'Obriši dokument'}
          </button>
        )}
        {doc.status !== 'error' && (
          <>
            <Link
              to={`/review/${docId}`}
              className={clsx('btn-primary', doc.status !== 'completed' && 'opacity-50 pointer-events-none')}
            >
              <Languages className="w-4 h-4" />
              Pregledaj prevode
            </Link>
            <button
              onClick={() => setShowPipeline(true)}
              disabled={doc.status !== 'completed'}
              className={clsx('btn-primary bg-violet-600 hover:bg-violet-700', doc.status !== 'completed' && 'opacity-50 pointer-events-none')}
            >
              <Zap className="w-4 h-4" />
              Auto Pipeline
            </button>
            <button
              onClick={handleExportPdf}
              disabled={doc.status !== 'completed' || downloadingPdf}
              className={clsx('btn-primary bg-emerald-600 hover:bg-emerald-700', doc.status !== 'completed' && 'opacity-50 pointer-events-none')}
            >
              {downloadingPdf ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
              Preuzmi PDF
            </button>
          </>
        )}
        <div className="flex items-center gap-2 text-sm text-gray-500 ml-auto">
          <Calendar className="w-4 h-4" />
          {new Date(doc.created_at).toLocaleString('sr-RS', {
            year: 'numeric', month: 'long', day: 'numeric',
            hour: '2-digit', minute: '2-digit',
          })}
        </div>
      </div>

      {/* Chunks section */}
      {doc.status !== 'pending' && (
        <div className="card overflow-hidden">
          {translationStatus && (
            <div className={clsx('px-6 py-3 text-sm flex items-center gap-2', translationStatus.color)}>
              <AlertCircle className="w-4 h-4" />
              {translationStatus.label}
              {translationStatus.label.includes('Nije prevedeno') && (
                <button
                  onClick={() => setShowPipeline(true)}
                  className="ml-auto text-xs font-medium underline hover:no-underline"
                >
                  Pokreni prevod
                </button>
              )}
            </div>
          )}
          <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
            <div>
              <h2 className="text-base font-bold text-gray-900">Odlomci (lekcije)</h2>
              <p className="text-xs text-gray-500 mt-0.5">
                {translatedCount} od {doc.total_chunks} prevedeno
              </p>
            </div>
            {doc.total_chunks > 0 && (
              <div className="flex items-center gap-2">
                <div className="w-24 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-indigo-500 to-violet-500 rounded-full"
                    style={{ width: `${doc.total_chunks > 0 ? (translatedCount / doc.total_chunks) * 100 : 0}%` }}
                  />
                </div>
                <span className="text-xs font-semibold text-gray-600">
                  {doc.total_chunks > 0 ? Math.round((translatedCount / doc.total_chunks) * 100) : 0}%
                </span>
              </div>
            )}
          </div>

          {Array.isArray(chunks?.data) && chunks.data.length > 0 ? (
            <div className="divide-y divide-gray-100">
              {chunks.data.map((chunk: any, idx: number) => (
                <div key={chunk.id} className="px-6 py-4 hover:bg-gray-50/80 transition-colors group">
                  <div className="flex items-start gap-3">
                    {/* Number + status */}
                    <div className="flex-shrink-0 flex flex-col items-center gap-1.5 pt-0.5">
                      <div className="w-7 h-7 rounded-lg bg-indigo-50 flex items-center justify-center">
                        <span className="text-xs font-bold text-indigo-600">{chunkPage * CHUNKS_PER_PAGE + idx + 1}</span>
                      </div>
                      {chunk.translated_content ? (
                        <CheckCircle className="w-3.5 h-3.5 text-emerald-500" />
                      ) : (
                        <Circle className="w-3.5 h-3.5 text-gray-300" />
                      )}
                    </div>

                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1.5">
                        {chunk.parent_heading && (
                          <div className="flex items-center gap-1 text-xs text-indigo-600 font-medium bg-indigo-50 px-2 py-0.5 rounded-lg">
                            <Hash className="w-3 h-3" />
                            {chunk.parent_heading}
                          </div>
                        )}
                        <span className={clsx(
                          'text-xs font-semibold px-2 py-0.5 rounded-lg',
                          chunk.translated_content ? 'bg-emerald-50 text-emerald-600' : 'bg-gray-100 text-gray-400'
                        )}>
                          {chunk.translated_content ? '✓ Prevedeno' : '⏳ Na čekanju'}
                        </span>
                      </div>
                      
                      <p className="text-gray-700 text-sm line-clamp-2 leading-relaxed">
                        {chunk.content}
                      </p>

                      {chunk.translated_content && (
                        <div className="mt-2 pt-2 border-t border-dashed border-gray-100">
                          <p className="text-gray-500 text-sm line-clamp-2 leading-relaxed italic">
                            {chunk.translated_content}
                          </p>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}

              {/* Pagination */}
              {doc && doc.total_chunks > CHUNKS_PER_PAGE && (
                <div className="px-6 py-4 border-t border-gray-100 bg-gray-50/50 flex items-center justify-between">
                  <button
                    onClick={() => setChunkPage(p => Math.max(0, p - 1))}
                    disabled={chunkPage === 0}
                    className="btn btn-secondary btn-sm disabled:opacity-50"
                  >
                    Prethodna
                  </button>
                  <span className="text-sm text-gray-500">
                    Stranica {chunkPage + 1} od {Math.ceil(doc.total_chunks / CHUNKS_PER_PAGE)}
                  </span>
                  <button
                    onClick={() => setChunkPage(p => p + 1)}
                    disabled={(chunkPage + 1) * CHUNKS_PER_PAGE >= doc.total_chunks}
                    className="btn btn-secondary btn-sm disabled:opacity-50"
                  >
                    Sledeća
                  </button>
                </div>
              )}
            </div>
          ) : (
            <div className="p-14 text-center">
              {doc.status === 'completed' && doc.total_chunks > 0 ? (
                <>
                  <Loader2 className="w-8 h-8 text-indigo-400 animate-spin mx-auto mb-3" />
                  <p className="text-gray-500 text-sm">Učitavanje odlomaka...</p>
                </>
              ) : doc.status === 'completed' && doc.total_chunks === 0 ? (
                <>
                  <AlertCircle className="w-8 h-8 text-orange-400 mx-auto mb-3" />
                  <p className="text-orange-600 text-sm font-medium">Nema odlomaka za prikaz</p>
                  <p className="text-gray-400 text-xs mt-1">Obrada dokumenta nije uspela da kreira odlomke</p>
                </>
              ) : (
                <>
                  <Loader2 className="w-8 h-8 text-indigo-400 animate-spin mx-auto mb-3" />
                  <p className="text-gray-500 text-sm">Odlomci se obrađuju...</p>
                </>
              )}
            </div>
          )}

          {doc.status === 'completed' && (
            <div className="px-6 py-4 border-t border-gray-100 bg-gray-50/50">
              <Link
                to={`/review/${docId}`}
                className="btn-primary w-full justify-center"
              >
                <Languages className="w-4 h-4" />
                Pregledaj i uredi sve prevode
              </Link>
            </div>
          )}
        </div>
      )}
      {showPipeline && doc && (
        <PipelineModal
          documentId={doc.id}
          documentTitle={doc.title}
          onClose={() => setShowPipeline(false)}
        />
      )}
    </div>
  )
}
