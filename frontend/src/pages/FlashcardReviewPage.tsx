import { useState, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { flashcardsApi } from '@/services/api'
import { Flashcard, ReviewResponse } from '@/types'
import { ArrowLeft, RotateCcw, Loader2, CheckCircle, XCircle, Award } from 'lucide-react'
import toast from 'react-hot-toast'

export default function FlashcardReviewPage() {
  const { deckId } = useParams<{ deckId: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [currentIndex, setCurrentIndex] = useState(0)
  const [isFlipped, setIsFlipped] = useState(false)
  const [reviews, setReviews] = useState<ReviewResponse[]>([])
  const [showSummary, setShowSummary] = useState(false)

  const { data: dueData, isLoading } = useQuery({
    queryKey: ['due-cards', deckId],
    queryFn: () => flashcardsApi.getDueCards(deckId),
  })

  const reviewMutation = useMutation({
    mutationFn: ({ cardId, quality }: { cardId: string; quality: number }) =>
      flashcardsApi.reviewCard(cardId, { quality }),
    onSuccess: (data) => {
      const review: ReviewResponse = data.data
      setReviews((prev) => [...prev, review])
      if (currentIndex < cards.length - 1) {
        setCurrentIndex((i) => i + 1)
        setIsFlipped(false)
      } else {
        setShowSummary(true)
      }
      queryClient.invalidateQueries({ queryKey: ['due-cards'] })
      queryClient.invalidateQueries({ queryKey: ['deck'] })
      queryClient.invalidateQueries({ queryKey: ['decks'] })
    },
    onError: () => {
      toast.error('Greška pri čuvanju ocene')
    },
  })

  const handleRate = useCallback((quality: number) => {
    if (!card) return
    reviewMutation.mutate({ cardId: card.id, quality })
  }, [reviewMutation, currentIndex, dueData])

  const cards: Flashcard[] = dueData?.data?.items ?? dueData?.data?.cards ?? []
  const card = cards[currentIndex]

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-indigo-600" />
      </div>
    )
  }

  if ((cards.length === 0 || !card) && !showSummary) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-12 text-center">
        <CheckCircle className="mx-auto h-12 w-12 text-green-500" />
        <h2 className="mt-4 text-xl font-semibold text-gray-900">Sve kartice su ponovljene!</h2>
        <p className="mt-2 text-gray-500">Nema kartica koje čekaju na ponavljanje.</p>
        <button onClick={() => navigate('/flashcards')} className="mt-6 text-indigo-600 hover:underline">
          Nazad na špilove
        </button>
      </div>
    )
  }

  if (showSummary || !card) {
    const totalXp = reviews.reduce((sum, r) => sum + r.xp_awarded, 0)
    const avgQuality = reviews.length > 0 ? Math.round(reviews.reduce((sum, r) => sum + r.quality, 0) / reviews.length) : 0

    return (
      <div className="mx-auto max-w-2xl px-4 py-12">
        <div className="rounded-lg border border-gray-200 bg-white p-8 text-center">
          <Award className="mx-auto h-12 w-12 text-yellow-500" />
          <h2 className="mt-4 text-xl font-semibold text-gray-900">Ponavljanje završeno!</h2>
          <p className="mt-2 text-gray-500">Ponovili ste {reviews.length} kartica.</p>
          <div className="mt-6 grid grid-cols-3 gap-4">
            <div className="rounded-lg bg-indigo-50 p-4">
              <p className="text-2xl font-bold text-indigo-600">{reviews.length}</p>
              <p className="text-sm text-gray-500">Ponovljeno</p>
            </div>
            <div className="rounded-lg bg-green-50 p-4">
              <p className="text-2xl font-bold text-green-600">{totalXp}</p>
              <p className="text-sm text-gray-500">XP</p>
            </div>
            <div className="rounded-lg bg-orange-50 p-4">
              <p className="text-2xl font-bold text-orange-600">{avgQuality}</p>
              <p className="text-sm text-gray-500">Prosek</p>
            </div>
          </div>
          <button
            onClick={() => navigate('/flashcards')}
            className="mt-6 rounded-lg bg-indigo-600 px-6 py-2 text-white hover:bg-indigo-700"
          >
            Nazad na špilove
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-2xl px-4 py-8">
      <button onClick={() => navigate('/flashcards')} className="mb-4 flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700">
        <ArrowLeft className="h-4 w-4" />
        Prekini ponavljanje
      </button>

      <div className="mb-4 flex items-center justify-between text-sm text-gray-500">
        <span>Kartica {currentIndex + 1} od {cards.length}</span>
        <span>{reviews.length} ocenjeno</span>
      </div>

      <div className="mb-6">
        <div className="h-2 rounded-full bg-gray-200">
          <div
            className="h-2 rounded-full bg-indigo-600 transition-all"
            style={{ width: `${((currentIndex) / cards.length) * 100}%` }}
          />
        </div>
      </div>

      <div
        className="min-h-[250px] cursor-pointer rounded-xl border-2 border-gray-200 bg-white p-8 transition-all hover:border-indigo-300"
        onClick={() => setIsFlipped(true)}
      >
        {!isFlipped ? (
          <div className="flex h-full items-center justify-center text-center">
            <div>
              <p className="text-lg font-medium text-gray-900">{card.front}</p>
              <p className="mt-4 text-sm text-gray-400">Kliknite da vidite odgovor</p>
            </div>
          </div>
        ) : (
          <div className="text-center">
            <p className="mb-4 text-sm font-medium text-indigo-600">Odgovor:</p>
            <p className="text-lg text-gray-900">{card.back}</p>
          </div>
        )}
      </div>

      {isFlipped && (
        <div className="mt-8">
          <p className="mb-3 text-center text-sm text-gray-500">Kako dobro znate odgovor?</p>
          <div className="grid grid-cols-5 gap-2">
            <button
              onClick={() => handleRate(1)}
              disabled={reviewMutation.isPending}
              className="flex flex-col items-center gap-1 rounded-lg border border-red-200 bg-red-50 px-2 py-3 text-red-700 hover:bg-red-100 disabled:opacity-50"
            >
              <XCircle className="h-5 w-5" />
              <span className="text-xs font-medium">1</span>
              <span className="text-[10px]">Nisam se setio</span>
            </button>
            <button
              onClick={() => handleRate(2)}
              disabled={reviewMutation.isPending}
              className="flex flex-col items-center gap-1 rounded-lg border border-orange-200 bg-orange-50 px-2 py-3 text-orange-700 hover:bg-orange-100 disabled:opacity-50"
            >
              <RotateCcw className="h-5 w-5" />
              <span className="text-xs font-medium">2</span>
              <span className="text-[10px]">Setio sam se</span>
            </button>
            <button
              onClick={() => handleRate(3)}
              disabled={reviewMutation.isPending}
              className="flex flex-col items-center gap-1 rounded-lg border border-blue-200 bg-blue-50 px-2 py-3 text-blue-700 hover:bg-blue-100 disabled:opacity-50"
            >
              <RotateCcw className="h-5 w-5" />
              <span className="text-xs font-medium">3</span>
              <span className="text-[10px]">Znao sam</span>
            </button>
            <button
              onClick={() => handleRate(4)}
              disabled={reviewMutation.isPending}
              className="flex flex-col items-center gap-1 rounded-lg border border-green-200 bg-green-50 px-2 py-3 text-green-700 hover:bg-green-100 disabled:opacity-50"
            >
              <CheckCircle className="h-5 w-5" />
              <span className="text-xs font-medium">4</span>
              <span className="text-[10px]">Bilo je lako</span>
            </button>
            <button
              onClick={() => handleRate(5)}
              disabled={reviewMutation.isPending}
              className="flex flex-col items-center gap-1 rounded-lg border border-emerald-300 bg-emerald-50 px-2 py-3 text-emerald-700 hover:bg-emerald-100 disabled:opacity-50"
            >
              <CheckCircle className="h-5 w-5" />
              <span className="text-xs font-medium">5</span>
              <span className="text-[10px]">Trenutno</span>
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
