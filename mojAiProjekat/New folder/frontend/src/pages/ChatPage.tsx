/**
 * ================================================================================
 * Petar II Petrović-Njegoš
 * "Blago tome ko dovijek živi, imao se rašta i roditi"
 * ================================================================================
 * 
 * AI Learning System
 * ChatPage.tsx
 * Verzija: 1.0.0
 * Autor: Branko Suznjevic
 * Datum: 2026
 * ================================================================================
 */

import { useState, useEffect, useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '@/services/api'
import toast from 'react-hot-toast'
import { 
  MessageSquare, 
  Send, 
  Plus, 
  Trash2, 
  Brain,
  Bot,
  User,
  Loader2,
  ChevronDown,
  Sparkles,
  Copy
} from 'lucide-react'
import clsx from 'clsx'

interface Message {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  tool_calls?: any[]
  tool_results?: any[]
  thinking?: string
  created_at: string
}

interface Conversation {
  id: string
  title: string
  provider: string
  is_active: boolean
  thinking_enabled: boolean
  enabled_tools?: string[]
  created_at: string
  updated_at: string
  message_count: number
}

interface Provider {
  id: string
  name: string
  available: boolean
  supports_tools: boolean
  supports_thinking: boolean
  default_model: string
}

const DEFAULT_TOOLS = [
  { id: 'search_knowledge', name: 'Baza Znanja', enabled: true },
  { id: 'translate_text', name: 'Prevod', enabled: true },
  { id: 'generate_quiz', name: 'Generisi Kviz', enabled: true },
  { id: 'get_document_summary', name: 'Rezime Dokumenta', enabled: true },
  { id: 'search_documents', name: 'Pretraga Dokumenata', enabled: true },
]

export default function ChatPage() {
  const queryClient = useQueryClient()
  const messagesEndRef = useRef<HTMLDivElement>(null)
  
  const [input, setInput] = useState('')
  const [selectedProvider, setSelectedProvider] = useState('auto')
  const [thinkingEnabled, setThinkingEnabled] = useState(false)
  const [selectedTools, setSelectedTools] = useState<string[]>(DEFAULT_TOOLS.filter(t => t.enabled).map(t => t.id))
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(null)

  // Fetch conversations
  const { data: conversations = [] } = useQuery<Conversation[]>({
    queryKey: ['chat-conversations'],
    queryFn: () => api.get('/chat/conversations').then(res => res.data)
  })

  // Fetch current conversation messages
  const { data: conversationDetail, refetch: refetchMessages } = useQuery<any>({
    queryKey: ['chat-conversation', currentConversationId],
    queryFn: () => api.get(`/chat/conversations/${currentConversationId}`).then(res => res.data),
    enabled: !!currentConversationId
  })

  // Fetch providers
  const { data: providersData } = useQuery<{ providers: Provider[] }>({
    queryKey: ['chat-providers'],
    queryFn: () => api.get('/chat/providers').then(res => res.data)
  })

  const providers = providersData?.providers || []

  // Send message mutation
  const sendMessageMutation = useMutation({
    mutationFn: (data: { message: string; conversation_id?: string; provider: string; thinking: boolean; tools: string[] }) =>
      api.post('/chat/chat', data),
    onSuccess: (response) => {
      queryClient.invalidateQueries({ queryKey: ['chat-conversations'] })
      queryClient.invalidateQueries({ queryKey: ['chat-conversation', currentConversationId] })
      refetchMessages()
      setCurrentConversationId(response.data.conversation_id)
    },
    onError: () => {
      toast.error('Greška pri slanju poruke')
    }
  })

  // Create conversation mutation
  const createConversationMutation = useMutation({
    mutationFn: (data: { title: string; provider: string; thinking_enabled: boolean; enabled_tools: string[] }) =>
      api.post('/chat/conversations', data),
    onSuccess: (response) => {
      queryClient.invalidateQueries({ queryKey: ['chat-conversations'] })
      setCurrentConversationId(response.data.id)
    }
  })

  // Delete conversation mutation
  const deleteConversationMutation = useMutation({
    mutationFn: (id: string) => api.delete(`/chat/conversations/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['chat-conversations'] })
      if (currentConversationId) {
        setCurrentConversationId(null)
      }
    }
  })

  const messages: Message[] = conversationDetail?.messages || []

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = async () => {
    if (!input.trim()) return

    const message = input.trim()
    setInput('')

    try {
      await sendMessageMutation.mutateAsync({
        message,
        conversation_id: currentConversationId || undefined,
        provider: selectedProvider,
        thinking: thinkingEnabled,
        tools: selectedTools
      })
    } catch (error) {
      console.error(error)
    }
  }

  const handleNewConversation = async () => {
    try {
      const result = await createConversationMutation.mutateAsync({
        title: 'Nova konverzacija',
        provider: selectedProvider,
        thinking_enabled: thinkingEnabled,
        enabled_tools: selectedTools
      })
      setCurrentConversationId(result.data.id)
    } catch (error) {
      console.error(error)
    }
  }

  const handleDeleteConversation = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation()
    if (confirm('Da li želite da obrišete ovu konverzaciju?')) {
      deleteConversationMutation.mutate(id)
    }
  }

  const toggleTool = (toolId: string) => {
    setSelectedTools(prev => 
      prev.includes(toolId) 
        ? prev.filter(t => t !== toolId)
        : [...prev, toolId]
    )
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
    toast.success('Kopirano!')
  }

  const currentProvider = providers.find(p => p.id === selectedProvider)

  return (
    <div className="flex h-[calc(100vh-4rem)]">
      {/* Sidebar */}
      <div className="w-64 bg-white border-r border-gray-200 flex flex-col">
        <div className="p-4 border-b border-gray-200">
          <button
            onClick={handleNewConversation}
            className="w-full btn-primary flex items-center justify-center gap-2"
          >
            <Plus className="w-5 h-5" />
            Nova konverzacija
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-2">
          {conversations.map(conv => (
            <div
              key={conv.id}
              onClick={() => setCurrentConversationId(conv.id)}
              className={clsx(
                'group p-3 rounded-lg cursor-pointer mb-1',
                currentConversationId === conv.id 
                  ? 'bg-indigo-50 border-indigo-200 border' 
                  : 'hover:bg-gray-50'
              )}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-sm text-gray-900 truncate">
                    {conv.title}
                  </p>
                  <p className="text-xs text-gray-500">
                    {new Date(conv.updated_at).toLocaleDateString('sr-RS')}
                  </p>
                </div>
                <button
                  onClick={(e) => handleDeleteConversation(conv.id, e)}
                  className="opacity-0 group-hover:opacity-100 p-1 hover:bg-red-100 rounded text-red-500 transition-opacity"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}

          {conversations.length === 0 && (
            <p className="text-center text-gray-500 text-sm py-8">
              Nema konverzacija
            </p>
          )}
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col bg-gray-50">
        {/* Header with settings */}
        <div className="bg-white border-b border-gray-200 p-4">
          <div className="flex items-center justify-between">
            <h1 className="text-xl font-bold text-gray-900 flex items-center gap-2">
              <MessageSquare className="w-6 h-6 text-indigo-600" />
              AI Chat
            </h1>
            
            <div className="flex items-center gap-3">
              {/* Provider Select */}
              <div className="relative">
                <select
                  value={selectedProvider}
                  onChange={(e) => setSelectedProvider(e.target.value)}
                  className="appearance-none bg-gray-50 border border-gray-200 rounded-lg px-4 py-2 pr-10 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="auto">Auto</option>
                  {providers.map(p => (
                    <option key={p.id} value={p.id} disabled={!p.available}>
                      {p.name} {!p.available && '(nedostupan)'}
                    </option>
                  ))}
                </select>
                <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
              </div>

              {/* Thinking Toggle */}
              {currentProvider?.supports_thinking && (
                <button
                  onClick={() => setThinkingEnabled(!thinkingEnabled)}
                  className={clsx(
                    'flex items-center gap-2 px-3 py-2 rounded-lg border text-sm',
                    thinkingEnabled 
                      ? 'bg-purple-50 border-purple-200 text-purple-700' 
                      : 'bg-gray-50 border-gray-200 text-gray-600'
                  )}
                >
                  <Brain className="w-4 h-4" />
                  Thinking
                </button>
              )}
            </div>
          </div>

          {/* Tools */}
          <div className="flex flex-wrap gap-2 mt-3">
            {DEFAULT_TOOLS.map(tool => (
              <button
                key={tool.id}
                onClick={() => toggleTool(tool.id)}
                className={clsx(
                  'px-3 py-1 rounded-full text-xs font-medium border transition-colors',
                  selectedTools.includes(tool.id)
                    ? 'bg-indigo-50 border-indigo-200 text-indigo-700'
                    : 'bg-gray-50 border-gray-200 text-gray-500 hover:bg-gray-100'
                )}
              >
                {tool.name}
              </button>
            ))}
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((message) => (
            <div
              key={message.id}
              className={clsx(
                'flex gap-3',
                message.role === 'user' ? 'justify-end' : 'justify-start'
              )}
            >
              {message.role !== 'user' && (
                <div className="w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center flex-shrink-0">
                  <Bot className="w-5 h-5 text-indigo-600" />
                </div>
              )}
              
              <div className={clsx(
                'max-w-[70%] rounded-2xl p-4',
                message.role === 'user' 
                  ? 'bg-indigo-600 text-white' 
                  : 'bg-white border border-gray-200'
              )}>
                {message.thinking && (
                  <div className="mb-2 p-2 bg-purple-50 rounded-lg text-xs text-purple-700">
                    <Brain className="w-3 h-3 inline mr-1" />
                    Razmišljanje...
                  </div>
                )}
                
                <div className="prose prose-sm max-w-none">
                  {message.content.split('\n').map((line, i) => (
                    <p key={i} className="mb-1">{line}</p>
                  ))}
                </div>

                <div className="flex items-center justify-end gap-2 mt-2">
                  <button
                    onClick={() => copyToClipboard(message.content)}
                    className={clsx(
                      'p-1 rounded hover:bg-gray-100',
                      message.role === 'user' ? 'text-indigo-200' : 'text-gray-400'
                    )}
                  >
                    <Copy className="w-4 h-4" />
                  </button>
                </div>
              </div>

              {message.role === 'user' && (
                <div className="w-8 h-8 rounded-full bg-indigo-600 flex items-center justify-center flex-shrink-0">
                  <User className="w-5 h-5 text-white" />
                </div>
              )}
            </div>
          ))}

          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full text-center">
              <div className="w-16 h-16 rounded-full bg-indigo-100 flex items-center justify-center mb-4">
                <Sparkles className="w-8 h-8 text-indigo-600" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                Dobrodošli u AI Chat
              </h3>
              <p className="text-gray-500 max-w-md">
                Postavite pitanje, tražite objašnjenje, ili zatražite pomoć sa dokumentima.
                Možete koristiti alate sa desne strane za pretraživanje baze znanja, prevod, generisanje kvizova i još mnogo toga.
              </p>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="bg-white border-t border-gray-200 p-4">
          <div className="flex gap-3">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSend()}
              placeholder="Unesite poruku..."
              className="flex-1 bg-gray-50 border border-gray-200 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              disabled={sendMessageMutation.isPending}
            />
            <button
              onClick={handleSend}
              disabled={!input.trim() || sendMessageMutation.isPending}
              className="btn-primary px-6"
            >
              {sendMessageMutation.isPending ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <Send className="w-5 h-5" />
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
