import React from 'react'
import { AuthProvider, useAuth } from './contexts/AuthContext'
import LoginPage from './pages/LoginPage'
import Navbar from './components/Navbar'
import DashboardPage from './pages/DashboardPage'

function DashboardShell() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      <Navbar />
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <DashboardPage />
      </main>
      <footer className="py-4 border-t border-slate-900 text-center text-xs text-slate-500">
        Tân Hưng Hà &bull; Hệ thống Quản trị Bản quyền Offline (OLM) &bull; Bảo mật Chữ ký số Ed25519
      </footer>
    </div>
  )
}

function MainApp() {
  const { isAuthenticated, loading } = useAuth()

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-3 border-emerald-500/30 border-t-emerald-500 rounded-full animate-spin" />
          <span className="text-xs text-slate-400">Đang khởi tạo phiên làm việc...</span>
        </div>
      </div>
    )
  }

  return isAuthenticated ? <DashboardShell /> : <LoginPage />
}

export default function App() {
  return (
    <AuthProvider>
      <MainApp />
    </AuthProvider>
  )
}
