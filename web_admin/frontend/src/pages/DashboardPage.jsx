import React, { useState, useEffect, useCallback } from 'react'
import { licenseApi } from '../api/licenseApi'
import { useAuth } from '../contexts/AuthContext'
import SearchFilter from '../components/SearchFilter'
import LicenseTable from '../components/LicenseTable'
import LicenseDetailModal from '../components/LicenseDetailModal'
import { Plus, Smartphone, ShieldCheck, HelpCircle } from 'lucide-react'

export default function DashboardPage({ onOpenCreate, onOpenUpgrade }) {
  const { isAdmin, isSale, user } = useAuth()
  const [licenses, setLicenses] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Bộ lọc tìm kiếm
  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState('ACTIVE')
  const [typeFilter, setTypeFilter] = useState('')

  // Modal Chi tiết & Cấp lại
  const [selectedLicense, setSelectedLicense] = useState(null)

  const fetchLicenses = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await licenseApi.getLicenses({
        q: searchQuery.trim() || undefined,
        status: statusFilter || undefined,
        license_type: typeFilter || undefined,
      })
      setLicenses(data)
    } catch (err) {
      console.error('Lỗi khi tải danh sách license:', err)
      setError('Không thể tải dữ liệu từ máy chủ. Vui lòng thử lại!')
    } finally {
      setLoading(false)
    }
  }, [searchQuery, statusFilter, typeFilter])

  useEffect(() => {
    const timer = setTimeout(() => {
      fetchLicenses()
    }, 250) // Debounce 250ms cho ô tìm kiếm
    return () => clearTimeout(timer)
  }, [fetchLicenses])

  return (
    <div className="space-y-6">
      {/* Thanh tiêu đề & Nút Tạo mới (Chỉ dành cho Admin) */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
            <Smartphone className="w-6 h-6 text-emerald-400" />
            Danh Sách Thiết Bị PDA & Bản Quyền
          </h1>
          <p className="text-xs text-slate-400 mt-0.5">
            {isSale
              ? 'Tra cứu mã DF hoặc số điện thoại của khách hàng để lấy lại mã QR khi máy bị reset.'
              : 'Quản lý toàn bộ vòng đời bản quyền, tạo license mới và nâng cấp gói cho các thiết bị PDA.'}
          </p>
        </div>

        {/* Nút Cấp License Mới (CHỈ ADMIN THẤY) */}
        {isAdmin && onOpenCreate && (
          <button
            onClick={onOpenCreate}
            className="inline-flex items-center gap-2 px-4 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-xs font-bold shadow-lg shadow-emerald-600/30 transition transform hover:-translate-y-0.5 active:translate-y-0"
          >
            <Plus className="w-4 h-4" />
            <span>Cấp License Mới</span>
          </button>
        )}
      </div>

      {/* Thông báo hướng dẫn nghiệp vụ dành riêng cho Sale */}
      {isSale && (
        <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-2xl p-4 flex items-start gap-3">
          <HelpCircle className="w-5 h-5 text-emerald-400 flex-shrink-0 mt-0.5" />
          <div className="text-xs text-slate-300 leading-relaxed">
            <span className="font-bold text-emerald-300">Hướng dẫn dành cho Nhân viên Kinh doanh: </span>
            Khi khách hàng bị Factory Reset máy hoặc gỡ cài đặt app, hãy gõ <strong>Số điện thoại</strong> hoặc <strong>Mã DF</strong> của khách vào ô tìm kiếm bên dưới &rarr; Bấm <strong>[Xem & Cấp lại]</strong> &rarr; Tải ảnh QR hoặc Copy Token gửi lại cho khách. Nếu có khách hàng mới, hãy gửi mã DF cho Quản trị viên (Admin) để tạo key mới.
          </div>
        </div>
      )}

      {/* Bộ lọc tìm kiếm thời gian thực */}
      <SearchFilter
        searchQuery={searchQuery}
        setSearchQuery={setSearchQuery}
        statusFilter={statusFilter}
        setStatusFilter={setStatusFilter}
        typeFilter={typeFilter}
        setTypeFilter={setTypeFilter}
        onRefresh={fetchLicenses}
        loading={loading}
      />

      {/* Bảng danh sách thiết bị */}
      {error ? (
        <div className="p-6 bg-rose-500/10 border border-rose-500/30 rounded-2xl text-center text-rose-300 text-sm">
          {error}
        </div>
      ) : (
        <LicenseTable
          licenses={licenses}
          loading={loading}
          onSelectLicense={(lic) => setSelectedLicense(lic)}
          onOpenUpgrade={onOpenUpgrade}
        />
      )}

      {/* Modal Xem & Cấp lại License */}
      {selectedLicense && (
        <LicenseDetailModal
          license={selectedLicense}
          onClose={() => setSelectedLicense(null)}
        />
      )}
    </div>
  )
}

