/**
 * ================================================================================
 * Petar II Petrović-Njegoš
 * "Blago tome ko dovijek živi, imao se rašta i roditi"
 * ================================================================================
 * 
 * AI Learning System
 * ReviewPage.tsx
 * Verzija: 2.0.0 - Prikazuje svih 20 chunks po stranici
 * Autor: Branko Suznjevic
 * Datum: 2026
 * ================================================================================
 */

import { useParams, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { documentsApi } from '@/services/api'
import { useState } from 'react'
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
  CheckCircle,
  Circle,
  Hash
} from 'lucide-react'
import clsx from 'clsx'

// Smart pagination helper - prikazuje relevantne stranice sa ... gde je potrebno
function generatePageNumbers(currentPage: number, totalPages: number): (number | '...')[] {
  if (totalPages <= 10) {
    return Array.from({ length: totalPages }, (_, i) => i)
  }

  const pages: (number | '...')[] = []
  const delta = 2

  const firstPages = [0, 1, 2, 3, 4]
  const lastPages = [
    totalPages - 5,
    totalPages - 4,
    totalPages - 3,
    totalPages - 2,
    totalPages - 1,
  ]

  const aroundCurrent = Array.from(
    { length: delta * 2 + 1 },
    (_, i) => currentPage - delta + i
  ).filter((p) => p > 4 && p < totalPages - 5)

  const allPages = [...new Set([...firstPages, ...aroundCurrent, ...lastPages])].sort((a, b) => a - b)

  for (let i = 0; i < allPages.length; i++) {
    pages.push(allPages[i])
    if (i < allPages.length - 1 && allPages[i + 1] - allPages[i] > 1) {
      pages.push('...')
    }
  }

  return pages
}

interface ChunkItem {
  id: string
  content: string
  translated_content?: string
  parent_heading?: string
  is_reviewed?: boolean
  is_translated?: boolean
}

export default function ReviewPage() {
  const { id } = useParams<{ id: string }>()
  const docId = id || ''
  const queryClient = useQueryClient()
  
  const CHUNKS_PER_PAGE = 20
  const [currentPage, setCurrentPage] = useState(0)
  const [editingChunkId, setEditingChunkId] = useState<string | null>(null)
  const [editedTexts, setEditedTexts] = useState<Record<string, string>>({})

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

  const chunkList: ChunkItem[] = Array.isArray(chunks?.data) ? chunks.data : []

  const updateMutation = useMutation({
    mutationFn: ({ chunkId, data }: { chunkId: string; data: { translated_content?: string; is_reviewed?: boolean } }) =>
      documentsApi.updateChunk(docId, chunkId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['document-chunks', docId] })
      queryClient.invalidateQueries({ queryKey: ['document', docId] })
      toast.success('Sačuvano!')
      setEditingChunkId(null)
      setEditedTexts({})
    },
    onError: () => toast.error('Greška pri čuvanju'),
  })

  const handleStartEdit = (chunk: ChunkItem) => {
    setEditingChunkId(chunk.id)
    setEditedTexts(prev => ({ ...prev, [chunk.id]: chunk.translated_content || '' }))
  }

  const handleCancelEdit = (chunkId: string) => {
    setEditingChunkId(null)
    setEditedTexts(prev => {
      const newTexts = { ...prev }
      delete newTexts[chunkId]
      return newTexts
    })
  }

  const handleSaveEdit = (chunk: ChunkItem) => {
    const text = editedTexts[chunk.id]
    updateMutation.mutate({ 
      chunkId: chunk.id, 
      data: { translated_content: text, is_reviewed: true } 
    })
  }

  const handleApprove = (chunkId: string) => {
    updateMutation.mutate({ chunkId, data: { is_reviewed: true } })
  }

  const handleTextChange = (chunkId: string, text: string) => {
    setEditedTexts(prev => ({ ...prev, [chunkId]: text }))
  }

  const handlePrevious = () => {
    if (currentPage > 0) {
      setCurrentPage(currentPage - 1)
      setEditingChunkId(null)
    }
  }

  const handleNext = () => {
    if ((currentPage + 1) * CHUNKS_PER_PAGE < totalChunks) {
      setCurrentPage(currentPage + 1)
      setEditingChunkId(null)
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
  const reviewedCount = doc?.reviewed_chunks || 0
  const progress = totalChunks > 0 ? Math.round((reviewedCount / totalChunks) * 100) : 0

  const pageStartIndex = currentPage * CHUNKS_PER_PAGE + 1

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
          <p className="text-sm text-gray-500 mt-0.5">
            Prikaz {currentPage + 1}/{totalPages} • {chunkList.length} odlomaka na ovoj stranici • {totalChunks} ukupno
          </p>
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

      {/* Chunks list - ALL chunks from current page */}
      <div className="space-y-4">
        {chunkList.map((chunk, idx) => {
          const globalIndex = pageStartIndex + idx
          const isEditing = editingChunkId === chunk.id
          const editText = editedTexts[chunk.id] ?? chunk.translated_content ?? ''
          const hasTranslation = !!chunk.translated_content

          return (
            <div key={chunk.id} className="card overflow-hidden">
              {/* Chunk header */}
              <div className="px-5 py-3 bg-gray-50 border-b border-gray-100 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-indigo-100 flex items-center justify-center">
                    <span className="text-xs font-bold text-indigo-600">{globalIndex}</span>
                  </div>
                  {chunk.parent_heading && (
                    <span className="flex items-center gap-1 text-xs text-indigo-600 font-medium bg-indigo-50 px-2 py-1 rounded-lg">
                      <Hash className="w-3 h-3" />
                      {chunk.parent_heading}
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  {hasTranslation ? (
                    chunk.is_reviewed ? (
                      <span className="badge badge-success">
                        <CheckCircle className="w-3 h-3 mr-1" />
                        Odobreno
                      </span>
                    ) : (
                      <span className="badge badge-warning">Prevedeno</span>
                    )
                  ) : (
                    <span className="badge badge-gray">
                      <Circle className="w-3 h-3 mr-1" />
                      Na čekanju
                    </span>
                  )}
                </div>
              </div>

              {/* Content */}
              <div className="p-5">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                  {/* Original */}
                  <div>
                    <div className="flex items-center gap-2 mb-2">
                      <div className="w-6 h-6 rounded bg-gray-100 flex items-center justify-center">
                        <span className="text-xs font-bold text-gray-600">EN</span>
                      </div>
                      <span className="text-xs font-semibold text-gray-500">Originalni tekst</span>
                    </div>
                    <div className="bg-gray-50 rounded-xl p-4">
                      <p className="text-gray-700 text-sm whitespace-pre-wrap leading-relaxed">
                        {chunk.content}
                      </p>
                    </div>
                  </div>

                  {/* Translation */}
                  <div>
                    <div className="flex items-center gap-2 mb-2">
                      <div className="w-6 h-6 rounded bg-indigo-100 flex items-center justify-center">
                        <span className="text-xs font-bold text-indigo-600">SR</span>
                      </div>
                      <span className="text-xs font-semibold text-gray-500">Prevedeni tekst</span>
                    </div>
                    
                    {isEditing ? (
                      <div className="space-y-2">
                        <textarea
                          value={editText}
                          onChange={(e) => handleTextChange(chunk.id, e.target.value)}
                          className="input min-h-[120px] resize-none text-sm leading-relaxed rounded-xl"
                          placeholder="Unesite prevod..."
                        />
                        <div className="flex gap-2">
                          <button
                            onClick={() => handleSaveEdit(chunk)}
                            disabled={updateMutation.isPending}
                            className="btn-primary btn-sm flex-1"
                          >
                            {updateMutation.isPending ? (
                              <Loader2 className="w-4 h-4 animate-spin" />
                            ) : (
                              <><Save className="w-4 h-4" /> Sačuvaj</>
                            )}
                          </button>
                          <button 
                            onClick={() => handleCancelEdit(chunk.id)} 
                            className="btn-secondary btn-sm"
                          >
                            <X className="w-4 h-4" />
                            Otkaži
                          </button>
                        </div>
                      </div>
                    ) : (
                      <div className={clsx(
                        'rounded-xl p-4',
                        chunk.is_reviewed ? 'bg-emerald-50' : 'bg-indigo-50'
                      )}>
                        {hasTranslation ? (
                          <p className="text-gray-700 text-sm whitespace-pre-wrap leading-relaxed">
                            {chunk.translated_content}
                          </p>
                        ) : (
                          <p className="text-gray-400 italic text-sm">Prevod nije dostupan</p>
                        )}
                      </div>
                    )}
                  </div>
                </div>

                {/* Actions - only when not editing this chunk */}
                {!isEditing && (
                  <div className="flex items-center gap-2 mt-4 pt-4 border-t border-gray-100">
                    <button 
                      onClick={() => handleStartEdit(chunk)} 
                      className="btn-secondary btn-sm"
                    >
                      <Edit3 className="w-4 h-4" />
                      Uredi
                    </button>
                    {hasTranslation && !chunk.is_reviewed && (
                      <button
                        onClick={() => handleApprove(chunk.id)}
                        disabled={updateMutation.isPending}
                        className="btn-primary btn-sm"
                      >
                        {updateMutation.isPending ? (
                          <Loader2 className="w-4 h-4 animate-spin" />
                        ) : (
                          <><Check className="w-4 h-4" /> Odobri</>
                        )}
                      </button>
                    )}
                  </div>
                )}
              </div>
            </div>
          )
        })}
      </div>

      {/* Page navigation */}
      <div className="card px-5 py-4">
        <div className="flex flex-wrap gap-2 items-center justify-center">
          {/* Previous button */}
          <button
            onClick={handlePrevious}
            disabled={currentPage === 0}
            className="btn-secondary px-3 py-2"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>

          {/* Page numbers */}
          {generatePageNumbers(currentPage, totalPages).map((page, idx) => {
            if (page === '...') {
              return (
                <span key={`ellipsis-${idx}`} className="w-10 h-10 flex items-center justify-center text-gray-400 text-sm">
                  ...
                </span>
              )
            }
            const pageNum = page as number
            const isCurrentPage = pageNum === currentPage
            return (
              <button
                key={pageNum}
                onClick={() => { setCurrentPage(pageNum); setEditingChunkId(null) }}
                title={`Stranica ${pageNum + 1}`}
                className={clsx(
                  'w-10 h-10 rounded-xl text-sm font-bold transition-all duration-150',
                  isCurrentPage
                    ? 'bg-gradient-to-br from-indigo-500 to-violet-500 text-white shadow-md shadow-indigo-500/30'
                    : 'bg-gray-100 text-gray-600 hover:bg-indigo-100 hover:text-indigo-700'
                )}
              >
                {pageNum + 1}
              </button>
            )
          })}

          {/* Next button */}
          <button
            onClick={handleNext}
            disabled={(currentPage + 1) * CHUNKS_PER_PAGE >= totalChunks}
            className="btn-secondary px-3 py-2"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>

        {/* Quick jump */}
        <div className="flex items-center justify-center gap-2 mt-3">
          <span className="text-xs text-gray-400">Idi na stranicu:</span>
          <input
            type="number"
            min={1}
            max={totalPages}
            defaultValue={currentPage + 1}
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                const input = e.currentTarget
                const page = Math.min(Math.max(1, parseInt(input.value) || 1), totalPages)
                setCurrentPage(page - 1)
                setEditingChunkId(null)
              }
            }}
            className="w-16 h-8 px-2 text-sm text-center border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
            placeholder="1"
          />
          <span className="text-xs text-gray-400">od {totalPages}</span>
        </div>

        <p className="text-xs text-gray-400 mt-3 text-center">
          Prikaz {currentPage * CHUNKS_PER_PAGE + 1}-{Math.min((currentPage + 1) * CHUNKS_PER_PAGE, totalChunks)} od {totalChunks} odlomaka
        </p>
      </div>
    </div>
  )
}
