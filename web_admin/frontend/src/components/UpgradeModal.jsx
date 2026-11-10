import React, { useState } from 'react'
import { X, Crown, ShieldCheck, Check, AlertCircle, Smartphone, Download, Copy, Sparkles, ArrowRight } from 'lucide-react'
import { licenseApi } from '../api/licenseApi'

export default function UpgradeModal({ license, onClose, onSuccess }) {
  const [isPermanent, setIsPermanent] = useState(true)
  const [daysValid, setDaysValid] = useState(365)
  const [upgradeNotes, setUpgradeNotes] = useState('Khách hàng mua bản quyền PRO vĩnh viễn sau dùng thử')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)
  const [copiedToken, setCopiedToken] = useState(false)

  if (!license) return null

  const handleUpgradeSubmit = async (e) => {
    e.preventDefault()
    setSubmitting(true)
    setError('')
    try {
      const payload = {
        license_type: 'PRO',
        days_valid: isPermanent ? 0 : Number(daysValid),
        is_permanent: isPermanent,
        notes: upgradeNotes.trim() || undefined
      }

      const res = await licenseApi.upgradeLicense(license.id, payload)
      setResult(res)
      if (onSuccess) onSuccess()
    } catch (err) {
      console.error(err)
      setError(err.response?.data?.detail || 'Lỗi khi nâng cấp license. Vui lòng thử lại!')
    } finally {
      setSubmitting(false)
    }
  }

  const handleDownloadQr = () => {
    if (!result) return
    const cleanDf = result.df.replace(/-/g, '')
    const link = document.createElement('a')
    link.href = result.qr_code_base64
    link.download = `qr_${cleanDf}_v${result.version}.png`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  const handleCopyToken = () => {
    if (!result) return
    navigator.clipboard.writeText(result.license_jwt)
    setCopiedToken(true)
    setTimeout(() => setCopiedToken(false), 2500)
  }

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="relative bg-slate-900 border border-slate-700 w-full max-w-xl rounded-2xl shadow-2xl overflow-hidden">
        {/* Modal Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-950/70">
          <div className="flex items-center gap-2.5">
            <div className="p-2 bg-amber-500/10 border border-amber-500/20 text-amber-400 rounded-xl">
              <Crown className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white">Nâng Cấp Gói Bản Quyền (Admin)</h3>
              <p className="text-xs text-slate-400">Giữ nguyên mã DF của máy, sinh chữ ký Ed25519 phiên bản mới</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {result ? (
          /* Màn hình kết quả sau khi nâng cấp thành công */
          <div className="p-6 text-center space-y-5">
            <div className="w-14 h-14 bg-amber-500/20 border border-amber-500/30 text-amber-300 rounded-2xl flex items-center justify-center mx-auto shadow-lg shadow-amber-500/20">
              <Crown className="w-8 h-8" />
            </div>
            <div>
              <h4 className="text-lg font-bold text-white">Nâng Cấp Bản Quyền Thành Công!</h4>
              <p className="text-xs text-slate-400 mt-1">
                Thiết bị <strong className="text-emerald-400">{result.model}</strong> đã được nâng cấp lên:{' '}
                <span className="font-bold text-amber-300">
                  {result.is_permanent ? 'PRO VĨNH VIỄN' : 'PRO GIA HẠN'} (v{result.version})
                </span>
              </p>
            </div>

            <div className="bg-slate-950 p-4 rounded-2xl border border-slate-800 inline-block mx-auto">
              <div className="bg-white p-2.5 rounded-xl inline-block border-2 border-amber-500/40">
                <img
                  src={result.qr_code_base64}
                  alt="QR Code nâng cấp"
                  className="w-44 h-44 object-contain"
                />
              </div>
              <p className="text-[11px] text-slate-400 mt-2">
                👉 Khách hàng quét mã QR này trên App PDA để nhận bản quyền mới tức thì.
              </p>
            </div>

            <div className="flex flex-col sm:flex-row gap-2.5 justify-center max-w-md mx-auto">
              <button
                type="button"
                onClick={handleDownloadQr}
                className="flex-1 flex items-center justify-center gap-2 py-2.5 px-4 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-xs font-semibold shadow-md transition"
              >
                <Download className="w-4 h-4" /> Tải ảnh QR (PNG)
              </button>
              <button
                type="button"
                onClick={handleCopyToken}
                className="flex-1 flex items-center justify-center gap-2 py-2.5 px-4 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-xl text-xs font-medium border border-slate-700 transition"
              >
                {copiedToken ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
                {copiedToken ? 'Đã sao chép' : 'Sao chép Token'}
              </button>
            </div>

            <div className="pt-4 border-t border-slate-800">
              <button
                onClick={onClose}
                className="px-6 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-xl text-xs font-semibold transition"
              >
                Hoàn tất & Đóng
              </button>
            </div>
          </div>
        ) : (
          /* Form nâng cấp */
          <form onSubmit={handleUpgradeSubmit} className="p-6 space-y-4">
            {error && (
              <div className="p-3 bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs rounded-xl flex items-center gap-2">
                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                <span>{error}</span>
              </div>
            )}

            {/* Thông tin thiết bị hiện tại */}
            <div className="p-4 bg-slate-950/70 border border-slate-800 rounded-xl space-y-2 text-xs">
              <div className="flex justify-between">
                <span className="text-slate-400">Khách hàng:</span>
                <span className="text-white font-bold">{license.customer_name}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Model thiết bị:</span>
                <span className="text-white font-semibold flex items-center gap-1">
                  <Smartphone className="w-3.5 h-3.5 text-blue-400" />
                  {license.model}
                </span>
              </div>
              <div className="flex justify-between items-center pt-1 border-t border-slate-800/80">
                <span className="text-slate-400">Mã DF (Hằng số):</span>
                <code className="text-emerald-400 font-mono font-bold">{license.df}</code>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-400">Gói hiện tại:</span>
                <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-slate-800 text-slate-300">
                  {license.is_permanent ? 'PRO VĨNH VIỄN' : license.license_type} (v{license.version})
                </span>
              </div>
            </div>

            {/* Lựa chọn gói nâng cấp mới */}
            <div>
              <label className="text-xs font-bold text-slate-300 block mb-2">
                CHỌN PHƯƠNG THỨC NÂNG CẤP:
              </label>

              <div className="space-y-2">
                {/* Option 1: PRO Vĩnh viễn (Khuyên dùng) */}
                <label
                  onClick={() => setIsPermanent(true)}
                  className={`flex items-start gap-3 p-3.5 rounded-xl border cursor-pointer transition ${
                    isPermanent
                      ? 'bg-amber-500/10 border-amber-500/40 text-white'
                      : 'bg-slate-950/60 border-slate-800 text-slate-400 hover:border-slate-700'
                  }`}
                >
                  <input
                    type="radio"
                    name="upgrade_type"
                    checked={isPermanent}
                    onChange={() => setIsPermanent(true)}
                    className="mt-0.5 text-amber-500 focus:ring-amber-400"
                  />
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold text-amber-300 flex items-center gap-1">
                        <Crown className="w-3.5 h-3.5" /> Gói PRO VĨNH VIỄN (Perpetual)
                      </span>
                      <span className="px-2 py-0.2 rounded text-[10px] font-bold bg-amber-500/20 text-amber-400">
                        Khuyên dùng
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-400 mt-0.5">
                      Khách hàng sử dụng trọn đời, không bao giờ bị hết hạn hay khóa máy.
                    </p>
                  </div>
                </label>

                {/* Option 2: Gia hạn có thời hạn */}
                <label
                  onClick={() => setIsPermanent(false)}
                  className={`flex items-start gap-3 p-3.5 rounded-xl border cursor-pointer transition ${
                    !isPermanent
                      ? 'bg-purple-500/10 border-purple-500/40 text-white'
                      : 'bg-slate-950/60 border-slate-800 text-slate-400 hover:border-slate-700'
                  }`}
                >
                  <input
                    type="radio"
                    name="upgrade_type"
                    checked={!isPermanent}
                    onChange={() => setIsPermanent(false)}
                    className="mt-0.5 text-purple-500 focus:ring-purple-400"
                  />
                  <div className="flex-1">
                    <span className="text-xs font-bold text-purple-300">
                      Gói PRO Gia Hạn Theo Năm
                    </span>
                    {!isPermanent && (
                      <div className="mt-2 flex items-center gap-2">
                        <span className="text-xs text-slate-400">Thời hạn:</span>
                        <select
                          value={daysValid}
                          onChange={(e) => setDaysValid(Number(e.target.value))}
                          className="px-2 py-1 bg-slate-900 border border-slate-700 rounded-lg text-xs text-white"
                        >
                          <option value="365">1 năm (365 ngày)</option>
                          <option value="730">2 năm (730 ngày)</option>
                        </select>
                      </div>
                    )}
                  </div>
                </label>
              </div>
            </div>

            {/* Ghi chú lý do nâng cấp */}
            <div>
              <label className="text-xs font-semibold text-slate-400 block mb-1">
                Ghi chú nâng cấp (Lưu vào nhật ký hệ thống):
              </label>
              <input
                type="text"
                value={upgradeNotes}
                onChange={(e) => setUpgradeNotes(e.target.value)}
                placeholder="VD: Khách hàng mua bản quyền chính thức sau dùng thử"
                className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-xl text-xs text-white"
              />
            </div>

            {/* Buttons */}
            <div className="pt-3 border-t border-slate-800 flex justify-end gap-2.5">
              <button
                type="button"
                onClick={onClose}
                disabled={submitting}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl text-xs font-semibold transition"
              >
                Hủy bỏ
              </button>
              <button
                type="submit"
                disabled={submitting}
                className="flex items-center gap-1.5 px-5 py-2 bg-gradient-to-r from-amber-600 to-amber-500 hover:from-amber-500 hover:to-amber-400 text-white rounded-xl text-xs font-bold shadow-lg shadow-amber-600/30 transition"
              >
                {submitting ? (
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                ) : (
                  <>
                    <Sparkles className="w-4 h-4" />
                    <span>Xác Nhận Nâng Cấp & Ký Số Token v{license.version + 1}</span>
                  </>
                )}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  )
}

