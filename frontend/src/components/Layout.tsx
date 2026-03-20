import { Outlet, NavLink, useNavigate, useLocation } from 'react-router-dom'
import { useAuthStore } from '@/stores/authStore'
import { 
  FileText, 
  Settings, 
  LogOut, 
  Menu, 
  X,
  Sparkles,
  LayoutDashboard,
  PenTool,
  Bell,
  BookOpen,
  BarChart2,
  Brain
} from 'lucide-react'
import { useState } from 'react'
import clsx from 'clsx'

const navigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'Dokumenti', href: '/documents', icon: FileText },
  { name: 'Pregled prevoda', href: '/review', icon: PenTool },
  { name: 'Kvizovi', href: '/quizzes', icon: BookOpen },
  { name: 'Test Inteligencije', href: '/intelligence-test', icon: Brain },
  { name: 'Baza Znanja', href: '/knowledge', icon: Brain },
  { name: 'Analitika', href: '/analytics', icon: BarChart2 },
  { name: 'Podešavanja', href: '/settings', icon: Settings },
]

const pageTitles: Record<string, string> = {
  '/': 'Dashboard',
  '/documents': 'Dokumenti',
  '/review': 'Pregled prevoda',
  '/quizzes': 'Kvizovi',
  '/intelligence-test': 'Test Inteligencije',
  '/knowledge': 'Baza Znanja',
  '/analytics': 'Analitika',
  '/settings': 'Podešavanja',
}

export default function Layout() {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()
  const location = useLocation()
  const [sidebarOpen, setSidebarOpen] = useState(false)

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const currentPageTitle = pageTitles[location.pathname] || 
    (location.pathname.startsWith('/documents/') ? 'Detalji dokumenta' :
     location.pathname.startsWith('/review/') ? 'Pregled prevoda' :
     location.pathname.includes('/play') ? 'Igraj kviz' :
     location.pathname.includes('/results') ? 'Rezultati kviza' :
     location.pathname.startsWith('/quizzes/') ? 'Kviz' : 'AI Learning')

  const userInitial = (user?.full_name?.[0] || user?.email?.[0] || 'U').toUpperCase()

  return (
    <div className="min-h-screen gradient-bg flex">
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div 
          className="lg:hidden fixed inset-0 bg-black/40 backdrop-blur-sm z-40"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={clsx(
          "fixed top-0 left-0 z-50 h-screen w-64 flex flex-col transition-transform duration-300 lg:translate-x-0 lg:static lg:z-auto",
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        )}
        style={{ background: 'linear-gradient(180deg, #1e1b4b 0%, #312e81 40%, #4c1d95 100%)' }}
      >
        {/* Logo */}
        <div className="flex items-center justify-between px-5 py-6">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl flex items-center justify-center"
              style={{ background: 'linear-gradient(135deg, #818cf8 0%, #a78bfa 100%)' }}>
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="font-extrabold text-white text-base leading-tight">AI Learning</h1>
              <p className="text-[10px] text-indigo-300 font-medium">Sistem za učenje</p>
            </div>
          </div>
          <button
            onClick={() => setSidebarOpen(false)}
            className="lg:hidden p-1.5 rounded-lg hover:bg-white/10 text-indigo-300"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Nav label */}
        <div className="px-5 mb-2">
          <p className="text-[10px] font-semibold tracking-widest text-indigo-400 uppercase">Navigacija</p>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-3 space-y-0.5 overflow-y-auto scrollbar-hide">
          {navigation.map((item) => (
            <NavLink
              key={item.name}
              to={item.href}
              end={item.href === '/'}
              onClick={() => setSidebarOpen(false)}
              className={({ isActive }) =>
                clsx("sidebar-item", isActive && "sidebar-item-active")
              }
            >
              <item.icon className="w-4.5 h-4.5 flex-shrink-0" style={{ width: '18px', height: '18px' }} />
              <span>{item.name}</span>
            </NavLink>
          ))}
        </nav>

        {/* User section */}
        <div className="px-3 pb-5 pt-3 border-t border-white/10">
          <div className="flex items-center gap-3 px-3 py-3 rounded-xl mb-2" style={{ background: 'rgba(255,255,255,0.07)' }}>
            <div className="w-9 h-9 rounded-full flex items-center justify-center text-white text-sm font-bold flex-shrink-0"
              style={{ background: 'linear-gradient(135deg, #818cf8, #a78bfa)' }}>
              {userInitial}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-white text-sm font-semibold truncate leading-tight">
                {user?.full_name || 'Korisnik'}
              </p>
              <p className="text-indigo-300 text-xs truncate">{user?.email}</p>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-slate-400 hover:bg-red-500/15 hover:text-red-300 transition-all duration-200 text-sm font-medium"
          >
            <LogOut className="w-4 h-4 flex-shrink-0" />
            <span>Odjavi se</span>
          </button>
        </div>
      </aside>

      {/* Main content */}
      <div className="flex-1 flex flex-col min-h-screen lg:min-w-0">
        {/* Top header */}
        <header className="sticky top-0 z-30 bg-white/90 backdrop-blur-md border-b border-gray-100 shadow-sm h-16 flex items-center px-6 gap-4">
          <button
            onClick={() => setSidebarOpen(true)}
            className="lg:hidden p-2 rounded-xl hover:bg-gray-100 text-gray-600 transition-colors"
          >
            <Menu className="w-5 h-5" />
          </button>
          
          <div className="flex-1">
            <h2 className="text-lg font-bold text-gray-900">{currentPageTitle}</h2>
          </div>

          <div className="flex items-center gap-3">
            <button className="p-2 rounded-xl hover:bg-gray-100 text-gray-500 transition-colors relative">
              <Bell className="w-5 h-5" />
            </button>
            <div className="w-9 h-9 rounded-full flex items-center justify-center text-white text-sm font-bold cursor-pointer"
              style={{ background: 'linear-gradient(135deg, #6366f1, #8b5cf6)' }}>
              {userInitial}
            </div>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 p-6 lg:p-8">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
