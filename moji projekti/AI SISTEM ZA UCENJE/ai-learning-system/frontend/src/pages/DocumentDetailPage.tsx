import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { documentsApi } from '@/services/api'
import { 
  ArrowLeft, 
  BookOpen, 
  Languages, 
  FileText,
  Clock,
  Calendar,
  Loader2
} from 'lucide-react'
import clsx from 'clsx'

export default function DocumentDetailPage() {
  const { id } = useParams<{ id: string }>()
  const docId = parseInt(id || '0')

  const { data: document, isLoading } = useQuery({
    queryKey: ['document', docId],
    queryFn: () => documentsApi.get(docId),
    enabled: !!docId,
  })

  const { data: chunks } = useQuery({
    queryKey: ['document-chunks', docId],
    queryFn: () => documentsApi.getChunks(docId, 1, 20),
    enabled: !!docId && document?.data?.status !== 'pending',
  })

  const doc = document?.data

  const getStatusBadge = (status: string) => {
    const styles: Record<string, string> = {
      pending: 'badge-gray',
      processing: 'badge-primary',
      processed: 'badge-success',
      translating: 'badge-primary',
      translated: 'badge-success',
      error: 'badge-error',
    }
    const labels: Record<string, string> = {
      pending: 'Na čekanju',
      processing: 'Obrađuje se',
      processed: 'Obrađeno',
      translating: 'Prevodi se',
      translated: 'Prevedeno',
      error: 'Greška',
    }
    return (
      <span className={clsx('badge', styles[status] || 'badge-gray')}>
        {labels[status] || status}
      </span>
    )
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="w-8 h-8 text-primary-500 animate-spin" />
      </div>
    )
  }

  if (!doc) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">Dokument nije pronađen</p>
        <Link to="/documents" className="btn-primary mt-4">
          Nazad na dokumente
        </Link>
      </div>
    )
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <Link 
        to="/documents" 
        className="inline-flex items-center gap-2 text-gray-500 hover:text-gray-700 transition-colors"
      >
        <ArrowLeft className="w-5 h-5" />
        <span>Nazad na dokumente</span>
      </Link>

      <div className="card p-6">
        <div className="flex items-start justify-between gap-4 mb-6">
          <div className="flex items-start gap-4">
            <div className="w-14 h-14 rounded-xl bg-primary-50 flex items-center justify-center">
              <BookOpen className="w-7 h-7 text-primary-600" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">{doc.title}</h1>
              {doc.author && (
                <p className="text-gray-500 mt-1">Autor: {doc.author}</p>
              )}
            </div>
          </div>
          {getStatusBadge(doc.status)}
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div className="p-4 rounded-xl bg-gray-50">
            <div className="flex items-center gap-2 text-gray-500 mb-1">
              <FileText className="w-4 h-4" />
              <span className="text-sm">Strane</span>
            </div>
            <p className="text-2xl font-bold text-gray-900">{doc.total_pages}</p>
          </div>
          <div className="p-4 rounded-xl bg-gray-50">
            <div className="flex items-center gap-2 text-gray-500 mb-1">
              <BookOpen className="w-4 h-4" />
              <span className="text-sm">Odlomci</span>
            </div>
            <p className="text-2xl font-bold text-gray-900">{doc.total_chunks}</p>
          </div>
          <div className="p-4 rounded-xl bg-gray-50">
            <div className="flex items-center gap-2 text-gray-500 mb-1">
              <Languages className="w-4 h-4" />
              <span className="text-sm">Jezik</span>
            </div>
            <p className="text-lg font-bold text-gray-900">
              {doc.source_language?.toUpperCase()} → {doc.target_language?.toUpperCase() || 'SR'}
            </p>
          </div>
          <div className="p-4 rounded-xl bg-gray-50">
            <div className="flex items-center gap-2 text-gray-500 mb-1">
              <Clock className="w-4 h-4" />
              <span className="text-sm">Status</span>
            </div>
            <p className="text-lg font-bold text-gray-900">{doc.processing_progress}%</p>
          </div>
        </div>

        <div className="flex items-center gap-2 mt-6 pt-6 border-t border-gray-100">
          <Calendar className="w-4 h-4 text-gray-400" />
          <span className="text-sm text-gray-500">
            Kreirano: {new Date(doc.created_at).toLocaleDateString('sr-RS', {
              year: 'numeric',
              month: 'long',
              day: 'numeric',
              hour: '2-digit',
              minute: '2-digit',
            })}
          </span>
        </div>
      </div>

      {doc.status !== 'pending' && (
        <div className="card">
          <div className="p-6 border-b border-gray-100">
            <h2 className="text-lg font-semibold text-gray-900">Odlomci</h2>
            <p className="text-sm text-gray-500 mt-1">
              Pregled izdvojenih odlomaka iz dokumenta
            </p>
          </div>

          {chunks?.data?.chunks?.length ? (
            <div className="divide-y divide-gray-100">
              {chunks.data.chunks.slice(0, 10).map((chunk: any) => (
                <div key={chunk.id} className="p-4 hover:bg-gray-50 transition-colors">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-gray-500">
                      Odlomak #{chunk.chunk_index + 1}
                      {chunk.page_number && ` • Strana ${chunk.page_number}`}
                    </span>
                    {chunk.heading && (
                      <span className="text-xs text-primary-600 font-medium bg-primary-50 px-2 py-1 rounded-lg">
                        {chunk.heading}
                      </span>
                    )}
                  </div>
                  <p className="text-gray-700 text-sm line-clamp-3">
                    {chunk.original_text}
                  </p>
                  {chunk.translated_text && (
                    <div className="mt-2 pt-2 border-t border-gray-100">
                      <p className="text-gray-600 text-sm line-clamp-3">
                        {chunk.translated_text}
                      </p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="p-12 text-center">
              <p className="text-gray-500">Odlomci se obrađuju...</p>
            </div>
          )}

          {doc.status === 'translated' && (
            <div className="p-4 border-t border-gray-100">
              <Link
                to={`/review/${docId}`}
                className="btn-primary w-full justify-center"
              >
                <Languages className="w-5 h-5" />
                Pregledaj i uredi prevode
              </Link>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
