import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import toast from 'react-hot-toast'
import { quizApi } from '@/services/api'
import {
  Trophy,
  Clock,
  Target,
  Play,
  Plus,
  Search,
  Filter,
  Loader2,
  BookOpen,
  CheckCircle,
  XCircle,
  Star,
  Flame,
  Award,
  TrendingUp,
  ChevronRight,
  Grid3X3,
  List,
  Sparkles
} from 'lucide-react'
import clsx from 'clsx'

export default function QuizzesPage() {
  const queryClient = useQueryClient()
  const [page, setPage] = useState(1)
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [difficultyFilter, setDifficultyFilter] = useState<string>('')
  const [searchQuery, setSearchQuery] = useState('')
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid')

  const { data: quizzes, isLoading } = useQuery({
    queryKey: ['quizzes', page, statusFilter, difficultyFilter],
    queryFn: () => quizApi.list(page, 20, statusFilter || undefined, difficultyFilter || undefined),
  })

  const { data: stats } = useQuery({
    queryKey: ['quiz-stats'],
    queryFn: () => quizApi.getStats(),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => quizApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['quizzes'] })
      toast.success('Kviz je obrisan')
    },
    onError: () => toast.error('Greška pri brisanju'),
  })

  const getDifficultyConfig = (difficulty: string) => {
    const configs: Record<string, { label: string; color: string; bgColor: string; stars: number }> = {
      easy: { label: 'Lako', color: 'text-green-600', bgColor: 'bg-green-100', stars: 1 },
      medium: { label: 'Srednje', color: 'text-amber-600', bgColor: 'bg-amber-100', stars: 2 },
      hard: { label: 'Teško', color: 'text-red-600', bgColor: 'bg-red-100', stars: 3 },
      mixed: { label: 'Mešano', color: 'text-purple-600', bgColor: 'bg-purple-100', stars: 2 },
    }
    return configs[difficulty] || configs.medium
  }

  const getStatusConfig = (status: string) => {
    const configs: Record<string, { label: string; color: string; bgColor: string }> = {
      draft: { label: 'U pripremi', color: 'text-gray-600', bgColor: 'bg-gray-100' },
      published: { label: 'Objavljen', color: 'text-green-600', bgColor: 'bg-green-100' },
      archived: { label: 'Arhiviran', color: 'text-amber-600', bgColor: 'bg-amber-100' },
    }
    return configs[status] || configs.draft
  }

  const filteredQuizzes = quizzes?.data?.quizzes?.filter((q: any) =>
    q.title.toLowerCase().includes(searchQuery.toLowerCase())
  ) || []

  const quizStats = stats?.data || {
    total_quizzes: 0,
    total_attempts: 0,
    average_score: 0,
    pass_rate: 0,
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Kvizovi</h1>
          <p className="text-gray-500 mt-1">Testirajte svoje znanje i pratite napredak</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1 p-1 bg-gray-100 rounded-lg">
            <button
              onClick={() => setViewMode('grid')}
              className={clsx(
                'p-2 rounded-lg transition-colors',
                viewMode === 'grid' ? 'bg-white text-primary-600 shadow-sm' : 'text-gray-400 hover:text-gray-600'
              )}
            >
              <Grid3X3 className="w-4 h-4" />
            </button>
            <button
              onClick={() => setViewMode('list')}
              className={clsx(
                'p-2 rounded-lg transition-colors',
                viewMode === 'list' ? 'bg-white text-primary-600 shadow-sm' : 'text-gray-400 hover:text-gray-600'
              )}
            >
              <List className="w-4 h-4" />
            </button>
          </div>
          <Link to="/quizzes/generate" className="btn-primary">
            <Plus className="w-5 h-5" />
            <span className="hidden sm:inline">Novi kviz</span>
          </Link>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="card p-5 relative overflow-hidden">
          <div className="absolute top-0 right-0 w-24 h-24 bg-gradient-to-br from-primary-500/10 to-transparent rounded-full -mr-12 -mt-12" />
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-primary-100">
              <Trophy className="w-5 h-5 text-primary-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900">{quizStats.total_quizzes}</p>
              <p className="text-sm text-gray-500">Kvizova</p>
            </div>
          </div>
        </div>
        <div className="card p-5 relative overflow-hidden">
          <div className="absolute top-0 right-0 w-24 h-24 bg-gradient-to-br from-amber-500/10 to-transparent rounded-full -mr-12 -mt-12" />
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-amber-100">
              <Flame className="w-5 h-5 text-amber-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900">{quizStats.total_attempts}</p>
              <p className="text-sm text-gray-500">Pokušaja</p>
            </div>
          </div>
        </div>
        <div className="card p-5 relative overflow-hidden">
          <div className="absolute top-0 right-0 w-24 h-24 bg-gradient-to-br from-green-500/10 to-transparent rounded-full -mr-12 -mt-12" />
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-green-100">
              <Target className="w-5 h-5 text-green-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900">{quizStats.average_score}%</p>
              <p className="text-sm text-gray-500">Prosečan rezultat</p>
            </div>
          </div>
        </div>
        <div className="card p-5 relative overflow-hidden">
          <div className="absolute top-0 right-0 w-24 h-24 bg-gradient-to-br from-purple-500/10 to-transparent rounded-full -mr-12 -mt-12" />
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-purple-100">
              <Award className="w-5 h-5 text-purple-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900">{quizStats.pass_rate}%</p>
              <p className="text-sm text-gray-500">Prolaznost</p>
            </div>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="flex-1 relative">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Pretraži kvizove..."
            className="input pl-12"
          />
        </div>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="input min-w-[150px]"
        >
          <option value="">Svi statusi</option>
          <option value="draft">U pripremi</option>
          <option value="published">Objavljeni</option>
          <option value="archived">Arhivirani</option>
        </select>
        <select
          value={difficultyFilter}
          onChange={(e) => setDifficultyFilter(e.target.value)}
          className="input min-w-[150px]"
        >
          <option value="">Sve težine</option>
          <option value="easy">Lako</option>
          <option value="medium">Srednje</option>
          <option value="hard">Teško</option>
          <option value="mixed">Mešano</option>
        </select>
      </div>

      {/* Quizzes */}
      {isLoading ? (
        <div className="flex justify-center py-16">
          <Loader2 className="w-8 h-8 text-primary-500 animate-spin" />
        </div>
      ) : filteredQuizzes.length === 0 ? (
        <div className="card p-16 text-center">
          <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-amber-100 to-orange-100 flex items-center justify-center mx-auto mb-4">
            <Trophy className="w-10 h-10 text-amber-500" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Nema kvizova</h3>
          <p className="text-gray-500 mb-6">Generišite svoj prvi kviz iz dokumenta</p>
          <Link to="/quizzes/generate" className="btn-primary">
            <Sparkles className="w-5 h-5" />
            Generiši kviz
          </Link>
        </div>
      ) : viewMode === 'grid' ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredQuizzes.map((quiz: any, i: number) => {
            const diffConfig = getDifficultyConfig(quiz.difficulty)
            const statusConfig = getStatusConfig(quiz.status)
            return (
              <div
                key={quiz.id}
                className="card p-5 hover:shadow-lg transition-all duration-300 group animate-slide-up"
                style={{ animationDelay: `${i * 50}ms` }}
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-amber-400 to-orange-500 flex items-center justify-center shadow-lg shadow-amber-500/20">
                    <Trophy className="w-6 h-6 text-white" />
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={clsx('px-2.5 py-1 rounded-full text-xs font-medium', diffConfig.bgColor, diffConfig.color)}>
                      {diffConfig.label}
                    </span>
                  </div>
                </div>

                <Link to={`/quizzes/${quiz.id}`} className="block mb-3">
                  <h3 className="font-semibold text-gray-900 group-hover:text-primary-600 transition-colors line-clamp-2">
                    {quiz.title}
                  </h3>
                  <p className="text-sm text-gray-500 mt-1 line-clamp-2">
                    {quiz.description || 'Bez opisa'}
                  </p>
                </Link>

                <div className="flex items-center gap-4 text-sm text-gray-500 mb-4">
                  <span className="flex items-center gap-1">
                    <Target className="w-4 h-4" />
                    {quiz.total_questions} pitanja
                  </span>
                  {quiz.time_limit > 0 && (
                    <span className="flex items-center gap-1">
                      <Clock className="w-4 h-4" />
                      {quiz.time_limit} min
                    </span>
                  )}
                </div>

                <div className="flex items-center gap-2 pt-4 border-t border-gray-100">
                  {quiz.status === 'published' ? (
                    <Link
                      to={`/quizzes/${quiz.id}/play`}
                      className="btn-sm btn-primary flex-1"
                    >
                      <Play className="w-4 h-4" />
                      Započni
                    </Link>
                  ) : (
                    <span className={clsx('text-xs font-medium px-3 py-1.5 rounded-full', statusConfig.bgColor, statusConfig.color)}>
                      {statusConfig.label}
                    </span>
                  )}
                  <Link
                    to={`/quizzes/${quiz.id}`}
                    className="btn-sm btn-secondary"
                  >
                    Detalji
                  </Link>
                  {quiz.status === 'draft' && (
                    <button
                      onClick={() => deleteMutation.mutate(quiz.id)}
                      disabled={deleteMutation.isPending}
                      className="btn-sm btn-ghost text-red-500 hover:bg-red-50"
                    >
                      <XCircle className="w-4 h-4" />
                    </button>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      ) : (
        <div className="card divide-y divide-gray-100">
          {filteredQuizzes.map((quiz: any) => {
            const diffConfig = getDifficultyConfig(quiz.difficulty)
            const statusConfig = getStatusConfig(quiz.status)
            return (
              <div key={quiz.id} className="flex items-center gap-4 p-4 hover:bg-gray-50 transition-colors group">
                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-amber-400 to-orange-500 flex items-center justify-center shadow-lg shadow-amber-500/20 flex-shrink-0">
                  <Trophy className="w-6 h-6 text-white" />
                </div>
                <div className="flex-1 min-w-0">
                  <Link to={`/quizzes/${quiz.id}`} className="font-medium text-gray-900 hover:text-primary-600">
                    {quiz.title}
                  </Link>
                  <div className="flex items-center gap-4 mt-1 text-sm text-gray-500">
                    <span>{quiz.total_questions} pitanja</span>
                    {quiz.time_limit > 0 && <span>{quiz.time_limit} min</span>}
                    <span className={clsx('font-medium', diffConfig.color)}>{diffConfig.label}</span>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {quiz.status === 'published' && (
                    <Link to={`/quizzes/${quiz.id}/play`} className="btn-sm btn-primary">
                      <Play className="w-4 h-4" />
                      Igraj
                    </Link>
                  )}
                  <Link to={`/quizzes/${quiz.id}`} className="p-2 rounded-lg hover:bg-gray-100 opacity-0 group-hover:opacity-100 transition-all">
                    <ChevronRight className="w-5 h-5 text-gray-400" />
                  </Link>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
