import { useState, useCallback } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { documentsApi, filesApi } from '@/services/api'
import { useDropzone } from 'react-dropzone'
import { useNavigate } from 'react-router-dom'
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
  X,
  ChevronDown,
  Eye
} from 'lucide-react'
import { Link } from 'react-router-dom'
import clsx from 'clsx'

export default function DocumentsPage() {
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const [page] = useState(1)
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [searchQuery, setSearchQuery] = useState('')
  const [uploadProgress, setUploadProgress] = useState(0)
  const [isUploading, setIsUploading] = useState(false)
  const [selectedProvider, setSelectedProvider] = useState('ollama')
  const [showTranslateModal, setShowTranslateModal] = useState<string | null>(null)
  const [showUpload, setShowUpload] = useState(true)
  const [docTitle, setDocTitle] = useState('')
  const [pendingFile, setPendingFile] = useState<File | null>(null)

  const { data: documents, isLoading } = useQuery({
    queryKey: ['documents', page, statusFilter],
    queryFn: () => documentsApi.list((page - 1) * 10, 10, statusFilter || undefined),
    // Poll every 5s if any document is in an active state
    refetchInterval: (query) => {
      const docs = (query.state.data as any)?.data?.documents || (query.state.data as any)?.data
      if (Array.isArray(docs) && docs.some((d: any) => ['pending', 'processing', 'translating'].includes(d.status))) {
        return 5000
      }
      return false
    },
  })

  const uploadMutation = useMutation({
    mutationFn: async (file: File) => {
      setIsUploading(true)
      setUploadProgress(0)
      const uploadResponse = await filesApi.upload(file, setUploadProgress)
      const fileId: string = uploadResponse.data.id
      // Pass custom title if set, otherwise backend uses filename
      const title = docTitle.trim() || undefined
      const docResponse = await documentsApi.create(fileId, title)
      // NOTE: backend already auto-starts processing in create_document
      return docResponse.data
    },
    onSuccess: (doc) => {
      queryClient.invalidateQueries({ queryKey: ['documents'] })
      toast.success('Dokument uploadovan — obrada je pokrenuta!')
      setShowUpload(false)
      setDocTitle('')
      setPendingFile(null)
      // Navigate to document detail so user can see processing progress
      navigate(`/documents/${doc.id}`)
    },
    onError: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] })
      toast.error('Greška pri upload-u dokumenta')
    },
    onSettled: () => {
      setIsUploading(false)
      setUploadProgress(0)
    },
  })

  const processMutation = useMutation({
    mutationFn: (id: string) => documentsApi.process(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] })
      toast.success('Započeto procesiranje dokumenta')
    },
    onError: () => toast.error('Greška pri procesiranju'),
  })

  const translateMutation = useMutation({
    mutationFn: ({ id, provider }: { id: string; provider: string }) => 
      documentsApi.translate(id, provider),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] })
      toast.success('Započeto prevođenje dokumenta')
      setShowTranslateModal(null)
    },
    onError: () => toast.error('Greška pri prevođenju'),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => documentsApi.delete(id),
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
      if (file.size > 100 * 1024 * 1024) {
        toast.error('Fajl mora biti manji od 100MB')
        return
      }
      // Store file and pre-fill title from filename (without extension)
      setPendingFile(file)
      if (!docTitle.trim()) {
        setDocTitle(file.name.replace(/\.pdf$/i, ''))
      }
    }
  }, [docTitle])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'] },
    maxFiles: 1,
  })

  const getStatusConfig = (status: string) => {
    const configs: Record<string, { badge: string; strip: string; label: string }> = {
      pending:     { badge: 'badge-gray',    strip: 'from-gray-400 to-slate-400',    label: 'Na čekanju' },
      processing:  { badge: 'badge-primary', strip: 'from-indigo-400 to-blue-500',   label: 'Obrađuje se' },
      completed:   { badge: 'badge-success', strip: 'from-emerald-400 to-green-500', label: 'Obrađeno' },
      translating: { badge: 'badge-primary', strip: 'from-violet-400 to-purple-500', label: 'Prevodi se' },
      error:       { badge: 'badge-error',   strip: 'from-red-400 to-rose-500',      label: 'Greška' },
    }
    return configs[status] || configs['pending']
  }

  const filteredDocs = documents?.data?.items?.filter((doc: any) =>
    doc.title.toLowerCase().includes(searchQuery.toLowerCase())
  ) || []

  const providers = [
    { id: 'ollama',   name: 'Ollama (Lokalni)', free: true },
    { id: 'gemini',   name: 'Google Gemini',    free: true },
    { id: 'groq',     name: 'Groq',             free: true },
    { id: 'deepseek', name: 'DeepSeek',         free: false },
    { id: 'openai',   name: 'OpenAI GPT',       free: false },
    { id: 'claude',   name: 'Anthropic Claude', free: false },
    { id: 'mistral',  name: 'Mistral',          free: false },
    { id: 'deepl',    name: 'DeepL',            free: false },
  ]

  const totalDocs = documents?.data?.items?.length || 0
  const completedDocs = documents?.data?.items?.filter((d: any) => d.status === 'completed').length || 0

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Page header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-extrabold text-gray-900">Dokumenti</h1>
          <p className="text-gray-500 mt-1 text-sm">
            {totalDocs} ukupno • {completedDocs} obrađeno
          </p>
        </div>
        <button
          onClick={() => setShowUpload(!showUpload)}
          className="btn-primary"
        >
          <Upload className="w-4 h-4" />
          Dodaj dokument
          <ChevronDown className={clsx('w-4 h-4 transition-transform', showUpload && 'rotate-180')} />
        </button>
      </div>

      {/* Upload zone */}
      {showUpload && (
        <div className="rounded-2xl border border-gray-200 bg-white overflow-hidden">
          {/* Dropzone */}
          <div
            {...getRootProps()}
            className={clsx(
              'border-2 border-dashed m-4 rounded-xl p-8 transition-all cursor-pointer text-center',
              isDragActive
                ? 'border-indigo-400 bg-indigo-50/80 scale-[1.01]'
                : pendingFile
                  ? 'border-emerald-300 bg-emerald-50/50'
                  : 'border-gray-200 hover:border-indigo-300 hover:bg-indigo-50/30',
              isUploading && 'pointer-events-none opacity-80'
            )}
          >
            <input {...getInputProps()} />
            {isUploading ? (
              <div className="flex flex-col items-center">
                <div className="w-14 h-14 rounded-2xl bg-indigo-100 flex items-center justify-center mb-4">
                  <Loader2 className="w-7 h-7 text-indigo-500 animate-spin" />
                </div>
                <p className="text-base font-semibold text-gray-800 mb-1">Uploaduje se...</p>
                <div className="w-56 h-2 bg-gray-100 rounded-full overflow-hidden mb-2">
                  <div
                    className="h-full bg-gradient-to-r from-indigo-500 to-violet-500 transition-all duration-300 rounded-full"
                    style={{ width: `${uploadProgress}%` }}
                  />
                </div>
                <p className="text-sm text-gray-400">{uploadProgress}%</p>
              </div>
            ) : pendingFile ? (
              <div className="flex flex-col items-center">
                <div className="w-14 h-14 rounded-2xl bg-emerald-100 flex items-center justify-center mb-3">
                  <FileText className="w-7 h-7 text-emerald-600" />
                </div>
                <p className="text-base font-semibold text-gray-800 mb-0.5">{pendingFile.name}</p>
                <p className="text-xs text-gray-400">{(pendingFile.size / 1024 / 1024).toFixed(1)} MB • Kliknite da promenite fajl</p>
              </div>
            ) : (
              <div className="flex flex-col items-center">
                <div className={clsx(
                  'w-14 h-14 rounded-2xl flex items-center justify-center mb-4 transition-colors',
                  isDragActive ? 'bg-indigo-100' : 'bg-gray-100'
                )}>
                  <Upload className={clsx('w-7 h-7 transition-colors', isDragActive ? 'text-indigo-500' : 'text-gray-400')} />
                </div>
                <p className="text-base font-semibold text-gray-800 mb-1">
                  {isDragActive ? 'Pustite PDF fajl ovde' : 'Prevucite PDF fajl ovde'}
                </p>
                <p className="text-sm text-gray-400">ili kliknite da izaberete • max 50MB</p>
              </div>
            )}
          </div>

          {/* Title input + confirm button — shown after file is selected */}
          {pendingFile && !isUploading && (
            <div className="px-4 pb-4 flex flex-col sm:flex-row gap-3 items-end">
              <div className="flex-1">
                <label className="block text-xs font-semibold text-gray-600 mb-1.5">Naziv dokumenta</label>
                <input
                  type="text"
                  value={docTitle}
                  onChange={(e) => setDocTitle(e.target.value)}
                  placeholder="Unesite naziv..."
                  className="input rounded-xl w-full"
                  onKeyDown={(e) => e.key === 'Enter' && uploadMutation.mutate(pendingFile)}
                />
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => { setPendingFile(null); setDocTitle('') }}
                  className="btn btn-ghost rounded-xl"
                >
                  Otkaži
                </button>
                <button
                  onClick={() => uploadMutation.mutate(pendingFile)}
                  disabled={uploadMutation.isPending}
                  className="btn-primary rounded-xl"
                >
                  {uploadMutation.isPending ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <><Upload className="w-4 h-4" /> Dodaj dokument</>
                  )}
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Search + filter */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="flex-1 relative">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Pretraži dokumente..."
            className="input pl-11 rounded-2xl"
          />
        </div>
        <div className="relative">
          <Filter className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="input pl-11 pr-10 appearance-none min-w-[180px] rounded-2xl"
          >
            <option value="">Svi statusi</option>
            <option value="pending">Na čekanju</option>
            <option value="completed">Obrađeno</option>
            <option value="error">Greška</option>
          </select>
        </div>
      </div>

      {/* Documents grid */}
      {isLoading ? (
        <div className="flex justify-center py-16">
          <Loader2 className="w-8 h-8 text-indigo-500 animate-spin" />
        </div>
      ) : filteredDocs.length === 0 ? (
        <div className="card p-14 text-center">
          <div className="w-16 h-16 rounded-2xl bg-indigo-50 flex items-center justify-center mx-auto mb-4">
            <FileText className="w-8 h-8 text-indigo-400" />
          </div>
          <p className="text-gray-700 font-semibold mb-1">Nema dokumenata</p>
          <p className="text-sm text-gray-400">Uploadujte PDF da biste počeli</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
          {filteredDocs.map((doc: any) => {
            const cfg = getStatusConfig(doc.status)
            const pct = doc.total_chunks > 0
              ? Math.round(((doc.translated_chunks || 0) / doc.total_chunks) * 100)
              : 0

            return (
              <div key={doc.id} className="course-card hover:shadow-xl hover:-translate-y-0.5 transition-all duration-200">
                {/* Colored header strip */}
                <div className={clsx('h-20 bg-gradient-to-r relative flex items-end px-4 pb-3', cfg.strip)}>
                  <div className="w-10 h-10 rounded-xl bg-white/20 backdrop-blur flex items-center justify-center">
                    <BookOpen className="w-5 h-5 text-white" />
                  </div>
                  <div className="absolute top-3 right-3">
                    <span className={clsx('badge', cfg.badge, 'bg-white/90 backdrop-blur')}>{cfg.label}</span>
                  </div>
                </div>

                {/* Card body */}
                <div className="p-4">
                  <Link to={`/documents/${doc.id}`}>
                    <h3 className="font-bold text-gray-900 text-sm line-clamp-2 mb-1 hover:text-indigo-600 transition-colors leading-snug">
                      {doc.title}
                    </h3>
                  </Link>
                  <p className="text-xs text-gray-400 mb-3">
                    {doc.total_pages} strana • {doc.total_chunks} odlomaka
                  </p>

                  {doc.status === 'completed' && doc.total_chunks > 0 && (
                    <div className="mb-3">
                      <div className="flex justify-between text-xs text-gray-400 mb-1">
                        <span>Prevod</span>
                        <span className="font-medium text-gray-600">{pct}%</span>
                      </div>
                      <div className="progress-bar">
                        <div
                          className="progress-fill bg-gradient-to-r from-indigo-500 to-violet-500"
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                    </div>
                  )}

                  <div className="pt-3 border-t border-gray-100 flex items-center gap-1.5 flex-wrap">
                    {doc.status === 'pending' && (
                      <button
                        onClick={() => processMutation.mutate(doc.id)}
                        disabled={processMutation.isPending}
                        className="btn btn-primary btn-xs flex-1"
                      >
                        {processMutation.isPending ? (
                          <Loader2 className="w-3.5 h-3.5 animate-spin" />
                        ) : (
                          <><RefreshCw className="w-3.5 h-3.5" /> Procesiraj</>
                        )}
                      </button>
                    )}

                    {(doc.status === 'processing') && (
                      <span className="flex items-center gap-1.5 text-xs text-indigo-500 font-medium flex-1">
                        <Loader2 className="w-3.5 h-3.5 animate-spin" /> 
                        {doc.total_pages > 0 
                          ? `Obrađuje se... (~${Math.ceil(doc.total_pages / 5)} min)` 
                          : 'Obrađuje se...'}
                      </span>
                    )}

                    {doc.status === 'translating' && (
                      <>
                        <span className="flex items-center gap-1.5 text-xs text-violet-500 font-medium flex-1">
                          <Loader2 className="w-3.5 h-3.5 animate-spin" /> 
                          {doc.total_chunks > 0 
                            ? `Prevodi se... (~${Math.ceil((doc.total_chunks - (doc.translated_chunks || 0)) / 20)} min)` 
                            : 'Prevodi se...'}
                        </span>
                        <button
                          onClick={() => setShowTranslateModal(doc.id)}
                          title="Ponovi prevod"
                          className="btn btn-ghost btn-xs text-violet-500 hover:bg-violet-50"
                        >
                          <RefreshCw className="w-3.5 h-3.5" />
                        </button>
                      </>
                    )}

                    {doc.status === 'completed' && (
                      <>
                        <button
                          onClick={() => setShowTranslateModal(doc.id)}
                          className="btn btn-secondary btn-xs flex-1"
                        >
                          <Languages className="w-3.5 h-3.5" />
                          Prevedi
                        </button>
                        <Link
                          to={`/review/${doc.id}`}
                          className="btn btn-ghost btn-xs"
                        >
                          <Eye className="w-3.5 h-3.5" />
                        </Link>
                      </>
                    )}

                    <button
                      onClick={() => deleteMutation.mutate(doc.id)}
                      disabled={deleteMutation.isPending}
                      className="btn btn-ghost btn-xs text-red-500 hover:bg-red-50 hover:text-red-600 ml-auto"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* Translate modal */}
      {showTranslateModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-3xl p-6 w-full max-w-sm shadow-2xl animate-slide-down">
            <div className="flex items-center justify-between mb-5">
              <h3 className="text-lg font-bold text-gray-900">Izaberite AI provajdera</h3>
              <button
                onClick={() => setShowTranslateModal(null)}
                className="p-1.5 rounded-xl hover:bg-gray-100 text-gray-500 transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            <div className="space-y-2">
              {providers.map((provider) => (
                <button
                  key={provider.id}
                  onClick={() => {
                    setSelectedProvider(provider.id)
                    translateMutation.mutate({ id: showTranslateModal, provider: provider.id })
                  }}
                  disabled={translateMutation.isPending}
                  className={clsx(
                    'w-full flex items-center justify-between p-3 rounded-xl border-2 transition-all text-left',
                    selectedProvider === provider.id
                      ? 'border-indigo-400 bg-indigo-50'
                      : 'border-gray-100 hover:border-indigo-200 hover:bg-gray-50'
                  )}
                >
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-indigo-100 flex items-center justify-center">
                      <Languages className="w-4 h-4 text-indigo-600" />
                    </div>
                    <div>
                      <p className="text-sm font-semibold text-gray-900">{provider.name}</p>
                      {provider.free && (
                        <p className="text-xs text-emerald-600 font-medium">Besplatno</p>
                      )}
                    </div>
                  </div>
                  {translateMutation.isPending && selectedProvider === provider.id && (
                    <Loader2 className="w-4 h-4 animate-spin text-indigo-500" />
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
