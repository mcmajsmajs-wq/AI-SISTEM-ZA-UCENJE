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
  SkipBack,
  Loader2
} from 'lucide-react'
import clsx from 'clsx'

export default function ReviewPage() {
  const { id } = useParams<{ id: string }>()
  const docId = parseInt(id || '0')
  const queryClient = useQueryClient()
  
  const [currentIndex, setCurrentIndex] = useState(0)
  const [editedText, setEditedText] = useState('')
  const [isEditing, setIsEditing] = useState(false)

  const { data: document } = useQuery({
    queryKey: ['document', docId],
    queryFn: () => documentsApi.get(docId),
    enabled: !!docId,
  })

  const { data: chunks, isLoading } = useQuery({
    queryKey: ['document-chunks', docId],
    queryFn: () => documentsApi.getChunks(docId, 1, 100),
    enabled: !!docId,
  })

  const chunkList = chunks?.data?.chunks || []
  const currentChunk = chunkList[currentIndex]

  useEffect(() => {
    if (currentChunk?.translated_text) {
      setEditedText(currentChunk.translated_text)
    }
  }, [currentChunk])

  const updateMutation = useMutation({
    mutationFn: (data: { translated_text: string; status: string }) =>
      documentsApi.updateChunk(docId, currentChunk.id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['document-chunks', docId] })
      toast.success('Sačuvano!')
      setIsEditing(false)
    },
    onError: () => toast.error('Greška pri čuvanju'),
  })

  const handleApprove = () => {
    updateMutation.mutate({ 
      translated_text: currentChunk.translated_text, 
      status: 'approved' 
    })
  }

  const handleEdit = () => {
    setIsEditing(true)
  }

  const handleSave = () => {
    updateMutation.mutate({ 
      translated_text: editedText, 
      status: 'edited' 
    })
  }

  const handleCancel = () => {
    setEditedText(currentChunk.translated_text || '')
    setIsEditing(false)
  }

  const handlePrevious = () => {
    if (currentIndex > 0) {
      setCurrentIndex(currentIndex - 1)
      setIsEditing(false)
    }
  }

  const handleNext = () => {
    if (currentIndex < chunkList.length - 1) {
      setCurrentIndex(currentIndex + 1)
      setIsEditing(false)
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="w-8 h-8 text-primary-500 animate-spin" />
      </div>
    )
  }

  if (!chunkList.length) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">Nema odlomaka za pregled</p>
        <Link to="/documents" className="btn-primary mt-4">
          Nazad na dokumente
        </Link>
      </div>
    )
  }

  const doc = document?.data
  const approvedCount = chunkList.filter((c: any) => c.status === 'approved' || c.status === 'edited').length
  const progress = Math.round((approvedCount / chunkList.length) * 100)

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <Link 
          to={`/documents/${docId}`}
          className="inline-flex items-center gap-2 text-gray-500 hover:text-gray-700 transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
          <span>Nazad na dokument</span>
        </Link>
        
        <div className="flex items-center gap-4">
          <span className="text-sm text-gray-500">
            {approvedCount}/{chunkList.length} pregledano
          </span>
          <div className="w-32 h-2 bg-gray-100 rounded-full overflow-hidden">
            <div 
              className="h-full bg-gradient-to-r from-primary-500 to-accent-500 transition-all"
              style={{ width: `${progress}%` }}
            />
          </div>
          <span className="text-sm font-medium text-gray-900">{progress}%</span>
        </div>
      </div>

      {doc && (
        <div className="card p-4">
          <h1 className="text-xl font-bold text-gray-900">{doc.title}</h1>
          <p className="text-sm text-gray-500 mt-1">
            Pregledajte i uredite prevedene odlomke
          </p>
        </div>
      )}

      <div className="card">
        <div className="p-4 border-b border-gray-100 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <span className="text-sm font-medium text-gray-500">
              Odlomak {currentIndex + 1} od {chunkList.length}
            </span>
            {currentChunk?.heading && (
              <span className="text-xs text-primary-600 font-medium bg-primary-50 px-2 py-1 rounded-lg">
                {currentChunk.heading}
              </span>
            )}
            {currentChunk?.page_number && (
              <span className="text-xs text-gray-500">
                Strana {currentChunk.page_number}
              </span>
            )}
          </div>
          
          <div className="flex items-center gap-2">
            <span className={clsx(
              "badge",
              currentChunk?.status === 'approved' && "badge-success",
              currentChunk?.status === 'edited' && "badge-primary",
              currentChunk?.status === 'translated' && "badge-warning",
            )}>
              {currentChunk?.status === 'approved' && 'Odobreno'}
              {currentChunk?.status === 'edited' && 'Uređeno'}
              {currentChunk?.status === 'translated' && 'Na čekanju'}
            </span>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 divide-y lg:divide-y-0 lg:divide-x divide-gray-100">
          <div className="p-6">
            <div className="flex items-center gap-2 mb-3">
              <div className="w-6 h-6 rounded-lg bg-gray-100 flex items-center justify-center">
                <span className="text-xs font-bold text-gray-600">EN</span>
              </div>
              <h3 className="font-semibold text-gray-700">Originalni tekst</h3>
            </div>
            <div className="bg-gray-50 rounded-xl p-4 min-h-[200px]">
              <p className="text-gray-700 whitespace-pre-wrap">
                {currentChunk?.original_text}
              </p>
            </div>
          </div>

          <div className="p-6">
            <div className="flex items-center gap-2 mb-3">
              <div className="w-6 h-6 rounded-lg bg-primary-100 flex items-center justify-center">
                <span className="text-xs font-bold text-primary-600">SR</span>
              </div>
              <h3 className="font-semibold text-gray-700">Prevedeni tekst</h3>
            </div>
            
            {isEditing ? (
              <div className="space-y-3">
                <textarea
                  value={editedText}
                  onChange={(e) => setEditedText(e.target.value)}
                  className="input min-h-[200px] resize-none font-mono text-sm"
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
                      <>
                        <Save className="w-4 h-4" />
                        Sačuvaj
                      </>
                    )}
                  </button>
                  <button
                    onClick={handleCancel}
                    className="btn-secondary btn-sm"
                  >
                    <X className="w-4 h-4" />
                    Otkaži
                  </button>
                </div>
              </div>
            ) : (
              <div className="bg-primary-50 rounded-xl p-4 min-h-[200px]">
                <p className="text-gray-700 whitespace-pre-wrap">
                  {currentChunk?.translated_text || (
                    <span className="text-gray-400 italic">Prevod nije dostupan</span>
                  )}
                </p>
              </div>
            )}
          </div>
        </div>

        {!isEditing && (
          <div className="p-4 border-t border-gray-100 flex items-center justify-between">
            <button
              onClick={handlePrevious}
              disabled={currentIndex === 0}
              className="btn-secondary"
            >
              <ChevronLeft className="w-5 h-5" />
              Prethodni
            </button>

            <div className="flex items-center gap-2">
              <button
                onClick={handleEdit}
                className="btn-secondary"
              >
                <Edit3 className="w-5 h-5" />
                Uredi
              </button>
              <button
                onClick={handleApprove}
                disabled={updateMutation.isPending || !currentChunk?.translated_text}
                className="btn-primary"
              >
                {updateMutation.isPending ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <>
                    <Check className="w-5 h-5" />
                    Odobri
                  </>
                )}
              </button>
            </div>

            <button
              onClick={handleNext}
              disabled={currentIndex === chunkList.length - 1}
              className="btn-secondary"
            >
              Sledeći
              <ChevronRight className="w-5 h-5" />
            </button>
          </div>
        )}
      </div>

      <div className="card p-4">
        <div className="flex items-center gap-2 justify-center">
          <button
            onClick={() => setCurrentIndex(0)}
            disabled={currentIndex === 0}
            className="btn-ghost btn-sm"
          >
            <SkipBack className="w-4 h-4" />
          </button>
          {Array.from({ length: Math.min(10, chunkList.length) }, (_, i) => {
            const idx = i
            const chunk = chunkList[idx]
            return (
              <button
                key={idx}
                onClick={() => {
                  setCurrentIndex(idx)
                  setIsEditing(false)
                }}
                className={clsx(
                  "w-8 h-8 rounded-lg text-sm font-medium transition-all",
                  idx === currentIndex
                    ? "bg-primary-500 text-white"
                    : chunk?.status === 'approved' || chunk?.status === 'edited'
                      ? "bg-green-100 text-green-700 hover:bg-green-200"
                      : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                )}
              >
                {idx + 1}
              </button>
            )
          })}
          {chunkList.length > 10 && (
            <span className="text-gray-400 text-sm">...({chunkList.length})</span>
          )}
        </div>
      </div>
    </div>
  )
}
