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
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useState, useEffect, useRef } from 'react'
import { documentsApi } from '@/services/api'
import {
  useDocumentDetail,
  useDocumentProgress,
  useDocumentChunks,
  useDocumentQuizAvailability,
  useDeleteDocument,
  useStopTranslation,
} from '@/hooks/useDocuments'
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
  Trash2,
  RotateCcw,
  Square,
  X,
  FileDown
} from 'lucide-react'
import clsx from 'clsx'
import PipelineModal from '@/components/PipelineModal'
import toast from 'react-hot-toast'
import { useExportProgressStore } from '@/stores/exportProgressStore'

export default function DocumentDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [showPipeline, setShowPipeline] = useState(false)
  const [downloadingPdf, setDownloadingPdf] = useState(false)
  const [downloadingDocx, setDownloadingDocx] = useState(false)
  const [downloadingXlsx, setDownloadingXlsx] = useState(false)
  const [downloadingPptx, setDownloadingPptx] = useState(false)
  const [pdfTaskId, setPdfTaskId] = useState<string | null>(null)
  const [docxTaskId, setDocxTaskId] = useState<string | null>(null)
  
  // Export progress states
  const [exportProgress, setExportProgress] = useState<{current: number, total: number, status: string} | null>(null)
  const [showExportModal, setShowExportModal] = useState(false)
  const [exportType, setExportType] = useState<'pdf' | 'docx' | 'xlsx' | 'pptx' | null>(null)
  
  // Export status persisted for page navigation
  const [pdfExportStatus, setPdfExportStatus] = useState<'idle' | 'processing' | 'completed' | 'failed'>('idle')
  const [docxExportStatus, setDocxExportStatus] = useState<'idle' | 'processing' | 'completed' | 'failed'>('idle')
  
  const docId = id || ''

  // Sync SSE export progress from store
  const exportStoreExports = useExportProgressStore((s) => s.exports)

  useEffect(() => {
    const matchedExport = Object.values(exportStoreExports).find(
      (e) => e.documentId === docId && e.format === exportType
    )
    if (matchedExport && matchedExport.status === 'progress') {
      setExportProgress({
        current: matchedExport.current,
        total: matchedExport.total,
        status: matchedExport.message || 'Procesiranje...',
      })
    }
  }, [exportStoreExports, docId, exportType])

  // Load persisted export status on mount
  useEffect(() => {
    if (docId) {
      const saved = localStorage.getItem(`export_status_${docId}`)
      if (saved) {
        try {
          const parsed = JSON.parse(saved)
          if (parsed.pdf) setPdfExportStatus(parsed.pdf as any)
          if (parsed.docx) setDocxExportStatus(parsed.docx as any)
        } catch (e) {}
      }
    }
  }, [docId])
  
  // Save export status to localStorage
  const saveExportStatus = (pdf: string, docx: string) => {
    if (docId) {
      localStorage.setItem(`export_status_${docId}`, JSON.stringify({ pdf, docx }))
    }
  }

  const deleteMutation = useDeleteDocument()

  const translateMutation = useMutation({
    mutationFn: async ({ docId }: { docId: string }) => {
      // Validiraj SVE provajdere prvo
      try {
        const validation = await documentsApi.validateTranslationProvider()
        const validationData = validation.data
        
        let hasValid = false
        let errorMessages: string[] = []
        
        if (validationData.providers) {
          for (const p of validationData.providers) {
            if (p.is_ok) {
              hasValid = true
              break
            }
            if (p.user_message) {
              errorMessages.push(p.user_message)
            }
          }
          
          if (!hasValid) {
            throw new Error(errorMessages.join('; ') || 'Nijedan prevod provider nije dostupan')
          }
        }
      } catch (validationError: any) {
        const message = validationError.response?.data?.user_message || 
                       validationError.message || 
                       'Neuspešna validacija'
        throw new Error(message)
      }
      
      // Pusti backend da izabere najbolji
      return documentsApi.translate(docId, undefined)
    },
    onSuccess: () => {
      toast.success('Prevođenje pokrenuto')
      queryClient.invalidateQueries({ queryKey: ['document', docId] })
      queryClient.invalidateQueries({ queryKey: ['document-progress', docId] })
    },
    onError: (error: any) => {
      const message = error.response?.data?.user_message || error.message || 'Greška pri pokretanju prevođenja'
      toast.error(message)
    },
  })

  const stopMutation = useStopTranslation()

  const handleTranslate = () => {
    translateMutation.mutate({ docId })
  }

  const handleExportPdf = async () => {
    console.log('[DEBUG] handleExportPdf called')
    console.log('[DEBUG] docId:', docId)
    console.log('[DEBUG] doc?.status:', doc?.status)
    console.log('[DEBUG] downloadingPdf before:', downloadingPdf)
    console.log('[DEBUG] document title:', doc?.title)
    
    if (!docId) {
      console.log('[DEBUG] No docId, returning')
      return
    }
    
    console.log('[DEBUG] Setting state...')
    setDownloadingPdf(true)
    setPdfTaskId(null)
    setExportType('pdf')
    setExportProgress({ current: 0, total: 100, status: 'Priprema...' })
    setShowExportModal(true)
    setPdfExportStatus('processing')
    saveExportStatus('processing', docxExportStatus)
    console.log('[DEBUG] State set, calling API...')
    
    try {
      console.log('[DEBUG] Calling documentsApi.exportPdf')
      const res = await documentsApi.exportPdf(docId)
      console.log('[DEBUG] exportPdf response:', res.data)
      const taskId = res.data.task_id
      setPdfTaskId(taskId)
      
      const poll = async () => {
        console.log('[DEBUG] Polling PDF status...')
        const statusRes = await documentsApi.exportPdfStatus(taskId)
        const status = statusRes.data.status
        console.log('[DEBUG] Task status:', status)
        console.log('[DEBUG] Full response:', statusRes.data)
        
        // Celery PROGRESS state has result field with progress info
        const info = statusRes.data.result || {}
        console.log('[DEBUG] Progress info:', info)
        
        // Update progress
        if (info.current !== undefined) {
          const progress = {
            current: info.current,
            total: info.total || 100,
            status: info.status || 'Procesiranje...'
          }
          console.log('[DEBUG] Setting export progress:', progress)
          setExportProgress(progress)
        }
        
        if (status === 'SUCCESS') {
          setExportProgress({ current: 100, total: 100, status: 'Preuzimanje...' })
          const downloadRes = await documentsApi.exportPdfDownload(docId, taskId)
          const url = window.URL.createObjectURL(new Blob([downloadRes.data], { type: 'application/pdf' }))
          const a = document.createElement('a')
          a.href = url
          a.download = `${doc?.title ?? 'dokument'}_prevod.pdf`
          a.click()
          window.URL.revokeObjectURL(url)
          toast.success('PDF uspešno generisan')
          setShowExportModal(false)
          setPdfExportStatus('completed')
          saveExportStatus('completed', docxExportStatus)
        } else if (status === 'FAILURE') {
          throw new Error(statusRes.data.error || 'PDF generisanje nije uspelo')
        } else if (status === 'PROGRESS') {
          setTimeout(poll, 3000)
        } else {
          setTimeout(poll, 3000)
        }
      }
      
      poll()
    } catch (err: any) {
      console.error('[DEBUG] exportPdf error:', err)
      console.error('[DEBUG] error response:', err.response)
      const message = err.response?.data?.detail || err.message || 'Greška pri eksportu PDF-a'
      toast.error(message)
      setShowExportModal(false)
      setPdfExportStatus('failed')
      saveExportStatus('failed', docxExportStatus)
    } finally {
      setDownloadingPdf(false)
    }
  }

  const handleExportDocx = async () => {
    if (!docId) return
    setDownloadingDocx(true)
    setDocxTaskId(null)
    setExportType('docx')
    setExportProgress({ current: 0, total: 100, status: 'Priprema...' })
    setShowExportModal(true)
    setDocxExportStatus('processing')
    saveExportStatus(pdfExportStatus, 'processing')
    
    try {
      const res = await documentsApi.exportDocx(docId)
      const taskId = res.data.task_id
      setDocxTaskId(taskId)
      
      const poll = async () => {
        const statusRes = await documentsApi.exportDocxStatus(taskId)
        const status = statusRes.data.status
        
        // Celery PROGRESS state has result field with progress info
        const info = statusRes.data.result || {}
        
        if (info.current !== undefined) {
          setExportProgress({
            current: info.current,
            total: info.total || 100,
            status: info.status || 'Procesiranje...'
          })
        }
        
        if (status === 'SUCCESS') {
          setExportProgress({ current: 100, total: 100, status: 'Preuzimanje...' })
          const downloadRes = await documentsApi.exportDocxDownload(docId, taskId)
          const url = window.URL.createObjectURL(new Blob([downloadRes.data], { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' }))
          const a = document.createElement('a')
          a.href = url
          a.download = `${doc?.title ?? 'dokument'}_prevod.docx`
          a.click()
          window.URL.revokeObjectURL(url)
          toast.success('DOCX uspešno generisan')
          setShowExportModal(false)
          setDocxExportStatus('completed')
          saveExportStatus(pdfExportStatus, 'completed')
        } else if (status === 'FAILURE') {
          throw new Error(statusRes.data.error || 'DOCX generisanje nije uspelo')
        } else if (status === 'PROGRESS' || status === 'PENDING' || status === 'STARTED') {
          setTimeout(poll, 3000)
        } else {
          setTimeout(poll, 3000)
        }
      }
      
      poll()
    } catch (err: any) {
      const message = err.response?.data?.detail || err.message || 'Greška pri eksportu DOCX-a'
      toast.error(message)
      setShowExportModal(false)
      setDocxExportStatus('failed')
      saveExportStatus(pdfExportStatus, 'failed')
    } finally {
      setDownloadingDocx(false)
    }
  }

  const handleExportXlsx = async () => {
    if (!docId) return
    setDownloadingXlsx(true)
    try {
      const res = await documentsApi.exportXlsx(docId)
      const url = window.URL.createObjectURL(new Blob([res.data], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' }))
      const a = document.createElement('a')
      a.href = url
      a.download = `${doc?.title ?? 'dokument'}_prevod.xlsx`
      a.click()
      window.URL.revokeObjectURL(url)
    } catch {
      toast.error('Greška pri eksportu XLSX-a')
    } finally {
      setDownloadingXlsx(false)
    }
  }

  const handleExportPptx = async () => {
    if (!docId) return
    setDownloadingPptx(true)
    try {
      const res = await documentsApi.exportPptx(docId)
      const url = window.URL.createObjectURL(new Blob([res.data], { type: 'application/vnd.openxmlformats-officedocument.presentationml.presentation' }))
      const a = document.createElement('a')
      a.href = url
      a.download = `${doc?.title ?? 'dokument'}_prevod.pptx`
      a.click()
      window.URL.revokeObjectURL(url)
    } catch {
      toast.error('Greška pri eksportu PPTX-a')
    } finally {
      setDownloadingPptx(false)
    }
  }

  // Track seconds since last worker activity
  const [secondsSinceActivity, setSecondsSinceActivity] = useState<number | null>(null)
  const activityTimerRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const { data: doc, isLoading } = useDocumentDetail(docId)

  const { data: progress } = useDocumentProgress(docId)

  const { data: quizAvailability } = useDocumentQuizAvailability(docId)

  // Update "seconds since last activity" counter every second
  useEffect(() => {
    if (!progress?.last_activity_at) {
      setSecondsSinceActivity(null)
      return
    }
    const lastActivity = progress.last_activity_at
    const update = () => {
      const diff = Math.floor((Date.now() - new Date(lastActivity).getTime()) / 1000)
      setSecondsSinceActivity(diff)
    }
    update()
    activityTimerRef.current = setInterval(update, 1000)
    return () => { if (activityTimerRef.current) clearInterval(activityTimerRef.current) }
  }, [progress?.last_activity_at])

  const [chunkPage, setChunkPage] = useState(0)
  const CHUNKS_PER_PAGE = 20

  const { data: chunks } = useDocumentChunks(docId, chunkPage * CHUNKS_PER_PAGE, CHUNKS_PER_PAGE)

  // Toast when processing completes
  const prevStatusRef = useRef<string | undefined>(undefined)
  useEffect(() => {
    const current = doc?.status
    if (prevStatusRef.current && prevStatusRef.current === 'processing' && current === 'completed') {
      const title = doc?.title || 'Dokument'
      toast.success(`"${title}" — obrada završena!`, { duration: 5000 })
    }
    if (current) prevStatusRef.current = current
  }, [doc?.status, doc?.title])

  // Toast when translation completes
  const prevTransStatusRef = useRef<string | undefined>(undefined)
  useEffect(() => {
    const current = doc?.status
    if (prevTransStatusRef.current && prevTransStatusRef.current === 'translating' && current === 'completed') {
      const title = doc?.title || 'Dokument'
      toast.success(`"${title}" — prevod završen!`, { duration: 5000 })
    }
    if (current) prevTransStatusRef.current = current
  }, [doc?.status, doc?.title])

  const getStatusConfig = (status: string, translatedChunks: number, totalChunks: number) => {
    const configs: Record<string, { badge: string; strip: string; label: string; hasSubstatus?: boolean }> = {
      pending:     { badge: 'badge-gray',    strip: 'from-gray-500 to-slate-600',     label: 'Na čekanju' },
      processing:  { badge: 'badge-primary', strip: 'from-indigo-500 to-blue-600',    label: 'Obrađuje se' },
      completed:   { 
        badge: translatedChunks === 0 && totalChunks > 0 ? 'badge-warning' : 'badge-success', 
        strip: translatedChunks === 0 && totalChunks > 0 ? 'from-orange-500 to-red-500' : 'from-emerald-500 to-green-600', 
        label: totalChunks === 0 ? 'Bez odlomaka' : (translatedChunks === 0 ? 'Nije prevedeno' : 'Obrađeno'),
        hasSubstatus: translatedChunks === 0 && totalChunks > 0
      },
      translating: { badge: 'badge-primary', strip: 'from-violet-500 to-purple-600',  label: 'Prevodi se' },
      error:       { badge: 'badge-error',   strip: 'from-red-500 to-rose-600',       label: 'Greška' },
      partial:     { badge: 'badge-warning', strip: 'from-amber-500 to-orange-500',   label: 'Delimično' },
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
  const translatedCount = Array.isArray(chunks?.items) 
    ? chunks.items.filter((c: any) => c.translated_content).length 
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
                {doc.status === 'completed' ? (
                  <span className="flex items-center gap-1 text-emerald-600">
                    <CheckCircle className="w-3 h-3" />
                    Obrada završena
                    {progress?.elapsed_seconds ? ` · za ${Math.floor(progress.elapsed_seconds / 60)}m ${progress.elapsed_seconds % 60}s` : ''}
                  </span>
                ) : secondsSinceActivity !== null ? (
                  secondsSinceActivity > 60 ? (
                    <span className="flex items-center gap-1 text-amber-600 font-medium">
                      <AlertTriangle className="w-3 h-3" />
                      Nema aktivnosti već {Math.floor(secondsSinceActivity / 60)}m
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
                { label: 'Strana obrađeno', value: (progress.pages_done ?? 0) > 0 ? `${progress.pages_done ?? 0} / ${progress.pages_total ?? '?'}` : '...' },
                { label: 'Odlomaka kreirano', value: (progress.chunks_so_far ?? 0) > 0 ? (progress.chunks_so_far ?? 0) : '...' },
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
      {doc?.status === 'completed' && quizAvailability && (
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
        {doc.status === 'translating' && (
          <button
            onClick={() => {
              if (confirm('Da li želite da prekinete prevođenje? Progress će biti sačuvan.')) {
                stopMutation.mutate(docId, {
                  onSuccess: () => toast.success('Prevođenje zaustavljeno. Možete nastaviti kasnije.'),
                  onError: (error: any) => {
                    const message = error.response?.data?.user_message || error.message || 'Greška pri zaustavljanju'
                    toast.error(message)
                  },
                })
              }
            }}
            disabled={stopMutation.isPending}
            className="btn-primary bg-red-600 hover:bg-red-700 disabled:opacity-50"
          >
            <Square className="w-4 h-4" />
            {stopMutation.isPending ? 'Prekid...' : 'Prekini prevod'}
          </button>
        )}
        {doc.status === 'error' && (
          <div className="w-full bg-red-50 border border-red-200 rounded-lg p-4 mb-2">
            <div className="flex items-center gap-2 text-red-700 font-medium mb-2">
              <AlertTriangle className="w-5 h-5" />
              Greška pri obradi dokumenta
            </div>
            <p className="text-red-600 text-sm mb-3">
              {(doc.metadata as any)?.processing_error || (doc.metadata as any)?.translation?.errors?.[0] || doc.description || 'Nepoznata greška'}
            </p>
            {((doc.metadata as any)?.processing_error || (doc.metadata as any)?.translation?.errors?.[0]) && (
              <p className="text-gray-600 text-xs">
                Tehnički detalji: {(doc.metadata as any).processing_error || (doc.metadata as any).translation?.errors?.[0]}
              </p>
            )}
          </div>
        )}
        {doc.status === 'partial' && (
          <div className="w-full bg-orange-50 border border-orange-200 rounded-lg p-4 mb-2">
            <div className="flex items-center gap-2 text-orange-700 font-medium mb-2">
              <AlertTriangle className="w-5 h-5" />
              Delimično prevedeno
            </div>
            <p className="text-orange-600 text-sm mb-3">
              Prevođenje je prekinuto pre kraja. Možete nastaviti od mesta gde je stalo.
            </p>
            {doc.translated_chunks > 0 && (
              <p className="text-gray-600 text-xs">
                Prevedeno: {doc.translated_chunks} od {doc.total_chunks} odlomaka
              </p>
            )}
          </div>
        )}
        {(doc.status === 'error' || doc.status === 'partial') && (
          <button
            onClick={() => {
              if (confirm('Da li želite da obrisete ovaj dokument?')) {
                deleteMutation.mutate(docId, {
                  onSuccess: () => {
                    toast.success('Dokument obrisan')
                    navigate('/documents')
                  },
                })
              }
            }}
            disabled={deleteMutation.isPending}
            className="btn-primary bg-red-600 hover:bg-red-700 disabled:opacity-50"
          >
            <Trash2 className="w-4 h-4" />
            {deleteMutation.isPending ? 'Brisanje...' : 'Obriši dokument'}
          </button>
        )}
        {doc.status === 'partial' && (
          <button
            onClick={handleTranslate}
            disabled={translateMutation.isPending}
            className="btn-primary bg-orange-600 hover:bg-orange-700 disabled:opacity-50"
          >
            <RotateCcw className="w-4 h-4" />
            {translateMutation.isPending ? 'Nastavak...' : 'Nastavi prevođenje'}
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
              onClick={() => {
                console.log('[DEBUG] PDF button clicked!')
                handleExportPdf()
              }}
              disabled={(doc.status !== 'completed' && doc.status !== 'partial') || downloadingPdf}
              className={clsx('btn-primary bg-emerald-600 hover:bg-emerald-700', (doc.status !== 'completed' && doc.status !== 'partial') && 'opacity-50 pointer-events-none')}
            >
              {downloadingPdf ? (
                <span className="flex items-center gap-2">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  {pdfTaskId ? 'Priprema PDF...' : 'PDF'}
                </span>
              ) : pdfExportStatus === 'completed' ? (
                <span className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4" />
                  PDF
                </span>
              ) : pdfExportStatus === 'processing' ? (
                <span className="flex items-center gap-2">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  PDF...
                </span>
              ) : pdfExportStatus === 'failed' ? (
                <span className="flex items-center gap-2">
                  <AlertCircle className="w-4 h-4" />
                  PDF
                </span>
              ) : (
                <>
                  <Download className="w-4 h-4" />
                  {doc.status === 'partial' ? 'Delimični PDF' : 'PDF'}
                </>
              )}
            </button>
            <button
              onClick={handleExportDocx}
              disabled={(doc.status !== 'completed' && doc.status !== 'partial') || downloadingDocx}
              className={clsx('btn-primary bg-blue-600 hover:bg-blue-700', (doc.status !== 'completed' && doc.status !== 'partial') && 'opacity-50 pointer-events-none')}
            >
              {downloadingDocx ? (
                <span className="flex items-center gap-2">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  {docxTaskId ? 'Priprema DOCX...' : 'DOCX'}
                </span>
              ) : docxExportStatus === 'completed' ? (
                <span className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4" />
                  DOCX
                </span>
              ) : docxExportStatus === 'processing' ? (
                <span className="flex items-center gap-2">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  DOCX...
                </span>
              ) : docxExportStatus === 'failed' ? (
                <span className="flex items-center gap-2">
                  <AlertCircle className="w-4 h-4" />
                  DOCX
                </span>
              ) : (
                <>
                  <Download className="w-4 h-4" />
                  DOCX
                </>
              )}
            </button>
            <button
              onClick={handleExportXlsx}
              disabled={(doc.status !== 'completed' && doc.status !== 'partial') || downloadingXlsx}
              className={clsx('btn-primary bg-green-600 hover:bg-green-700', (doc.status !== 'completed' && doc.status !== 'partial') && 'opacity-50 pointer-events-none')}
            >
              {downloadingXlsx ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
              XLSX
            </button>
            <button
              onClick={handleExportPptx}
              disabled={(doc.status !== 'completed' && doc.status !== 'partial') || downloadingPptx}
              className={clsx('btn-primary bg-orange-600 hover:bg-orange-700', (doc.status !== 'completed' && doc.status !== 'partial') && 'opacity-50 pointer-events-none')}
            >
              {downloadingPptx ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
              PPTX
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

          {Array.isArray(chunks?.items) && chunks.items.length > 0 ? (
            <div className="divide-y divide-gray-100">
              {chunks.items.map((chunk: any, idx: number) => (
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
                    Prikaz {chunkPage + 1}/{Math.ceil(doc.total_chunks / CHUNKS_PER_PAGE)}
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
      
      {/* Export Progress Modal */}
      {showExportModal && exportProgress && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md mx-4 overflow-hidden">
            {/* Header */}
            <div className="bg-gradient-to-r from-indigo-600 to-violet-600 px-6 py-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-white/20 rounded-xl flex items-center justify-center">
                    <FileDown className="w-5 h-5 text-white" />
                  </div>
                  <div>
                    <h3 className="text-white font-semibold text-lg">
                      {exportType?.toUpperCase()} Export
                    </h3>
                    <p className="text-white/80 text-sm">
                      Generisanje dokumenta
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => setShowExportModal(false)}
                  className="p-2 hover:bg-white/20 rounded-lg transition-colors"
                >
                  <X className="w-5 h-5 text-white" />
                </button>
              </div>
            </div>

            {/* Progress Content */}
            <div className="p-6">
              {/* Status Message */}
              <p className="text-center text-gray-700 font-medium mb-4">
                {exportProgress.status}
              </p>

              {/* Progress Bar */}
              <div className="relative h-4 bg-gray-100 rounded-full overflow-hidden mb-2">
                <div
                  className="absolute left-0 top-0 h-full bg-gradient-to-r from-indigo-500 to-violet-500 transition-all duration-500 ease-out"
                  style={{ width: `${exportProgress.current}%` }}
                />
              </div>

              {/* Percentage */}
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">
                  {exportProgress.current}%
                </span>
                <span className="text-gray-500">
                  {exportProgress.current}/{exportProgress.total}
                </span>
              </div>

              {/* Spinner */}
              <div className="flex justify-center mt-6">
                <div className="relative">
                  <div className="w-16 h-16 border-4 border-indigo-100 rounded-full" />
                  <div className="absolute inset-0 border-4 border-indigo-600 rounded-full border-t-transparent animate-spin" />
                </div>
              </div>

              {/* Tips */}
              <p className="text-center text-gray-400 text-xs mt-4">
                Molimo sačekajte. Vreme generisanja zavisi od veličine dokumenta.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
