import React, { useState } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { ShieldCheck, Lock, User, Eye, EyeOff, LogIn } from 'lucide-react'

export default function LoginPage() {
  const { login } = useAuth()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!username.trim() || !password) {
      setError('Vui lòng nhập đầy đủ tên đăng nhập và mật khẩu!')
      return
    }

    setError('')
    setLoading(true)
    try {
      await login(username.trim(), password)
    } catch (err) {
      console.error(err)
      if (err.response?.data?.detail) {
        setError(err.response.data.detail)
      } else {
        setError('Không thể kết nối tới máy chủ. Vui lòng kiểm tra lại!')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-emerald-950 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        {/* Logo & Tiêu đề */}
        <div className="flex justify-center">
          <div className="w-16 h-16 bg-emerald-600 rounded-2xl flex items-center justify-center shadow-lg shadow-emerald-500/30 border border-emerald-400/40">
            <ShieldCheck className="w-10 h-10 text-white" />
          </div>
        </div>
        <h2 className="mt-4 text-center text-2xl font-extrabold text-white tracking-tight">
          TÂN HƯNG HÀ OLM
        </h2>
        <p className="mt-1 text-center text-sm text-slate-300">
          Cổng Quản Trị Cấp Bản Quyền Offline (Ed25519 PDA)
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-slate-800/90 backdrop-blur-md py-8 px-6 shadow-2xl rounded-2xl border border-slate-700/80 sm:px-10">
          {error && (
            <div className="mb-5 bg-rose-500/10 border border-rose-500/30 text-rose-300 text-sm p-3.5 rounded-xl flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-rose-400"></span>
              {error}
            </div>
          )}

          <form className="space-y-5" onSubmit={handleSubmit}>
            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                Tên đăng nhập
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                  <User className="h-5 w-5" />
                </div>
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="Nhập tên đăng nhập..."
                  autoComplete="username"
                  className="block w-full pl-10 pr-3 py-2.5 bg-slate-950/80 border border-slate-700 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent text-sm transition"
                  disabled={loading}
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                Mật khẩu
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                  <Lock className="h-5 w-5" />
                </div>
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Nhập mật khẩu..."
                  autoComplete="current-password"
                  className="block w-full pl-10 pr-10 py-2.5 bg-slate-950/80 border border-slate-700 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent text-sm transition"
                  disabled={loading}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-slate-400 hover:text-slate-200 transition"
                >
                  {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full flex justify-center items-center gap-2 py-3 px-4 border border-transparent rounded-xl shadow-md text-sm font-semibold text-white bg-emerald-600 hover:bg-emerald-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-emerald-500 disabled:opacity-50 transition"
            >
              {loading ? (
                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                <>
                  <LogIn className="w-4 h-4" /> Đăng nhập hệ thống
                </>
              )}
            </button>
          </form>
        </div>

        {/* Footer ghi chú bảo mật */}
        <p className="mt-6 text-center text-xs text-slate-400">
          Chữ ký số Ed25519 &bull; Chuẩn JWT RFC 8037 &bull; Tân Hưng Hà
        </p>
      </div>
    </div>
  )
}
