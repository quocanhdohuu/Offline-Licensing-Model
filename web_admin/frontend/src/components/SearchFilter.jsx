import React from 'react'
import { Search, Filter, RotateCw, X } from 'lucide-react'

export default function SearchFilter({
  searchQuery,
  setSearchQuery,
  statusFilter,
  setStatusFilter,
  typeFilter,
  setTypeFilter,
  onRefresh,
  loading
}) {
  return (
    <div className="bg-slate-900/90 border border-slate-800 p-4 rounded-2xl shadow-lg mb-6 backdrop-blur-sm">
      <div className="flex flex-col md:flex-row gap-3 items-stretch md:items-center justify-between">
        {/* Ô tìm kiếm thông minh */}
        <div className="relative flex-1">
          <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
            <Search className="w-4 h-4" />
          </div>
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Tìm theo Mã DF, Số điện thoại, Tên khách hàng, Model PDA..."
            className="w-full pl-10 pr-9 py-2.5 bg-slate-950/80 border border-slate-700/80 rounded-xl text-white placeholder-slate-500 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery('')}
              className="absolute inset-y-0 right-0 pr-3 flex items-center text-slate-400 hover:text-white"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>

        {/* Bộ lọc Dropdowns */}
        <div className="flex items-center gap-2.5 flex-wrap">
          {/* Lọc theo Gói */}
          <div className="flex items-center gap-1.5 bg-slate-950/80 border border-slate-700/80 rounded-xl px-3 py-2">
            <Filter className="w-3.5 h-3.5 text-slate-400" />
            <select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
              className="bg-transparent text-xs text-slate-200 focus:outline-none cursor-pointer pr-1"
            >
              <option value="" className="bg-slate-900 text-slate-200">Tất cả gói</option>
              <option value="PRO" className="bg-slate-900 text-slate-200">Gói PRO</option>
              <option value="TRIAL" className="bg-slate-900 text-slate-200">Gói TRIAL</option>
            </select>
          </div>

          {/* Lọc theo Trạng thái */}
          <div className="flex items-center gap-1.5 bg-slate-950/80 border border-slate-700/80 rounded-xl px-3 py-2">
            <span className="text-xs text-slate-400">Trạng thái:</span>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="bg-transparent text-xs text-slate-200 focus:outline-none cursor-pointer pr-1 font-medium"
            >
              <option value="ACTIVE" className="bg-slate-900 text-emerald-400">Đang kích hoạt (ACTIVE)</option>
              <option value="ALL" className="bg-slate-900 text-slate-300">Tất cả lịch sử</option>
            </select>
          </div>

          {/* Nút Làm mới */}
          <button
            onClick={onRefresh}
            disabled={loading}
            title="Tải lại danh sách"
            className="p-2.5 bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white rounded-xl border border-slate-700 transition disabled:opacity-50"
          >
            <RotateCw className={`w-4 h-4 ${loading ? 'animate-spin text-emerald-400' : ''}`} />
          </button>
        </div>
      </div>
    </div>
  )
}

