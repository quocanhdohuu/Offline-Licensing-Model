import React from 'react'
import { useAuth } from '../contexts/AuthContext'
import { ShieldCheck, Shield, UserCheck, LogOut, KeyRound } from 'lucide-react'

export default function Navbar() {
  const { user, isAdmin, logout } = useAuth()

  return (
    <header className="bg-slate-900 border-b border-slate-800 sticky top-0 z-40 shadow-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16 items-center">
          {/* Logo & Brand */}
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-emerald-600 rounded-xl flex items-center justify-center shadow-md shadow-emerald-500/20 border border-emerald-400/30">
              <ShieldCheck className="w-6 h-6 text-white" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-extrabold text-white text-base tracking-tight">TÂN HƯNG HÀ</span>
                <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                  OLM v1.0
                </span>
              </div>
              <p className="text-xs text-slate-400 hidden sm:block">
                Cổng Quản Trị Cấp Bản Quyền Thiết Bị PDA
              </p>
            </div>
          </div>

          {/* User Info & Role Badge & Logout */}
          <div className="flex items-center gap-4">
            {/* Role Badge */}
            {isAdmin ? (
              <div className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-indigo-500/15 text-indigo-400 border border-indigo-500/30 shadow-sm">
                <Shield className="w-3.5 h-3.5 text-indigo-400" />
                <span>QUẢN TRỊ VIÊN (ADMIN)</span>
              </div>
            ) : (
              <div className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 shadow-sm">
                <UserCheck className="w-3.5 h-3.5 text-emerald-400" />
                <span>KINH DOANH (SALE)</span>
              </div>
            )}

            {/* Profile */}
            <div className="hidden md:flex flex-col text-right">
              <span className="text-xs font-bold text-slate-200">{user?.full_name}</span>
              <span className="text-[11px] text-slate-400">@{user?.username}</span>
            </div>

            {/* Logout button */}
            <button
              onClick={logout}
              title="Đăng xuất"
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700/80 border border-slate-700 transition"
            >
              <LogOut className="w-3.5 h-3.5 text-rose-400" />
              <span className="hidden sm:inline">Đăng xuất</span>
            </button>
          </div>
        </div>
      </div>
    </header>
  )
}

