import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { flashcardsApi, documentsApi } from '@/services/api'
import { Deck, Flashcard, Document } from '@/types'
import { ArrowLeft, Plus, Trash2, Sparkles, Loader2, Eye, EyeOff } from 'lucide-react'
import toast from 'react-hot-toast'

export default function DeckDetailPage() {
  const { deckId } = useParams<{ deckId: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [showAddCard, setShowAddCard] = useState(false)
  const [front, setFront] = useState('')
  const [back, setBack] = useState('')
  const [showGenerate, setShowGenerate] = useState(false)
  const [selectedDocId, setSelectedDocId] = useState('')
  const [generateMode, setGenerateMode] = useState<'auto' | 'ai'>('auto')
  const [maxCards, setMaxCards] = useState(20)
  const [flippedCards, setFlippedCards] = useState<Set<string>>(new Set())

  const { data: deckData, isLoading } = useQuery({
    queryKey: ['deck', deckId],
    queryFn: () => flashcardsApi.getDeck(deckId!),
    enabled: !!deckId,
  })

  const { data: docsData } = useQuery({
    queryKey: ['documents', 'completed'],
    queryFn: () => documentsApi.list(0, 100, 'completed'),
  })

  const deck: Deck | undefined = deckData?.data
  const docs: Document[] = docsData?.data?.items ?? docsData?.data ?? []

  const toggleFlip = (cardId: string) => {
    setFlippedCards((prev) => {
      const next = new Set(prev)
      if (next.has(cardId)) next.delete(cardId)
      else next.add(cardId)
      return next
    })
  }

  const addCardMutation = useMutation({
    mutationFn: () => flashcardsApi.addCard(deckId!, { front, back }),
    onSuccess: () => {
      toast.success('Kartica dodata!')
      queryClient.invalidateQueries({ queryKey: ['deck', deckId] })
      setFront('')
      setBack('')
      setShowAddCard(false)
    },
  })

  const deleteCardMutation = useMutation({
    mutationFn: (cardId: string) => flashcardsApi.deleteCard(deckId!, cardId),
    onSuccess: () => {
      toast.success('Kartica obrisana')
      queryClient.invalidateQueries({ queryKey: ['deck', deckId] })
    },
  })

  const [generateStartedAt, setGenerateStartedAt] = useState<number | null>(null)
  const [elapsedSec, setElapsedSec] = useState(0)

  useEffect(() => {
    if (!generateStartedAt) return
    const timer = setInterval(() => {
      setElapsedSec(Math.floor((Date.now() - generateStartedAt) / 1000))
    }, 1000)
    return () => clearInterval(timer)
  }, [generateStartedAt])

  const generateMutation = useMutation({
    mutationFn: () => flashcardsApi.generateFromDocument(selectedDocId, { mode: generateMode, max_cards: maxCards, deck_name: null, deck_id: deckId }),
    onSuccess: (res: any) => {
      const prov = res?.data?.provider_used
      const provLabel = prov === 'crewai' ? 'CrewAI' : prov ? prov.charAt(0).toUpperCase() + prov.slice(1) : null
      toast.success(provLabel ? `Kartice generisane putem ${provLabel}!` : 'Kartice generisane!')
      queryClient.invalidateQueries({ queryKey: ['deck', deckId] })
      queryClient.invalidateQueries({ queryKey: ['decks'] })
      setShowGenerate(false)
      setSelectedDocId('')
      setGenerateStartedAt(null)
      setElapsedSec(0)
    },
    onError: (err: any) => {
      console.error('Generate flashcards error:', err)
      const apiMsg = err?.response?.data?.detail
      const fallback = apiMsg || err?.message || 'Greška pri generisanju kartica'
      toast.error(fallback, { duration: 6000 })
      setGenerateStartedAt(null)
      setElapsedSec(0)
    },
  })

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-indigo-600" />
      </div>
    )
  }

  if (!deck) {
    return (
      <div className="mx-auto max-w-4xl px-4 py-8 text-center">
        <p className="text-gray-500">Špil nije pronađen.</p>
        <button onClick={() => navigate('/flashcards')} className="mt-4 text-indigo-600 hover:underline">
          Nazad na špilove
        </button>
      </div>
    )
  }

  const cards: Flashcard[] = (deck as any).cards ?? []

  return (
    <div className="mx-auto max-w-4xl px-4 py-8">
      <button onClick={() => navigate('/flashcards')} className="mb-4 flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700">
        <ArrowLeft className="h-4 w-4" />
        Nazad na špilove
      </button>

      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">{deck.name}</h1>
        {deck.description && <p className="mt-1 text-gray-500">{deck.description}</p>}
        <p className="mt-2 text-sm text-gray-400">
          {cards.length} kartica &middot; {deck.due_today} na redosledu danas
        </p>
      </div>

      <div className="mb-6 flex flex-wrap gap-3">
        {deck.due_today > 0 && (
          <button
            onClick={() => navigate(`/flashcards/review/${deckId}`)}
            className="flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-white hover:bg-indigo-700"
          >
            Započni ponavljanje ({deck.due_today})
          </button>
        )}
        <button
          onClick={() => setShowAddCard(!showAddCard)}
          className="flex items-center gap-2 rounded-lg border border-gray-300 px-4 py-2 text-gray-700 hover:bg-gray-50"
        >
          <Plus className="h-4 w-4" />
          Dodaj karticu
        </button>
        <button
          onClick={() => setShowGenerate(!showGenerate)}
          className="flex items-center gap-2 rounded-lg border border-gray-300 px-4 py-2 text-gray-700 hover:bg-gray-50"
        >
          <Sparkles className="h-4 w-4" />
          Generiši iz dokumenta
        </button>
      </div>

      {showAddCard && (
        <div className="mb-6 rounded-lg border border-gray-200 bg-white p-4">
          <h3 className="mb-3 font-medium text-gray-900">Nova kartica</h3>
          <div className="space-y-3">
            <div>
              <label className="block text-sm font-medium text-gray-700">Pitanje (prednja strana)</label>
              <textarea
                value={front}
                onChange={(e) => setFront(e.target.value)}
                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2"
                rows={2}
                placeholder="Unesite pitanje..."
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Odgovor (zadnja strana)</label>
              <textarea
                value={back}
                onChange={(e) => setBack(e.target.value)}
                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2"
                rows={2}
                placeholder="Unesite odgovor..."
              />
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => addCardMutation.mutate()}
                disabled={!front.trim() || !back.trim() || addCardMutation.isPending}
                className="rounded-md bg-indigo-600 px-4 py-2 text-white hover:bg-indigo-700 disabled:opacity-50"
              >
                {addCardMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Dodaj'}
              </button>
              <button onClick={() => { setShowAddCard(false); setFront(''); setBack('') }} className="rounded-md border border-gray-300 px-4 py-2 text-gray-700 hover:bg-gray-50">
                Odustani
              </button>
            </div>
          </div>
        </div>
      )}

      {showGenerate && (
        <div className="mb-6 rounded-lg border border-gray-200 bg-white p-4">
          <h3 className="mb-3 font-medium text-gray-900">Generiši kartice iz dokumenta</h3>
          {generateMutation.isPending ? (
            <div className="flex flex-col items-center py-6">
              <Loader2 className="h-8 w-8 animate-spin text-indigo-600" />
              {generateMode === 'ai' ? (
                <>
                  <p className="mt-3 text-sm font-medium text-gray-700">
                    {elapsedSec < 15 ? '1/3 Čitanje dokumenta...' :
                     elapsedSec < 35 ? '2/3 Generisanje kartica...' :
                     elapsedSec < 55 ? '3/3 Validacija kartica...' :
                     'Završna obrada...'}
                  </p>
                  <div className="mt-3 h-2 w-48 rounded-full bg-gray-200">
                    <div
                      className="h-2 rounded-full bg-indigo-600 transition-all duration-500"
                      style={{ width: `${Math.min(100, (elapsedSec / 60) * 100)}%` }}
                    />
                  </div>
                  <p className="mt-2 text-xs text-gray-400">CrewAI - 3 agenta za bolji kvalitet</p>
                  {elapsedSec > 5 && (
                    <p className="mt-1 text-xs text-gray-500">Proteklo: {elapsedSec}s</p>
                  )}
                </>
              ) : (
                <>
                  <p className="mt-3 text-sm font-medium text-gray-700">Ekstrahujem termine iz dokumenta...</p>
                  <p className="mt-1 text-xs text-gray-400">Ovo može potrajati do 30 sekundi</p>
                  {elapsedSec > 5 && (
                    <p className="mt-2 text-xs text-gray-500">Proteklo: {elapsedSec}s</p>
                  )}
                </>
              )}
            </div>
          ) : (
            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-gray-700">Dokument</label>
                <select
                  value={selectedDocId}
                  onChange={(e) => setSelectedDocId(e.target.value)}
                  className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2"
                >
                  <option value="">Izaberite dokument...</option>
                  {docs.map((doc: any) => (
                    <option key={doc.id} value={doc.id}>{doc.title || doc.filename}</option>
                  ))}
                </select>
              </div>
              <div className="flex gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Mod</label>
                  <select
                    value={generateMode}
                    onChange={(e) => setGenerateMode(e.target.value as 'auto' | 'ai')}
                    className="mt-1 block rounded-md border border-gray-300 px-3 py-2"
                  >
                    <option value="auto">Auto (regex)</option>
                    <option value="ai">AI (ako je API ključ podešen)</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Maks kartica</label>
                  <input
                    type="number"
                    value={maxCards}
                    onChange={(e) => setMaxCards(Math.max(1, Number(e.target.value)))}
                    className="mt-1 block w-24 rounded-md border border-gray-300 px-3 py-2"
                    min={1}
                    max={200}
                  />
                </div>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => {
                    setGenerateStartedAt(Date.now())
                    setElapsedSec(0)
                    generateMutation.mutate()
                  }}
                  disabled={!selectedDocId}
                  className="flex items-center gap-2 rounded-md bg-indigo-600 px-4 py-2 text-white hover:bg-indigo-700 disabled:opacity-50"
                >
                  <Sparkles className="h-4 w-4" />
                  Generiši
                </button>
                <button onClick={() => { setShowGenerate(false); setSelectedDocId('') }} className="rounded-md border border-gray-300 px-4 py-2 text-gray-700 hover:bg-gray-50">
                  Odustani
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {cards.length === 0 ? (
        <div className="rounded-lg border-2 border-dashed border-gray-300 p-12 text-center">
          <p className="text-gray-500">Još uvek nema kartica u ovom špilu.</p>
          <p className="mt-1 text-sm text-gray-400">Dodajte kartice ručno ili generišite iz dokumenta.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {cards.map((card) => (
            <div key={card.id} className="rounded-lg border border-gray-200 bg-white">
              <div className="flex items-start justify-between p-4">
                <div className="flex-1">
                  <p className={`font-medium text-gray-900 ${flippedCards.has(card.id) ? '' : 'mb-0'}`}>{card.front}</p>
                  {flippedCards.has(card.id) && (
                    <div className="mt-3 border-t border-gray-100 pt-3">
                      <p className="text-sm text-indigo-600">{card.back}</p>
                    </div>
                  )}
                </div>
                <div className="ml-4 flex items-center gap-1">
                  <button
                    onClick={() => toggleFlip(card.id)}
                    className="rounded p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
                  >
                    {flippedCards.has(card.id) ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                  <button
                    onClick={() => deleteCardMutation.mutate(card.id)}
                    className="rounded p-1 text-gray-400 hover:bg-red-50 hover:text-red-500"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
