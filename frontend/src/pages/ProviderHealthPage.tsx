import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { providersHealthApi } from '@/services/api'
import {
  Activity,
  RefreshCw,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  WifiOff,
  DollarSign,
  Clock,
  ShieldAlert,
  Key,
  User,
  Globe,
} from 'lucide-react'
import clsx from 'clsx'

interface ProviderStatus {
  id: string
  name: string
  status: string
  available: boolean
  system_key_set: boolean
  user_key_set: boolean
  message: string
}

interface HealthResponse {
  providers: ProviderStatus[]
  summary: string
}

const STATUS_CONFIG: Record<string, { icon: typeof Activity; color: string; bg: string; label: string }> = {
  ok: {
    icon: CheckCircle2,
    color: 'text-emerald-600',
    bg: 'bg-emerald-50 border-emerald-200',
    label: 'Dostupan',
  },
  missing_key: {
    icon: Key,
    color: 'text-amber-600',
    bg: 'bg-amber-50 border-amber-200',
    label: 'Nema ključa',
  },
  invalid_key: {
    icon: ShieldAlert,
    color: 'text-red-600',
    bg: 'bg-red-50 border-red-200',
    label: 'Neispravan ključ',
  },
  insufficient_balance: {
    icon: DollarSign,
    color: 'text-orange-600',
    bg: 'bg-orange-50 border-orange-200',
    label: 'Nema kredita',
  },
  forbidden: {
    icon: XCircle,
    color: 'text-red-600',
    bg: 'bg-red-50 border-red-200',
    label: 'Pristup odbijen',
  },
  rate_limited: {
    icon: Clock,
    color: 'text-amber-600',
    bg: 'bg-amber-50 border-amber-200',
    label: 'Limit dosegnut',
  },
  timeout: {
    icon: Clock,
    color: 'text-amber-600',
    bg: 'bg-amber-50 border-amber-200',
    label: 'Timeout',
  },
  unavailable: {
    icon: WifiOff,
    color: 'text-gray-500',
    bg: 'bg-gray-50 border-gray-200',
    label: 'Nedostupan',
  },
  error: {
    icon: AlertTriangle,
    color: 'text-red-600',
    bg: 'bg-red-50 border-red-200',
    label: 'Greška',
  },
}

function ProviderCard({ provider }: { provider: ProviderStatus }) {
  const cfg = STATUS_CONFIG[provider.status] || STATUS_CONFIG.error
  const Icon = cfg.icon

  return (
    <div
      className={clsx(
        'rounded-xl border p-5 transition-all duration-200 hover:shadow-md',
        cfg.bg
      )}
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          <div className={clsx('w-10 h-10 rounded-lg flex items-center justify-center', cfg.color, 'bg-white/80')}>
            <Icon className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-semibold text-gray-900">{provider.name}</h3>
            <p className={clsx('text-sm font-medium', cfg.color)}>{cfg.label}</p>
          </div>
        </div>
        <div className={clsx('w-3 h-3 rounded-full flex-shrink-0', provider.available ? 'bg-emerald-500 shadow-sm shadow-emerald-200' : 'bg-red-400')} />
      </div>

      <p className="text-sm text-gray-600 mb-3">{provider.message}</p>

      <div className="flex items-center gap-4 text-xs text-gray-500">
        {provider.system_key_set && (
          <span className="flex items-center gap-1.5">
            <Globe className="w-3.5 h-3.5" />
            Sistemski ključ
          </span>
        )}
        {provider.user_key_set && (
          <span className="flex items-center gap-1.5">
            <User className="w-3.5 h-3.5" />
            Tvoj ključ
          </span>
        )}
        {!provider.system_key_set && !provider.user_key_set && (
          <span className="text-gray-400">Nije podešen</span>
        )}
      </div>
    </div>
  )
}

export default function ProviderHealthPage() {
  const [refreshing, setRefreshing] = useState(false)

  const { data, isLoading, error, refetch } = useQuery<HealthResponse>({
    queryKey: ['providers-health'],
    queryFn: async () => {
      const res = await providersHealthApi.check()
      return res.data
    },
    refetchInterval: 60000,
  })

  const handleRefresh = async () => {
    setRefreshing(true)
    await refetch()
    setTimeout(() => setRefreshing(false), 500)
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin" />
          <p className="text-gray-500 font-medium">Proveravam provajdere...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <AlertTriangle className="w-12 h-12 text-red-400 mx-auto mb-3" />
          <p className="text-gray-600 font-medium">Greška pri učitavanju</p>
          <button
            onClick={handleRefresh}
            className="mt-4 px-4 py-2 bg-indigo-500 text-white rounded-lg hover:bg-indigo-600 transition-colors text-sm font-medium"
          >
            Pokušaj ponovo
          </button>
        </div>
      </div>
    )
  }

  const providers = data?.providers || []
  const available = providers.filter(p => p.available).length
  const total = providers.length

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Status provajdera</h1>
          <p className="text-gray-500 mt-1">Provera dostupnosti AI modela</p>
        </div>
        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className="flex items-center gap-2 px-4 py-2.5 bg-white border border-gray-200 rounded-xl hover:bg-gray-50 transition-all text-sm font-medium text-gray-700 disabled:opacity-50"
        >
          <RefreshCw className={clsx('w-4 h-4', refreshing && 'animate-spin')} />
          Osveži
        </button>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="bg-white rounded-xl border border-gray-200 p-4">
          <p className="text-2xl font-bold text-gray-900">{available}/{total}</p>
          <p className="text-sm text-gray-500 mt-1">Dostupno</p>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-4">
          <p className="text-2xl font-bold text-emerald-600">{available}</p>
          <p className="text-sm text-gray-500 mt-1">Aktivni</p>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-4">
          <p className="text-2xl font-bold text-red-500">{total - available}</p>
          <p className="text-sm text-gray-500 mt-1">Nedostupni</p>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-4">
          <p className="text-2xl font-bold text-indigo-500">{providers.filter(p => p.system_key_set || p.user_key_set).length}</p>
          <p className="text-sm text-gray-500 mt-1">Sa ključem</p>
        </div>
      </div>

      {/* Provider cards */}
      <div className="grid sm:grid-cols-2 gap-4">
        {providers.map(provider => (
          <ProviderCard key={provider.id} provider={provider} />
        ))}
      </div>

      {/* Legend */}
      <div className="bg-white rounded-xl border border-gray-200 p-4">
        <p className="text-sm font-medium text-gray-700 mb-2">Šta znače statusi?</p>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs text-gray-500">
          <span className="flex items-center gap-1.5">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" /> Dostupan
          </span>
          <span className="flex items-center gap-1.5">
            <DollarSign className="w-3.5 h-3.5 text-orange-500" /> Nema kredita
          </span>
          <span className="flex items-center gap-1.5">
            <ShieldAlert className="w-3.5 h-3.5 text-red-500" /> Neispravan ključ
          </span>
          <span className="flex items-center gap-1.5">
            <Key className="w-3.5 h-3.5 text-amber-500" /> Nije podešen
          </span>
          <span className="flex items-center gap-1.5">
            <WifiOff className="w-3.5 h-3.5 text-gray-500" /> Servis nedostupan
          </span>
          <span className="flex items-center gap-1.5">
            <Clock className="w-3.5 h-3.5 text-amber-500" /> Timeout / Limit
          </span>
        </div>
      </div>
    </div>
  )
}
