import { Outlet } from 'react-router-dom'
import { useEffect } from 'react'
import Sidebar from '@/components/Sidebar'
import BadgeUnlockModal from '@/components/BadgeUnlockModal'
import { useAppStore } from '@/store/useAppStore'

export default function Layout() {
  const { initDemoData, initialized } = useAppStore()

  useEffect(() => {
    if (!initialized) {
      initDemoData()
    }
  }, [initialized, initDemoData])

  return (
    <div className="min-h-screen bg-[#FFFDF7]">
      <Sidebar />
      <main className="md:ml-[240px] p-4 md:p-8 pb-24 md:pb-8">
        <Outlet />
      </main>
      <BadgeUnlockModal />
    </div>
  )
}
