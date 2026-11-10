import React, { useState, useEffect } from 'react'
import { createPortal } from 'react-dom'
import { X, Key, ShieldCheck, Check, AlertCircle, Smartphone, User, Calendar, Download, Copy, Sparkles } from 'lucide-react'
import { licenseApi } from '../api/licenseApi'

const CROCKFORD_CHARS = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"

export default function CreateLicenseModal({ onClose, onSuccess }) {
  // Form fields
  const [rawDf, setRawDf] = useState('')
  const [model, setModel] = useState('Newland NLS-MT90')
  const [customModel, setCustomModel] = useState('')
  const [customerName, setCustomerName] = useState('')
  const [customerPhone, setCustomerPhone] = useState('')
  const [customerEmail, setCustomerEmail] = useState('')
  const [notes, setNotes] = useState('')
  const [licenseType, setLicenseType] = useState('PRO')
  const [daysValid, setDaysValid] = useState(365)
  const [isPermanent, setIsPermanent] = useState(false)
  const [features, setFeatures] = useState(['SCANNER', 'INVENTORY', 'DIRECT_PRINT'])

  // Status
  const [dfError, setDfError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [generalError, setGeneralError] = useState('')
  const [createdResult, setCreatedResult] = useState(null)
  const [copiedToken, setCopiedToken] = useState(false)

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

  // Xử lý và chuẩn hóa mã DF thời gian thực theo chuẩn Crockford Base32
  const handleDfChange = (e) => {
    let input = e.target.value.toUpperCase().replace(/[^0-9A-Z]/g, '')
    
    // Kiểm tra ký tự cấm (I, L, O, U)
    let invalidChar = null
    for (const ch of input) {
      if (!CROCKFORD_CHARS.includes(ch)) {
        invalidChar = ch
        break
      }
    }

    if (invalidChar) {
      setDfError(`Ký tự '${invalidChar}' không thuộc bảng Crockford Base32 (không dùng I, L, O, U)!`)
    } else {
      setDfError('')
    }

    // Giới hạn tối đa 16 ký tự
    if (input.length > 16) {
      input = input.slice(0, 16)
    }

    // Tự động chèn dấu gạch nối XXXX-XXXX-XXXX-XXXX
    let formatted = ''
    for (let i = 0; i < input.length; i++) {
      if (i > 0 && i % 4 === 0) formatted += '-'
      formatted += input[i]
    }

    setRawDf(formatted)
  }

  const isDfValid = rawDf.replace(/-/g, '').length === 16 && !dfError

  const handleFeatureToggle = (feat) => {
    if (features.includes(feat)) {
      setFeatures(features.filter((f) => f !== feat))
    } else {
      setFeatures([...features, feat])
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!isDfValid) {
      setDfError('Vui lòng nhập đúng 16 ký tự Crockford Base32 của máy PDA!')
      return
    }
    if (!customerName.trim()) {
      setGeneralError('Vui lòng nhập tên khách hàng hoặc đơn vị!')
      return
    }

    const finalModel = model === 'OTHER' ? customModel.trim() || 'PDA Android' : model

    setSubmitting(true)
    setGeneralError('')
    try {
      const payload = {
        df: rawDf,
        model: finalModel,
        customer_name: customerName.trim(),
        customer_phone: customerPhone.trim() || null,
        customer_email: customerEmail.trim() || null,
        notes: notes.trim() || null,
        license_type: isPermanent ? 'PRO' : licenseType,
        days_valid: isPermanent ? 0 : Number(daysValid),
        is_permanent: isPermanent,
        features: features
      }

      const res = await licenseApi.createLicense(payload)
      setCreatedResult(res)
      if (onSuccess) onSuccess()
    } catch (err) {
      console.error(err)
      setGeneralError(err.response?.data?.detail || 'Lỗi khi khởi tạo license. Vui lòng kiểm tra lại!')
    } finally {
      setSubmitting(false)
    }
  }

  // Tải trực tiếp file QR PNG từ chuỗi base64 của license vừa tạo
  const handleDownloadQr = () => {
    if (!createdResult) return
    const cleanDf = createdResult.df.replace(/-/g, '')
    const link = document.createElement('a')
    link.href = createdResult.qr_code_base64
    link.download = `qr_${cleanDf}.png`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  const handleCopyToken = () => {
    if (!createdResult) return
    navigator.clipboard.writeText(createdResult.license_jwt)
    setCopiedToken(true)
    setTimeout(() => setCopiedToken(false), 2500)
  }

  return createPortal(
    <div
      onClick={onClose}
      className="fixed inset-0 top-0 left-0 right-0 bottom-0 z-[9999] w-screen h-screen min-h-screen bg-black/80 backdrop-blur-md flex items-center justify-center p-4 overflow-y-auto"
    >
      <div
        onClick={(e) => e.stopPropagation()}
        className="relative bg-slate-900 border border-slate-700 w-full max-w-2xl rounded-2xl shadow-2xl overflow-hidden my-auto animate-in fade-in zoom-in-95 duration-150"
      >
        {/* Modal Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-950/70">
          <div className="flex items-center gap-2.5">
            <div className="p-2 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 rounded-xl">
              <Key className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white">Khởi Tạo & Ký Số License Mới (Admin)</h3>
              <p className="text-xs text-slate-400">Sinh chữ ký Ed25519 cho thiết bị PDA theo chuẩn RFC 8037</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Màn hình thông báo kết quả sau khi tạo thành công */}
        {createdResult ? (
          <div className="p-6 text-center space-y-5">
            <div className="w-14 h-14 bg-emerald-500/20 border border-emerald-500/30 text-emerald-400 rounded-2xl flex items-center justify-center mx-auto shadow-lg shadow-emerald-500/20">
              <ShieldCheck className="w-8 h-8" />
            </div>
            <div>
              <h4 className="text-lg font-bold text-white">Khởi Tạo License Thành Công!</h4>
              <p className="text-xs text-slate-400 mt-1">
                Đã ký số bằng Private Key Ed25519 cho thiết bị: <strong className="text-emerald-400">{createdResult.model}</strong> ({createdResult.df})
              </p>
            </div>

            <div className="bg-slate-950 p-4 rounded-2xl border border-slate-800 inline-block mx-auto">
              <div className="bg-white p-2.5 rounded-xl inline-block border-2 border-emerald-500/40">
                <img
                  src={createdResult.qr_code_base64}
                  alt="QR Code vừa tạo"
                  className="w-44 h-44 object-contain"
                />
              </div>
              <div className="text-[11px] text-slate-400 mt-2">
                Gói: <span className="font-bold text-emerald-400">{createdResult.license_type}</span> &bull; Version: <strong>v{createdResult.version}</strong>
              </div>
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
                {copiedToken ? 'Đã sao chép token' : 'Sao chép chuỗi Token'}
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
          /* Form nhập liệu cấp License */
          <form onSubmit={handleSubmit} className="p-6 space-y-4">
            {generalError && (
              <div className="p-3 bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs rounded-xl flex items-center gap-2">
                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                <span>{generalError}</span>
              </div>
            )}

            {/* Ô nhập DF thông minh */}
            <div>
              <div className="flex justify-between items-center mb-1.5">
                <label className="text-xs font-bold text-slate-300 flex items-center gap-1.5">
                  <Smartphone className="w-3.5 h-3.5 text-emerald-400" />
                  MÃ ĐỊNH DANH PHẦN CỨNG (DF 16 KÝ TỰ CROCKFORD) <span className="text-rose-400">*</span>
                </label>
                <span className="text-[11px] text-slate-400">
                  {rawDf.replace(/-/g, '').length}/16 ký tự
                </span>
              </div>
              <div className="relative">
                <input
                  type="text"
                  value={rawDf}
                  onChange={handleDfChange}
                  placeholder="VD: MN73-006Q-5G96-S3E8"
                  className="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-700 rounded-xl text-emerald-400 font-mono text-sm tracking-wider focus:outline-none focus:ring-2 focus:ring-emerald-500 uppercase"
                />
                {isDfValid && (
                  <div className="absolute inset-y-0 right-0 pr-3 flex items-center text-emerald-400">
                    <Check className="w-4 h-4" />
                  </div>
                )}
              </div>
              {dfError ? (
                <p className="text-[11px] text-rose-400 mt-1">{dfError}</p>
              ) : (
                <p className="text-[11px] text-slate-500 mt-1">
                  Mã do App Android hiển thị khi mở máy (Chấp nhận 0-9 và A-Z, không có I, L, O, U).
                </p>
              )}
            </div>

            {/* Chọn Model máy */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1.5">
                  Model Thiết Bị PDA <span className="text-rose-400">*</span>
                </label>
                <select
                  value={model}
                  onChange={(e) => setModel(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-xl text-xs text-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
                >
                  <option value="Newland NLS-MT90">Newland NLS-MT90</option>
                  <option value="Zebra MC3300x">Zebra MC3300x</option>
                  <option value="iMin Swift 2">iMin Swift 2</option>
                  <option value="Honeywell ScanPal EDA51">Honeywell ScanPal EDA51</option>
                  <option value="Honeywell CT40">Honeywell CT40</option>
                  <option value="OTHER">Model khác...</option>
                </select>
              </div>

              {model === 'OTHER' ? (
                <div>
                  <label className="text-xs font-semibold text-slate-300 block mb-1.5">
                    Nhập tên model máy khác
                  </label>
                  <input
                    type="text"
                    value={customModel}
                    onChange={(e) => setCustomModel(e.target.value)}
                    placeholder="VD: Point Mobile PM85"
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-xl text-xs text-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
                  />
                </div>
              ) : (
                <div>
                  <label className="text-xs font-semibold text-slate-300 block mb-1.5">
                    Số điện thoại liên hệ
                  </label>
                  <input
                    type="text"
                    value={customerPhone}
                    onChange={(e) => setCustomerPhone(e.target.value)}
                    placeholder="VD: 0912345678"
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-xl text-xs text-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
                  />
                </div>
              )}
            </div>

            {/* Thông tin Khách hàng */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1.5">
                  Tên Khách Hàng / Đơn Vị <span className="text-rose-400">*</span>
                </label>
                <input
                  type="text"
                  value={customerName}
                  onChange={(e) => setCustomerName(e.target.value)}
                  placeholder="VD: Công ty Kho Vận Á Châu"
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-xl text-xs text-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1.5">
                  Email nhận License (nếu có)
                </label>
                <input
                  type="email"
                  value={customerEmail}
                  onChange={(e) => setCustomerEmail(e.target.value)}
                  placeholder="contact@achau.vn"
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-xl text-xs text-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
                />
              </div>
            </div>

            {/* Chọn Gói & Hạn dùng */}
            <div className="p-3.5 bg-slate-950/80 rounded-xl border border-slate-800 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-300 flex items-center gap-1.5">
                  <Calendar className="w-3.5 h-3.5 text-purple-400" /> GÓI BẢN QUYỀN & THỜI HẠN
                </span>

                {/* Checkbox Vĩnh viễn */}
                <label className="flex items-center gap-2 cursor-pointer text-xs font-semibold text-amber-400">
                  <input
                    type="checkbox"
                    checked={isPermanent}
                    onChange={(e) => setIsPermanent(e.target.checked)}
                    className="w-4 h-4 rounded text-amber-500 focus:ring-amber-400 bg-slate-900 border-slate-700"
                  />
                  <span>Bản quyền Vĩnh viễn (Perpetual)</span>
                </label>
              </div>

              {!isPermanent && (
                <div className="grid grid-cols-2 gap-3 pt-1">
                  <div>
                    <label className="text-[11px] text-slate-400 block mb-1">Loại gói:</label>
                    <select
                      value={licenseType}
                      onChange={(e) => {
                        const val = e.target.value
                        setLicenseType(val)
                        if (val === 'TRIAL') setDaysValid(15)
                        if (val === 'PRO') setDaysValid(365)
                      }}
                      className="w-full px-2.5 py-1.5 bg-slate-900 border border-slate-700 rounded-lg text-xs text-white"
                    >
                      <option value="PRO">Gói PRO (Có phí)</option>
                      <option value="TRIAL">Gói TRIAL (Dùng thử)</option>
                    </select>
                  </div>

                  <div>
                    <label className="text-[11px] text-slate-400 block mb-1">Thời hạn sử dụng:</label>
                    <select
                      value={daysValid}
                      onChange={(e) => setDaysValid(Number(e.target.value))}
                      className="w-full px-2.5 py-1.5 bg-slate-900 border border-slate-700 rounded-lg text-xs text-white"
                    >
                      {licenseType === 'TRIAL' ? (
                        <>
                          <option value="15">15 ngày dùng thử</option>
                          <option value="30">30 ngày dùng thử</option>
                        </>
                      ) : (
                        <>
                          <option value="365">1 năm (365 ngày)</option>
                          <option value="730">2 năm (730 ngày)</option>
                          <option value="1095">3 năm (1095 ngày)</option>
                        </>
                      )}
                    </select>
                  </div>
                </div>
              )}
            </div>

            {/* Tính năng mở khóa */}
            <div>
              <label className="text-xs font-semibold text-slate-400 block mb-1.5">
                Tính Năng Mở Khóa Trên PDA:
              </label>
              <div className="flex flex-wrap gap-2">
                {[
                  { key: 'SCANNER', label: 'Quét Barcode/QR' },
                  { key: 'INVENTORY', label: 'Kiểm Kê Kho Bãi' },
                  { key: 'DIRECT_PRINT', label: 'In Tem Nhãn Trực Tiếp' },
                ].map((f) => (
                  <button
                    key={f.key}
                    type="button"
                    onClick={() => handleFeatureToggle(f.key)}
                    className={`px-2.5 py-1 rounded-lg text-xs font-medium border transition ${
                      features.includes(f.key)
                        ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
                        : 'bg-slate-950 text-slate-500 border-slate-800'
                    }`}
                  >
                    {features.includes(f.key) ? '✓ ' : '+ '} {f.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Ghi chú */}
            <div>
              <label className="text-xs font-semibold text-slate-400 block mb-1">
                Ghi chú thêm (Tùy chọn)
              </label>
              <input
                type="text"
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="VD: Cấp theo hợp đồng số HD-2026/THH"
                className="w-full px-3 py-1.5 bg-slate-950 border border-slate-700 rounded-xl text-xs text-white"
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
                disabled={submitting || !isDfValid}
                className="flex items-center gap-1.5 px-5 py-2 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white rounded-xl text-xs font-bold shadow-lg shadow-emerald-600/30 transition"
              >
                {submitting ? (
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                ) : (
                  <>
                    <Sparkles className="w-4 h-4" />
                    <span>Sinh License & Ký Số Ed25519</span>
                  </>
                )}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>,
    document.body
  )
}
