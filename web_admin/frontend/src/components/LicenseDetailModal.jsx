import React, { useState, useEffect } from 'react'
import { createPortal } from 'react-dom'
import { X, Copy, Check, Download, QrCode, FileText, Smartphone, Calendar, User, ShieldCheck } from 'lucide-react'

export default function LicenseDetailModal({ license, onClose }) {
  const [copiedToken, setCopiedToken] = useState(false)
  const [copiedDf, setCopiedDf] = useState(false)

  // Khóa cuộn trang và lắng nghe phím ESC để đóng modal
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', handleKeyDown)
    document.body.style.overflow = 'hidden'

    return () => {
      document.removeEventListener('keydown', handleKeyDown)
      document.body.style.overflow = 'unset'
    }
  }, [onClose])

  if (!license) return null

  const cleanDf = license.df.replace(/-/g, '')

  const handleCopyToken = () => {
    navigator.clipboard.writeText(license.license_jwt)
    setCopiedToken(true)
    setTimeout(() => setCopiedToken(false), 2500)
  }

  const handleCopyDf = () => {
    navigator.clipboard.writeText(license.df)
    setCopiedDf(true)
    setTimeout(() => setCopiedDf(false), 2500)
  }

  // Tải trực tiếp file ảnh PNG từ chuỗi Base64
  const handleDownloadQr = () => {
    const link = document.createElement('a')
    link.href = license.qr_code_base64
    link.download = `qr_${cleanDf}.png`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  // Tải trực tiếp file text .lic từ chuỗi JWT
  const handleDownloadLic = () => {
    const blob = new Blob([license.license_jwt], { type: 'text/plain;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `license_${cleanDf}.lic`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  }

  const formatDate = (isoString) => {
    if (!isoString) return 'Vĩnh viễn (Perpetual)'
    try {
      const d = new Date(isoString)
      return d.toLocaleDateString('vi-VN', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      })
    } catch {
      return isoString
    }
  }

  return createPortal(
    <div
      onClick={onClose}
      className="fixed inset-0 top-0 left-0 right-0 bottom-0 z-[9999] w-screen h-screen min-h-screen bg-black/80 backdrop-blur-md flex items-center justify-center p-4 overflow-y-auto"
    >
      <div
        onClick={(e) => e.stopPropagation()}
        className="relative bg-slate-900 border border-slate-700 w-full max-w-3xl rounded-2xl shadow-2xl overflow-hidden my-auto animate-in fade-in zoom-in-95 duration-150"
      >
        {/* Modal Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-950/60">
          <div className="flex items-center gap-2.5">
            <div className="p-2 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 rounded-xl">
              <QrCode className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white">Chi Tiết Bản Quyền PDA & Cấp Lại</h3>
              <p className="text-xs text-slate-400">Hỗ trợ khôi phục khi Factory Reset hoặc cài lại ứng dụng</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Content */}
        <div className="p-6 grid grid-cols-1 md:grid-cols-12 gap-6">
          {/* Cột trái: Mã QR Code & Các nút Tải */}
          <div className="md:col-span-5 flex flex-col items-center justify-between bg-slate-950/70 p-5 rounded-2xl border border-slate-800 text-center">
            <div className="w-full">
              <span className="text-[11px] font-semibold text-emerald-400 uppercase tracking-wider block mb-3">
                MÃ QR KÍCH HOẠT (OFFLINE)
              </span>
              <div className="bg-white p-3 rounded-xl shadow-inner inline-block mx-auto border-2 border-emerald-500/30">
                <img
                  src={license.qr_code_base64}
                  alt="QR Code License"
                  className="w-48 h-48 object-contain"
                />
              </div>
              <p className="text-[11px] text-slate-400 mt-3 leading-relaxed">
                👉 Dùng camera app PDA quét mã QR trên màn hình hoặc tải ảnh về gửi cho khách.
              </p>
            </div>

            {/* Cụm nút tải file */}
            <div className="w-full space-y-2.5 mt-4 pt-4 border-t border-slate-800">
              <button
                type="button"
                onClick={handleDownloadQr}
                className="w-full flex items-center justify-center gap-2 py-2.5 px-3 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-xs font-semibold shadow-md transition active:scale-[0.98]"
              >
                <Download className="w-4 h-4" /> Tải ảnh QR Code (PNG)
              </button>
              <button
                type="button"
                onClick={handleDownloadLic}
                className="w-full flex items-center justify-center gap-2 py-2.5 px-3 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-xl text-xs font-medium border border-slate-700 transition active:scale-[0.98]"
              >
                <FileText className="w-4 h-4 text-blue-400" /> Tải file bản quyền (.lic)
              </button>
            </div>
          </div>

          {/* Cột phải: Thông tin chi tiết PDA & License */}
          <div className="md:col-span-7 space-y-4">
            {/* Thông tin Khách hàng */}
            <div className="bg-slate-950/50 p-4 rounded-xl border border-slate-800/80">
              <div className="flex items-center gap-1.5 text-xs font-bold text-slate-300 mb-2">
                <User className="w-4 h-4 text-emerald-400" /> THÔNG TIN KHÁCH HÀNG
              </div>
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div>
                  <span className="text-slate-500 block">Đơn vị / Tên:</span>
                  <span className="text-white font-semibold">{license.customer_name}</span>
                </div>
                <div>
                  <span className="text-slate-500 block">Số điện thoại:</span>
                  <span className="text-white font-semibold">{license.customer_phone || 'Chưa cập nhật'}</span>
                </div>
                {license.customer_email && (
                  <div className="col-span-2 mt-1">
                    <span className="text-slate-500 block">Email:</span>
                    <span className="text-slate-300">{license.customer_email}</span>
                  </div>
                )}
              </div>
            </div>

            {/* Thông tin Thiết bị PDA */}
            <div className="bg-slate-950/50 p-4 rounded-xl border border-slate-800/80">
              <div className="flex items-center gap-1.5 text-xs font-bold text-slate-300 mb-2">
                <Smartphone className="w-4 h-4 text-blue-400" /> ĐỊNH DANH PHẦN CỨNG PDA
              </div>
              <div className="space-y-2 text-xs">
                <div className="flex items-center justify-between">
                  <span className="text-slate-500">Model máy:</span>
                  <span className="text-white font-bold">{license.model}</span>
                </div>
                <div className="flex items-center justify-between bg-slate-900/90 p-2 rounded-lg border border-slate-800">
                  <span className="text-slate-400 text-[11px]">Mã DF:</span>
                  <div className="flex items-center gap-2">
                    <code className="text-emerald-400 font-mono font-bold tracking-wider">{license.df}</code>
                    <button
                      onClick={handleCopyDf}
                      title="Sao chép mã DF"
                      className="p-1 hover:bg-slate-800 rounded text-slate-400 hover:text-white transition"
                    >
                      {copiedDf ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                    </button>
                  </div>
                </div>
              </div>
            </div>

            {/* Trạng thái Gói & Hạn dùng */}
            <div className="bg-slate-950/50 p-4 rounded-xl border border-slate-800/80">
              <div className="flex items-center gap-1.5 text-xs font-bold text-slate-300 mb-2">
                <Calendar className="w-4 h-4 text-purple-400" /> GÓI & THỜI HẠN BẢN QUYỀN
              </div>
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div>
                  <span className="text-slate-500 block">Gói bản quyền:</span>
                  <span className="inline-flex items-center gap-1 px-2 py-0.5 mt-0.5 rounded text-[11px] font-bold bg-purple-500/20 text-purple-300 border border-purple-500/30">
                    <ShieldCheck className="w-3 h-3" />
                    {license.is_permanent ? 'PRO VĨNH VIỄN' : license.license_type}
                  </span>
                </div>
                <div>
                  <span className="text-slate-500 block">Phiên bản license:</span>
                  <span className="text-slate-200 font-semibold">v{license.version}</span>
                </div>
                <div>
                  <span className="text-slate-500 block">Ngày cấp:</span>
                  <span className="text-slate-300">{formatDate(license.issued_at)}</span>
                </div>
                <div>
                  <span className="text-slate-500 block">Ngày hết hạn:</span>
                  <span className={`font-semibold ${license.is_permanent ? 'text-emerald-400' : 'text-amber-400'}`}>
                    {license.is_permanent ? 'VĨNH VIỄN' : formatDate(license.expires_at)}
                  </span>
                </div>
              </div>
            </div>

            {/* Sao chép nhanh Token JWT */}
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-[11px] font-semibold text-slate-400">CHUỖI TOKEN LICENSE (JWT RFC 8037):</span>
                <button
                  onClick={handleCopyToken}
                  className="flex items-center gap-1 text-xs font-bold text-emerald-400 hover:text-emerald-300 transition"
                >
                  {copiedToken ? (
                    <>
                      <Check className="w-3.5 h-3.5" /> Đã sao chép!
                    </>
                  ) : (
                    <>
                      <Copy className="w-3.5 h-3.5" /> Sao chép gửi khách
                    </>
                  )}
                </button>
              </div>
              <textarea
                readOnly
                value={license.license_jwt}
                rows={2}
                className="w-full p-2.5 bg-slate-950 border border-slate-800 rounded-xl font-mono text-[11px] text-slate-400 focus:outline-none resize-none"
              />
            </div>
          </div>
        </div>

        {/* Modal Footer */}
        <div className="px-6 py-3.5 bg-slate-950/80 border-t border-slate-800 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-xl text-xs font-semibold transition"
          >
            Đóng cửa sổ
          </button>
        </div>
      </div>
    </div>,
    document.body
  )
}
