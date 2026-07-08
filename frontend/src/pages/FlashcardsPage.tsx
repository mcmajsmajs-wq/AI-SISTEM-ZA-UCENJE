import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { flashcardsApi } from '@/services/api'
import { Deck } from '@/types'
import { BookOpen, Plus, Trash2, GraduationCap, Loader2 } from 'lucide-react'
import toast from 'react-hot-toast'

export default function FlashcardsPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [newName, setNewName] = useState('')
  const [newDescription, setNewDescription] = useState('')

  const { data: decksData, isLoading } = useQuery({
    queryKey: ['decks'],
    queryFn: () => flashcardsApi.listDecks(),
  })

  const createMutation = useMutation({
    mutationFn: () => flashcardsApi.createDeck({ name: newName, description: newDescription || null }),
    onSuccess: () => {
      toast.success('Špil kreiran!')
      queryClient.invalidateQueries({ queryKey: ['decks'] })
      setShowCreateForm(false)
      setNewName('')
      setNewDescription('')
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => flashcardsApi.deleteDeck(id),
    onSuccess: () => {
      toast.success('Špil obrisan')
      queryClient.invalidateQueries({ queryKey: ['decks'] })
    },
  })

  const decks: Deck[] = (decksData as any)?.data?.items ?? []

  return (
    <div className="mx-auto max-w-4xl px-4 py-8">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Flash kartice</h1>
          <p className="mt-1 text-gray-500">Spaced repetition za efikasno učenje</p>
        </div>
        <button
          onClick={() => setShowCreateForm(true)}
          className="flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-white hover:bg-indigo-700"
        >
          <Plus className="h-4 w-4" />
          Novi špil
        </button>
      </div>

      {showCreateForm && (
        <div className="mb-6 rounded-lg border border-gray-200 bg-white p-6">
          <h2 className="mb-4 text-lg font-semibold text-gray-900">Kreiraj novi špil</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Naziv</label>
              <input
                type="text"
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2"
                placeholder="Npr. Biologija - Ćelija"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Opis (opciono)</label>
              <textarea
                value={newDescription}
                onChange={(e) => setNewDescription(e.target.value)}
                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2"
                rows={2}
                placeholder="Kratak opis..."
              />
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => createMutation.mutate()}
                disabled={!newName.trim() || createMutation.isPending}
                className="rounded-md bg-indigo-600 px-4 py-2 text-white hover:bg-indigo-700 disabled:opacity-50"
              >
                {createMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Kreiraj'}
              </button>
              <button
                onClick={() => { setShowCreateForm(false); setNewName(''); setNewDescription('') }}
                className="rounded-md border border-gray-300 px-4 py-2 text-gray-700 hover:bg-gray-50"
              >
                Odustani
              </button>
            </div>
          </div>
        </div>
      )}

      {isLoading ? (
        <div className="flex justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-indigo-600" />
        </div>
      ) : decks.length === 0 ? (
        <div className="rounded-lg border-2 border-dashed border-gray-300 p-12 text-center">
          <GraduationCap className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-4 text-lg font-medium text-gray-900">Još uvek nema špilova</h3>
          <p className="mt-2 text-gray-500">Kreirajte prvi špil ili generišite kartice iz dokumenta.</p>
          <button
            onClick={() => setShowCreateForm(true)}
            className="mt-4 inline-flex items-center gap-2 rounded-md bg-indigo-600 px-4 py-2 text-white hover:bg-indigo-700"
          >
            <Plus className="h-4 w-4" />
            Kreiraj prvi špil
          </button>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {decks.map((deck) => (
            <div
              key={deck.id}
              className="group cursor-pointer rounded-lg border border-gray-200 bg-white p-5 transition-shadow hover:shadow-md"
              onClick={() => navigate(`/decks/${deck.id}`)}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className="rounded-lg bg-indigo-100 p-2">
                    <BookOpen className="h-5 w-5 text-indigo-600" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900">{deck.name}</h3>
                    {deck.description && (
                      <p className="mt-0.5 text-sm text-gray-500">{deck.description}</p>
                    )}
                  </div>
                </div>
                <button
                  onClick={(e) => { e.stopPropagation(); deleteMutation.mutate(deck.id) }}
                  className="rounded p-1 text-gray-400 opacity-0 hover:bg-red-50 hover:text-red-500 group-hover:opacity-100"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
              <div className="mt-4 flex items-center gap-4 text-sm text-gray-500">
                <span>{deck.total_cards} kartica</span>
                {deck.due_today > 0 && (
                  <span className="font-medium text-indigo-600">{deck.due_today} na redosledu</span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
