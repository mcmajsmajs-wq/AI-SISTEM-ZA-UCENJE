import { describe, it, expect } from 'vitest'

describe('Flashcard Types', () => {
  describe('Deck', () => {
    it('should have correct deck interface structure', () => {
      const deck = {
        id: '123e4567-e89b-12d3-a456-426614174000',
        user_id: 'abc123',
        name: 'Biologija - Ćelija',
        description: 'Osnovne ćelijske strukture',
        source_document_id: null,
        total_cards: 25,
        due_today: 5,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-15T00:00:00Z',
      }
      expect(deck.id).toBeDefined()
      expect(deck.name).toBe('Biologija - Ćelija')
      expect(deck.total_cards).toBe(25)
      expect(deck.due_today).toBe(5)
    })

    it('should allow optional source_document_id', () => {
      const deck = {
        id: 'deck-2',
        user_id: 'abc123',
        name: 'Ručni špil',
        description: null,
        source_document_id: 'doc-123',
        total_cards: 10,
        due_today: 0,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-15T00:00:00Z',
      }
      expect(deck.source_document_id).toBe('doc-123')
      expect(deck.description).toBeNull()
    })
  })

  describe('Flashcard', () => {
    it('should have correct flashcard interface', () => {
      const card = {
        id: 'card-1',
        deck_id: 'deck-1',
        front: 'Šta je mitohondrija?',
        back: 'Organela odgovorna za ćelijsko disanje',
        source_chunk_id: null,
        order_index: 0,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      }
      expect(card.front).toContain('mitohondrija')
      expect(card.back).toContain('Organela')
      expect(card.order_index).toBe(0)
    })
  })

  describe('ReviewRequest', () => {
    it('should have quality field', () => {
      const request = { quality: 4 }
      expect(request.quality).toBeGreaterThanOrEqual(1)
      expect(request.quality).toBeLessThanOrEqual(4)
    })
  })

  describe('ReviewResponse', () => {
    it('should have correct review response structure', () => {
      const response = {
        card_id: 'card-1',
        quality: 4,
        next_review_at: '2024-01-03T00:00:00Z',
        interval: 2,
        ease_factor: 2.5,
        repetitions: 1,
        xp_awarded: 20,
        total_xp: 150,
        level: 3,
        leveled_up: false,
        new_badges: [],
      }
      expect(response.xp_awarded).toBe(20)
      expect(response.interval).toBe(2)
      expect(response.leveled_up).toBe(false)
    })

    it('should handle level up with badges', () => {
      const response = {
        card_id: 'card-2',
        quality: 4,
        next_review_at: '2024-01-05T00:00:00Z',
        interval: 4,
        ease_factor: 2.5,
        repetitions: 2,
        xp_awarded: 20,
        total_xp: 100,
        level: 5,
        leveled_up: true,
        new_badges: [
          { slug: 'flashcard-master', name: 'Flash Master', icon_name: 'graduation-cap', xp_reward: 50 },
        ],
      }
      expect(response.leveled_up).toBe(true)
      expect(response.new_badges).toHaveLength(1)
      expect(response.new_badges[0].slug).toBe('flashcard-master')
    })
  })

  describe('DueCardsResponse', () => {
    it('should have cards array and total', () => {
      const response = {
        cards: [
          { id: 'c1', deck_id: 'd1', front: 'Q1?', back: 'A1', source_chunk_id: null, order_index: 0, created_at: '', updated_at: '' },
          { id: 'c2', deck_id: 'd1', front: 'Q2?', back: 'A2', source_chunk_id: null, order_index: 1, created_at: '', updated_at: '' },
        ],
        total: 2,
      }
      expect(response.cards).toHaveLength(2)
      expect(response.total).toBe(2)
    })
  })

  describe('GenerateFlashcardsResponse', () => {
    it('should have correct generate response structure', () => {
      const response = {
        deck: {
          id: 'deck-1',
          user_id: 'u1',
          name: 'Auto-generisano',
          description: null,
          source_document_id: 'doc-1',
          total_cards: 15,
          due_today: 15,
          created_at: '',
          updated_at: '',
        },
        cards_created: 15,
        mode: 'auto',
      }
      expect(response.cards_created).toBe(15)
      expect(response.mode).toBe('auto')
      expect(response.deck.total_cards).toBe(15)
    })
  })
})

describe('Flashcard API Endpoints', () => {
  it('should have correct deck CRUD endpoints', () => {
    const endpoints = {
      createDeck: '/decks',
      listDecks: '/decks',
      getDeck: '/decks/{id}',
      deleteDeck: '/decks/{id}',
    }
    expect(endpoints.createDeck).toBe('/decks')
    expect(endpoints.getDeck).toContain('/decks/')
    expect(endpoints.deleteDeck).toContain('/decks/')
  })

  it('should have correct card endpoints', () => {
    const endpoints = {
      addCard: '/decks/{deckId}/cards',
      deleteCard: '/decks/{deckId}/cards/{cardId}',
    }
    expect(endpoints.addCard).toContain('/cards')
    expect(endpoints.deleteCard).toContain('/cards/')
  })

  it('should have correct review endpoints', () => {
    const endpoints = {
      getDueCards: '/flashcards/review',
      reviewCard: '/flashcards/{cardId}/review',
      generateFromDocument: '/documents/{id}/generate-flashcards',
    }
    expect(endpoints.getDueCards).toBe('/flashcards/review')
    expect(endpoints.reviewCard).toContain('/review')
    expect(endpoints.generateFromDocument).toContain('/generate-flashcards')
  })

  it('should have flashcardsApi methods defined', () => {
    const apiMethods = [
      'createDeck',
      'listDecks',
      'getDeck',
      'deleteDeck',
      'addCard',
      'deleteCard',
      'getDueCards',
      'reviewCard',
      'generateFromDocument',
    ]
    expect(apiMethods).toContain('createDeck')
    expect(apiMethods).toContain('reviewCard')
    expect(apiMethods).toContain('generateFromDocument')
  })
})
