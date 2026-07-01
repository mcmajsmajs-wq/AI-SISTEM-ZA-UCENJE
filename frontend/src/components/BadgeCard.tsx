import { Trophy, Star, Zap, Flame, FileText, Search, Lock } from 'lucide-react'
import clsx from 'clsx'
import type { BadgeInfo } from '@/types'

const ICON_MAP: Record<string, typeof Trophy> = {
  trophy: Trophy,
  star: Star,
  zap: Zap,
  flame: Flame,
  'file-text': FileText,
  search: Search,
}

interface BadgeCardProps {
  badge: BadgeInfo
  className?: string
}

export default function BadgeCard({ badge, className }: BadgeCardProps) {
  const Icon = ICON_MAP[badge.icon_name] || Trophy

  return (
    <div
      className={clsx(
        'rounded-xl border p-4 transition-all duration-200',
        badge.earned
          ? 'bg-white border-indigo-200 hover:shadow-md'
          : 'bg-gray-50 border-gray-200 opacity-60',
        className
      )}
    >
      <div className="flex items-start gap-3">
        <div
          className={clsx(
            'w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0',
            badge.earned ? 'bg-indigo-100 text-indigo-600' : 'bg-gray-200 text-gray-400'
          )}
        >
          {badge.earned ? <Icon className="w-5 h-5" /> : <Lock className="w-4 h-4" />}
        </div>
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <h4 className={clsx('font-semibold text-sm', badge.earned ? 'text-gray-900' : 'text-gray-500')}>
              {badge.name}
            </h4>
            {badge.xp_reward > 0 && (
              <span className="text-xs text-indigo-500 font-medium">+{badge.xp_reward} XP</span>
            )}
          </div>
          <p className="text-xs text-gray-500 mt-0.5">{badge.description}</p>
        </div>
      </div>
    </div>
  )
}
