import React from 'react'
import { AuthProvider, useAuth } from './contexts/AuthContext'
import LoginPage from './pages/LoginPage'
import Navbar from './components/Navbar'
import { Shield, UserCheck, Key, RefreshCw, Search, CheckCircle } from 'lucide-react'

function DashboardShell() {
  const { user, isAdmin, isSale } = useAuth()

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      <Navbar />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Banner thông báo trạng thái phân quyền */}
        <div className="mb-8 p-6 rounded-2xl bg-gradient-to-r from-slate-900 via-slate-800 to-slate-900 border border-slate-700/80 shadow-xl">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <span className="text-xl font-bold text-white">Xin chào, {user?.full_name}!</span>
                <span className="inline-flex items-center gap-1 text-xs px-2.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  <CheckCircle className="w-3 h-3" /> Đã kết nối API
                </span>
              </div>
              <p className="text-sm text-slate-400">
                {isAdmin
                  ? 'Bạn đang truy cập với quyền QUẢN TRỊ VIÊN: Có thể sinh license mới, nâng cấp gói và tra cứu toàn bộ thiết bị.'
                  : 'Bạn đang truy cập với quyền KINH DOANH (SALE): Tra cứu license và lấy lại mã QR cấp lại cho khách hàng khi bị Factory Reset.'}
              </p>
            </div>

            <div className="flex items-center gap-2">
              {isAdmin && (
                <span className="px-3.5 py-1.5 rounded-xl text-xs font-semibold bg-indigo-600/20 text-indigo-300 border border-indigo-500/30 flex items-center gap-1.5">
                  <Key className="w-3.5 h-3.5" /> Chế độ Quản trị (Admin Mode)
                </span>
              )}
              {isSale && (
                <span className="px-3.5 py-1.5 rounded-xl text-xs font-semibold bg-emerald-600/20 text-emerald-300 border border-emerald-500/30 flex items-center gap-1.5">
                  <UserCheck className="w-3.5 h-3.5" /> Chế độ Kinh doanh (Sale Mode)
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Khung giới thiệu sẵn sàng cho Bước 5 & Bước 6 */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800">
            <div className="w-10 h-10 rounded-xl bg-blue-500/10 text-blue-400 flex items-center justify-center mb-4">
              <Search className="w-5 h-5" />
            </div>
            <h3 className="text-base font-bold text-white mb-1">Bước 5: Tra cứu & Cấp lại</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Thanh tìm kiếm theo DF/SĐT, bảng danh sách thiết bị PDA và Modal xem QR Code phóng to để gửi lại khách hàng.
            </p>
          </div>

          <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800">
            <div className="w-10 h-10 rounded-xl bg-indigo-500/10 text-indigo-400 flex items-center justify-center mb-4">
              <Key className="w-5 h-5" />
            </div>
            <h3 className="text-base font-bold text-white mb-1">Bước 6: Sinh Key Mới (Admin)</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Modal tạo license mới từ mã DF Crockford 16 ký tự, tự động ký Ed25519 và sinh ảnh QR Code tức thì.
            </p>
          </div>

          <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800">
            <div className="w-10 h-10 rounded-xl bg-emerald-500/10 text-emerald-400 flex items-center justify-center mb-4">
              <RefreshCw className="w-5 h-5" />
            </div>
            <h3 className="text-base font-bold text-white mb-1">Bước 6: Nâng Cấp Gói (Admin)</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Chuyển đổi từ gói Dùng thử (Trial) sang gói PRO Vĩnh viễn cho cùng mã DF, tăng version và lưu lịch sử.
            </p>
          </div>
        </div>
      </main>
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
