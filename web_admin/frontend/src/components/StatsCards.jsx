import React, { useEffect, useState } from 'react'
import { licenseApi } from '../api/licenseApi'
import { Smartphone, Crown, Clock, AlertTriangle, Cpu } from 'lucide-react'

export default function StatsCards({ refreshTrigger = 0 }) {
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function loadStats() {
      try {
        const data = await licenseApi.getStats()
        setStats(data)
      } catch (err) {
        console.error('Không thể tải thống kê KPI:', err)
      } finally {
        setLoading(false)
      }
    }
    loadStats()
  }, [refreshTrigger])

  if (loading || !stats) {
    return (
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="h-24 bg-slate-900/60 border border-slate-800 rounded-2xl animate-pulse" />
        ))}
      </div>
    )
  }

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      {/* Tổng số thiết bị */}
      <div className="p-4 rounded-2xl bg-slate-900/90 border border-slate-800/90 shadow-md flex items-center justify-between">
        <div>
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
            TỔNG THIẾT BỊ PDA
          </span>
          <span className="text-2xl font-extrabold text-white mt-1 block">
            {stats.total_devices} <span className="text-xs font-normal text-slate-400">máy</span>
          </span>
          <span className="text-[11px] text-emerald-400 font-medium">
            {stats.total_active_licenses} license kích hoạt
          </span>
        </div>
        <div className="p-3 bg-blue-500/10 border border-blue-500/20 text-blue-400 rounded-2xl">
          <Smartphone className="w-5 h-5" />
        </div>
      </div>

      {/* Gói PRO Vĩnh viễn */}
      <div className="p-4 rounded-2xl bg-slate-900/90 border border-slate-800/90 shadow-md flex items-center justify-between">
        <div>
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
            PRO VĨNH VIỄN
          </span>
          <span className="text-2xl font-extrabold text-amber-300 mt-1 block">
            {stats.permanent_licenses} <span className="text-xs font-normal text-slate-400">máy</span>
          </span>
          <span className="text-[11px] text-amber-400/90 font-medium">Bản quyền trọn đời</span>
        </div>
        <div className="p-3 bg-amber-500/10 border border-amber-500/20 text-amber-400 rounded-2xl">
          <Crown className="w-5 h-5" />
        </div>
      </div>

      {/* Gói Dùng thử Trial */}
      <div className="p-4 rounded-2xl bg-slate-900/90 border border-slate-800/90 shadow-md flex items-center justify-between">
        <div>
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
            DÙNG THỬ (TRIAL)
          </span>
          <span className="text-2xl font-extrabold text-purple-300 mt-1 block">
            {stats.trial_licenses} <span className="text-xs font-normal text-slate-400">máy</span>
          </span>
          <span className="text-[11px] text-purple-400/90 font-medium">Đang trải nghiệm</span>
        </div>
        <div className="p-3 bg-purple-500/10 border border-purple-500/20 text-purple-400 rounded-2xl">
          <Clock className="w-5 h-5" />
        </div>
      </div>

      {/* Sắp hết hạn */}
      <div className="p-4 rounded-2xl bg-slate-900/90 border border-slate-800/90 shadow-md flex items-center justify-between">
        <div>
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
            HẾT HẠN &lt; 30 NGÀY
          </span>
          <span className={`text-2xl font-extrabold mt-1 block ${stats.expiring_soon_licenses > 0 ? 'text-rose-400' : 'text-slate-200'}`}>
            {stats.expiring_soon_licenses} <span className="text-xs font-normal text-slate-400">máy</span>
          </span>
          <span className="text-[11px] text-slate-400 font-medium">Cần nhắc gia hạn</span>
        </div>
        <div className="p-3 bg-rose-500/10 border border-rose-500/20 text-rose-400 rounded-2xl">
          <AlertTriangle className="w-5 h-5" />
        </div>
      </div>
    </div>
  )
}

