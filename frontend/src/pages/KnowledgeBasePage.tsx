import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { knowledgeApi } from '@/services/api'
import { Brain, Database, Globe, FileText, Plus, Trash2, RefreshCw, Send, Loader2, BookOpen, ChevronRight, AlertCircle } from 'lucide-react'
import toast from 'react-hot-toast'
import clsx from 'clsx'

interface Source {
  id: string
  source_type: string
  name: string
  url?: string
  total_chunks: number
  status: string
  last_indexed?: string
  created_at: string
}

interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  sources?: { name: string; type: string; url?: string }[]
  provider?: string
}

const SOURCE_TYPE_ICON: Record<string, React.ReactNode> = {
  pdf: <FileText className="w-4 h-4 text-red-500" />,
  url: <Globe className="w-4 h-4 text-blue-500" />,
  markdown: <BookOpen className="w-4 h-4 text-green-500" />,
  manual: <Database className="w-4 h-4 text-purple-500" />,
  log: <AlertCircle className="w-4 h-4 text-orange-500" />,
}

const STATUS_COLOR: Record<string, string> = {
  indexed: 'bg-green-100 text-green-700',
  pending: 'bg-yellow-100 text-yellow-700',
  error: 'bg-red-100 text-red-700',
}

export default function KnowledgeBasePage() {
  const qc = useQueryClient()
  const [chat, setChat] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [urlInput, setUrlInput] = useState('')
  const [crawlRecursive, setCrawlRecursive] = useState(false)
  const [crawlDepth, setCrawlDepth] = useState(2)
  const [crawlMaxPages, setCrawlMaxPages] = useState(30)
  const [showAddURL, setShowAddURL] = useState(false)
  const [activeTab, setActiveTab] = useState<'chat' | 'sources'>('chat')
  const [selectedProvider, setSelectedProvider] = useState('auto')
  const [pendingProvider, setPendingProvider] = useState('Auto')

const AI_PROVIDERS = [
    { id: 'auto',    label: 'Auto',           emoji: '🤖' },
    { id: 'ollamas',  label: 'Ollama (lokalni)', emoji: '🖥️' },
    { id: 'gemini',  label: 'Gemini',          emoji: '✨' },
    { id: 'groq',    label: 'Groq',            emoji: '⚡' },
    { id: 'openai',  label: 'OpenAI',          emoji: '🔵' },
    { id: 'claude',  label: 'Claude',          emoji: '🟠' },
    { id: 'mistral', label: 'Mistral',         emoji: '🌊' },
    { id: 'deepseek', label: 'DeepSeek',        emoji: '🔮' },
  ]

  const { data: statsData } = useQuery({
    queryKey: ['knowledge-stats'],
    queryFn: () => knowledgeApi.stats(),
    refetchInterval: 10000,
  })
  const stats = (statsData as any)?.data

  const { data: sourcesData, isLoading: sourcesLoading } = useQuery({
    queryKey: ['knowledge-sources'],
    queryFn: () => knowledgeApi.sources(),
    enabled: activeTab === 'sources',
  })
  const sources: Source[] = (sourcesData as any)?.data ?? []

  const queryMutation = useMutation({
    mutationFn: (query: string) => knowledgeApi.query(query, 5, selectedProvider === 'auto' ? undefined : selectedProvider),
    onSuccess: (res) => {
      const data = (res as any).data
      setChat(prev => [...prev, {
        role: 'assistant',
        content: data.answer,
        sources: data.sources,
        provider: pendingProvider,
      }])
    },
    onError: () => {
      setChat(prev => [...prev, {
        role: 'assistant',
        content: 'Greška pri komunikaciji sa AI-jem. Pokušaj ponovo.',
      }])
    },
  })

  const ingestUrlMutation = useMutation({
    mutationFn: (url: string) => knowledgeApi.ingestUrl(url, {
      recursive: crawlRecursive,
      max_depth: crawlDepth,
      max_pages: crawlMaxPages,
    }),
    onSuccess: () => {
      toast.success('URL dodat u red za indeksiranje')
      setUrlInput('')
      setShowAddURL(false)
      qc.invalidateQueries({ queryKey: ['knowledge-sources'] })
      qc.invalidateQueries({ queryKey: ['knowledge-stats'] })
    },
    onError: () => toast.error('Greška pri dodavanju URL-a'),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => knowledgeApi.deleteSource(id),
    onSuccess: () => {
      toast.success('Izvor uklonjen')
      qc.invalidateQueries({ queryKey: ['knowledge-sources'] })
      qc.invalidateQueries({ queryKey: ['knowledge-stats'] })
    },
    onError: () => toast.error('Greška pri uklanjanju izvora'),
  })

  const reindexMutation = useMutation({
    mutationFn: () => knowledgeApi.reindex(),
    onSuccess: () => toast.success('Re-indeksiranje pokrenuto'),
  })

  const sendMessage = () => {
    if (!input.trim() || queryMutation.isPending) return
    const msg = input.trim()
    const providerLabel = AI_PROVIDERS.find(p => p.id === selectedProvider)?.label || selectedProvider
    setChat(prev => [...prev, { role: 'user', content: msg }])
    setInput('')
    queryMutation.mutate(msg)
    // Track which provider was used for this message
    setPendingProvider(providerLabel)
  }

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-1">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
            <Brain className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Baza Znanja</h1>
            <p className="text-sm text-gray-500">Lokalni AI sistem koji uči iz vaše dokumentacije</p>
          </div>
        </div>
      </div>

      {/* Stats bar */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
          {[
            { label: 'Ukupno izvora', value: stats.total_sources, color: 'text-indigo-600' },
            { label: 'Indeksirano', value: stats.indexed_sources, color: 'text-green-600' },
            { label: 'Chunk-ova', value: stats.total_chunks?.toLocaleString(), color: 'text-purple-600' },
            { label: 'Greške', value: stats.error_sources, color: 'text-red-600' },
          ].map((s) => (
            <div key={s.label} className="bg-white rounded-xl border border-gray-100 p-3 text-center shadow-sm">
              <div className={clsx('text-2xl font-bold', s.color)}>{s.value ?? 0}</div>
              <div className="text-xs text-gray-500 mt-0.5">{s.label}</div>
            </div>
          ))}
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-1 bg-gray-100 rounded-xl p-1 mb-4 w-fit">
        {(['chat', 'sources'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={clsx(
              'px-4 py-2 rounded-lg text-sm font-medium transition-all',
              activeTab === tab ? 'bg-white shadow-sm text-gray-900' : 'text-gray-500 hover:text-gray-700'
            )}
          >
            {tab === 'chat' ? '💬 Pitaj AI' : '📚 Izvori'}
          </button>
        ))}
      </div>

      {/* CHAT TAB */}
      {activeTab === 'chat' && (
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
          {/* Messages */}
          <div className="h-[460px] overflow-y-auto p-6 flex flex-col gap-4">
            {chat.length === 0 && (
              <div className="flex flex-col items-center justify-center h-full text-center text-gray-400 gap-3">
                <Brain className="w-12 h-12 text-indigo-200" />
                <div>
                  <p className="font-medium text-gray-600">Pitaj AI o bilo čemu iz dokumentacije</p>
                  <p className="text-sm mt-1">AI pretražuje svu indeksiranu dokumentaciju i daje precizne odgovore</p>
                </div>
                <div className="flex flex-wrap gap-2 mt-2 justify-center">
                  {['Kako funkcioniše Docker?', 'Objasni JWT autentikaciju', 'Šta je RAG sistem?'].map(q => (
                    <button
                      key={q}
                      onClick={() => { setInput(q); }}
                      className="text-xs px-3 py-1.5 rounded-full bg-indigo-50 text-indigo-600 hover:bg-indigo-100 border border-indigo-100"
                    >
                      {q}
                    </button>
                  ))}
                </div>
              </div>
            )}
            {chat.map((msg, i) => (
              <div key={i} className={clsx('flex', msg.role === 'user' ? 'justify-end' : 'justify-start')}>
                <div className={clsx(
                  'max-w-[80%] rounded-2xl px-4 py-3',
                  msg.role === 'user'
                    ? 'bg-indigo-600 text-white rounded-br-sm'
                    : 'bg-gray-50 border border-gray-100 text-gray-700 rounded-bl-sm'
                )}>
                  {msg.role === 'assistant' && msg.provider && (
                    <p className="text-xs text-indigo-400 font-medium mb-1.5">🤖 {msg.provider}</p>
                  )}
                  <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.content}</p>
                  {msg.sources && msg.sources.length > 0 && (
                    <div className="mt-2 pt-2 border-t border-gray-200">
                      <p className="text-xs text-gray-400 mb-1">Izvori:</p>
                      {msg.sources.map((s, j) => (
                        <div key={j} className="flex items-center gap-1 text-xs text-gray-500">
                          <ChevronRight className="w-3 h-3" />
                          {s.url ? <a href={s.url} target="_blank" rel="noopener noreferrer" className="hover:underline">{s.name}</a> : <span>{s.name}</span>}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}
            {queryMutation.isPending && (
              <div className="flex justify-start">
                <div className="bg-gray-50 border border-gray-100 rounded-2xl rounded-bl-sm px-4 py-3">
                  <Loader2 className="w-4 h-4 animate-spin text-indigo-400" />
                </div>
              </div>
            )}
          </div>

          {/* Provider selector + input */}
          <div className="border-t border-gray-100 p-4 space-y-3">
            {/* Provider chips */}
            <div className="flex items-center gap-1.5 flex-wrap">
              <span className="text-xs text-gray-400 font-medium mr-1">AI:</span>
              {AI_PROVIDERS.map(p => (
                <button
                  key={p.id}
                  onClick={() => setSelectedProvider(p.id)}
                  className={clsx(
                    'px-2.5 py-1 rounded-full text-xs font-medium transition-all border',
                    selectedProvider === p.id
                      ? 'bg-indigo-600 text-white border-indigo-600'
                      : 'bg-white text-gray-500 border-gray-200 hover:border-indigo-300 hover:text-indigo-600'
                  )}
                >
                  {p.emoji} {p.label}
                </button>
              ))}
            </div>
            {/* Message input */}
            <div className="flex gap-3">
              <input
                type="text"
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && !e.shiftKey && sendMessage()}
                placeholder="Postavi pitanje o dokumentaciji..."
                className="flex-1 px-4 py-2.5 rounded-xl border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300"
                disabled={queryMutation.isPending}
              />
              <button
                onClick={sendMessage}
                disabled={!input.trim() || queryMutation.isPending}
                className="px-4 py-2.5 rounded-xl bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-40 transition-colors"
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      )}

      {/* SOURCES TAB */}
      {activeTab === 'sources' && (
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm">
          {/* Toolbar */}
          <div className="flex items-center justify-between p-4 border-b border-gray-100">
            <span className="text-sm font-medium text-gray-700">{sources.length} izvora</span>
            <div className="flex gap-2">
              <button
                onClick={() => reindexMutation.mutate()}
                disabled={reindexMutation.isPending}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs rounded-lg border border-gray-200 hover:bg-gray-50 text-gray-600"
              >
                <RefreshCw className={clsx('w-3 h-3', reindexMutation.isPending && 'animate-spin')} />
                Re-indeksiraj
              </button>
              <button
                onClick={() => setShowAddURL(!showAddURL)}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs rounded-lg bg-indigo-600 text-white hover:bg-indigo-700"
              >
                <Plus className="w-3 h-3" />
                Dodaj URL
              </button>
            </div>
          </div>

          {/* Add URL form */}
          {showAddURL && (
            <div className="p-4 bg-indigo-50 border-b border-indigo-100 space-y-3">
              {/* URL input row */}
              <div className="flex gap-2">
                <input
                  type="url"
                  value={urlInput}
                  onChange={e => setUrlInput(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && urlInput && ingestUrlMutation.mutate(urlInput)}
                  placeholder="https://docs.example.com/..."
                  className="flex-1 px-3 py-2 text-sm rounded-lg border border-indigo-200 focus:outline-none focus:ring-2 focus:ring-indigo-300 bg-white"
                />
                <button
                  onClick={() => urlInput && ingestUrlMutation.mutate(urlInput)}
                  disabled={!urlInput || ingestUrlMutation.isPending}
                  className="px-4 py-2 text-sm rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-40 flex items-center gap-1.5"
                >
                  {ingestUrlMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Dodaj'}
                </button>
              </div>

              {/* Recursive options */}
              <div className="flex flex-wrap items-center gap-4">
                <label className="flex items-center gap-2 cursor-pointer select-none">
                  <input
                    type="checkbox"
                    checked={crawlRecursive}
                    onChange={e => setCrawlRecursive(e.target.checked)}
                    className="w-4 h-4 rounded accent-indigo-600"
                  />
                  <span className="text-sm text-gray-700 font-medium">Rekurzivni crawler</span>
                  <span className="text-xs text-gray-400">(prati linkove unutar domena)</span>
                </label>

                {crawlRecursive && (
                  <>
                    <label className="flex items-center gap-2 text-sm text-gray-600">
                      Dubina:
                      <select
                        value={crawlDepth}
                        onChange={e => setCrawlDepth(Number(e.target.value))}
                        className="px-2 py-1 rounded border border-indigo-200 bg-white text-sm"
                      >
                        <option value={1}>1 — samo ova stranica</option>
                        <option value={2}>2 — stranica + linkovi</option>
                        <option value={3}>3 — duboko (sporo)</option>
                      </select>
                    </label>
                    <label className="flex items-center gap-2 text-sm text-gray-600">
                      Max stranica:
                      <select
                        value={crawlMaxPages}
                        onChange={e => setCrawlMaxPages(Number(e.target.value))}
                        className="px-2 py-1 rounded border border-indigo-200 bg-white text-sm"
                      >
                        <option value={10}>10</option>
                        <option value={30}>30</option>
                        <option value={50}>50</option>
                        <option value={100}>100</option>
                      </select>
                    </label>
                  </>
                )}
              </div>

              {crawlRecursive && (
                <p className="text-xs text-amber-600 flex items-center gap-1">
                  ⚠️ Rekurzivni crawler može potrajati nekoliko minuta zavisno od broja stranica.
                </p>
              )}
            </div>
          )}

          {/* Sources list */}
          {sourcesLoading ? (
            <div className="p-8 flex justify-center"><Loader2 className="w-6 h-6 animate-spin text-indigo-400" /></div>
          ) : sources.length === 0 ? (
            <div className="p-8 text-center text-gray-400">
              <Database className="w-10 h-10 mx-auto mb-2 text-gray-200" />
              <p>Baza znanja je prazna. Uploaduj PDF ili dodaj URL.</p>
            </div>
          ) : (
            <div className="divide-y divide-gray-50">
              {sources.map(src => (
                <div key={src.id} className="flex items-center gap-3 px-4 py-3 hover:bg-gray-50">
                  <div className="flex-shrink-0">{SOURCE_TYPE_ICON[src.source_type] ?? <Database className="w-4 h-4" />}</div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-800 truncate">{src.name}</p>
                    {src.url && <p className="text-xs text-gray-400 truncate">{src.url}</p>}
                  </div>
                  <span className={clsx('text-xs px-2 py-0.5 rounded-full font-medium', STATUS_COLOR[src.status] ?? 'bg-gray-100 text-gray-600')}>
                    {src.status}
                  </span>
                  <span className="text-xs text-gray-400 w-16 text-right">{src.total_chunks} chunks</span>
                  <button
                    onClick={() => deleteMutation.mutate(src.id)}
                    className="p-1 rounded hover:bg-red-50 text-gray-300 hover:text-red-400"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
