import { useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { usersApi } from '@/services/api'
import { useAuthStore } from '@/stores/authStore'
import toast from 'react-hot-toast'
import { 
  User, 
  Mail, 
  Lock, 
  Globe, 
  Clock,
  Save,
  Loader2,
  Eye,
  EyeOff,
  Shield
} from 'lucide-react'
import clsx from 'clsx'

export default function SettingsPage() {
  const { user, fetchUser } = useAuthStore()
  const [fullName, setFullName] = useState(user?.full_name || '')
  const [timezone, setTimezone] = useState(user?.timezone || 'Europe/Belgrade')
  const [language, setLanguage] = useState(user?.language || 'sr')
  
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [showPasswords, setShowPasswords] = useState(false)

  const { data: stats } = useQuery({
    queryKey: ['user-stats'],
    queryFn: () => usersApi.getStats(),
  })

  const updateProfileMutation = useMutation({
    mutationFn: () => usersApi.updateMe({ 
      full_name: fullName, 
      timezone, 
      language 
    }),
    onSuccess: () => {
      fetchUser()
      toast.success('Profil je ažuriran!')
    },
    onError: () => toast.error('Greška pri ažuriranju'),
  })

  const changePasswordMutation = useMutation({
    mutationFn: () => usersApi.changePassword(currentPassword, newPassword),
    onSuccess: () => {
      setCurrentPassword('')
      setNewPassword('')
      setConfirmPassword('')
      toast.success('Lozinka je promenjena!')
    },
    onError: () => toast.error('Greška pri promeni lozinke'),
  })

  const handleUpdateProfile = (e: React.FormEvent) => {
    e.preventDefault()
    updateProfileMutation.mutate()
  }

  const handleChangePassword = (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!currentPassword || !newPassword || !confirmPassword) {
      toast.error('Popunite sva polja')
      return
    }
    
    if (newPassword !== confirmPassword) {
      toast.error('Nove lozinke se ne poklapaju')
      return
    }
    
    if (newPassword.length < 8) {
      toast.error('Lozinka mora imati najmanje 8 karaktera')
      return
    }
    
    changePasswordMutation.mutate()
  }

  const timezones = [
    'Europe/Belgrade',
    'Europe/Zagreb',
    'Europe/Sarajevo',
    'Europe/Podgorica',
    'Europe/Ljubljana',
    'Europe/Vienna',
    'Europe/Berlin',
    'Europe/London',
    'America/New_York',
    'America/Los_Angeles',
  ]

  const languages = [
    { code: 'sr', name: 'Srpski' },
    { code: 'en', name: 'English' },
    { code: 'hr', name: 'Hrvatski' },
    { code: 'bs', name: 'Bosanski' },
  ]

  return (
    <div className="max-w-3xl mx-auto space-y-8 animate-fade-in">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Podešavanja</h1>
        <p className="text-gray-500 mt-1">Upravljajte vašim profilom i nalogom</p>
      </div>

      <div className="card p-6">
        <div className="flex items-center gap-4 mb-6">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-primary-400 to-accent-400 flex items-center justify-center text-white text-2xl font-bold">
            {user?.full_name?.[0] || user?.email[0].toUpperCase()}
          </div>
          <div>
            <h2 className="text-xl font-semibold text-gray-900">
              {user?.full_name || 'Korisnik'}
            </h2>
            <p className="text-gray-500">{user?.email}</p>
          </div>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 p-4 rounded-xl bg-gray-50">
          <div className="text-center">
            <p className="text-2xl font-bold text-gray-900">{stats?.data?.total_documents || 0}</p>
            <p className="text-sm text-gray-500">Dokumenata</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-gray-900">{stats?.data?.translated_chunks || 0}</p>
            <p className="text-sm text-gray-500">Prevedeno</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-gray-900">{stats?.data?.total_quizzes || 0}</p>
            <p className="text-sm text-gray-500">Kvizova</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-gray-900">{stats?.data?.study_streak || 0}</p>
            <p className="text-sm text-gray-500">Dana niz</p>
          </div>
        </div>
      </div>

      <form onSubmit={handleUpdateProfile} className="card p-6 space-y-6">
        <div className="flex items-center gap-3 pb-4 border-b border-gray-100">
          <User className="w-5 h-5 text-gray-400" />
          <h2 className="text-lg font-semibold text-gray-900">Lični podaci</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label htmlFor="fullName" className="label">
              Ime i prezime
            </label>
            <div className="relative">
              <User className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                id="fullName"
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                className="input pl-12"
                placeholder="Petar Petrović"
              />
            </div>
          </div>

          <div>
            <label htmlFor="email" className="label">
              Email adresa
            </label>
            <div className="relative">
              <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                id="email"
                type="email"
                value={user?.email || ''}
                className="input pl-12 bg-gray-50 cursor-not-allowed"
                disabled
              />
            </div>
            <p className="text-xs text-gray-400 mt-1">Email se ne može promeniti</p>
          </div>

          <div>
            <label htmlFor="timezone" className="label">
              Vremenska zona
            </label>
            <div className="relative">
              <Clock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
              <select
                id="timezone"
                value={timezone}
                onChange={(e) => setTimezone(e.target.value)}
                className="input pl-12 appearance-none"
              >
                {timezones.map((tz) => (
                  <option key={tz} value={tz}>{tz}</option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label htmlFor="language" className="label">
              Jezik
            </label>
            <div className="relative">
              <Globe className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
              <select
                id="language"
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                className="input pl-12 appearance-none"
              >
                {languages.map((lang) => (
                  <option key={lang.code} value={lang.code}>{lang.name}</option>
                ))}
              </select>
            </div>
          </div>
        </div>

        <div className="flex justify-end">
          <button
            type="submit"
            disabled={updateProfileMutation.isPending}
            className="btn-primary"
          >
            {updateProfileMutation.isPending ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <>
                <Save className="w-5 h-5" />
                Sačuvaj izmene
              </>
            )}
          </button>
        </div>
      </form>

      <form onSubmit={handleChangePassword} className="card p-6 space-y-6">
        <div className="flex items-center gap-3 pb-4 border-b border-gray-100">
          <Shield className="w-5 h-5 text-gray-400" />
          <h2 className="text-lg font-semibold text-gray-900">Promena lozinke</h2>
        </div>

        <div className="space-y-4">
          <div>
            <label htmlFor="currentPassword" className="label">
              Trenutna lozinka
            </label>
            <div className="relative">
              <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                id="currentPassword"
                type={showPasswords ? 'text' : 'password'}
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                className="input pl-12 pr-12"
                placeholder="••••••••"
              />
              <button
                type="button"
                onClick={() => setShowPasswords(!showPasswords)}
                className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
              >
                {showPasswords ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
              </button>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label htmlFor="newPassword" className="label">
                Nova lozinka
              </label>
              <div className="relative">
                <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  id="newPassword"
                  type={showPasswords ? 'text' : 'password'}
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  className="input pl-12"
                  placeholder="••••••••"
                />
              </div>
            </div>

            <div>
              <label htmlFor="confirmPassword" className="label">
                Potvrdi novu lozinku
              </label>
              <div className="relative">
                <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  id="confirmPassword"
                  type={showPasswords ? 'text' : 'password'}
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className={clsx(
                    "input pl-12",
                    confirmPassword && newPassword !== confirmPassword && "input-error"
                  )}
                  placeholder="••••••••"
                />
              </div>
              {confirmPassword && newPassword !== confirmPassword && (
                <p className="text-xs text-red-500 mt-1">Lozinke se ne poklapaju</p>
              )}
            </div>
          </div>
        </div>

        <div className="flex justify-end">
          <button
            type="submit"
            disabled={changePasswordMutation.isPending}
            className="btn-primary"
          >
            {changePasswordMutation.isPending ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <>
                <Lock className="w-5 h-5" />
                Promeni lozinku
              </>
            )}
          </button>
        </div>
      </form>

      <div className="card p-6 border-red-100">
        <div className="flex items-center gap-3 pb-4 border-b border-gray-100">
          <Shield className="w-5 h-5 text-red-400" />
          <h2 className="text-lg font-semibold text-gray-900">Opasna zona</h2>
        </div>
        <div className="mt-4 flex items-center justify-between">
          <div>
            <p className="font-medium text-gray-900">Izbriši nalog</p>
            <p className="text-sm text-gray-500">Ova radnja je nepovratna</p>
          </div>
          <button
            disabled
            className="btn-danger opacity-50 cursor-not-allowed"
          >
            Izbriši nalog
          </button>
        </div>
      </div>
    </div>
  )
}
