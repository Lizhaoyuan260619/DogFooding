import { Outlet } from 'react-router-dom'
import Sidebar from '@/components/Sidebar'

export default function Layout() {
  return (
    <div className="min-h-screen bg-[#FFFDF7]">
      <Sidebar />
      <main className="md:ml-[240px] p-4 md:p-8 pb-24 md:pb-8">
        <Outlet />
      </main>
    </div>
  )
}
