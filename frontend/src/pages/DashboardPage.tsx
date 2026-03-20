import { useQuery } from '@tanstack/react-query'
import { usersApi, documentsApi, analyticsApi, aiSettingsApi } from '@/services/api'
import { 
  FileText, 
  Languages, 
  TrendingUp,
  BookOpen,
  ArrowRight,
  Sparkles,
  Flame,
  Trophy,
  Plus,
  ChevronRight,
  BarChart2,
  Bot,
  Cpu,
  Cloud,
  Settings
} from 'lucide-react'
import { Link } from 'react-router-dom'
import { useAuthStore } from '@/stores/authStore'
import clsx from 'clsx'

export default function DashboardPage() {
  const { user } = useAuthStore()

  const { data: stats } = useQuery({
    queryKey: ['user-stats'],
    queryFn: () => usersApi.getStats(),
  })

  const { data: recentDocs } = useQuery({
    queryKey: ['documents', 1, 5],
    queryFn: () => documentsApi.list(0, 5),
  })

  const { data: analyticsData } = useQuery({
    queryKey: ['analytics-overview'],
    queryFn: () => analyticsApi.getOverview(),
    staleTime: 60_000,
  })

  const { data: aiSettingsData } = useQuery({
    queryKey: ['ai-settings'],
    queryFn: () => aiSettingsApi.get().then(r => r.data),
  })

  const userStats = {
    total_documents: stats?.data?.total_documents ?? 0,
    total_chunks: stats?.data?.total_chunks ?? 0,
    translated_chunks: stats?.data?.translated_chunks ?? 0,
    total_quizzes_taken: stats?.data?.total_quizzes_taken ?? 0,
    average_score: stats?.data?.average_score ?? 0,
    study_streak: stats?.data?.study_streak ?? stats?.data?.current_streak_days ?? 0,
  }

  const analytics = (analyticsData as any)?.data

  const translationPct = userStats.total_chunks > 0
    ? Math.round((userStats.translated_chunks / userStats.total_chunks) * 100)
    : 0
  const translationDisplay = translationPct === 0 && userStats.translated_chunks > 0
    ? '< 1%'
    : `${translationPct}%`

  const today = new Date().toLocaleDateString('sr-RS', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })
  const now = new Date().toLocaleTimeString('sr-RS', { hour: '2-digit', minute: '2-digit' })

  const statCards = [
    {
      name: 'Ukupno dokumenata',
      value: userStats.total_documents,
      icon: FileText,
      gradient: 'from-indigo-500 to-indigo-600',
      lightBg: 'bg-indigo-50',
      iconBg: 'bg-gradient-to-br from-indigo-500 to-indigo-600',
      iconColor: 'text-indigo-600',
      trend: '+2 ovog meseca',
    },
    {
      name: 'Prevedeni odlomci',
      value: userStats.translated_chunks,
      icon: Languages,
      gradient: 'from-violet-500 to-violet-600',
      lightBg: 'bg-violet-50',
      iconBg: 'bg-gradient-to-br from-violet-500 to-violet-600',
      iconColor: 'text-violet-600',
      trend: `${translationDisplay} ukupno`,
    },
    {
      name: 'Napredak prevoda',
      value: translationDisplay,
      icon: TrendingUp,
      gradient: 'from-cyan-500 to-cyan-600',
      lightBg: 'bg-cyan-50',
      iconBg: 'bg-gradient-to-br from-cyan-500 to-cyan-600',
      iconColor: 'text-cyan-600',
      trend: `${userStats.total_chunks} ukupno`,
    },
    {
      name: 'Dana niz učenja',
      value: userStats.study_streak,
      icon: Flame,
      gradient: 'from-orange-500 to-amber-500',
      lightBg: 'bg-orange-50',
      iconBg: 'bg-gradient-to-br from-orange-500 to-amber-500',
      iconColor: 'text-orange-600',
      trend: 'Nastavite niz!',
    },
  ]

  const getStatusConfig = (status: string) => {
    const configs: Record<string, { badge: string; strip: string; label: string }> = {
      pending:    { badge: 'badge-gray',    strip: 'from-gray-400 to-gray-500',     label: 'Na čekanju' },
      processing: { badge: 'badge-primary', strip: 'from-indigo-400 to-indigo-500', label: 'Obrađuje se' },
      completed:  { badge: 'badge-success', strip: 'from-green-400 to-emerald-500', label: 'Obrađeno' },
      translating:{ badge: 'badge-primary', strip: 'from-violet-400 to-violet-500', label: 'Prevodi se' },
      error:      { badge: 'badge-error',   strip: 'from-red-400 to-red-500',       label: 'Greška' },
    }
    return configs[status] || configs['pending']
  }

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-extrabold text-gray-900">
            Dobrodošli, {user?.full_name?.split(' ')[0] || 'korisnik'}! 👋
          </h1>
          <p className="text-gray-500 mt-1 capitalize">{today} • {now}</p>
        </div>
        {userStats.study_streak > 0 && (
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-2xl text-white text-sm font-semibold shadow-lg shadow-orange-500/25"
            style={{ background: 'linear-gradient(135deg, #f97316, #ef4444)' }}>
            <Flame className="w-4 h-4" />
            {userStats.study_streak} dana niz
          </div>
        )}
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        {statCards.map((stat, i) => (
          <div
            key={stat.name}
            className="card p-6 relative overflow-hidden group hover:scale-[1.02] hover:shadow-lg transition-all duration-200"
            style={{ animationDelay: `${i * 80}ms` }}
          >
            {/* Background decoration */}
            <div className={clsx('absolute -top-8 -right-8 w-28 h-28 rounded-full opacity-[0.07]', stat.iconBg)} />
            
            <div className="flex items-start justify-between mb-4">
              <div className={clsx('w-11 h-11 rounded-2xl flex items-center justify-center shadow-lg', stat.iconBg)}>
                <stat.icon className="w-5 h-5 text-white" />
              </div>
            </div>
            <p className="text-3xl font-extrabold text-gray-900 mb-1">{stat.value}</p>
            <p className="text-sm text-gray-500 font-medium mb-2">{stat.name}</p>
            <p className="text-xs text-gray-400">{stat.trend}</p>
          </div>
        ))}
      </div>

      {/* Main grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent documents - 2/3 */}
        <div className="lg:col-span-2">
          <div className="card overflow-hidden">
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
              <h2 className="text-base font-bold text-gray-900">Nedavni dokumenti</h2>
              <Link to="/documents" className="text-sm text-primary-600 font-semibold hover:text-primary-700 flex items-center gap-1 transition-colors">
                Vidi sve <ChevronRight className="w-4 h-4" />
              </Link>
            </div>

            {recentDocs?.data?.items?.length ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-0 divide-y sm:divide-y-0 sm:divide-x divide-gray-100">
                {recentDocs.data.items.slice(0, 4).map((doc: any) => {
                  const cfg = getStatusConfig(doc.status)
                  const pct = doc.total_chunks > 0
                    ? Math.round(((doc.translated_chunks || 0) / doc.total_chunks) * 100)
                    : 0
                  return (
                    <Link
                      key={doc.id}
                      to={`/documents/${doc.id}`}
                      className="block p-5 hover:bg-gray-50/80 transition-colors group/card"
                    >
                      {/* Colored strip */}
                      <div className={clsx('h-1.5 rounded-full mb-4 bg-gradient-to-r', cfg.strip)} />
                      
                      <div className="flex items-start justify-between mb-2">
                        <div className="w-9 h-9 rounded-xl bg-indigo-50 flex items-center justify-center flex-shrink-0">
                          <BookOpen className="w-4.5 h-4.5 text-indigo-600" style={{ width: '18px', height: '18px' }} />
                        </div>
                        <span className={clsx('badge', cfg.badge)}>{cfg.label}</span>
                      </div>
                      
                      <h3 className="font-semibold text-gray-900 text-sm line-clamp-2 mt-2 mb-1 group-hover/card:text-primary-700 transition-colors">
                        {doc.title}
                      </h3>
                      <p className="text-xs text-gray-400 mb-3">
                        {doc.total_pages} str • {doc.total_chunks} odl • {new Date(doc.created_at).toLocaleString('sr-RS', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })}
                      </p>
                      
                      {doc.total_chunks > 0 && (
                        <div>
                          <div className="flex justify-between text-xs text-gray-400 mb-1">
                            <span>Prevod</span>
                            <span>{pct}%</span>
                          </div>
                          <div className="progress-bar">
                            <div
                              className="progress-fill bg-gradient-to-r from-indigo-500 to-violet-500"
                              style={{ width: `${pct}%` }}
                            />
                          </div>
                        </div>
                      )}
                    </Link>
                  )
                })}
              </div>
            ) : (
              <div className="p-14 text-center">
                <div className="w-16 h-16 rounded-2xl bg-indigo-50 flex items-center justify-center mx-auto mb-4">
                  <FileText className="w-8 h-8 text-indigo-400" />
                </div>
                <p className="text-gray-700 font-semibold mb-1">Nema dokumenata</p>
                <p className="text-gray-400 text-sm mb-5">Uploadujte PDF da biste počeli</p>
                <Link to="/documents" className="btn-primary btn-sm">
                  <Plus className="w-4 h-4" />
                  Dodaj dokument
                </Link>
              </div>
            )}
          </div>
        </div>

        {/* Sidebar - 1/3 */}
        <div className="space-y-5">
          {/* Quick actions */}
          <div className="card p-5">
            <h2 className="text-sm font-bold text-gray-900 mb-4">Brze akcije</h2>
            <div className="space-y-2">
              <Link
                to="/documents"
                className="flex items-center gap-3 p-3 rounded-xl bg-indigo-50 hover:bg-indigo-100 transition-colors group"
              >
                <div className="w-8 h-8 rounded-lg bg-indigo-500 flex items-center justify-center">
                  <Plus className="w-4 h-4 text-white" />
                </div>
                <span className="text-sm font-semibold text-indigo-700">Dodaj dokument</span>
                <ArrowRight className="w-4 h-4 text-indigo-400 ml-auto group-hover:translate-x-0.5 transition-transform" />
              </Link>
              <Link
                to="/review"
                className="flex items-center gap-3 p-3 rounded-xl bg-violet-50 hover:bg-violet-100 transition-colors group"
              >
                <div className="w-8 h-8 rounded-lg bg-violet-500 flex items-center justify-center">
                  <Languages className="w-4 h-4 text-white" />
                </div>
                <span className="text-sm font-semibold text-violet-700">Pregledaj prevode</span>
                <ArrowRight className="w-4 h-4 text-violet-400 ml-auto group-hover:translate-x-0.5 transition-transform" />
              </Link>
              <Link
                to="/quizzes"
                className="flex items-center gap-3 p-3 rounded-xl bg-emerald-50 hover:bg-emerald-100 transition-colors group"
              >
                <div className="w-8 h-8 rounded-lg bg-emerald-500 flex items-center justify-center">
                  <Trophy className="w-4 h-4 text-white" />
                </div>
                <span className="text-sm font-semibold text-emerald-700">Kvizovi</span>
                {userStats.total_quizzes_taken > 0 && (
                  <span className="text-xs text-emerald-500 ml-auto">{userStats.total_quizzes_taken} kvizova</span>
                )}
                <ArrowRight className="w-4 h-4 text-emerald-400 ml-auto group-hover:translate-x-0.5 transition-transform" />
              </Link>
              <Link
                to="/analytics"
                className="flex items-center gap-3 p-3 rounded-xl bg-amber-50 hover:bg-amber-100 transition-colors group"
              >
                <div className="w-8 h-8 rounded-lg bg-amber-500 flex items-center justify-center">
                  <BarChart2 className="w-4 h-4 text-white" />
                </div>
                <span className="text-sm font-semibold text-amber-700">Analitika</span>
                {analytics?.avg_score > 0 && (
                  <span className="text-xs text-amber-500 ml-auto">avg {analytics.avg_score}%</span>
                )}
                <ArrowRight className="w-4 h-4 text-amber-400 ml-auto group-hover:translate-x-0.5 transition-transform" />
              </Link>
            </div>
          </div>

          {/* Translation progress */}
          <div className="card p-5">
            <h3 className="text-sm font-bold text-gray-900 mb-4">Napredak prevoda</h3>
            {userStats.total_chunks === 0 ? (
              <div className="text-center py-3">
                <p className="text-sm text-gray-400">Još nema obrađenih dokumenata</p>
                <Link to="/documents" className="text-xs text-indigo-500 hover:underline mt-1 inline-block">
                  Dodaj dokument →
                </Link>
              </div>
            ) : (
              <>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs text-gray-500">Prevedeni odlomci</span>
                  <span className="text-xs font-bold text-gray-900">
                    {userStats.translated_chunks} / {userStats.total_chunks}
                  </span>
                </div>
                <div className="progress-bar mb-3">
                  <div
                    className="progress-fill bg-gradient-to-r from-indigo-500 to-violet-500"
                    style={{ width: `${translationPct}%` }}
                  />
                </div>
                <div className="flex justify-between items-end">
                  <span className="text-2xl font-extrabold text-gray-900">{translationDisplay}</span>
                  <span className="text-xs text-gray-400 mb-1">
                    {translationPct === 100 ? '✓ Sve prevedeno' : `${userStats.total_chunks - userStats.translated_chunks} odlomaka preostalo`}
                  </span>
                </div>
              </>
            )}
          </div>

          {/* AI Provider Card */}
          <div className="card p-5">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <Bot className="w-4 h-4 text-indigo-500" />
                <h3 className="text-sm font-bold text-gray-900">AI Provajder</h3>
              </div>
              <Link to="/settings" state={{ tab: 'ai' }} className="text-xs text-indigo-600 hover:text-indigo-700 flex items-center gap-1">
                <Settings className="w-3 h-3" />
                Podesi
              </Link>
            </div>
            {(() => {
              const p = aiSettingsData?.ai_provider || 'auto'
              const label: Record<string, string> = { auto: 'Automatski', ollama: 'Ollama (lokalni)', openai: 'OpenAI (GPT)', claude: 'Claude' }
              const icon: Record<string, React.ElementType> = { auto: Bot, ollama: Cpu, openai: Cloud, claude: Cloud }
              const color: Record<string, string> = { auto: 'bg-indigo-100 text-indigo-700', ollama: 'bg-green-100 text-green-700', openai: 'bg-blue-100 text-blue-700', claude: 'bg-orange-100 text-orange-700' }
              const Icon = icon[p] || Bot
              return (
                <div className={clsx('flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium', color[p] || color.auto)}>
                  <Icon className="w-4 h-4" />
                  {label[p] || 'Automatski'}
                  {p === 'openai' && aiSettingsData?.has_openai_key && <span className="text-xs opacity-70 ml-1">• ključ aktivan</span>}
                  {p === 'claude' && aiSettingsData?.has_claude_key && <span className="text-xs opacity-70 ml-1">• ključ aktivan</span>}
                </div>
              )
            })()}
          </div>

          {/* AI tip */}
          <div className="rounded-2xl p-5 text-white"
            style={{ background: 'linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)' }}>
            <div className="flex items-center gap-2 mb-3">
              <Sparkles className="w-4 h-4 text-indigo-200" />
              <h3 className="text-sm font-bold">AI savet dana</h3>
            </div>
            <p className="text-indigo-100 text-xs leading-relaxed">
              Redovno ponavljanje je ključ dugoročnog pamćenja. Pregledajte prevedene materijale svakih nekoliko dana za najbolje rezultate.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
