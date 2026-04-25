import { useQuery } from '@tanstack/react-query'
import { usersApi, documentsApi, quizApi } from '@/services/api'
import { useAuthStore } from '@/stores/authStore'
import { Link } from 'react-router-dom'
import {
  BookOpen,
  Clock,
  Trophy,
  TrendingUp,
  TrendingDown,
  Target,
  Award,
  FileText,
  Languages,
  ChevronRight,
  Play,
  Calendar,
  Flame,
  Star,
  BarChart3,
  Zap,
  CheckCircle2,
  ArrowUpRight,
  Sparkles
} from 'lucide-react'
import clsx from 'clsx'
import { useState } from 'react'

const mockWeeklyActivity = [
  { day: 'Pon', hours: 1.5 },
  { day: 'Uto', hours: 2.3 },
  { day: 'Sre', hours: 0.8 },
  { day: 'Čet', hours: 3.1 },
  { day: 'Pet', hours: 1.2 },
  { day: 'Sub', hours: 2.0 },
  { day: 'Ned', hours: 0.5 },
]

const mockSkills = [
  { name: 'Prevodjenje', progress: 78, color: 'bg-blue-500' },
  { name: 'Kviz rezultati', progress: 85, color: 'bg-green-500' },
  { name: 'Dokumenti', progress: 60, color: 'bg-purple-500' },
]

export default function DashboardPage() {
  const { user } = useAuthStore()
  const [selectedPeriod, setSelectedPeriod] = useState<'week' | 'month' | 'year'>('week')

  const { data: stats } = useQuery({
    queryKey: ['user-stats'],
    queryFn: () => usersApi.getStats(),
  })

  const { data: recentDocs } = useQuery({
    queryKey: ['documents-recent'],
    queryFn: () => documentsApi.list(1, 4),
  })

  const { data: quizStats } = useQuery({
    queryKey: ['quiz-stats'],
    queryFn: () => quizApi.getStats(),
  })

  const userStats = stats?.data || {
    total_documents: 0,
    total_chunks: 0,
    translated_chunks: 0,
    total_quizzes: 0,
    average_score: 0,
    study_streak: 0,
    total_hours: 0,
  }

  const quizData = quizStats?.data || {
    total_quizzes: 0,
    total_attempts: 0,
    average_score: 0,
    pass_rate: 0,
  }

  const getGreeting = () => {
    const hour = new Date().getHours()
    if (hour < 12) return 'Dobro jutro'
    if (hour < 18) return 'Dobar dan'
    return 'Dobro veče'
  }

  const totalHours = userStats.total_hours || mockWeeklyActivity.reduce((a, b) => a + b.hours, 0)
  const maxHours = Math.max(...mockWeeklyActivity.map(a => a.hours))

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Hero Section */}
      <div className="bg-gradient-to-r from-primary-600 via-primary-500 to-accent-500 rounded-3xl p-8 text-white relative overflow-hidden">
        <div className="absolute inset-0 bg-[url('data:image/svg+xml,%3Csvg width=\"60\" height=\"60\" viewBox=\"0 0 60 60\" xmlns=\"http://www.w3.org/2000/svg\"%3E%3Cg fill=\"none\" fill-rule=\"evenodd\"%3E%3Cg fill=\"%23ffffff\" fill-opacity=\"0.05\"%3E%3Cpath d=\"M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z\"/%3E%3C/g%3E%3C/g%3E%3C/svg%3E')] opacity-50" />
        
        <div className="relative z-10 flex flex-col md:flex-row md:items-center md:justify-between gap-6">
          <div>
            <p className="text-white/80 text-sm mb-1">{getGreeting()},</p>
            <h1 className="text-3xl font-bold mb-2">{user?.full_name || 'Korisnik'}</h1>
            <p className="text-white/80 flex items-center gap-2">
              <Flame className="w-4 h-4 text-orange-300" />
              <span>
                {userStats.study_streak > 0 
                  ? `${userStats.study_streak} dana uzastopnog učenja!` 
                  : 'Započnite svoj niz učenja danas!'}
              </span>
            </p>
          </div>
          
          <div className="flex items-center gap-4">
            <div className="bg-white/10 backdrop-blur-sm rounded-2xl px-6 py-4 text-center">
              <p className="text-white/70 text-sm mb-1">Ove nedelje</p>
              <p className="text-3xl font-bold">{totalHours.toFixed(1)}h</p>
              <p className="text-white/70 text-xs mt-1">vremena učenja</p>
            </div>
            <div className="bg-white/10 backdrop-blur-sm rounded-2xl px-6 py-4 text-center">
              <p className="text-white/70 text-sm mb-1">XP poeni</p>
              <p className="text-3xl font-bold">
                {(userStats.translated_chunks * 10 + quizData.total_attempts * 50).toLocaleString()}
              </p>
              <p className="text-white/70 text-xs mt-1">ukupno</p>
            </div>
          </div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          {
            label: 'Dokumenti',
            value: userStats.total_documents,
            icon: BookOpen,
            trend: '+2',
            trendUp: true,
            color: 'bg-blue-500',
            lightColor: 'bg-blue-50',
            textColor: 'text-blue-600',
          },
          {
            label: 'Prevedenih segmenata',
            value: userStats.translated_chunks,
            icon: Languages,
            trend: '+15',
            trendUp: true,
            color: 'bg-purple-500',
            lightColor: 'bg-purple-50',
            textColor: 'text-purple-600',
          },
          {
            label: 'Kvizova položeno',
            value: quizData.total_quizzes,
            icon: Trophy,
            trend: `${quizData.pass_rate}%`,
            trendUp: true,
            color: 'bg-amber-500',
            lightColor: 'bg-amber-50',
            textColor: 'text-amber-600',
          },
          {
            label: 'Prosečan rezultat',
            value: `${quizData.average_score || userStats.average_score}%`,
            icon: Target,
            trend: '+5%',
            trendUp: true,
            color: 'bg-green-500',
            lightColor: 'bg-green-50',
            textColor: 'text-green-600',
          },
        ].map((stat, i) => (
          <div
            key={stat.label}
            className="card p-5 hover:shadow-lg transition-all duration-300 group"
            style={{ animationDelay: `${i * 50}ms` }}
          >
            <div className="flex items-start justify-between mb-3">
              <div className={clsx('p-2.5 rounded-xl', stat.lightColor)}>
                <stat.icon className={clsx('w-5 h-5', stat.textColor)} />
              </div>
              <div className={clsx(
                'flex items-center gap-0.5 text-xs font-medium',
                stat.trendUp ? 'text-green-600' : 'text-red-600'
              )}>
                {stat.trendUp ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
                {stat.trend}
              </div>
            </div>
            <p className="text-2xl font-bold text-gray-900">{stat.value}</p>
            <p className="text-sm text-gray-500 mt-0.5">{stat.label}</p>
          </div>
        ))}
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Activity & Continue Learning */}
        <div className="lg:col-span-2 space-y-6">
          {/* Weekly Activity Chart */}
          <div className="card p-6">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-lg font-semibold text-gray-900">Aktivnost učenja</h2>
                <p className="text-sm text-gray-500">Vaša aktivnost ove nedelje</p>
              </div>
              <div className="flex items-center gap-1 p-1 bg-gray-100 rounded-lg">
                {(['week', 'month', 'year'] as const).map((period) => (
                  <button
                    key={period}
                    onClick={() => setSelectedPeriod(period)}
                    className={clsx(
                      'px-3 py-1.5 text-sm font-medium rounded-md transition-all',
                      selectedPeriod === period
                        ? 'bg-white text-gray-900 shadow-sm'
                        : 'text-gray-500 hover:text-gray-700'
                    )}
                  >
                    {period === 'week' ? 'Nedelja' : period === 'month' ? 'Mesec' : 'Godina'}
                  </button>
                ))}
              </div>
            </div>

            <div className="flex items-end justify-between gap-2 h-40">
              {mockWeeklyActivity.map((activity, i) => (
                <div key={activity.day} className="flex-1 flex flex-col items-center gap-2">
                  <div className="w-full bg-gray-100 rounded-lg relative h-32 flex items-end overflow-hidden">
                    <div
                      className="w-full bg-gradient-to-t from-primary-500 to-primary-400 rounded-lg transition-all duration-500 hover:from-primary-600 hover:to-primary-500"
                      style={{
                        height: `${(activity.hours / maxHours) * 100}%`,
                        animationDelay: `${i * 100}ms`,
                      }}
                    />
                  </div>
                  <span className="text-xs text-gray-500 font-medium">{activity.day}</span>
                </div>
              ))}
            </div>

            <div className="flex items-center justify-center gap-6 mt-6 pt-4 border-t border-gray-100">
              <div className="text-center">
                <p className="text-2xl font-bold text-gray-900">{totalHours.toFixed(1)}h</p>
                <p className="text-xs text-gray-500">Ukupno vreme</p>
              </div>
              <div className="w-px h-8 bg-gray-200" />
              <div className="text-center">
                <p className="text-2xl font-bold text-gray-900">{mockWeeklyActivity.filter(a => a.hours > 0).length}</p>
                <p className="text-xs text-gray-500">Aktivnih dana</p>
              </div>
              <div className="w-px h-8 bg-gray-200" />
              <div className="text-center">
                <p className="text-2xl font-bold text-gray-900">{(totalHours / 7).toFixed(1)}h</p>
                <p className="text-xs text-gray-500">Prosečno dnevno</p>
              </div>
            </div>
          </div>

          {/* Continue Learning */}
          <div className="card">
            <div className="flex items-center justify-between p-6 border-b border-gray-100">
              <h2 className="text-lg font-semibold text-gray-900">Nastavite učenje</h2>
              <Link to="/documents" className="text-primary-600 hover:text-primary-700 text-sm font-medium flex items-center gap-1">
                Vidi sve <ChevronRight className="w-4 h-4" />
              </Link>
            </div>
            
            {recentDocs?.data?.documents?.length ? (
              <div className="divide-y divide-gray-100">
                {recentDocs.data.documents.slice(0, 3).map((doc: any) => (
                  <Link
                    key={doc.id}
                    to={`/documents/${doc.id}`}
                    className="flex items-center gap-4 p-4 hover:bg-gray-50 transition-colors group"
                  >
                    <div className="relative">
                      <div className="w-16 h-16 rounded-xl bg-gradient-to-br from-primary-100 to-accent-100 flex items-center justify-center">
                        <BookOpen className="w-6 h-6 text-primary-600" />
                      </div>
                      <div className="absolute -bottom-1 -right-1 w-6 h-6 rounded-full bg-primary-500 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                        <Play className="w-3 h-3 text-white fill-white" />
                      </div>
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-gray-900 truncate group-hover:text-primary-600 transition-colors">
                        {doc.title}
                      </p>
                      <p className="text-sm text-gray-500 mt-0.5">
                        {doc.chunks_count || doc.total_chunks || 0} segmenata
                      </p>
                      <div className="mt-2 flex items-center gap-2">
                        <div className="flex-1 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                          <div
                            className="h-full bg-gradient-to-r from-primary-500 to-accent-500 rounded-full"
                            style={{ width: `${doc.progress || 45}%` }}
                          />
                        </div>
                        <span className="text-xs text-gray-500 font-medium">{doc.progress || 45}%</span>
                      </div>
                    </div>
                    <ChevronRight className="w-5 h-5 text-gray-300 group-hover:text-primary-500 transition-colors" />
                  </Link>
                ))}
              </div>
            ) : (
              <div className="p-12 text-center">
                <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-primary-100 to-accent-100 flex items-center justify-center mx-auto mb-4">
                  <BookOpen className="w-8 h-8 text-primary-500" />
                </div>
                <h3 className="font-medium text-gray-900 mb-1">Započnite učenje</h3>
                <p className="text-gray-500 text-sm mb-4">Dodajte svoj prvi dokument da biste počeli</p>
                <Link to="/documents" className="btn-primary">
                  <FileText className="w-4 h-4" />
                  Dodaj dokument
                </Link>
              </div>
            )}
          </div>
        </div>

        {/* Right Column - Skills & Quick Actions */}
        <div className="space-y-6">
          {/* Skills Progress */}
          <div className="card p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900">Veštine</h2>
              <BarChart3 className="w-5 h-5 text-gray-400" />
            </div>
            <div className="space-y-4">
              {mockSkills.map((skill) => (
                <div key={skill.name}>
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-sm font-medium text-gray-700">{skill.name}</span>
                    <span className="text-sm font-bold text-gray-900">{skill.progress}%</span>
                  </div>
                  <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                    <div
                      className={clsx('h-full rounded-full transition-all duration-500', skill.color)}
                      style={{ width: `${skill.progress}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Achievements */}
          <div className="card p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900">Dostignuća</h2>
              <Award className="w-5 h-5 text-gray-400" />
            </div>
            <div className="grid grid-cols-3 gap-3">
              {[
                { icon: Flame, name: 'Streak', unlocked: userStats.study_streak >= 3, color: 'from-orange-400 to-red-500' },
                { icon: Star, name: 'Prvi kviz', unlocked: quizData.total_attempts > 0, color: 'from-amber-400 to-yellow-500' },
                { icon: BookOpen, name: 'Prvi dok', unlocked: userStats.total_documents > 0, color: 'from-blue-400 to-blue-600' },
                { icon: Target, name: 'Savršeno', unlocked: false, color: 'from-green-400 to-green-600' },
                { icon: Trophy, name: 'Expert', unlocked: false, color: 'from-purple-400 to-purple-600' },
                { icon: Zap, name: 'Brzo', unlocked: false, color: 'from-cyan-400 to-blue-500' },
              ].map((achievement) => (
                <div
                  key={achievement.name}
                  className={clsx(
                    'relative p-3 rounded-xl text-center transition-all',
                    achievement.unlocked
                      ? 'bg-gradient-to-br shadow-lg'
                      : 'bg-gray-100 opacity-50'
                  )}
                >
                  <div className={clsx(
                    'w-10 h-10 rounded-full mx-auto flex items-center justify-center',
                    achievement.unlocked
                      ? `bg-gradient-to-br ${achievement.color}`
                      : 'bg-gray-200'
                  )}>
                    <achievement.icon className={clsx(
                      'w-5 h-5',
                      achievement.unlocked ? 'text-white' : 'text-gray-400'
                    )} />
                  </div>
                  <p className={clsx(
                    'text-xs font-medium mt-1.5',
                    achievement.unlocked ? 'text-gray-700' : 'text-gray-400'
                  )}>
                    {achievement.name}
                  </p>
                  {achievement.unlocked && (
                    <div className="absolute -top-1 -right-1 w-4 h-4 bg-green-500 rounded-full flex items-center justify-center">
                      <CheckCircle2 className="w-3 h-3 text-white" />
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Quick Actions */}
          <div className="card p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Brze akcije</h2>
            <div className="space-y-2">
              <Link
                to="/documents"
                className="flex items-center gap-3 p-3 rounded-xl bg-gradient-to-r from-primary-50 to-primary-100 text-primary-700 hover:from-primary-100 hover:to-primary-200 transition-all group"
              >
                <div className="p-2 rounded-lg bg-primary-500 text-white">
                  <FileText className="w-4 h-4" />
                </div>
                <span className="font-medium flex-1">Dodaj dokument</span>
                <ArrowUpRight className="w-4 h-4 opacity-0 group-hover:opacity-100 transition-opacity" />
              </Link>
              <Link
                to="/quizzes/generate"
                className="flex items-center gap-3 p-3 rounded-xl bg-gradient-to-r from-amber-50 to-amber-100 text-amber-700 hover:from-amber-100 hover:to-amber-200 transition-all group"
              >
                <div className="p-2 rounded-lg bg-amber-500 text-white">
                  <Trophy className="w-4 h-4" />
                </div>
                <span className="font-medium flex-1">Generiši kviz</span>
                <ArrowUpRight className="w-4 h-4 opacity-0 group-hover:opacity-100 transition-opacity" />
              </Link>
              <Link
                to="/quizzes"
                className="flex items-center gap-3 p-3 rounded-xl bg-gradient-to-r from-green-50 to-green-100 text-green-700 hover:from-green-100 hover:to-green-200 transition-all group"
              >
                <div className="p-2 rounded-lg bg-green-500 text-white">
                  <Play className="w-4 h-4" />
                </div>
                <span className="font-medium flex-1">Započni kviz</span>
                <ArrowUpRight className="w-4 h-4 opacity-0 group-hover:opacity-100 transition-opacity" />
              </Link>
            </div>
          </div>

          {/* AI Tip */}
          <div className="card p-6 bg-gradient-to-br from-primary-500 to-accent-500 text-white">
            <div className="flex items-center gap-2 mb-3">
              <Sparkles className="w-5 h-5" />
              <h3 className="font-semibold">Savet dana</h3>
            </div>
            <p className="text-white/90 text-sm leading-relaxed">
              Istraživanja pokazuju da je učenje u kratkim intervalima od 25-30 minuta 
              najefikasnije. Pokušajte sa <strong>Pomodoro</strong> tehnikom!
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
