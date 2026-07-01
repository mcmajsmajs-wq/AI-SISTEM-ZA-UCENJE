import { useQuery } from '@tanstack/react-query'
import { gamificationApi } from '@/services/api'
import { Trophy, Flame, Loader2, AlertTriangle, Target } from 'lucide-react'
import XpBar from '@/components/XpBar'
import BadgeCard from '@/components/BadgeCard'
import StreakBadge from '@/components/StreakBadge'
import type { GamificationProfile } from '@/types'

export default function AchievementsPage() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['gamification-profile'],
    queryFn: async () => {
      const res = await gamificationApi.profile()
      return res.data as GamificationProfile
    },
  })

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-indigo-400" />
      </div>
    )
  }

  if (isError || !data) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-center">
        <AlertTriangle className="w-10 h-10 text-gray-200 mb-3" />
        <p className="text-gray-500 font-semibold">Greška pri učitavanju</p>
      </div>
    )
  }

  const earned = data.badges.filter(b => b.earned).length
  const total = data.badges.length

  return (
    <div className="max-w-4xl mx-auto space-y-6 pb-10">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dostignuća</h1>
        <p className="text-gray-500 mt-1">Tvoj napredak i osvojeni badge-evi</p>
      </div>

      {/* Level + XP Card */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="w-14 h-14 rounded-full bg-gradient-to-br from-indigo-500 to-violet-500 flex items-center justify-center text-white font-bold text-xl shadow-md">
              {data.level}
            </div>
            <div>
              <p className="text-lg font-bold text-gray-900">Nivo {data.level}</p>
              <p className="text-sm text-gray-500">Ukupno {data.total_xp_earned} XP osvojeno</p>
            </div>
          </div>
          <StreakBadge streak={data.current_streak} />
        </div>
        <XpBar
          level={data.level}
          xpCurrent={data.xp_current_in_level}
          xpNeeded={data.xp_needed_for_next}
          progressPct={data.progress_pct}
        />
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-white rounded-xl border border-gray-200 p-4 text-center">
          <Trophy className="w-5 h-5 text-amber-500 mx-auto mb-1" />
          <p className="text-xl font-bold text-gray-900">{earned}/{total}</p>
          <p className="text-xs text-gray-500">Badge-evi</p>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-4 text-center">
          <Flame className="w-5 h-5 text-orange-500 mx-auto mb-1" />
          <p className="text-xl font-bold text-gray-900">{data.current_streak}</p>
          <p className="text-xs text-gray-500">Trenutni streak</p>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-4 text-center">
          <Target className="w-5 h-5 text-indigo-500 mx-auto mb-1" />
          <p className="text-xl font-bold text-gray-900">{data.longest_streak}</p>
          <p className="text-xs text-gray-500">Najbolji streak</p>
        </div>
      </div>

      {/* Badges */}
      <div>
        <h2 className="text-lg font-bold text-gray-900 mb-4">Svi badge-evi</h2>
        <div className="grid sm:grid-cols-2 gap-3">
          {data.badges.map(badge => (
            <BadgeCard key={badge.slug} badge={badge} />
          ))}
        </div>
      </div>
    </div>
  )
}
