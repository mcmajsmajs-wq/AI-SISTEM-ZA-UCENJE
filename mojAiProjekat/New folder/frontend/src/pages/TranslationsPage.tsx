/**
 * ================================================================================
 * Petar II Petrović-Njegoš
 * "Blago tome ko dovijek živi, imao se rašta i roditi"
 * ================================================================================
 * 
 * AI Learning System
 * TranslationsPage.tsx
 * Verzija: 1.0.0
 * Autor: Branko Suznjevic
 * Datum: 2026
 * ================================================================================
 */

import { useQuery } from '@tanstack/react-query'
import { documentsApi } from '@/services/api'
import { Link } from 'react-router-dom'
import { Languages, BookOpen, Eye, Loader2, FileText } from 'lucide-react'

export default function TranslationsPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['documents', 0, 100],
    queryFn: () => documentsApi.list(0, 100),
    // Poll every 3s if any document is currently translating
    refetchInterval: (query) => {
      const items: any[] = query.state.data?.data?.items || []
      return items.some((d) => d.status === 'translating') ? 3000 : false
    },
  })

  const allDocs: any[] = data?.data?.items || []
  const translatedDocs = allDocs.filter((d: any) => (d.translated_chunks || 0) > 0 || d.status === 'translating')

  return (
    <div className="max-w-5xl mx-auto py-8 px-4">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 rounded-xl bg-violet-100 flex items-center justify-center">
          <Languages className="w-5 h-5 text-violet-600" />
        </div>
        <div>
          <h1 className="text-xl font-bold text-gray-900">Pregled prevoda</h1>
          <p className="text-sm text-gray-500">Svi prevedeni dokumenti</p>
        </div>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-16">
          <Loader2 className="w-8 h-8 text-violet-500 animate-spin" />
        </div>
      ) : translatedDocs.length === 0 ? (
        <div className="card p-14 text-center">
          <div className="w-16 h-16 rounded-2xl bg-violet-50 flex items-center justify-center mx-auto mb-4">
            <FileText className="w-8 h-8 text-violet-400" />
          </div>
          <p className="text-gray-700 font-semibold mb-1">Nema prevedenih dokumenata</p>
          <p className="text-sm text-gray-400">
            Idite na{' '}
            <Link to="/documents" className="text-violet-600 underline">Dokumenti</Link>
            {' '}i pokrenite prevod
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
          {translatedDocs.map((doc: any) => {
            const pct = doc.total_chunks > 0
              ? Math.round(((doc.translated_chunks || 0) / doc.total_chunks) * 100)
              : 0
            const isTranslating = doc.status === 'translating'
            return (
              <div key={doc.id} className="course-card hover:shadow-xl hover:-translate-y-0.5 transition-all duration-200">
                <div className="h-20 bg-gradient-to-r from-violet-500 to-purple-600 relative flex items-end px-4 pb-3">
                  <div className="w-10 h-10 rounded-xl bg-white/20 backdrop-blur flex items-center justify-center">
                    {isTranslating
                      ? <Loader2 className="w-5 h-5 text-white animate-spin" />
                      : <BookOpen className="w-5 h-5 text-white" />
                    }
                  </div>
                  <div className="absolute top-3 right-3">
                    {isTranslating ? (
                      <span className="badge bg-yellow-100 text-yellow-800 text-xs font-semibold px-2 py-0.5 rounded-full flex items-center gap-1">
                        <Loader2 className="w-3 h-3 animate-spin" />
                        Prevodi se...
                      </span>
                    ) : (
                      <span className="badge bg-white/90 backdrop-blur text-violet-700 text-xs font-semibold px-2 py-0.5 rounded-full">
                        {pct}% prevedeno
                      </span>
                    )}
                  </div>
                </div>
                <div className="p-4">
                  <Link to={`/documents/${doc.id}`}>
                    <h3 className="font-bold text-gray-900 text-sm line-clamp-2 mb-1 hover:text-violet-600 transition-colors leading-snug">
                      {doc.title}
                    </h3>
                  </Link>
                  <p className="text-xs text-gray-400 mb-3">
                    {isTranslating
                      ? <span className="text-yellow-600 font-medium">{doc.translated_chunks || 0} / {doc.total_chunks} odlomaka prevedeno</span>
                      : `${doc.translated_chunks} / ${doc.total_chunks} odlomaka prevedeno`
                    }
                  </p>
                  <div className="mb-3">
                    <div className="progress-bar">
                      <div
                        className={`progress-fill ${isTranslating ? 'bg-gradient-to-r from-yellow-400 to-orange-400' : 'bg-gradient-to-r from-violet-500 to-purple-500'}`}
                        style={{ width: `${isTranslating ? Math.max(pct, 2) : pct}%` }}
                      />
                    </div>
                  </div>
                  <Link
                    to={`/documents/${doc.id}`}
                    className="btn btn-secondary btn-xs w-full flex items-center justify-center gap-1.5"
                  >
                    {isTranslating ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Eye className="w-3.5 h-3.5" />}
                    {isTranslating ? 'Prati napredak' : 'Pregledaj prevod'}
                  </Link>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
