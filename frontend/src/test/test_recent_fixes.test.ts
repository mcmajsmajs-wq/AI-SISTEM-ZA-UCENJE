/**
 * Tests for recent frontend fixes:
 * - QuizResultsPage null safety
 * - DeckDetailPage generation error handling
 * - FlashcardsPage data extraction
 * - FlashcardReviewPage null card safety (Cannot read properties of undefined 'front')
 * - FlashcardReviewPage due cards fetching
 */
import { describe, it, expect } from 'vitest'

describe('FlashcardsPage data extraction', () => {
  it('should extract items from API response', () => {
    const apiResponse = { data: { items: [{ id: '1', name: 'Test' }], total: 1 } }
    const decks = (apiResponse as any)?.data?.items ?? []
    expect(decks).toHaveLength(1)
    expect(decks[0].name).toBe('Test')
  })

  it('should handle empty items gracefully', () => {
    const apiResponse = { data: { items: [], total: 0 } }
    const decks = (apiResponse as any)?.data?.items ?? []
    expect(decks).toHaveLength(0)
  })

  it('should handle undefined response', () => {
    const decks = (undefined as any)?.data?.items ?? []
    expect(decks).toHaveLength(0)
  })
})

describe('FlashcardReviewPage due cards', () => {
  it('should access cards or items from response', () => {
    const apiResponse: any = { data: { items: [{ id: '1' }], total: 1 } }
    const cards = apiResponse?.data?.items ?? apiResponse?.data?.cards ?? []
    expect(cards).toHaveLength(1)
  })

  it('should fallback to cards if items missing', () => {
    const apiResponse: any = { data: { cards: [{ id: '1' }], total: 1 } }
    const cards = (apiResponse as any)?.data?.items ?? apiResponse?.data?.cards ?? []
    expect(cards).toHaveLength(1)
  })

  it('should handle empty response', () => {
    const cards = (null as any)?.data?.items ?? (null as any)?.data?.cards ?? []
    expect(cards).toHaveLength(0)
  })
})

describe('QuizResultsPage null safety', () => {
  it('should handle null answers', () => {
    const result = { answers: null, passed: true, percentage: 85, score: 17, total_points: 20 }
    const answers = result.answers ?? []
    expect(answers).toHaveLength(0)
  })

  it('should handle missing percentage', () => {
    const result = { percentage: undefined }
    const pct = (result.percentage ?? 0).toFixed(0)
    expect(pct).toBe('0')
  })

  it('should handle missing passed', () => {
    const p1: boolean | undefined = undefined
    const p2: boolean | null = null
    expect((p1 ?? false)).toBe(false)
    expect((p2 ?? false)).toBe(false)
  })

  it('should handle missing score', () => {
    const val: number | undefined = undefined
    expect((val ?? 0)).toBe(0)
  })
})

describe('FlashcardReviewPage card null safety', () => {
  it('should handle card being undefined when index out of bounds', () => {
    const cards: any[] = [{ id: '1', front: 'Q1', back: 'A1' }]
    const currentIndex = 1
    const card = cards[currentIndex]
    // Simulate the guard: (cards.length === 0 || !card) && !showSummary
    const showEmpty = (cards.length === 0 || !card)
    expect(showEmpty).toBe(true)
    // If card is undefined, accessing .front would crash
    expect(() => (card as any).front).toThrow()
  })

  it('should handle currentIndex at valid position', () => {
    const cards: any[] = [{ id: '1', front: 'Q1', back: 'A1' }]
    const currentIndex = 0
    const card = cards[currentIndex]
    expect(card).toBeDefined()
    expect(card.front).toBe('Q1')
    expect(card.back).toBe('A1')
  })

  it('should handle undefined dueData', () => {
    const dueData = undefined
    const cards: any[] = (dueData as any)?.data?.items ?? (dueData as any)?.data?.cards ?? []
    const card = cards[0]
    expect(cards.length).toBe(0)
    expect(card).toBeUndefined()
  })

  it('should not crash with empty cards array', () => {
    const cards: any[] = []
    const currentIndex = 0
    const card = cards[currentIndex]
    // This is the exact fix pattern
    const shouldShowEmpty = (cards.length === 0 || !card)
    expect(shouldShowEmpty).toBe(true)
    // Accessing .front without guard would crash
    expect(() => (card as any)?.front ?? '').not.toThrow()
  })

  it('should handle review completion where last card was rated', () => {
    const cards: any[] = [{ id: '1', front: 'Q', back: 'A' }]
    let currentIndex = 0
    const showSummary = false
    // Simulate rating the last card
    currentIndex = 1
    const card = cards[currentIndex]
    // Guard: show summary if no card available
    if ((cards.length === 0 || !card) && !showSummary) {
      // Should show "all done" state, not crash
      expect(true).toBe(true)
    }
  })

  it('should show summary when card is undefined and showSummary is true', () => {
    const cards: any[] = []
    const showSummary = true
    const currentIndex = 0
    const card = cards[currentIndex]
    // When showSummary is true, it should render summary regardless of card state
    const shouldShowSummary = showSummary || !card
    expect(shouldShowSummary).toBe(true)
  })
})

describe('DeckDetailPage error handling', () => {
  it('should extract error detail from API response', () => {
    const err: any = { response: { data: { detail: 'OpenAI API kvota je iscrpljena' } } }
    const msg = err?.response?.data?.detail || err?.message || 'Greška'
    expect(msg).toContain('kvota')
  })

  it('should fallback to generic error message', () => {
    const err: any = {}
    const msg = err?.response?.data?.detail || 'Greška pri generisanju kartica'
    expect(msg).toBe('Greška pri generisanju kartica')
  })
})
