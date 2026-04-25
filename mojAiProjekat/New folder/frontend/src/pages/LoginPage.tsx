/**
 * ================================================================================
 * Petar II Petrović-Njegoš
 * "Blago tome ko dovijek živi, imao se rašta i roditi"
 * ================================================================================
 * 
 * AI Learning System
 * LoginPage.tsx
 * Verzija: 1.0.0
 * Autor: Branko Suznjevic
 * Datum: 2026
 * ================================================================================
 */

import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuthStore } from '@/stores/authStore'
import { Eye, EyeOff, Mail, Lock, Sparkles, ArrowRight, CheckCircle, Zap, Shield, Brain } from 'lucide-react'
import toast from 'react-hot-toast'

export default function LoginPage() {
  const navigate = useNavigate()
  const { login } = useAuthStore()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [isLoading, setIsLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!email || !password) {
      toast.error('Molimo vas da popunite sva polja')
      return
    }

    setIsLoading(true)
    try {
      await login(email, password)
      toast.success('Uspešno ste se prijavili!')
      navigate('/')
    } catch {
      toast.error('Neispravni podaci za prijavu')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex">
      {/* Left panel */}
      <div className="hidden lg:flex lg:w-[52%] relative overflow-hidden flex-col justify-between p-12"
        style={{ background: 'linear-gradient(135deg, #4338ca 0%, #6d28d9 50%, #7c3aed 100%)' }}>
        
        {/* Decorative circles */}
        <div className="absolute -top-32 -left-32 w-96 h-96 rounded-full opacity-20"
          style={{ background: 'radial-gradient(circle, #a5b4fc, transparent)' }} />
        <div className="absolute -bottom-24 -right-24 w-80 h-80 rounded-full opacity-15"
          style={{ background: 'radial-gradient(circle, #c4b5fd, transparent)' }} />
        <div className="absolute top-1/2 right-0 w-64 h-64 rounded-full opacity-10"
          style={{ background: 'radial-gradient(circle, #67e8f9, transparent)' }} />

        {/* Logo */}
        <div className="relative z-10 flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-white/20 backdrop-blur flex items-center justify-center">
            <Sparkles className="w-6 h-6 text-white" />
          </div>
          <span className="text-white font-bold text-xl">AI Learning</span>
        </div>

        {/* Main content */}
        <div className="relative z-10">
          <div className="inline-flex items-center gap-2 bg-white/15 backdrop-blur rounded-full px-4 py-1.5 mb-6">
            <Zap className="w-3.5 h-3.5 text-yellow-300" />
            <span className="text-white/90 text-xs font-medium">Powered by AI</span>
          </div>
          <h1 className="text-5xl font-extrabold text-white leading-tight mb-4">
            Učite brže<br />uz veštačku<br />inteligenciju
          </h1>
          <p className="text-lg text-indigo-200 mb-10 leading-relaxed">
            Transformišite PDF dokumente u interaktivne materijale za učenje.
          </p>

          <div className="space-y-4 mb-10">
            {[
              { icon: CheckCircle, text: 'Automatski prevod dokumenata' },
              { icon: Brain, text: 'AI analiza i ekstrakcija znanja' },
              { icon: Shield, text: 'Lokalni AI – potpuna privatnost' },
            ].map((item, i) => (
              <div key={i} className="flex items-center gap-3">
                <div className="w-7 h-7 rounded-lg bg-white/20 flex items-center justify-center flex-shrink-0">
                  <item.icon className="w-4 h-4 text-white" />
                </div>
                <span className="text-white/85 text-sm font-medium">{item.text}</span>
              </div>
            ))}
          </div>

          {/* Stats */}
          <div className="grid grid-cols-3 gap-4">
            {[
              { value: '10K+', label: 'Dokumenata' },
              { value: '99%', label: 'Preciznost' },
              { value: '5min', label: 'Prosečno' },
            ].map((stat, i) => (
              <div key={i} className="text-center bg-white/10 backdrop-blur rounded-2xl py-3 px-2">
                <p className="text-2xl font-extrabold text-white">{stat.value}</p>
                <p className="text-xs text-indigo-300 mt-0.5">{stat.label}</p>
              </div>
            ))}
          </div>
        </div>

        <p className="relative z-10 text-indigo-300 text-xs">© 2024 AI Learning System</p>
      </div>

      {/* Right panel - form */}
      <div className="flex-1 flex items-center justify-center p-8" style={{ background: 'linear-gradient(135deg, #f0f4ff 0%, #faf5ff 100%)' }}>
        <div className="w-full max-w-md">
          {/* Mobile logo */}
          <div className="lg:hidden flex items-center justify-center gap-3 mb-8">
            <div className="w-10 h-10 rounded-xl flex items-center justify-center"
              style={{ background: 'linear-gradient(135deg, #6366f1, #8b5cf6)' }}>
              <Sparkles className="w-6 h-6 text-white" />
            </div>
            <h1 className="text-2xl font-extrabold text-gray-900">AI Learning</h1>
          </div>

          <div className="bg-white rounded-3xl shadow-2xl shadow-indigo-100/50 p-8 border border-indigo-50">
            <div className="mb-8">
              <h2 className="text-3xl font-extrabold text-gray-900 mb-1">Dobrodošli nazad</h2>
              <p className="text-gray-500 text-sm">Prijavite se da nastavite učenje</p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-5">
              <div>
                <label htmlFor="email" className="label">Email adresa</label>
                <div className="relative">
                  <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-4.5 h-4.5 text-gray-400" style={{ width: '18px', height: '18px' }} />
                  <input
                    id="email"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="input pl-11"
                    placeholder="vas@email.com"
                    autoComplete="email"
                  />
                </div>
              </div>

              <div>
                <label htmlFor="password" className="label">Lozinka</label>
                <div className="relative">
                  <Lock className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" style={{ width: '18px', height: '18px' }} />
                  <input
                    id="password"
                    type={showPassword ? 'text' : 'password'}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="input pl-11 pr-11"
                    placeholder="••••••••"
                    autoComplete="current-password"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors"
                  >
                    {showPassword ? <EyeOff style={{ width: '18px', height: '18px' }} /> : <Eye style={{ width: '18px', height: '18px' }} />}
                  </button>
                </div>
              </div>

              <button
                type="submit"
                disabled={isLoading}
                className="btn-primary w-full btn-lg mt-2"
              >
                {isLoading ? (
                  <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                ) : (
                  <>
                    Prijavi se
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>

              <div className="text-right mt-2">
                <Link to="/forgot-password" className="text-sm text-gray-500 hover:text-primary-600 transition-colors">
                  Zaboravili ste lozinku?
                </Link>
              </div>
            </form>

            <div className="mt-6 pt-6 border-t border-gray-100 text-center">
              <p className="text-gray-500 text-sm">
                Nemate nalog?{' '}
                <Link to="/register" className="text-primary-600 font-semibold hover:text-primary-700 transition-colors">
                  Registrujte se besplatno
                </Link>
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
