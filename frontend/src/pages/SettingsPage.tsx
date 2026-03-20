import { useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { usersApi, aiSettingsApi } from '@/services/api'
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
  Shield,
  Bell,
  FileText,
  Languages,
  Trophy,
  Calendar,
  Bot,
  Key,
  Cpu,
  Cloud,
  CheckCircle2
} from 'lucide-react'
import clsx from 'clsx'
import StudyPlanTab from '@/components/StudyPlanTab'

type Tab = 'profil' | 'sigurnost' | 'podesavanja' | 'plan' | 'ai'

export default function SettingsPage() {
  const { user, fetchUser } = useAuthStore()
  const [activeTab, setActiveTab] = useState<Tab>('profil')
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

  const userInitial = (user?.full_name?.[0] || user?.email?.[0] || 'U').toUpperCase()

  const tabs: { id: Tab; label: string; icon: React.ElementType }[] = [
    { id: 'profil', label: 'Profil', icon: User },
    { id: 'sigurnost', label: 'Sigurnost', icon: Shield },
    { id: 'podesavanja', label: 'Podešavanja', icon: Bell },
    { id: 'plan', label: 'Plan učenja', icon: Calendar },
    { id: 'ai', label: 'AI Provajder', icon: Bot },
  ]

  return (
    <div className="max-w-3xl mx-auto space-y-6 animate-fade-in">
      {/* Page header */}
      <div>
        <h1 className="text-3xl font-extrabold text-gray-900">Podešavanja</h1>
        <p className="text-gray-500 mt-1 text-sm">Upravljajte vašim profilom i nalogom</p>
      </div>

      {/* Profile hero card */}
      <div className="card overflow-hidden">
        <div className="h-24 bg-gradient-to-r from-indigo-500 via-violet-500 to-purple-600" />
        <div className="px-6 pb-6 -mt-8">
          <div className="flex items-end gap-4 mb-4">
            <div className="w-16 h-16 rounded-2xl flex items-center justify-center text-white text-2xl font-extrabold ring-4 ring-white shadow-lg"
              style={{ background: 'linear-gradient(135deg, #6366f1, #8b5cf6)' }}>
              {userInitial}
            </div>
            <div className="pb-1">
              <h2 className="text-lg font-extrabold text-gray-900">{user?.full_name || 'Korisnik'}</h2>
              <p className="text-sm text-gray-500">{user?.email}</p>
            </div>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {[
              { icon: FileText,  label: 'Dokumenta',   value: stats?.data?.total_documents || 0,  color: 'bg-indigo-50 text-indigo-600' },
              { icon: Languages, label: 'Prevedeno',    value: stats?.data?.translated_chunks || 0, color: 'bg-violet-50 text-violet-600' },
              { icon: Trophy,    label: 'Kvizova',      value: stats?.data?.total_quizzes || 0,    color: 'bg-amber-50 text-amber-600' },
              { icon: Clock,     label: 'Dana niz',     value: stats?.data?.study_streak || 0,     color: 'bg-emerald-50 text-emerald-600' },
            ].map((item, i) => (
              <div key={i} className={clsx('rounded-2xl p-3 text-center', item.color)}>
                <p className="text-2xl font-extrabold">{item.value}</p>
                <p className="text-xs font-medium mt-0.5 opacity-80">{item.label}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Tab navigation */}
      <div className="flex gap-1 p-1 bg-gray-100 rounded-2xl">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={clsx(
              'flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl text-sm font-semibold transition-all duration-200',
              activeTab === tab.id
                ? 'bg-gradient-to-r from-indigo-500 to-violet-600 text-white shadow-md shadow-indigo-500/25'
                : 'text-gray-500 hover:text-gray-700 hover:bg-white/60'
            )}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab: Profil */}
      {activeTab === 'profil' && (
        <form onSubmit={handleUpdateProfile} className="card p-6 space-y-5">
          <h3 className="text-base font-bold text-gray-900">Lični podaci</h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            <div>
              <label htmlFor="fullName" className="label">Ime i prezime</label>
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
              <label htmlFor="email" className="label">Email adresa</label>
              <div className="relative">
                <Mail className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" style={{ width: '18px', height: '18px' }} />
                <input
                  id="email"
                  type="email"
                  value={user?.email || ''}
                  className="input pl-11 bg-gray-50 cursor-not-allowed text-gray-400"
                  disabled
                />
              </div>
              <p className="text-xs text-gray-400 mt-1">Email se ne može promeniti</p>
            </div>

            <div>
              <label htmlFor="timezone" className="label">Vremenska zona</label>
              <div className="relative">
                <Clock className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" style={{ width: '18px', height: '18px' }} />
                <select
                  id="timezone"
                  value={timezone}
                  onChange={(e) => setTimezone(e.target.value)}
                  className="input pl-11 appearance-none"
                >
                  {timezones.map((tz) => (
                    <option key={tz} value={tz}>{tz}</option>
                  ))}
                </select>
              </div>
            </div>

            <div>
              <label htmlFor="language" className="label">Jezik interfejsa</label>
              <div className="relative">
                <Globe className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" style={{ width: '18px', height: '18px' }} />
                <select
                  id="language"
                  value={language}
                  onChange={(e) => setLanguage(e.target.value)}
                  className="input pl-11 appearance-none"
                >
                  {languages.map((lang) => (
                    <option key={lang.code} value={lang.code}>{lang.name}</option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          <div className="flex justify-end pt-2">
            <button
              type="submit"
              disabled={updateProfileMutation.isPending}
              className="btn-primary"
            >
              {updateProfileMutation.isPending ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <><Save className="w-4 h-4" /> Sačuvaj izmene</>
              )}
            </button>
          </div>
        </form>
      )}

      {/* Tab: Sigurnost */}
      {activeTab === 'sigurnost' && (
        <div className="space-y-5">
          <form onSubmit={handleChangePassword} className="card p-6 space-y-5">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-xl bg-indigo-100 flex items-center justify-center">
                <Lock className="w-4.5 h-4.5 text-indigo-600" style={{ width: '18px', height: '18px' }} />
              </div>
              <div>
                <h3 className="text-base font-bold text-gray-900">Promena lozinke</h3>
                <p className="text-xs text-gray-500">Ažurirajte vašu lozinku</p>
              </div>
              <button
                type="button"
                onClick={() => setShowPasswords(!showPasswords)}
                className="ml-auto p-2 rounded-xl hover:bg-gray-100 text-gray-400 transition-colors"
              >
                {showPasswords ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>

            <div>
              <label htmlFor="currentPassword" className="label">Trenutna lozinka</label>
              <div className="relative">
                <Lock className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" style={{ width: '18px', height: '18px' }} />
                <input
                  id="currentPassword"
                  type={showPasswords ? 'text' : 'password'}
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  className="input pl-11"
                  placeholder="••••••••"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label htmlFor="newPassword" className="label">Nova lozinka</label>
                <div className="relative">
                  <Lock className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" style={{ width: '18px', height: '18px' }} />
                  <input
                    id="newPassword"
                    type={showPasswords ? 'text' : 'password'}
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    className="input pl-11"
                    placeholder="••••••••"
                  />
                </div>
              </div>
              <div>
                <label htmlFor="confirmPassword" className="label">Potvrdi lozinku</label>
                <div className="relative">
                  <Lock className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" style={{ width: '18px', height: '18px' }} />
                  <input
                    id="confirmPassword"
                    type={showPasswords ? 'text' : 'password'}
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    className={clsx(
                      'input pl-11',
                      confirmPassword && newPassword !== confirmPassword && 'input-error'
                    )}
                    placeholder="••••••••"
                  />
                </div>
                {confirmPassword && newPassword !== confirmPassword && (
                  <p className="text-xs text-red-500 mt-1">Lozinke se ne poklapaju</p>
                )}
              </div>
            </div>

            <div className="flex justify-end pt-2">
              <button
                type="submit"
                disabled={changePasswordMutation.isPending}
                className="btn-primary"
              >
                {changePasswordMutation.isPending ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <><Lock className="w-4 h-4" /> Promeni lozinku</>
                )}
              </button>
            </div>
          </form>

          {/* Danger zone */}
          <div className="card p-6 border-red-100">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-9 h-9 rounded-xl bg-red-100 flex items-center justify-center">
                <Shield className="w-4.5 h-4.5 text-red-500" style={{ width: '18px', height: '18px' }} />
              </div>
              <div>
                <h3 className="text-base font-bold text-gray-900">Opasna zona</h3>
                <p className="text-xs text-gray-500">Nepovratne radnje</p>
              </div>
            </div>
            <div className="flex items-center justify-between p-4 rounded-2xl bg-red-50 border border-red-100">
              <div>
                <p className="font-semibold text-gray-900 text-sm">Izbriši nalog</p>
                <p className="text-xs text-gray-500">Svi vaši podaci biće trajno obrisani</p>
              </div>
              <button disabled className="btn-danger opacity-40 cursor-not-allowed text-sm">
                Izbriši nalog
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Tab: Podešavanja */}
      {activeTab === 'podesavanja' && (
        <div className="card p-6 space-y-5">
          <h3 className="text-base font-bold text-gray-900">Notifikacije i preference</h3>
          
          <div className="space-y-3">
            {[
              { label: 'Email notifikacije', desc: 'Primajte obaveštenja o napretku prevoda', checked: true },
              { label: 'Nedeljni izveštaj', desc: 'Pregled vašeg napretka svake nedelje', checked: false },
              { label: 'Podsetnik za učenje', desc: 'Dnevni podsetnik za pregled materijala', checked: true },
            ].map((item, i) => (
              <div key={i} className="flex items-center justify-between p-4 rounded-2xl bg-gray-50 hover:bg-gray-100/80 transition-colors">
                <div>
                  <p className="text-sm font-semibold text-gray-900">{item.label}</p>
                  <p className="text-xs text-gray-500 mt-0.5">{item.desc}</p>
                </div>
                <button
                  className={clsx(
                    'relative w-11 h-6 rounded-full transition-colors duration-200 flex-shrink-0',
                    item.checked ? 'bg-indigo-500' : 'bg-gray-300'
                  )}
                  disabled
                >
                  <span className={clsx(
                    'absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform duration-200',
                    item.checked && 'translate-x-5'
                  )} />
                </button>
              </div>
            ))}
          </div>

          <div className="pt-2 flex justify-end">
            <button disabled className="btn-primary opacity-50 cursor-not-allowed">
              <Save className="w-4 h-4" />
              Sačuvaj preference
            </button>
          </div>
        </div>
      )}

      {/* Tab: Plan učenja */}
      {activeTab === 'plan' && (
        <StudyPlanTab />
      )}

      {/* Tab: AI Provajder */}
      {activeTab === 'ai' && (
        <AIProviderTab />
      )}
    </div>
  )
}


// ================================================================================
// AI PROVIDER TAB
// ================================================================================
function AIProviderTab() {
  const { data: settings, refetch } = useQuery({
    queryKey: ['ai-settings'],
    queryFn: () => aiSettingsApi.get().then(r => r.data),
  })

  const [provider, setProvider] = useState<string>('')
  const [openaiKey, setOpenaiKey] = useState('')
  const [claudeKey, setClaudeKey] = useState('')
  const [geminiKey, setGeminiKey] = useState('')
  const [groqKey, setGroqKey] = useState('')
  const [mistralKey, setMistralKey] = useState('')
  const [deepseekKey, setDeepseekKey] = useState('')
  const [customBaseUrl, setCustomBaseUrl] = useState('')
  const [customKey, setCustomKey] = useState('')
  const [showKeys, setShowKeys] = useState<Record<string, boolean>>({})

  const toggleShow = (k: string) => setShowKeys(v => ({ ...v, [k]: !v[k] }))

  // Sync state when data loads
  if (settings && !provider) {
    setProvider(settings.ai_provider || 'auto')
    if (settings.custom_base_url && !customBaseUrl) setCustomBaseUrl(settings.custom_base_url)
  }

  const saveMutation = useMutation({
    mutationFn: () => aiSettingsApi.update({
      ai_provider: provider,
      ai_api_key_openai: openaiKey || undefined,
      ai_api_key_claude: claudeKey || undefined,
      ai_api_key_gemini: geminiKey || undefined,
      ai_api_key_groq: groqKey || undefined,
      ai_api_key_mistral: mistralKey || undefined,
      ai_api_key_deepseek: deepseekKey || undefined,
      ai_custom_base_url: customBaseUrl || undefined,
      ai_api_key_custom: customKey || undefined,
    }),
    onSuccess: () => {
      toast.success('AI podešavanja sačuvana!')
      setOpenaiKey(''); setClaudeKey(''); setGeminiKey('')
      setGroqKey(''); setMistralKey(''); setDeepseekKey(''); setCustomKey('')
      refetch()
    },
    onError: () => toast.error('Greška pri čuvanju'),
  })

  type ProviderConfig = {
    id: string
    name: string
    desc: string
    icon: typeof Bot
    color: string
    requiresKey: boolean
    badge?: string
  }

  const providers: ProviderConfig[] = [
    {
      id: 'auto',
      name: 'Automatski',
      desc: 'Sistem automatski bira dostupni provajder (preporučeno)',
      icon: Bot,
      color: 'indigo',
      requiresKey: false,
    },
    {
      id: 'ollama',
      name: 'Ollama (lokalni)',
      desc: 'Besplatan lokalni AI model. Nema potrebe za API ključem.',
      icon: Cpu,
      color: 'green',
      requiresKey: false,
      badge: 'Besplatan',
    },
    {
      id: 'openai',
      name: 'OpenAI (GPT)',
      desc: 'GPT-4o i GPT-4o-mini modeli.',
      icon: Cloud,
      color: 'blue',
      requiresKey: true,
    },
    {
      id: 'claude',
      name: 'Anthropic Claude',
      desc: 'Claude 3.5 Sonnet i ostali Claude modeli.',
      icon: Cloud,
      color: 'orange',
      requiresKey: true,
    },
    {
      id: 'gemini',
      name: 'Google Gemini',
      desc: 'Gemini 1.5 Flash i Pro modeli. Besplatan tier dostupan.',
      icon: Cloud,
      color: 'sky',
      requiresKey: true,
      badge: 'Besplatan tier',
    },
    {
      id: 'groq',
      name: 'Groq',
      desc: 'Ultra-brzi Llama 3 i Mixtral modeli putem Groq Cloud-a.',
      icon: Cpu,
      color: 'purple',
      requiresKey: true,
      badge: 'Besplatan tier',
    },
    {
      id: 'mistral',
      name: 'Mistral AI',
      desc: 'Mistral Large i Mistral 7B modeli.',
      icon: Cloud,
      color: 'yellow',
      requiresKey: true,
    },
    {
      id: 'deepseek',
      name: 'DeepSeek',
      desc: 'DeepSeek V3 i R1 modeli. Odličan odnos cene i kvaliteta.',
      icon: Cpu,
      color: 'cyan',
      requiresKey: true,
      badge: 'Novi',
    },
    {
      id: 'custom',
      name: 'Custom (OpenAI-compatible)',
      desc: 'LM Studio, vLLM, Ollama REST, ili bilo koji OpenAI-compatible API.',
      icon: Key,
      color: 'slate',
      requiresKey: true,
    },
  ]

  const colorMap: Record<string, string> = {
    indigo: 'border-indigo-500 bg-indigo-50',
    green:  'border-green-500 bg-green-50',
    blue:   'border-blue-500 bg-blue-50',
    orange: 'border-orange-500 bg-orange-50',
    sky:    'border-sky-500 bg-sky-50',
    purple: 'border-purple-500 bg-purple-50',
    yellow: 'border-yellow-500 bg-yellow-50',
    slate:  'border-slate-500 bg-slate-50',
    cyan:   'border-cyan-500 bg-cyan-50',
  }

  const badgeColor: Record<string, string> = {
    indigo: 'bg-indigo-100 text-indigo-700',
    green:  'bg-green-100 text-green-700',
    sky:    'bg-sky-100 text-sky-700',
    purple: 'bg-purple-100 text-purple-700',
  }

  type KeyField = {
    label: string
    placeholder: string
    value: string
    onChange: (v: string) => void
    savedKey: string | undefined | null
    hasKey: boolean
    link: string
    linkLabel: string
    bgClass: string
    borderClass: string
    textClass: string
    showExtra?: React.ReactNode
  }

  const keyFields: Record<string, KeyField> = {
    openai: {
      label: 'OpenAI API ključ',
      placeholder: settings?.has_openai_key ? 'Ostavi prazno da zadržiš ključ' : 'sk-...',
      value: openaiKey, onChange: setOpenaiKey,
      savedKey: settings?.openai_key_preview, hasKey: settings?.has_openai_key,
      link: 'https://platform.openai.com/api-keys', linkLabel: 'platform.openai.com',
      bgClass: 'bg-blue-50', borderClass: 'border-blue-200', textClass: 'text-blue-700',
    },
    claude: {
      label: 'Anthropic Claude API ključ',
      placeholder: settings?.has_claude_key ? 'Ostavi prazno da zadržiš ključ' : 'sk-ant-...',
      value: claudeKey, onChange: setClaudeKey,
      savedKey: settings?.claude_key_preview, hasKey: settings?.has_claude_key,
      link: 'https://console.anthropic.com/', linkLabel: 'console.anthropic.com',
      bgClass: 'bg-orange-50', borderClass: 'border-orange-200', textClass: 'text-orange-700',
    },
    gemini: {
      label: 'Google Gemini API ključ',
      placeholder: settings?.has_gemini_key ? 'Ostavi prazno da zadržiš ključ' : 'AIza...',
      value: geminiKey, onChange: setGeminiKey,
      savedKey: settings?.gemini_key_preview, hasKey: settings?.has_gemini_key,
      link: 'https://aistudio.google.com/app/apikey', linkLabel: 'aistudio.google.com',
      bgClass: 'bg-sky-50', borderClass: 'border-sky-200', textClass: 'text-sky-700',
    },
    groq: {
      label: 'Groq API ključ',
      placeholder: settings?.has_groq_key ? 'Ostavi prazno da zadržiš ključ' : 'gsk_...',
      value: groqKey, onChange: setGroqKey,
      savedKey: settings?.groq_key_preview, hasKey: settings?.has_groq_key,
      link: 'https://console.groq.com/keys', linkLabel: 'console.groq.com',
      bgClass: 'bg-purple-50', borderClass: 'border-purple-200', textClass: 'text-purple-700',
    },
    mistral: {
      label: 'Mistral AI API ključ',
      placeholder: settings?.has_mistral_key ? 'Ostavi prazno da zadržiš ključ' : 'xxxx...',
      value: mistralKey, onChange: setMistralKey,
      savedKey: settings?.mistral_key_preview, hasKey: settings?.has_mistral_key,
      link: 'https://console.mistral.ai/api-keys/', linkLabel: 'console.mistral.ai',
      bgClass: 'bg-yellow-50', borderClass: 'border-yellow-200', textClass: 'text-yellow-700',
    },
    deepseek: {
      label: 'DeepSeek API ključ',
      placeholder: settings?.has_deepseek_key ? 'Ostavi prazno da zadržiš ključ' : 'sk-...',
      value: deepseekKey, onChange: setDeepseekKey,
      savedKey: settings?.deepseek_key_preview, hasKey: settings?.has_deepseek_key,
      link: 'https://platform.deepseek.com/api-keys', linkLabel: 'platform.deepseek.com',
      bgClass: 'bg-cyan-50', borderClass: 'border-cyan-200', textClass: 'text-cyan-700',
    },
  }

  const showKeyField = (id: string) =>
    provider === id || (provider === 'auto' && ['openai', 'claude'].includes(id))

  const KeyInput = ({ id }: { id: string }) => {
    const f = keyFields[id]
    if (!f) return null
    return (
      <div className={clsx('rounded-xl p-5 space-y-3', f.bgClass)}>
        <div className="flex items-center gap-2">
          <Key className={clsx('w-4 h-4', f.textClass)} />
          <span className={clsx('font-medium text-sm', f.textClass)}>{f.label}</span>
          {f.hasKey && (
            <span className={clsx('text-xs px-2 py-0.5 rounded-full', f.bgClass, f.textClass, 'border', f.borderClass)}>
              Sačuvan: {f.savedKey}
            </span>
          )}
        </div>
        <div className="relative">
          <input
            type={showKeys[id] ? 'text' : 'password'}
            placeholder={f.placeholder}
            value={f.value}
            onChange={e => f.onChange(e.target.value)}
            className={clsx('w-full px-3 py-2 pr-10 border rounded-lg text-sm focus:outline-none focus:ring-2 bg-white', f.borderClass)}
          />
          <button type="button" onClick={() => toggleShow(id)}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400">
            {showKeys[id] ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
          </button>
        </div>
        <p className={clsx('text-xs', f.textClass)}>
          Dobij ključ na{' '}
          <a href={f.link} target="_blank" rel="noreferrer" className="underline font-medium">{f.linkLabel}</a>
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold text-gray-900">AI Provajder za generisanje kvizova</h3>
        <p className="text-sm text-gray-500 mt-1">
          Izaberite koji AI model će generisati pitanja iz vaših PDF dokumenata i odgovarati na pitanja.
        </p>
      </div>

      {/* Provider cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-3">
        {providers.map(p => {
          const Icon = p.icon
          const isSelected = provider === p.id
          return (
            <button
              key={p.id}
              onClick={() => setProvider(p.id)}
              className={clsx(
                'relative text-left p-4 rounded-xl border-2 transition-all duration-200',
                isSelected ? colorMap[p.color] : 'border-gray-200 bg-white hover:border-gray-300'
              )}
            >
              {isSelected && (
                <CheckCircle2 className="absolute top-3 right-3 w-4 h-4" />
              )}
              {p.badge && (
                <span className={clsx(
                  'absolute top-3 right-3 text-[10px] font-bold px-1.5 py-0.5 rounded-full',
                  isSelected ? 'hidden' : (badgeColor[p.color] || 'bg-gray-100 text-gray-600')
                )}>
                  {p.badge}
                </span>
              )}
              <div className="flex items-center gap-2 mb-2">
                <div className={clsx(
                  'w-8 h-8 rounded-lg flex items-center justify-center',
                  isSelected ? 'bg-white/60' : 'bg-gray-100'
                )}>
                  <Icon className="w-4 h-4" />
                </div>
                <span className="font-semibold text-gray-900 text-sm leading-tight">{p.name}</span>
              </div>
              <p className="text-xs text-gray-500 leading-snug">{p.desc}</p>
            </button>
          )
        })}
      </div>

      {/* Key inputs — shown for active provider */}
      {['openai', 'claude', 'gemini', 'groq', 'mistral', 'deepseek'].map(id =>
        showKeyField(id) ? <KeyInput key={id} id={id} /> : null
      )}

      {/* Ollama info */}
      {provider === 'ollama' && (
        <div className="bg-green-50 rounded-xl p-5 flex gap-3">
          <Cpu className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-medium text-green-900 text-sm">Lokalni Ollama model</p>
            <p className="text-xs text-green-700 mt-1">
              Nema potrebe za API ključem. Ollama mora biti pokrenut na serveru na portu 11434.
              Preporučeni modeli:{' '}
              <code className="bg-green-100 px-1 rounded">llama3.1</code>,{' '}
              <code className="bg-green-100 px-1 rounded">mistral</code>,{' '}
              <code className="bg-green-100 px-1 rounded">qwen2.5</code>
            </p>
          </div>
        </div>
      )}

      {/* Custom provider */}
      {provider === 'custom' && (
        <div className="bg-slate-50 rounded-xl p-5 space-y-4 border border-slate-200">
          <div className="flex items-center gap-2">
            <Key className="w-4 h-4 text-slate-600" />
            <span className="font-medium text-slate-900 text-sm">Custom OpenAI-compatible endpoint</span>
          </div>
          <div className="space-y-1">
            <label className="text-xs font-medium text-slate-700">Base URL</label>
            <input
              type="text"
              placeholder="http://localhost:1234/v1"
              value={customBaseUrl}
              onChange={e => setCustomBaseUrl(e.target.value)}
              className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-slate-400 bg-white"
            />
            <p className="text-xs text-slate-500">
              LM Studio: <code className="bg-slate-100 px-1 rounded">http://localhost:1234/v1</code> ·{' '}
              vLLM: <code className="bg-slate-100 px-1 rounded">http://localhost:8000/v1</code>
            </p>
          </div>
          <div className="space-y-1">
            <label className="text-xs font-medium text-slate-700">
              API ključ{' '}
              <span className="font-normal text-slate-500">(opciono — ostavi prazno ako nije potreban)</span>
            </label>
            <div className="relative">
              <input
                type={showKeys['custom'] ? 'text' : 'password'}
                placeholder={settings?.has_custom_key ? 'Ostavi prazno da zadržiš ključ' : 'sk-... ili ostavi prazno'}
                value={customKey}
                onChange={e => setCustomKey(e.target.value)}
                className="w-full px-3 py-2 pr-10 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-slate-400 bg-white"
              />
              <button type="button" onClick={() => toggleShow('custom')}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400">
                {showKeys['custom'] ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
            {settings?.has_custom_key && (
              <p className="text-xs text-slate-500">Trenutni ključ: {settings.custom_key_preview}</p>
            )}
          </div>
        </div>
      )}

      <button
        onClick={() => saveMutation.mutate()}
        disabled={saveMutation.isPending || !provider}
        className="btn btn-primary gap-2"
      >
        {saveMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
        Sačuvaj podešavanja
      </button>
    </div>
  )
}
