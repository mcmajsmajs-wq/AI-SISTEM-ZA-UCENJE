import { Flame } from 'lucide-react'
import clsx from 'clsx'

interface StreakBadgeProps {
  streak: number
  className?: string
}

export default function StreakBadge({ streak, className }: StreakBadgeProps) {
  const intensity = Math.min((streak ?? 0) / 30, 1)
  const flameColor = streak === 0
    ? 'text-gray-300'
    : streak >= 30
    ? 'text-orange-500'
    : streak >= 7
    ? 'text-orange-400'
    : 'text-yellow-500'

  return (
    <div className={clsx('flex items-center gap-1.5', className)}>
      <Flame
        className={clsx('w-5 h-5', flameColor)}
        style={{ opacity: streak === 0 ? 0.4 : 0.6 + intensity * 0.4 }}
      />
      <span className={clsx('font-bold text-sm', flameColor)}>
        {streak}
      </span>
      <span className="text-xs text-gray-400">dana</span>
    </div>
  )
}
