import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { analyticsApi } from '@/services/api'
import {
  TrendingUp, Target, Flame, BookOpen, FileText,
  Trophy, BarChart2, Calendar, Loader2, CheckCircle, XCircle
} from 'lucide-react'
import clsx from 'clsx'

const ACTIVITY_DAYS_OPTIONS = [7, 14, 30, 60]

export default function AnalyticsPage() {
  const [activityDays, setActivityDays] = useState(30)

  const { data: overviewData, isLoading: ovLoading, isError: ovError } = useQuery({
    queryKey: ['analytics-overview'],
    queryFn: () => analyticsApi.getOverview(),
  })

  const { data: activityData, isLoading: actLoading } = useQuery({
    queryKey: ['analytics-activity', activityDays],
    queryFn: () => analyticsApi.getActivity(activityDays),
  })

  const { data: quizPerfData } = useQuery({
    queryKey: ['analytics-quiz-perf'],
    queryFn: () => analyticsApi.getQuizPerformance(10),
  })

  const { data: docStatsData } = useQuery({
    queryKey: ['analytics-docs'],
    queryFn: () => analyticsApi.getDocumentStats(),
  })

  const { data: streakData } = useQuery({
    queryKey: ['analytics-streak'],
    queryFn: () => analyticsApi.getStreakHistory(8),
  })

  const ov = (overviewData as any)?.data
  const activity: { date: string; count: number; avg_pct: number }[] =
    (activityData as any)?.data?.data ?? []
  const quizzes: any[] = (quizPerfData as any)?.data?.quizzes ?? []
  const docs: any[] = (docStatsData as any)?.data?.documents ?? []
  const heatmap: { date: string; count: number }[] =
    (streakData as any)?.data?.data ?? []

  const maxActivity = Math.max(...activity.map(d => d.count), 1)
  const maxHeat = Math.max(...heatmap.map(d => d.count), 1)

  if (ovLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-indigo-400" />
      </div>
    )
  }

  if (ovError) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-center">
        <BarChart2 className="w-10 h-10 text-gray-200 mb-3" />
        <p className="text-gray-500 font-semibold">Nije moguće učitati analitiku</p>
        <p className="text-gray-400 text-sm mt-1">Proverite da li je backend pokrenut</p>
      </div>
    )
  }

  return (
    <div className="max-w-5xl mx-auto space-y-6 pb-10">
      {/* Naslov */}
      <div>
        <h1 className="text-2xl font-extrabold text-gray-900">Analitika</h1>
        <p className="text-gray-400 text-sm mt-0.5">Pregled vašeg napretka i aktivnosti</p>
      </div>

      {/* Overview kartice */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <OverviewCard icon={<Flame className="w-5 h-5 text-orange-500" />} label="Streak" value={`${ov?.current_streak ?? 0} d`} sub="uzastopnih dana" color="bg-orange-50" />
        <OverviewCard icon={<Target className="w-5 h-5 text-indigo-600" />} label="Prosečan score" value={`${ov?.avg_score ?? 0}%`} sub={`${ov?.total_attempts ?? 0} pokušaja`} color="bg-indigo-50" />
        <OverviewCard icon={<Trophy className="w-5 h-5 text-amber-500" />} label="Prolaznost" value={`${ov?.pass_rate ?? 0}%`} sub={`${ov?.passed_attempts ?? 0} položenih`} color="bg-amber-50" />
        <OverviewCard icon={<BookOpen className="w-5 h-5 text-emerald-600" />} label="Kvizovi" value={ov?.total_quizzes ?? 0} sub={`${ov?.total_documents ?? 0} dokumenata`} color="bg-emerald-50" />
      </div>

      {/* Dnevna aktivnost — bar chart */}
      <div className="card p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-sm font-bold text-gray-900 flex items-center gap-2">
            <BarChart2 className="w-4 h-4 text-indigo-500" /> Dnevna aktivnost
          </h2>
          <div className="flex gap-1">
            {ACTIVITY_DAYS_OPTIONS.map(d => (
              <button
                key={d}
                onClick={() => setActivityDays(d)}
                className={clsx(
                  'px-2.5 py-1 rounded-lg text-xs font-semibold transition-colors',
                  activityDays === d
                    ? 'text-white'
                    : 'bg-gray-100 text-gray-500 hover:bg-gray-200'
                )}
                style={activityDays === d ? { background: 'linear-gradient(135deg,#6366f1,#8b5cf6)' } : undefined}
              >
                {d}d
              </button>
            ))}
          </div>
        </div>

        {actLoading ? (
          <div className="flex justify-center py-8"><Loader2 className="w-6 h-6 animate-spin text-indigo-300" /></div>
        ) : (
          <div className="flex items-end gap-1 h-32 overflow-x-auto pb-2">
            {activity.map(day => {
              const pct = (day.count / maxActivity) * 100
              const isToday = day.date === new Date().toISOString().split('T')[0]
              return (
                <div key={day.date} className="flex flex-col items-center flex-shrink-0" style={{ minWidth: activityDays <= 14 ? '2rem' : '0.75rem' }}>
                  <div
                    title={`${day.date}: ${day.count} kviz${day.count !== 1 ? 'a' : ''}, avg ${day.avg_pct}%`}
                    className={clsx('w-full rounded-t transition-all cursor-pointer', isToday ? 'opacity-100' : 'opacity-80')}
                    style={{
                      height: `${Math.max(pct, 2)}%`,
                      background: day.count === 0
                        ? '#e5e7eb'
                        : 'linear-gradient(180deg,#6366f1,#8b5cf6)',
                      minHeight: '4px',
                    }}
                  />
                  {activityDays <= 14 && (
                    <span className="text-[9px] text-gray-400 mt-1 rotate-45 origin-left">
                      {new Date(day.date + 'T00:00:00').toLocaleDateString('sr-RS', { day: 'numeric', month: 'numeric' })}
                    </span>
                  )}
                </div>
              )
            })}
          </div>
        )}

        <div className="flex justify-between mt-1 text-[10px] text-gray-400">
          <span>{activity[0]?.date}</span>
          <span>{activity[activity.length - 1]?.date}</span>
        </div>
      </div>

      {/* Streak heatmap (GitHub-style) */}
      <div className="card p-6">
        <h2 className="text-sm font-bold text-gray-900 flex items-center gap-2 mb-4">
          <Calendar className="w-4 h-4 text-violet-500" /> Aktivnost — zadnjih 8 nedelja
        </h2>
        <div className="flex gap-1 flex-wrap">
          {Array.from({ length: 56 }).map((_, i) => {
            const d = new Date()
            d.setDate(d.getDate() - (55 - i))
            const key = d.toISOString().split('T')[0]
            const entry = heatmap.find(h => h.date === key)
            const intensity = entry ? Math.min((entry.count / maxHeat), 1) : 0
            const bg = intensity === 0
              ? '#f3f4f6'
              : `rgba(99,102,241,${0.2 + intensity * 0.8})`
            return (
              <div
                key={key}
                title={`${key}: ${entry?.count ?? 0} kviz${(entry?.count ?? 0) !== 1 ? 'a' : ''}`}
                className="w-4 h-4 rounded-sm cursor-pointer"
                style={{ background: bg }}
              />
            )
          })}
        </div>
        <div className="flex items-center gap-2 mt-3">
          <span className="text-[10px] text-gray-400">Manje</span>
          {[0, 0.25, 0.5, 0.75, 1].map(v => (
            <div key={v} className="w-3 h-3 rounded-sm"
              style={{ background: v === 0 ? '#f3f4f6' : `rgba(99,102,241,${0.2 + v * 0.8})` }} />
          ))}
          <span className="text-[10px] text-gray-400">Više</span>
        </div>
      </div>

      {/* Performanse kvizova */}
      {quizzes.length > 0 && (
        <div className="card p-6">
          <h2 className="text-sm font-bold text-gray-900 flex items-center gap-2 mb-4">
            <TrendingUp className="w-4 h-4 text-emerald-500" /> Performanse po kvizovima
          </h2>
          <div className="space-y-3">
            {quizzes.map(q => (
              <div key={q.quiz_id} className="flex items-center gap-3">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-semibold text-gray-700 truncate max-w-[260px]">{q.quiz_title}</span>
                    <div className="flex items-center gap-1.5 ml-2 flex-shrink-0">
                      {q.last_passed
                        ? <CheckCircle className="w-3.5 h-3.5 text-green-500" />
                        : <XCircle className="w-3.5 h-3.5 text-red-400" />}
                      <span className="text-xs font-bold text-gray-600">{q.best_score}%</span>
                    </div>
                  </div>
                  <div className="w-full bg-gray-100 rounded-full h-2">
                    <div
                      className="h-2 rounded-full"
                      style={{
                        width: `${q.avg_score}%`,
                        background: q.avg_score >= 60
                          ? 'linear-gradient(90deg,#10b981,#34d399)'
                          : 'linear-gradient(90deg,#f59e0b,#fbbf24)',
                      }}
                    />
                  </div>
                  <div className="flex justify-between text-[10px] text-gray-400 mt-0.5">
                    <span>Avg: {q.avg_score}%</span>
                    <span>{q.attempt_count} pokušaj{q.attempt_count !== 1 ? 'a' : ''}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Statistike po dokumentima */}
      {docs.filter(d => d.quiz_count > 0).length > 0 && (
        <div className="card p-6">
          <h2 className="text-sm font-bold text-gray-900 flex items-center gap-2 mb-4">
            <FileText className="w-4 h-4 text-sky-500" /> Aktivnost po dokumentima
          </h2>
          <div className="space-y-2">
            {docs.filter(d => d.quiz_count > 0).map(doc => (
              <div key={doc.document_id} className="flex items-center gap-3 p-3 rounded-xl bg-gray-50 hover:bg-gray-100 transition-colors">
                <FileText className="w-4 h-4 text-gray-400 flex-shrink-0" />
                <span className="flex-1 text-sm font-medium text-gray-700 truncate">{doc.document_title}</span>
                <span className="text-xs text-gray-400">{doc.quiz_count} kviz{doc.quiz_count !== 1 ? 'a' : ''}</span>
                <span className="text-xs font-bold text-indigo-600">{doc.attempt_count} pokušaja</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Empty state */}
      {(ov?.total_attempts ?? 0) === 0 && (
        <div className="card p-12 text-center">
          <BarChart2 className="w-12 h-12 text-gray-200 mx-auto mb-4" />
          <p className="text-gray-500 font-semibold">Još nema podataka</p>
          <p className="text-gray-400 text-sm mt-1">Igrajte kvizove da biste videli statistike napretka</p>
        </div>
      )}
    </div>
  )
}

function OverviewCard({
  icon, label, value, sub, color,
}: { icon: React.ReactNode; label: string; value: string | number; sub: string; color: string }) {
  return (
    <div className={clsx('rounded-2xl p-4', color)}>
      <div className="flex items-center gap-2 mb-1">{icon}<span className="text-xs font-semibold text-gray-500">{label}</span></div>
      <p className="text-2xl font-extrabold text-gray-900">{value}</p>
      <p className="text-xs text-gray-500 mt-0.5">{sub}</p>
    </div>
  )
}
