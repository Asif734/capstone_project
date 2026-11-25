import React from 'react';
import {
  ShieldCheck,
  RefreshCw,
  LogOut,
  MessageSquare,
  AlertOctagon,
  Activity,
  Layers,
} from 'lucide-react';

const AdminHeader = ({
  loading,
  criticalNewCount = 0,
  onRefresh,
  onLogout,
  onBackToChat,
  activeTab,
  setActiveTab,
}) => {
  return (
    <header className="rounded-2xl border border-purple-500/20 bg-slate-900/80 p-5 shadow-2xl backdrop-blur-md">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        {/* Brand & Subtitle */}
        <div className="flex items-center space-x-3.5">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-tr from-purple-600 via-pink-600 to-amber-500 shadow-lg shadow-purple-500/25">
            <ShieldCheck className="h-6 w-6 text-white" />
          </div>
          <div>
            <div className="flex items-center space-x-2.5">
              <h1 className="text-xl sm:text-2xl font-black tracking-tight text-white">
                BUP Admin Console
              </h1>
              <span className="flex items-center space-x-1.5 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2.5 py-0.5 text-[11px] font-semibold text-emerald-300">
                <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
                <span>Operational</span>
              </span>
            </div>
            <p className="text-xs text-purple-200/70 font-medium">
              Student Well-being Triage, FERPA Access Audit, and Academic Administration
            </p>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex flex-wrap items-center gap-2.5">
          {/* Critical Alert Warning Pill */}
          {criticalNewCount > 0 && (
            <button
              onClick={() => setActiveTab('alerts')}
              className="flex items-center space-x-2 rounded-xl border border-red-500/50 bg-red-500/20 px-3.5 py-2 text-xs font-bold text-red-200 shadow-lg shadow-red-500/20 transition-all hover:bg-red-500/30 animate-pulse cursor-pointer"
              title="Click to view new critical alerts"
            >
              <AlertOctagon className="h-4 w-4 text-red-300" />
              <span>{criticalNewCount} Urgent Alert{criticalNewCount > 1 ? 's' : ''}</span>
            </button>
          )}

          {/* Quick Switch to Chat */}
          {onBackToChat && (
            <button
              type="button"
              onClick={onBackToChat}
              className="flex items-center space-x-2 rounded-xl border border-purple-500/30 bg-purple-950/40 px-3.5 py-2 text-xs font-semibold text-purple-200 shadow-sm transition-all hover:border-purple-400/50 hover:bg-purple-900/50 hover:text-white cursor-pointer"
            >
              <MessageSquare className="h-4 w-4 text-pink-400" />
              <span>Student Chat</span>
            </button>
          )}

          {/* Refresh Dashboard */}
          <button
            type="button"
            onClick={onRefresh}
            disabled={loading}
            className="flex items-center space-x-2 rounded-xl border border-slate-700 bg-slate-800/80 px-3.5 py-2 text-xs font-semibold text-slate-200 shadow-sm transition-all hover:border-purple-500/40 hover:bg-purple-950/40 hover:text-white disabled:opacity-60 cursor-pointer"
          >
            <RefreshCw className={`h-4 w-4 text-purple-300 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>

          {/* Admin Logout */}
          <button
            type="button"
            onClick={onLogout}
            disabled={loading}
            className="flex items-center space-x-2 rounded-xl border border-red-500/30 bg-red-500/10 px-3.5 py-2 text-xs font-semibold text-red-200 shadow-sm transition-all hover:border-red-500/50 hover:bg-red-500/20 hover:text-white disabled:opacity-60 cursor-pointer"
          >
            <LogOut className="h-4 w-4" />
            <span>Logout</span>
          </button>
        </div>
      </div>
    </header>
  );
};

export default AdminHeader;
