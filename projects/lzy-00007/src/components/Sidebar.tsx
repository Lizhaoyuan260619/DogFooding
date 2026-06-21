import { NavLink } from 'react-router-dom'
import { LayoutDashboard, ListChecks, CalendarDays, BarChart3, Settings, Trophy, Users } from 'lucide-react'

const navItems = [
  { to: '/', label: '仪表盘', icon: LayoutDashboard },
  { to: '/habits', label: '习惯管理', icon: ListChecks },
  { to: '/calendar', label: '日历热力图', icon: CalendarDays },
  { to: '/stats', label: '统计分析', icon: BarChart3 },
  { to: '/achievements', label: '成就中心', icon: Trophy },
  { to: '/circle', label: '打卡圈', icon: Users },
  { to: '/settings', label: '设置', icon: Settings },
]

export default function Sidebar() {
  return (
    <>
      <aside className="hidden md:flex fixed left-0 top-0 h-screen w-[240px] flex-col bg-white shadow-sm z-40">
        <div className="flex items-center gap-2 px-6 py-5 border-b border-gray-100">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-emerald-500 text-white">
            <ListChecks size={20} />
          </div>
          <span className="text-lg font-bold text-gray-800">习惯追踪</span>
        </div>

        <nav className="flex-1 px-3 py-4 space-y-1">
          {navItems.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-emerald-50 text-emerald-600'
                    : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                }`
              }
            >
              <Icon size={20} />
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>
      </aside>

      <nav className="fixed bottom-0 left-0 right-0 z-40 flex md:hidden items-center justify-around bg-white border-t border-gray-100 shadow-[0_-1px_4px_rgba(0,0,0,0.05)]">
        {navItems.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              `flex flex-col items-center gap-0.5 py-2 px-1 text-[10px] font-medium transition-colors ${
                isActive
                  ? 'text-emerald-600'
                  : 'text-gray-400'
              }`
            }
          >
            <Icon size={20} />
            <span>{label}</span>
          </NavLink>
        ))}
      </nav>
    </>
  )
}
