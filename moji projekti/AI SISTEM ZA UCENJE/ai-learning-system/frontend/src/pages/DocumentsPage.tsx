import { useState, useCallback } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { documentsApi, filesApi } from '@/services/api'
import { useDropzone } from 'react-dropzone'
import toast from 'react-hot-toast'
import {
  Upload,
  FileText,
  Trash2,
  Languages,
  RefreshCw,
  Search,
  Filter,
  BookOpen,
  Loader2,
  File,
  Clock,
  CheckCircle2,
  AlertCircle,
  ChevronRight,
  Grid3X3,
  List,
  ArrowUpRight,
  Sparkles,
  X
} from 'lucide-react'
import { Link } from 'react-router-dom'
import clsx from 'clsx'

export default function DocumentsPage() {
  const queryClient = useQueryClient()
  const [page, setPage] = useState(1)
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [searchQuery, setSearchQuery] = useState('')
  const [uploadProgress, setUploadProgress] = useState(0)
  const [isUploading, setIsUploading] = useState(false)
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid')
  const [showTranslateModal, setShowTranslateModal] = useState<number | null>(null)

  const { data: documents, isLoading } = useQuery({
    queryKey: ['documents', page, statusFilter],
    queryFn: () => documentsApi.list(page, 20, statusFilter || undefined),
  })

  const uploadMutation = useMutation({
    mutationFn: async (file: File) => {
      setIsUploading(true)
      setUploadProgress(0)
      const uploadResponse = await filesApi.upload(file, setUploadProgress)
      const fileId = uploadResponse.data.id
      const docResponse = await documentsApi.create(fileId)
      return docResponse.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] })
      toast.success('Dokument je uspešno uploadovan!')
    },
    onError: () => toast.error('Greška pri upload-u dokumenta'),
    onSettled: () => {
      setIsUploading(false)
      setUploadProgress(0)
    },
  })

  const processMutation = useMutation({
    mutationFn: (id: number) => documentsApi.process(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] })
      toast.success('Započeto procesiranje dokumenta')
    },
    onError: () => toast.error('Greška pri procesiranju'),
  })

  const translateMutation = useMutation({
    mutationFn: ({ id, provider }: { id: number; provider: string }) =>
      documentsApi.translate(id, provider),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] })
      toast.success('Započeto prevođenje dokumenta')
      setShowTranslateModal(null)
    },
    onError: () => toast.error('Greška pri prevođenju'),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => documentsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] })
      toast.success('Dokument je obrisan')
    },
    onError: () => toast.error('Greška pri brisanju'),
  })

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const file = acceptedFiles[0]
    if (file) {
      if (file.type !== 'application/pdf') {
        toast.error('Dozvoljeni su samo PDF fajlovi')
        return
      }
      if (file.size > 50 * 1024 * 1024) {
        toast.error('Fajl mora biti manji od 50MB')
        return
      }
      uploadMutation.mutate(file)
    }
  }, [uploadMutation])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'] },
    maxFiles: 1,
  })

  const getStatusConfig = (status: string) => {
    const configs: Record<string, { label: string; color: string; bgColor: string; icon: any }> = {
      pending: { label: 'Na čekanju', color: 'text-gray-600', bgColor: 'bg-gray-100', icon: Clock },
      processing: { label: 'Obrađuje se', color: 'text-blue-600', bgColor: 'bg-blue-100', icon: Loader2 },
      processed: { label: 'Spremno', color: 'text-green-600', bgColor: 'bg-green-100', icon: CheckCircle2 },
      translating: { label: 'Prevodi se', color: 'text-purple-600', bgColor: 'bg-purple-100', icon: Loader2 },
      translated: { label: 'Prevedeno', color: 'text-emerald-600', bgColor: 'bg-emerald-100', icon: CheckCircle2 },
      error: { label: 'Greška', color: 'text-red-600', bgColor: 'bg-red-100', icon: AlertCircle },
    }
    return configs[status] || configs.pending
  }

  const filteredDocs = documents?.data?.documents?.filter((doc: any) =>
    doc.title.toLowerCase().includes(searchQuery.toLowerCase())
  ) || []

  const providers = [
    { id: 'ollama', name: 'Ollama', desc: 'Lokalni, besplatni', free: true, color: 'from-green-500 to-emerald-600' },
    { id: 'deepl', name: 'DeepL', desc: 'Visoki kvalitet', free: false, color: 'from-blue-500 to-blue-600' },
    { id: 'openai', name: 'OpenAI GPT', desc: 'GPT-4 Turbo', free: false, color: 'from-purple-500 to-purple-600' },
    { id: 'google', name: 'Google Translate', desc: 'Brzo i pouzdano', free: false, color: 'from-red-500 to-orange-500' },
    { id: 'claude', name: 'Claude', desc: 'Anthropic AI', free: false, color: 'from-orange-500 to-amber-500' },
  ]

  const stats = {
    total: documents?.data?.total || filteredDocs.length,
    processing: filteredDocs.filter((d: any) => d.status === 'processing' || d.status === 'translating').length,
    completed: filteredDocs.filter((d: any) => d.status === 'translated').length,
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Biblioteka dokumenata</h1>
          <p className="text-gray-500 mt-1">Upravljajte svojim PDF dokumentima i prevodima</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setViewMode('grid')}
            className={clsx(
              'p-2 rounded-lg transition-colors',
              viewMode === 'grid' ? 'bg-primary-100 text-primary-600' : 'text-gray-400 hover:bg-gray-100'
            )}
          >
            <Grid3X3 className="w-5 h-5" />
          </button>
          <button
            onClick={() => setViewMode('list')}
            className={clsx(
              'p-2 rounded-lg transition-colors',
              viewMode === 'list' ? 'bg-primary-100 text-primary-600' : 'text-gray-400 hover:bg-gray-100'
            )}
          >
            <List className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4">
        <div className="card p-4 text-center">
          <p className="text-3xl font-bold text-gray-900">{stats.total}</p>
          <p className="text-sm text-gray-500">Ukupno</p>
        </div>
        <div className="card p-4 text-center">
          <p className="text-3xl font-bold text-blue-600">{stats.processing}</p>
          <p className="text-sm text-gray-500">U obradi</p>
        </div>
        <div className="card p-4 text-center">
          <p className="text-3xl font-bold text-green-600">{stats.completed}</p>
          <p className="text-sm text-gray-500">Završeno</p>
        </div>
      </div>

      {/* Upload Area */}
      <div
        {...getRootProps()}
        className={clsx(
          "relative overflow-hidden rounded-2xl border-2 border-dashed transition-all cursor-pointer",
          isDragActive
            ? "border-primary-500 bg-primary-50"
            : "border-gray-200 bg-gradient-to-r from-gray-50 to-white hover:border-primary-300 hover:from-primary-50/50",
          isUploading && "pointer-events-none"
        )}
      >
        {isDragActive && (
          <div className="absolute inset-0 bg-gradient-to-r from-primary-500/10 to-accent-500/10 animate-pulse" />
        )}
        <input {...getInputProps()} />
        <div className="p-8 flex items-center gap-6">
          <div className={clsx(
            "w-16 h-16 rounded-2xl flex items-center justify-center flex-shrink-0 transition-all",
            isDragActive
              ? "bg-primary-500 text-white"
              : "bg-gradient-to-br from-primary-500 to-accent-500 text-white shadow-lg"
          )}>
            {isUploading ? (
              <Loader2 className="w-7 h-7 animate-spin" />
            ) : (
              <Upload className="w-7 h-7" />
            )}
          </div>
          <div className="flex-1">
            {isUploading ? (
              <>
                <p className="font-semibold text-gray-900 mb-2">Uploaduje se...</p>
                <div className="flex items-center gap-3">
                  <div className="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-primary-500 to-accent-500 rounded-full transition-all duration-300"
                      style={{ width: `${uploadProgress}%` }}
                    />
                  </div>
                  <span className="text-sm font-medium text-gray-600">{uploadProgress}%</span>
                </div>
              </>
            ) : (
              <>
                <p className="font-semibold text-gray-900 mb-1">
                  {isDragActive ? 'Pustite fajl ovde' : 'Dodajte novi dokument'}
                </p>
                <p className="text-sm text-gray-500">
                  Prevucite PDF fajl ili kliknite da izaberete • Max 50MB
                </p>
              </>
            )}
          </div>
          {!isUploading && (
            <div className="hidden md:flex items-center gap-2 text-primary-600">
              <Sparkles className="w-4 h-4" />
              <span className="text-sm font-medium">AI prevođenje</span>
            </div>
          )}
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="flex-1 relative">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Pretraži dokumente..."
            className="input pl-12"
          />
        </div>
        <div className="relative">
          <Filter className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="input pl-12 pr-10 appearance-none min-w-[180px]"
          >
            <option value="">Svi statusi</option>
            <option value="pending">Na čekanju</option>
            <option value="processed">Spremno</option>
            <option value="translated">Prevedeno</option>
            <option value="error">Greška</option>
          </select>
        </div>
      </div>

      {/* Documents */}
      {isLoading ? (
        <div className="flex justify-center py-16">
          <Loader2 className="w-8 h-8 text-primary-500 animate-spin" />
        </div>
      ) : filteredDocs.length === 0 ? (
        <div className="card p-16 text-center">
          <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-gray-100 to-gray-50 flex items-center justify-center mx-auto mb-4">
            <FileText className="w-10 h-10 text-gray-300" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Nema dokumenata</h3>
          <p className="text-gray-500 mb-6">Uploadujte svoj prvi PDF dokument da biste počeli</p>
        </div>
      ) : viewMode === 'grid' ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredDocs.map((doc: any, i: number) => {
            const statusConfig = getStatusConfig(doc.status)
            return (
              <div
                key={doc.id}
                className="card p-5 hover:shadow-lg transition-all duration-300 group animate-slide-up"
                style={{ animationDelay: `${i * 50}ms` }}
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary-100 to-accent-100 flex items-center justify-center">
                    <File className="w-6 h-6 text-primary-600" />
                  </div>
                  <div className={clsx(
                    'flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium',
                    statusConfig.bgColor, statusConfig.color
                  )}>
                    <statusConfig.icon className={clsx('w-3.5 h-3.5', doc.status === 'processing' || doc.status === 'translating' ? 'animate-spin' : '')} />
                    {statusConfig.label}
                  </div>
                </div>

                <Link to={`/documents/${doc.id}`} className="block mb-3">
                  <h3 className="font-semibold text-gray-900 group-hover:text-primary-600 transition-colors line-clamp-2">
                    {doc.title}
                  </h3>
                </Link>

                <div className="flex items-center gap-4 text-sm text-gray-500 mb-4">
                  <span className="flex items-center gap-1">
                    <BookOpen className="w-4 h-4" />
                    {doc.total_pages || 0} str.
                  </span>
                  <span className="flex items-center gap-1">
                    <FileText className="w-4 h-4" />
                    {doc.total_chunks || doc.chunks_count || 0} seg.
                  </span>
                </div>

                <div className="flex items-center gap-2">
                  {doc.status === 'pending' && (
                    <button
                      onClick={() => processMutation.mutate(doc.id)}
                      disabled={processMutation.isPending}
                      className="btn-sm btn-primary flex-1"
                    >
                      <RefreshCw className="w-4 h-4" />
                      Procesiraj
                    </button>
                  )}
                  {(doc.status === 'processed' || doc.status === 'translated') && (
                    <>
                      <button
                        onClick={() => setShowTranslateModal(doc.id)}
                        className="btn-sm btn-secondary flex-1"
                      >
                        <Languages className="w-4 h-4" />
                        Prevedi
                      </button>
                      <Link
                        to={`/review/${doc.id}`}
                        className="btn-sm btn-ghost"
                      >
                        <ArrowUpRight className="w-4 h-4" />
                      </Link>
                    </>
                  )}
                  <button
                    onClick={() => deleteMutation.mutate(doc.id)}
                    disabled={deleteMutation.isPending}
                    className="btn-sm btn-ghost text-red-500 hover:bg-red-50"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            )
          })}
        </div>
      ) : (
        <div className="card divide-y divide-gray-100">
          {filteredDocs.map((doc: any) => {
            const statusConfig = getStatusConfig(doc.status)
            return (
              <div key={doc.id} className="flex items-center gap-4 p-4 hover:bg-gray-50 transition-colors group">
                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary-100 to-accent-100 flex items-center justify-center flex-shrink-0">
                  <File className="w-6 h-6 text-primary-600" />
                </div>
                <div className="flex-1 min-w-0">
                  <Link to={`/documents/${doc.id}`} className="font-medium text-gray-900 hover:text-primary-600">
                    {doc.title}
                  </Link>
                  <p className="text-sm text-gray-500">
                    {doc.total_pages || 0} strana • {doc.total_chunks || doc.chunks_count || 0} segmenata
                  </p>
                </div>
                <div className={clsx(
                  'flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium',
                  statusConfig.bgColor, statusConfig.color
                )}>
                  <statusConfig.icon className={clsx('w-3.5 h-3.5', doc.status === 'processing' || doc.status === 'translating' ? 'animate-spin' : '')} />
                  {statusConfig.label}
                </div>
                <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  <Link to={`/documents/${doc.id}`} className="p-2 rounded-lg hover:bg-gray-100">
                    <ChevronRight className="w-5 h-5 text-gray-400" />
                  </Link>
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* Translate Modal */}
      {showTranslateModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="card p-6 w-full max-w-md animate-scale-in">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-semibold text-gray-900">Izaberite prevodioca</h3>
              <button
                onClick={() => setShowTranslateModal(null)}
                className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
              >
                <X className="w-5 h-5 text-gray-400" />
              </button>
            </div>
            <div className="space-y-2">
              {providers.map((provider) => (
                <button
                  key={provider.id}
                  onClick={() => translateMutation.mutate({ id: showTranslateModal, provider: provider.id })}
                  disabled={translateMutation.isPending}
                  className="w-full flex items-center gap-4 p-4 rounded-xl border-2 border-gray-100 hover:border-primary-200 hover:bg-primary-50/50 transition-all group"
                >
                  <div className={clsx('w-10 h-10 rounded-xl bg-gradient-to-br flex items-center justify-center text-white', provider.color)}>
                    <Languages className="w-5 h-5" />
                  </div>
                  <div className="flex-1 text-left">
                    <p className="font-medium text-gray-900">{provider.name}</p>
                    <p className="text-sm text-gray-500">{provider.desc}</p>
                  </div>
                  {provider.free && (
                    <span className="px-2 py-1 rounded-full bg-green-100 text-green-700 text-xs font-medium">
                      Besplatno
                    </span>
                  )}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
