/**
 * ================================================================================
 * Petar II Petrović-Njegoš
 * "Blago tome ko dovijek živi, imao se rašta i roditi"
 * ================================================================================
 * 
 * AI Learning System
 * RegisterPage.tsx
 * Verzija: 1.0.0
 * Autor: Branko Suznjevic
 * Datum: 2026
 * ================================================================================
 */

import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuthStore } from '@/stores/authStore'
import { Eye, EyeOff, Mail, Lock, User, Sparkles, ArrowRight, Check, BookOpen, Globe, Cpu } from 'lucide-react'
import toast from 'react-hot-toast'

export default function RegisterPage() {
  const navigate = useNavigate()
  const { register } = useAuthStore()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [fullName, setFullName] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [isLoading, setIsLoading] = useState(false)

  const passwordStrength = () => {
    let strength = 0
    if (password.length >= 8) strength++
    if (/[a-z]/.test(password) && /[A-Z]/.test(password)) strength++
    if (/\d/.test(password)) strength++
    if (/[^a-zA-Z0-9]/.test(password)) strength++
    return strength
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!email || !password || !confirmPassword) {
      toast.error('Molimo vas da popunite sva obavezna polja')
      return
    }

    if (password !== confirmPassword) {
      toast.error('Lozinke se ne poklapaju')
      return
    }

    if (password.length < 8) {
      toast.error('Lozinka mora imati najmanje 8 karaktera')
      return
    }

    setIsLoading(true)
    try {
      await register(email, password, fullName || undefined)
      toast.success('Nalog je uspešno kreiran!')
      navigate('/')
    } catch {
      toast.error('Greška pri kreiranju naloga')
    } finally {
      setIsLoading(false)
    }
  }

  const strength = passwordStrength()
  const strengthLabels = ['Slaba', 'Slaba', 'Srednja', 'Dobra', 'Jaka']
  const strengthColors = ['bg-red-500', 'bg-orange-500', 'bg-yellow-500', 'bg-green-400', 'bg-green-500']

  return (
    <div className="min-h-screen flex">
      {/* Left panel */}
      <div className="hidden lg:flex lg:w-[52%] relative overflow-hidden flex-col justify-between p-12"
        style={{ background: 'linear-gradient(135deg, #5b21b6 0%, #7c3aed 40%, #4338ca 100%)' }}>
        
        <div className="absolute -top-40 -right-20 w-96 h-96 rounded-full opacity-15"
          style={{ background: 'radial-gradient(circle, #c4b5fd, transparent)' }} />
        <div className="absolute -bottom-32 -left-16 w-80 h-80 rounded-full opacity-10"
          style={{ background: 'radial-gradient(circle, #67e8f9, transparent)' }} />

        <div className="relative z-10 flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-white/20 backdrop-blur flex items-center justify-center">
            <Sparkles className="w-6 h-6 text-white" />
          </div>
          <span className="text-white font-bold text-xl">AI Learning</span>
        </div>

        <div className="relative z-10">
          <h1 className="text-5xl font-extrabold text-white leading-tight mb-4">
            Započnite<br />vaše<br />putovanje
          </h1>
          <p className="text-lg text-purple-200 mb-10 leading-relaxed">
            Kreirajte nalog i otključajte moć AI-podržanog učenja.
          </p>

          <div className="space-y-5 mb-10">
            {[
              { icon: BookOpen, title: 'Brza registracija', desc: 'Samo par koraka do početka' },
              { icon: Globe, title: 'Lokalni AI', desc: 'Ollama integracija za privatnost' },
              { icon: Cpu, title: 'Napredna obrada', desc: 'PDF analiza u sekundi' },
            ].map((item, i) => (
              <div key={i} className="flex items-start gap-4">
                <div className="w-9 h-9 rounded-xl bg-white/15 flex items-center justify-center flex-shrink-0">
                  <item.icon className="w-4.5 h-4.5 text-white" style={{ width: '18px', height: '18px' }} />
                </div>
                <div>
                  <p className="text-white font-semibold text-sm">{item.title}</p>
                  <p className="text-purple-300 text-xs mt-0.5">{item.desc}</p>
                </div>
              </div>
            ))}
          </div>

          <div className="bg-white/10 backdrop-blur rounded-2xl p-5 border border-white/15">
            <div className="flex items-center gap-3 mb-3">
              <div className="flex -space-x-2">
                {['#6366f1','#8b5cf6','#06b6d4'].map((c, i) => (
                  <div key={i} className="w-8 h-8 rounded-full border-2 border-white/30 flex items-center justify-center text-white text-xs font-bold"
                    style={{ background: c }}>
                    {String.fromCharCode(65 + i)}
                  </div>
                ))}
              </div>
              <p className="text-white/80 text-sm">Pridružite se korisnicima</p>
            </div>
            <div className="flex">
              {[1,2,3,4,5].map(i => (
                <svg key={i} className="w-4 h-4 text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                </svg>
              ))}
              <span className="text-white/70 text-xs ml-2">4.9/5 ocena</span>
            </div>
          </div>
        </div>

        <p className="relative z-10 text-purple-300 text-xs">© 2024 AI Learning System</p>
      </div>

      {/* Right panel - form */}
      <div className="flex-1 flex items-center justify-center p-8 overflow-y-auto" style={{ background: 'linear-gradient(135deg, #f5f3ff 0%, #f0f4ff 100%)' }}>
        <div className="w-full max-w-md py-4">
          <div className="lg:hidden flex items-center justify-center gap-3 mb-8">
            <div className="w-10 h-10 rounded-xl flex items-center justify-center"
              style={{ background: 'linear-gradient(135deg, #8b5cf6, #6366f1)' }}>
              <Sparkles className="w-6 h-6 text-white" />
            </div>
            <h1 className="text-2xl font-extrabold text-gray-900">AI Learning</h1>
          </div>

          <div className="bg-white rounded-3xl shadow-2xl shadow-purple-100/50 p-8 border border-purple-50">
            <div className="mb-7">
              <h2 className="text-3xl font-extrabold text-gray-900 mb-1">Kreirajte nalog</h2>
              <p className="text-gray-500 text-sm">Pridružite se zajednici učenika</p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label htmlFor="fullName" className="label">
                  Ime i prezime <span className="text-gray-400 font-normal">(opciono)</span>
                </label>
                <div className="relative">
                  <User className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" style={{ width: '18px', height: '18px' }} />
                  <input
                    id="fullName"
                    type="text"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    className="input pl-11"
                    placeholder="Petar Petrović"
                  />
                </div>
              </div>

              <div>
                <label htmlFor="email" className="label">
                  Email adresa <span className="text-red-400">*</span>
                </label>
                <div className="relative">
                  <Mail className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" style={{ width: '18px', height: '18px' }} />
                  <input
                    id="email"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="input pl-11"
                    placeholder="vas@email.com"
                    autoComplete="email"
                    required
                  />
                </div>
              </div>

              <div>
                <label htmlFor="password" className="label">
                  Lozinka <span className="text-red-400">*</span>
                </label>
                <div className="relative">
                  <Lock className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" style={{ width: '18px', height: '18px' }} />
                  <input
                    id="password"
                    type={showPassword ? 'text' : 'password'}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="input pl-11 pr-11"
                    placeholder="••••••••"
                    autoComplete="new-password"
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors"
                  >
                    {showPassword ? <EyeOff style={{ width: '18px', height: '18px' }} /> : <Eye style={{ width: '18px', height: '18px' }} />}
                  </button>
                </div>
                {password && (
                  <div className="mt-2">
                    <div className="flex gap-1 mb-1">
                      {[0, 1, 2, 3].map((i) => (
                        <div
                          key={i}
                          className={`h-1 flex-1 rounded-full transition-colors duration-300 ${
                            i < strength ? strengthColors[strength] : 'bg-gray-200'
                          }`}
                        />
                      ))}
                    </div>
                    <p className="text-xs text-gray-400">{strengthLabels[strength]}</p>
                  </div>
                )}
              </div>

              <div>
                <label htmlFor="confirmPassword" className="label">
                  Potvrdi lozinku <span className="text-red-400">*</span>
                </label>
                <div className="relative">
                  <Lock className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" style={{ width: '18px', height: '18px' }} />
                  <input
                    id="confirmPassword"
                    type={showPassword ? 'text' : 'password'}
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    className={`input pl-11 ${confirmPassword && password !== confirmPassword ? 'input-error' : ''}`}
                    placeholder="••••••••"
                    autoComplete="new-password"
                    required
                  />
                  {confirmPassword && password === confirmPassword && (
                    <Check className="absolute right-4 top-1/2 -translate-y-1/2 text-green-500" style={{ width: '18px', height: '18px' }} />
                  )}
                </div>
                {confirmPassword && password !== confirmPassword && (
                  <p className="text-xs text-red-500 mt-1">Lozinke se ne poklapaju</p>
                )}
              </div>

              <button
                type="submit"
                disabled={isLoading}
                className="btn-accent w-full btn-lg mt-2"
              >
                {isLoading ? (
                  <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                ) : (
                  <>
                    Registruj se
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>
            </form>

            <div className="mt-6 pt-6 border-t border-gray-100 text-center">
              <p className="text-gray-500 text-sm">
                Već imate nalog?{' '}
                <Link to="/login" className="text-secondary-600 font-semibold hover:text-secondary-700 transition-colors">
                  Prijavite se
                </Link>
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
