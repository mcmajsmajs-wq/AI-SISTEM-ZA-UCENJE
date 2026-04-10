/**
 * ================================================================================
 * Petar II Petrović-Njegoš
 * "Blago tome ko dovijek živi, imao se rašta i roditi"
 * ================================================================================
 * 
 * AI Learning System
 * NotFoundPage.tsx
 * Verzija: 1.0.0
 * Autor: Branko Suznjevic
 * Datum: 2026
 * ================================================================================
 */

import { Link } from 'react-router-dom'
import { Home, Search, Sparkles } from 'lucide-react'

export default function NotFoundPage() {
  return (
    <div className="min-h-screen gradient-bg flex items-center justify-center p-8">
      <div className="max-w-md w-full text-center">
        <div className="w-24 h-24 rounded-3xl bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center mx-auto mb-8">
          <Search className="w-12 h-12 text-white" />
        </div>
        
        <h1 className="text-6xl font-bold text-gray-900 mb-2">404</h1>
        <h2 className="text-2xl font-semibold text-gray-700 mb-4">
          Stranica nije pronađena
        </h2>
        <p className="text-gray-500 mb-8">
          Izgleda da stranica koju tražite ne postoji ili je premeštena.
        </p>
        
        <Link to="/" className="btn-primary btn-lg">
          <Home className="w-5 h-5" />
          Vrati se na početnu
        </Link>

        <div className="mt-12 p-6 rounded-2xl bg-white/50 backdrop-blur-sm border border-white/20">
          <div className="flex items-center gap-2 justify-center mb-3">
            <Sparkles className="w-5 h-5 text-primary-500" />
            <span className="font-medium text-gray-700">Da li vam treba pomoć?</span>
          </div>
          <p className="text-sm text-gray-500">
            Ako mislite da je ovo greška, kontaktirajte podršku.
          </p>
        </div>
      </div>
    </div>
  )
}
