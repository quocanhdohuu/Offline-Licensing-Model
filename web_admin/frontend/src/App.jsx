import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { ShieldCheck, Server, Laptop, CheckCircle, AlertCircle } from 'lucide-react'

export default function App() {
  const [health, setHealth] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    axios.get('/api/health')
      .then(res => {
        setHealth(res.data)
        setLoading(false)
      })
      .catch(err => {
        console.error(err)
        setError('Không thể kết nối tới Backend API')
        setLoading(false)
      })
  }, [])

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-6 bg-slate-900 text-white">
      <div className="max-w-xl w-full bg-slate-800 border border-slate-700 rounded-2xl p-8 shadow-2xl">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-xl">
            <ShieldCheck className="w-8 h-8 text-emerald-400" />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight">Tân Hưng Hà OLM - Admin Portal</h1>
            <p className="text-xs text-slate-400">Offline Licensing Model (JWT Ed25519 PDA)</p>
          </div>
        </div>

        <div className="space-y-4">
          <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-700/50 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Laptop className="w-5 h-5 text-blue-400" />
              <div>
                <div className="text-sm font-medium">Frontend React (Vite + Tailwind)</div>
                <div className="text-xs text-slate-400">Chạy tại http://localhost:5173</div>
              </div>
            </div>
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              <CheckCircle className="w-3.5 h-3.5" /> Sẵn sàng
            </span>
          </div>

          <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-700/50 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Server className="w-5 h-5 text-purple-400" />
              <div>
                <div className="text-sm font-medium">Backend Python (FastAPI REST API)</div>
                <div className="text-xs text-slate-400">Chạy tại http://localhost:8000</div>
              </div>
            </div>
            {loading ? (
              <span className="text-xs text-slate-400 animate-pulse">Đang kiểm tra...</span>
            ) : health ? (
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                <CheckCircle className="w-3.5 h-3.5" /> Đã kết nối API
              </span>
            ) : (
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">
                <AlertCircle className="w-3.5 h-3.5" /> {error}
              </span>
            )}
          </div>
        </div>

        <div className="mt-8 pt-6 border-t border-slate-700/50 flex items-center justify-between text-xs text-slate-400">
          <span>Trạng thái: Hoàn thành Bước 1 (Scaffolding & Setup)</span>
          <span className="text-emerald-400 font-medium">Sẵn sàng sang Bước 2</span>
        </div>
      </div>
    </div>
  )
}

