import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { studyPlanApi, quizzesApi } from '@/services/api'
import {
  Target, Calendar, Clock, Bell, Plus, Trash2, CheckCircle,
  Circle, Flame, TrendingUp, Save, Loader2, BookOpen
} from 'lucide-react'
import toast from 'react-hot-toast'
import clsx from 'clsx'

const DAYS = ['Ned', 'Pon', 'Uto', 'Sre', 'Čet', 'Pet', 'Sub']
const PRIORITY_LABELS: Record<number, string> = { 1: 'Normalan', 2: 'Visok', 3: 'Kritičan' }
const PRIORITY_COLORS: Record<number, string> = {
  1: 'bg-gray-100 text-gray-600',
  2: 'bg-amber-100 text-amber-700',
  3: 'bg-red-100 text-red-600',
}

export default function StudyPlanTab() {
  const queryClient = useQueryClient()

  const { data: progressData, isLoading } = useQuery({
    queryKey: ['study-plan-progress'],
    queryFn: () => studyPlanApi.getProgress(),
  })

  const { data: quizzesData } = useQuery({
    queryKey: ['quizzes-ready'],
    queryFn: () => quizzesApi.list(0, 100),
  })

  const progress = (progressData as any)?.data
  const plan = progress?.plan
  const allQuizzes = ((quizzesData as any)?.data?.items ?? []).filter((q: any) => q.status === 'ready')

  // Lokalni state za editovanje plana
  const [dailyGoal, setDailyGoal] = useState<number | null>(null)
  const [weeklyGoal, setWeeklyGoal] = useState<number | null>(null)
  const [sessionMin, setSessionMin] = useState<number | null>(null)
  const [studyDays, setStudyDays] = useState<number[] | null>(null)
  const [reminderEnabled, setReminderEnabled] = useState<boolean | null>(null)
  const [reminderTime, setReminderTime] = useState<string | null>(null)
  const [notes, setNotes] = useState<string | null>(null)

  // Za dodavanje stavke
  const [addQuizId, setAddQuizId] = useState('')
  const [addDate, setAddDate] = useState(new Date().toISOString().split('T')[0])
  const [addPriority, setAddPriority] = useState(1)
  const [showAddForm, setShowAddForm] = useState(false)

  const updatePlanMutation = useMutation({
    mutationFn: () => studyPlanApi.updatePlan({
      daily_quiz_goal: dailyGoal ?? plan?.daily_quiz_goal,
      weekly_quiz_goal: weeklyGoal ?? plan?.weekly_quiz_goal,
      session_duration_min: sessionMin ?? plan?.session_duration_min,
      study_days: studyDays ?? plan?.study_days,
      reminder_enabled: reminderEnabled ?? plan?.reminder_enabled,
      reminder_time: reminderTime ?? plan?.reminder_time,
      notes: notes ?? plan?.notes,
    }),
    onSuccess: () => {
      toast.success('Plan učenja sačuvan!')
      queryClient.invalidateQueries({ queryKey: ['study-plan-progress'] })
    },
    onError: () => toast.error('Greška pri čuvanju plana'),
  })

  const addItemMutation = useMutation({
    mutationFn: () => studyPlanApi.addItem({
      quiz_id: addQuizId,
      scheduled_for: addDate,
      priority: addPriority,
    }),
    onSuccess: () => {
      toast.success('Kviz dodat u plan!')
      queryClient.invalidateQueries({ queryKey: ['study-plan-progress'] })
      setShowAddForm(false)
      setAddQuizId('')
    },
    onError: () => toast.error('Greška pri dodavanju'),
  })

  const completeItemMutation = useMutation({
    mutationFn: (id: string) => studyPlanApi.completeItem(id),
    onSuccess: () => {
      toast.success('Označeno kao završeno!')
      queryClient.invalidateQueries({ queryKey: ['study-plan-progress'] })
    },
  })

  const deleteItemMutation = useMutation({
    mutationFn: (id: string) => studyPlanApi.deleteItem(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['study-plan-progress'] })
    },
  })

  if (isLoading) {
    return (
      <div className="flex justify-center py-16">
        <Loader2 className="w-8 h-8 animate-spin text-indigo-400" />
      </div>
    )
  }

  const effectiveDays = studyDays ?? plan?.study_days ?? [1, 2, 3, 4, 5]
  const effectiveDaily = dailyGoal ?? plan?.daily_quiz_goal ?? 1
  const effectiveWeekly = weeklyGoal ?? plan?.weekly_quiz_goal ?? 5
  const effectiveSession = sessionMin ?? plan?.session_duration_min ?? 20
  const effectiveReminder = reminderEnabled ?? plan?.reminder_enabled ?? false
  const effectiveTime = reminderTime ?? plan?.reminder_time ?? '09:00'
  const effectiveNotes = notes ?? plan?.notes ?? ''

  const toggleDay = (day: number) => {
    const current = effectiveDays
    if (current.includes(day)) {
      setStudyDays(current.filter((d: number) => d !== day))
    } else {
      setStudyDays([...current, day].sort())
    }
  }

  const weekPct = progress?.week_pct ?? 0

  return (
    <div className="space-y-6">
      {/* Progres kartice */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <StatCard
          icon={<Flame className="w-5 h-5 text-orange-500" />}
          label="Streak"
          value={`${progress?.current_streak ?? 0} dana`}
          bg="bg-orange-50"
        />
        <StatCard
          icon={<Target className="w-5 h-5 text-indigo-600" />}
          label="Nedeljni cilj"
          value={`${progress?.week_completed ?? 0}/${progress?.week_goal ?? effectiveWeekly}`}
          bg="bg-indigo-50"
        />
        <StatCard
          icon={<TrendingUp className="w-5 h-5 text-emerald-600" />}
          label="Danas"
          value={`${progress?.today_completed ?? 0}/${progress?.today_goal ?? effectiveDaily}`}
          bg="bg-emerald-50"
        />
        <StatCard
          icon={<Clock className="w-5 h-5 text-violet-600" />}
          label="Po sesiji"
          value={`${effectiveSession} min`}
          bg="bg-violet-50"
        />
      </div>

      {/* Progress bar — nedeljno */}
      <div className="card p-5">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-semibold text-gray-700">Nedeljni napredak</span>
          <span className="text-sm font-bold text-indigo-600">{weekPct.toFixed(0)}%</span>
        </div>
        <div className="w-full bg-gray-100 rounded-full h-3">
          <div
            className="h-3 rounded-full transition-all duration-500"
            style={{ width: `${weekPct}%`, background: 'linear-gradient(90deg, #6366f1, #8b5cf6)' }}
          />
        </div>
        <p className="text-xs text-gray-400 mt-1.5">
          {progress?.week_completed ?? 0} od {progress?.week_goal ?? effectiveWeekly} kvizova ove nedelje
        </p>
      </div>

      {/* Ciljevi — forma */}
      <div className="card p-6 space-y-5">
        <h3 className="text-base font-bold text-gray-900 flex items-center gap-2">
          <Target className="w-4 h-4 text-indigo-600" /> Ciljevi i tempo
        </h3>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <SliderField
            label="Dnevni cilj"
            value={effectiveDaily}
            min={1} max={10}
            onChange={setDailyGoal}
            suffix="kviz/dan"
          />
          <SliderField
            label="Nedeljni cilj"
            value={effectiveWeekly}
            min={1} max={30}
            onChange={setWeeklyGoal}
            suffix="kvizova/ned"
          />
          <SliderField
            label="Trajanje sesije"
            value={effectiveSession}
            min={5} max={120} step={5}
            onChange={setSessionMin}
            suffix="minuta"
          />
        </div>

        {/* Dani u nedelji */}
        <div>
          <label className="text-xs font-semibold text-gray-600 mb-2 block">Dani učenja</label>
          <div className="flex gap-2 flex-wrap">
            {DAYS.map((day, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => toggleDay(idx)}
                className={clsx(
                  'w-10 h-10 rounded-xl text-xs font-bold transition-all',
                  effectiveDays.includes(idx)
                    ? 'text-white shadow-md'
                    : 'bg-gray-100 text-gray-500 hover:bg-gray-200'
                )}
                style={effectiveDays.includes(idx)
                  ? { background: 'linear-gradient(135deg, #6366f1, #8b5cf6)' }
                  : undefined}
              >
                {day}
              </button>
            ))}
          </div>
        </div>

        {/* Reminder */}
        <div className="flex items-center gap-4">
          <label className="flex items-center gap-2 cursor-pointer">
            <div className="relative">
              <input type="checkbox" className="sr-only"
                checked={effectiveReminder}
                onChange={e => setReminderEnabled(e.target.checked)} />
              <div className={clsx('w-10 h-5 rounded-full transition-colors',
                effectiveReminder ? 'bg-indigo-500' : 'bg-gray-200')}>
                <div className={clsx('w-4 h-4 bg-white rounded-full shadow transition-transform mt-0.5',
                  effectiveReminder ? 'translate-x-5 ml-0.5' : 'translate-x-0.5')} />
              </div>
            </div>
            <Bell className="w-4 h-4 text-gray-500" />
            <span className="text-sm font-medium text-gray-700">Dnevni podsetnik</span>
          </label>
          {effectiveReminder && (
            <input
              type="time"
              value={effectiveTime}
              onChange={e => setReminderTime(e.target.value)}
              className="border border-gray-200 rounded-xl px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300"
            />
          )}
        </div>

        {/* Beleška */}
        <div>
          <label className="text-xs font-semibold text-gray-600 mb-1 block">Motivaciona beleška</label>
          <textarea
            rows={2}
            value={effectiveNotes}
            onChange={e => setNotes(e.target.value)}
            placeholder="Npr. Svaki dan malo = veliki napredak za mesec dana!"
            className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-indigo-300"
          />
        </div>

        <div className="flex justify-end">
          <button
            onClick={() => updatePlanMutation.mutate()}
            disabled={updatePlanMutation.isPending}
            className="flex items-center gap-2 px-5 py-2.5 rounded-xl text-white text-sm font-semibold"
            style={{ background: 'linear-gradient(135deg, #6366f1, #8b5cf6)' }}
          >
            {updatePlanMutation.isPending
              ? <Loader2 className="w-4 h-4 animate-spin" />
              : <Save className="w-4 h-4" />}
            Sačuvaj plan
          </button>
        </div>
      </div>

      {/* Zakazani kvizovi */}
      <div className="card p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-base font-bold text-gray-900 flex items-center gap-2">
            <Calendar className="w-4 h-4 text-indigo-600" /> Zakazani kvizovi
          </h3>
          <button
            onClick={() => setShowAddForm(!showAddForm)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold text-white"
            style={{ background: 'linear-gradient(135deg, #6366f1, #8b5cf6)' }}
          >
            <Plus className="w-3.5 h-3.5" /> Dodaj
          </button>
        </div>

        {/* Forma za dodavanje */}
        {showAddForm && (
          <div className="bg-gray-50 rounded-xl p-4 space-y-3">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div className="sm:col-span-1">
                <label className="text-xs font-medium text-gray-600 mb-1 block">Kviz</label>
                <select
                  value={addQuizId}
                  onChange={e => setAddQuizId(e.target.value)}
                  className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300"
                >
                  <option value="">— Izaberi kviz —</option>
                  {allQuizzes.map((q: any) => (
                    <option key={q.id} value={q.id}>{q.title}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="text-xs font-medium text-gray-600 mb-1 block">Datum</label>
                <input
                  type="date"
                  value={addDate}
                  onChange={e => setAddDate(e.target.value)}
                  min={new Date().toISOString().split('T')[0]}
                  className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300"
                />
              </div>
              <div>
                <label className="text-xs font-medium text-gray-600 mb-1 block">Prioritet</label>
                <select
                  value={addPriority}
                  onChange={e => setAddPriority(Number(e.target.value))}
                  className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300"
                >
                  <option value={1}>Normalan</option>
                  <option value={2}>Visok</option>
                  <option value={3}>Kritičan</option>
                </select>
              </div>
            </div>
            <div className="flex gap-2 justify-end">
              <button onClick={() => setShowAddForm(false)}
                className="px-4 py-2 rounded-xl border border-gray-200 text-sm text-gray-600 hover:bg-gray-100">
                Otkaži
              </button>
              <button
                disabled={!addQuizId || addItemMutation.isPending}
                onClick={() => addItemMutation.mutate()}
                className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-white text-sm font-semibold disabled:opacity-50"
                style={{ background: 'linear-gradient(135deg, #6366f1, #8b5cf6)' }}
              >
                {addItemMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
                Zakaži
              </button>
            </div>
          </div>
        )}

        {/* Lista nadolazećih */}
        {(progress?.upcoming_items?.length ?? 0) === 0 && (progress?.today_items?.length ?? 0) === 0 ? (
          <div className="text-center py-8">
            <BookOpen className="w-10 h-10 text-gray-200 mx-auto mb-3" />
            <p className="text-gray-400 text-sm">Nema zakazanih kvizova</p>
            <p className="text-gray-300 text-xs mt-0.5">Klikni "Dodaj" da zakažeš kviz</p>
          </div>
        ) : (
          <div className="space-y-2">
            {/* Danas */}
            {(progress?.today_items?.length ?? 0) > 0 && (
              <>
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Danas</p>
                {progress.today_items.map((item: any) => (
                  <PlanItemRow
                    key={item.id}
                    item={item}
                    onComplete={() => completeItemMutation.mutate(item.id)}
                    onDelete={() => deleteItemMutation.mutate(item.id)}
                  />
                ))}
              </>
            )}
            {/* Predstojeći */}
            {(progress?.upcoming_items?.filter((i: any) =>
              i.scheduled_for !== new Date().toISOString().split('T')[0]
            ).length ?? 0) > 0 && (
              <>
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mt-3">Predstojeći</p>
                {progress.upcoming_items
                  .filter((i: any) => i.scheduled_for !== new Date().toISOString().split('T')[0])
                  .map((item: any) => (
                    <PlanItemRow
                      key={item.id}
                      item={item}
                      onComplete={() => completeItemMutation.mutate(item.id)}
                      onDelete={() => deleteItemMutation.mutate(item.id)}
                    />
                  ))
                }
              </>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

// ── Helper komponente ──────────────────────────────────────

function StatCard({ icon, label, value, bg }: { icon: React.ReactNode; label: string; value: string; bg: string }) {
  return (
    <div className={clsx('rounded-2xl p-4 text-center', bg)}>
      <div className="flex justify-center mb-1">{icon}</div>
      <p className="text-lg font-extrabold text-gray-800">{value}</p>
      <p className="text-xs text-gray-500 mt-0.5">{label}</p>
    </div>
  )
}

function SliderField({ label, value, min, max, step = 1, onChange, suffix }: {
  label: string; value: number; min: number; max: number; step?: number
  onChange: (v: number) => void; suffix: string
}) {
  return (
    <div>
      <label className="text-xs font-semibold text-gray-600 mb-1 block">
        {label}: <span className="text-indigo-600">{value} {suffix}</span>
      </label>
      <input
        type="range" min={min} max={max} step={step} value={value}
        onChange={e => onChange(Number(e.target.value))}
        className="w-full accent-indigo-600"
      />
      <div className="flex justify-between text-[10px] text-gray-300 mt-0.5">
        <span>{min}</span><span>{max}</span>
      </div>
    </div>
  )
}

function PlanItemRow({ item, onComplete, onDelete }: {
  item: any; onComplete: () => void; onDelete: () => void
}) {
  return (
    <div className={clsx(
      'flex items-center gap-3 p-3 rounded-xl border',
      item.is_completed ? 'bg-gray-50 border-gray-100 opacity-60' : 'bg-white border-gray-200'
    )}>
      <button onClick={onComplete} disabled={item.is_completed}
        className="flex-shrink-0 disabled:cursor-default">
        {item.is_completed
          ? <CheckCircle className="w-5 h-5 text-green-500" />
          : <Circle className="w-5 h-5 text-gray-300 hover:text-indigo-500 transition-colors" />}
      </button>
      <div className="flex-1 min-w-0">
        <p className={clsx('text-sm font-semibold truncate', item.is_completed && 'line-through text-gray-400')}>
          {item.quiz?.title || 'Kviz'}
        </p>
        <p className="text-xs text-gray-400">
          {new Date(item.scheduled_for + 'T00:00:00').toLocaleDateString('sr-RS', { weekday: 'short', day: 'numeric', month: 'short' })}
        </p>
      </div>
      <span className={clsx('text-xs font-medium px-2 py-0.5 rounded-full', PRIORITY_COLORS[item.priority])}>
        {PRIORITY_LABELS[item.priority]}
      </span>
      <button onClick={onDelete}
        className="p-1.5 rounded-lg text-gray-300 hover:text-red-400 hover:bg-red-50 transition-colors">
        <Trash2 className="w-3.5 h-3.5" />
      </button>
    </div>
  )
}
