import clsx from 'clsx'

interface XpBarProps {
  level: number
  xpCurrent: number
  xpNeeded: number
  progressPct: number
  className?: string
}

export default function XpBar({ level, xpCurrent, xpNeeded, progressPct, className }: XpBarProps) {
  return (
    <div className={clsx('space-y-1', className)}>
      <div className="flex items-center justify-between text-xs">
        <span className="font-semibold text-gray-700">Nivo {level}</span>
        <span className="text-gray-500">{xpCurrent ?? 0} / {xpNeeded ?? 0} XP</span>
      </div>
      <div className="w-full bg-gray-100 rounded-full h-2.5 overflow-hidden">
        <div
          className="h-full rounded-full bg-gradient-to-r from-indigo-500 to-violet-500 transition-all duration-500"
          style={{ width: `${Math.min(progressPct ?? 0, 100)}%` }}
        />
      </div>
    </div>
  )
}
