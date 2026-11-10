import React from 'react'
import { QrCode, Smartphone, User, ShieldCheck, Clock, Crown, ArrowUpRight } from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'

export default function LicenseTable({ licenses, loading, onSelectLicense, onOpenUpgrade }) {
  const { isAdmin } = useAuth()

  const formatDate = (isoString) => {
    if (!isoString) return 'Vĩnh viễn'
    try {
      const d = new Date(isoString)
      return d.toLocaleDateString('vi-VN', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
      })
    } catch {
      return isoString
    }
  }

  const isExpiringSoon = (expiresAt, isPermanent) => {
    if (isPermanent || !expiresAt) return false
    const exp = new Date(expiresAt).getTime()
    const now = new Date().getTime()
    const diffDays = (exp - now) / (1000 * 3600 * 24)
    return diffDays > 0 && diffDays <= 30
  }

  const isExpired = (expiresAt, isPermanent) => {
    if (isPermanent || !expiresAt) return false
    return new Date(expiresAt).getTime() < new Date().getTime()
  }

  if (loading) {
    return (
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-12 text-center shadow-lg">
        <div className="w-8 h-8 border-3 border-emerald-500/30 border-t-emerald-500 rounded-full animate-spin mx-auto mb-3" />
        <p className="text-xs text-slate-400">Đang đồng bộ dữ liệu thiết bị PDA từ máy chủ...</p>
      </div>
    )
  }

  if (!licenses || licenses.length === 0) {
    return (
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-12 text-center shadow-lg">
        <div className="w-12 h-12 rounded-2xl bg-slate-800 text-slate-400 flex items-center justify-center mx-auto mb-3">
          <Smartphone className="w-6 h-6" />
        </div>
        <h4 className="text-sm font-bold text-white mb-1">Không tìm thấy thiết bị nào</h4>
        <p className="text-xs text-slate-400 max-w-sm mx-auto">
          Không có kết quả nào khớp với từ khóa tìm kiếm. Vui lòng kiểm tra lại mã DF hoặc số điện thoại.
        </p>
      </div>
    )
  }

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          {/* Table Header */}
          <thead className="bg-slate-950/80 text-slate-400 uppercase tracking-wider text-[11px] border-b border-slate-800">
            <tr>
              <th className="py-3.5 px-4 font-semibold">Khách Hàng</th>
              <th className="py-3.5 px-4 font-semibold">Thiết Bị PDA</th>
              <th className="py-3.5 px-4 font-semibold">Mã DF (Phần cứng)</th>
              <th className="py-3.5 px-4 font-semibold">Gói Bản Quyền</th>
              <th className="py-3.5 px-4 font-semibold">Hạn Sử Dụng</th>
              <th className="py-3.5 px-4 font-semibold text-center">Trạng Thái</th>
              <th className="py-3.5 px-4 font-semibold text-right">Thao Tác</th>
            </tr>
          </thead>

          {/* Table Body */}
          <tbody className="divide-y divide-slate-800/60 text-slate-300">
            {licenses.map((item) => {
              const expired = isExpired(item.expires_at, item.is_permanent)
              const expiring = isExpiringSoon(item.expires_at, item.is_permanent)

              return (
                <tr
                  key={item.id}
                  className="hover:bg-slate-800/40 transition group"
                >
                  {/* Khách hàng */}
                  <td className="py-3.5 px-4">
                    <div className="font-bold text-white text-xs mb-0.5">{item.customer_name}</div>
                    <div className="text-[11px] text-slate-400 flex items-center gap-1">
                      <span>SĐT:</span>
                      <span className="font-medium text-slate-300">{item.customer_phone || '---'}</span>
                    </div>
                  </td>

                  {/* Thiết bị PDA */}
                  <td className="py-3.5 px-4">
                    <div className="font-semibold text-slate-200 flex items-center gap-1.5">
                      <Smartphone className="w-3.5 h-3.5 text-blue-400" />
                      {item.model}
                    </div>
                    <div className="text-[10px] text-slate-500">v{item.version}</div>
                  </td>

                  {/* Mã DF Crockford */}
                  <td className="py-3.5 px-4">
                    <code className="px-2 py-1 rounded bg-slate-950 font-mono text-[11px] text-emerald-400 border border-slate-800 font-semibold">
                      {item.df}
                    </code>
                  </td>

                  {/* Gói Bản quyền */}
                  <td className="py-3.5 px-4">
                    {item.is_permanent ? (
                      <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[10px] font-bold bg-amber-500/15 text-amber-300 border border-amber-500/30">
                        <Crown className="w-3 h-3 text-amber-400" /> PRO VĨNH VIỄN
                      </span>
                    ) : item.license_type === 'PRO' ? (
                      <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[10px] font-bold bg-purple-500/15 text-purple-300 border border-purple-500/30">
                        <ShieldCheck className="w-3 h-3 text-purple-400" /> GÓI PRO
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[10px] font-bold bg-blue-500/15 text-blue-300 border border-blue-500/30">
                        <Clock className="w-3 h-3 text-blue-400" /> DÙNG THỬ (TRIAL)
                      </span>
                    )}
                  </td>

                  {/* Hạn sử dụng */}
                  <td className="py-3.5 px-4">
                    {item.is_permanent ? (
                      <span className="text-emerald-400 font-semibold text-xs">Vĩnh viễn</span>
                    ) : (
                      <div>
                        <div className={`font-semibold ${expired ? 'text-rose-400' : expiring ? 'text-amber-400' : 'text-slate-200'}`}>
                          {formatDate(item.expires_at)}
                        </div>
                        {expired && <span className="text-[10px] text-rose-400">Đã hết hạn</span>}
                        {expiring && !expired && <span className="text-[10px] text-amber-400">Sắp hết hạn</span>}
                      </div>
                    )}
                  </td>

                  {/* Trạng thái */}
                  <td className="py-3.5 px-4 text-center">
                    {item.status === 'ACTIVE' ? (
                      <span className="inline-block w-2 h-2 rounded-full bg-emerald-400 shadow-sm shadow-emerald-400/50" title="Đang kích hoạt (ACTIVE)" />
                    ) : (
                      <span className="inline-block w-2 h-2 rounded-full bg-slate-600" title="Đã nâng cấp (SUPERSEDED)" />
                    )}
                  </td>

                  {/* Thao tác */}
                  <td className="py-3.5 px-4 text-right">
                    <div className="flex items-center justify-end gap-1.5">
                      {/* Nút Xem & Cấp lại: SALE và ADMIN đều thấy */}
                      <button
                        onClick={() => onSelectLicense(item)}
                        className="inline-flex items-center gap-1.5 px-2.5 py-1.5 bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-400 border border-emerald-500/30 rounded-lg text-xs font-semibold transition"
                        title="Xem mã QR và cấp lại cho khách"
                      >
                        <QrCode className="w-3.5 h-3.5" />
                        <span>Xem & Cấp lại</span>
                      </button>

                      {/* Nút Nâng cấp gói: Chỉ ADMIN mới thấy */}
                      {isAdmin && onOpenUpgrade && (
                        <button
                          onClick={() => onOpenUpgrade(item)}
                          className="inline-flex items-center gap-1 px-2.5 py-1.5 bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-300 border border-indigo-500/30 rounded-lg text-xs font-semibold transition"
                          title="Nâng cấp lên gói PRO vĩnh viễn"
                        >
                          <ArrowUpRight className="w-3.5 h-3.5" />
                          <span>Nâng cấp</span>
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}

