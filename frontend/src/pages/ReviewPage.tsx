/**
 * ================================================================================
 * Petar II Petrović-Njegoš
 * "Blago tome ko dovijek živi, imao se rašta i roditi"
 * ================================================================================
 * 
 * AI Learning System
 * ReviewPage.tsx
 * Verzija: 1.0.0
 * Autor: Branko Suznjevic
 * Datum: 2026
 * ================================================================================
 */

import { useParams, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { documentsApi } from '@/services/api'
import { useState, useEffect } from 'react'
import toast from 'react-hot-toast'
import { 
  ArrowLeft, 
  ChevronLeft, 
  ChevronRight,
  Check,
  X,
  Edit3,
  Save,
  Loader2,
  CheckCircle
} from 'lucide-react'
import clsx from 'clsx'

export default function ReviewPage() {
  const { id } = useParams<{ id: string }>()
  const docId = id || ''
  const queryClient = useQueryClient()
  
  const CHUNKS_PER_PAGE = 20
  const [currentPage, setCurrentPage] = useState(0)
  const [editedText, setEditedText] = useState('')
  const [isEditing, setIsEditing] = useState(false)

  // First, get total count of chunks
  const { data: document } = useQuery({
    queryKey: ['document', docId],
    queryFn: () => documentsApi.get(docId),
    enabled: !!docId,
  })

  const totalChunks = document?.data?.total_chunks || 0
  const totalPages = Math.ceil(totalChunks / CHUNKS_PER_PAGE)

  // Fetch chunks for current page
  const { data: chunks, isLoading } = useQuery({
    queryKey: ['document-chunks', docId, currentPage],
    queryFn: () => documentsApi.getChunks(docId, currentPage * CHUNKS_PER_PAGE, CHUNKS_PER_PAGE),
    enabled: !!docId && totalChunks > 0,
  })

  const chunkList: any[] = Array.isArray(chunks?.data) ? chunks.data : []
  const currentChunk = chunkList[currentPage % CHUNKS_PER_PAGE] // Handle case where page changed

  useEffect(() => {
    if (currentChunk?.translated_content) {
      setEditedText(currentChunk.translated_content)
    }
  }, [currentChunk])

  const updateMutation = useMutation({
    mutationFn: (data: { translated_content?: string; is_reviewed?: boolean }) =>
      documentsApi.updateChunk(docId, currentChunk.id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['document-chunks', docId] })
      toast.success('Sačuvano!')
      setIsEditing(false)
    },
    onError: () => toast.error('Greška pri čuvanju'),
  })

  const handleApprove = () => {
    updateMutation.mutate({ is_reviewed: true })
  }

  const handleEdit = () => {
    setIsEditing(true)
  }

  const handleSave = () => {
    updateMutation.mutate({ translated_content: editedText, is_reviewed: true })
  }

  const handleCancel = () => {
    setEditedText(currentChunk.translated_content || '')
    setIsEditing(false)
  }

  const handlePrevious = () => {
    if (currentPage > 0) {
      setCurrentPage(currentPage - 1)
      setIsEditing(false)
    }
  }

  const handleNext = () => {
    if ((currentPage + 1) * CHUNKS_PER_PAGE < totalChunks) {
      setCurrentPage(currentPage + 1)
      setIsEditing(false)
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="w-8 h-8 text-indigo-500 animate-spin" />
      </div>
    )
  }

  if (!chunkList.length) {
    return (
      <div className="text-center py-16">
        <div className="w-16 h-16 rounded-2xl bg-indigo-50 flex items-center justify-center mx-auto mb-4">
          <Edit3 className="w-8 h-8 text-indigo-400" />
        </div>
        <p className="text-gray-700 font-semibold mb-1">Nema odlomaka za pregled</p>
        <Link to="/documents" className="btn-primary mt-4">
          Nazad na dokumente
        </Link>
      </div>
    )
  }

  const doc = document?.data
  
  // Get total reviewed count from the document
  const reviewedCount = doc?.reviewed_chunks || 0
  const progress = totalChunks > 0 ? Math.round((reviewedCount / totalChunks) * 100) : 0

  return (
    <div className="space-y-5 animate-fade-in max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex items-start gap-4">
        <Link 
          to={`/documents/${docId}`}
          className="flex items-center gap-2 px-3 py-2 rounded-xl hover:bg-gray-100 text-gray-500 hover:text-gray-700 transition-colors flex-shrink-0 mt-0.5 text-sm font-medium"
        >
          <ArrowLeft className="w-5 h-5" />
          <span className="hidden sm:inline">Nazad</span>
        </Link>
        <div className="flex-1 min-w-0">
          <h1 className="text-xl font-extrabold text-gray-900 truncate">
            {doc?.title || 'Pregled prevoda'}
          </h1>
          <p className="text-sm text-gray-500 mt-0.5">Stranica {currentPage + 1} od {totalPages} ({totalChunks} odlomaka)</p>
        </div>
      </div>

      {/* Progress bar */}
      <div className="card px-5 py-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-semibold text-gray-700">Napredak pregleda</span>
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-500">{reviewedCount}/{totalChunks}</span>
            <span className="text-sm font-bold text-indigo-600">{progress}%</span>
          </div>
        </div>
        <div className="progress-bar">
          <div
            className="progress-fill bg-gradient-to-r from-indigo-500 to-violet-500"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {/* Chunk status */}
      <div className="flex items-center gap-3">
        {currentChunk?.parent_heading && (
          <span className="text-xs text-indigo-600 font-medium bg-indigo-50 px-3 py-1 rounded-full">
            {currentChunk.parent_heading}
          </span>
        )}
        <span className={clsx(
          'badge ml-auto',
          currentChunk?.is_reviewed ? 'badge-success' :
          currentChunk?.is_translated ? 'badge-warning' : 'badge-gray'
        )}>
          {currentChunk?.is_reviewed ? '✓ Odobreno' : currentChunk?.is_translated ? 'Prevedeno' : 'Na čekanju'}
        </span>
      </div>

      {/* Main split panel */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* Original */}
        <div className="card p-5">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-8 h-8 rounded-xl bg-gray-100 flex items-center justify-center">
              <span className="text-xs font-extrabold text-gray-700">EN</span>
            </div>
            <div>
              <h3 className="text-sm font-bold text-gray-900">Originalni tekst</h3>
              <p className="text-xs text-gray-400">Engleski</p>
            </div>
          </div>
          <div className="bg-gray-50 rounded-2xl p-4 min-h-[220px]">
            <p className="text-gray-700 text-sm whitespace-pre-wrap leading-relaxed">
              {currentChunk?.content}
            </p>
          </div>
        </div>

        {/* Translation */}
        <div className="card p-5">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-8 h-8 rounded-xl bg-indigo-100 flex items-center justify-center">
              <span className="text-xs font-extrabold text-indigo-700">SR</span>
            </div>
            <div>
              <h3 className="text-sm font-bold text-gray-900">Prevedeni tekst</h3>
              <p className="text-xs text-gray-400">Srpski</p>
            </div>
          </div>

          {isEditing ? (
            <div className="space-y-3">
              <textarea
                value={editedText}
                onChange={(e) => setEditedText(e.target.value)}
                className="input min-h-[220px] resize-none text-sm leading-relaxed rounded-2xl"
                placeholder="Unesite prevod..."
              />
              <div className="flex gap-2">
                <button
                  onClick={handleSave}
                  disabled={updateMutation.isPending}
                  className="btn-primary btn-sm flex-1"
                >
                  {updateMutation.isPending ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <><Save className="w-4 h-4" /> Sačuvaj</>
                  )}
                </button>
                <button onClick={handleCancel} className="btn-secondary btn-sm">
                  <X className="w-4 h-4" />
                  Otkaži
                </button>
              </div>
            </div>
          ) : (
            <div className={clsx(
              'rounded-2xl p-4 min-h-[220px]',
              currentChunk?.is_reviewed ? 'bg-emerald-50' : 'bg-indigo-50'
            )}>
              {currentChunk?.is_reviewed && (
                <div className="flex items-center gap-1.5 mb-3">
                  <CheckCircle className="w-4 h-4 text-emerald-500" />
                  <span className="text-xs text-emerald-600 font-semibold">Odobreno</span>
                </div>
              )}
              <p className="text-gray-700 text-sm whitespace-pre-wrap leading-relaxed">
                {currentChunk?.translated_content || (
                  <span className="text-gray-400 italic text-sm">Prevod nije dostupan</span>
                )}
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Controls */}
      {!isEditing && (
        <div className="card px-5 py-4 flex items-center justify-between gap-3">
          <button
            onClick={handlePrevious}
            disabled={currentPage === 0}
            className="btn-secondary"
          >
            <ChevronLeft className="w-4 h-4" />
            Prethodna strana
          </button>

          <div className="flex items-center gap-2">
            <button onClick={handleEdit} className="btn-secondary">
              <Edit3 className="w-4 h-4" />
              Uredi
            </button>
            <button
              onClick={handleApprove}
              disabled={updateMutation.isPending || !currentChunk?.translated_content}
              className="btn-primary"
            >
              {updateMutation.isPending ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <><Check className="w-4 h-4" /> Odobri</>
              )}
            </button>
          </div>

          <button
            onClick={handleNext}
            disabled={(currentPage + 1) * CHUNKS_PER_PAGE >= totalChunks}
            className="btn-secondary"
          >
            Sledeća strana
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Page navigation */}
      <div className="card px-5 py-4">
        <p className="text-xs text-gray-400 mb-3 font-medium">Navigacija stranica</p>
        <div className="flex flex-wrap gap-2">
          {/* Previous button */}
          <button
            onClick={handlePrevious}
            disabled={currentPage === 0}
            className="btn-secondary px-3 py-2"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
          
          {/* Page numbers - simple version */}
          {Array.from({ length: Math.min(totalPages, 30) }, (_, i) => {
            const isCurrentPage = i === currentPage
            return (
              <button
                key={i}
                onClick={() => { setCurrentPage(i); setIsEditing(false) }}
                title={`Stranica ${i + 1}`}
                className={clsx(
                  'w-10 h-10 rounded-xl text-sm font-bold transition-all duration-150',
                  isCurrentPage
                    ? 'bg-gradient-to-br from-indigo-500 to-violet-500 text-white shadow-md shadow-indigo-500/30'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                )}
              >
                {i + 1}
              </button>
            )
          })}
          
          {totalPages > 30 && (
            <span className="self-center text-gray-400 text-sm font-medium ml-1">
              ... do {totalPages} stranica
            </span>
          )}
          
          {/* Next button */}
          <button
            onClick={handleNext}
            disabled={(currentPage + 1) * CHUNKS_PER_PAGE >= totalChunks}
            className="btn-secondary px-3 py-2"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
        <p className="text-xs text-gray-400 mt-3 text-center">
          Ukupno {totalChunks} odlomaka na {totalPages} stranica
        </p>
      </div>
    </div>
  )
}
