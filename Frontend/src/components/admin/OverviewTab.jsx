import React from 'react';
import {
  AlertOctagon,
  Activity,
  Users,
  ShieldCheck,
  CheckCircle2,
  Clock,
  ArrowRight,
  UserPlus,
  ClipboardList,
  FileText,
  AlertTriangle,
  ChevronRight,
  TrendingUp,
} from 'lucide-react';

const OverviewTab = ({
  summary = {},
  students = [],
  alerts = [],
  auditLogsCount = 0,
  documentsCount = 0,
  criticalNewCount = 0,
  setActiveTab,
  onSelectAlert,
}) => {
  const totalAlerts = summary?.total_alerts || alerts.length || 0;
  const newAlerts = summary?.new_alerts ?? alerts.filter((a) => a.status === 'new').length;
  const criticalAlerts = summary?.critical_alerts ?? alerts.filter((a) => a.severity === 'critical').length;
  const highAlerts = summary?.high_alerts ?? alerts.filter((a) => a.severity === 'high').length;
  const moderateAlerts = summary?.moderate_alerts ?? alerts.filter((a) => a.severity === 'moderate').length;
  const resolvedCount = totalAlerts - newAlerts;
  const resolutionRate = totalAlerts > 0 ? Math.round((resolvedCount / totalAlerts) * 100) : 100;

  // Recent unresolved alerts needing attention
  const priorityAlerts = alerts
    .filter((a) => a.status === 'new' || a.severity === 'critical' || a.severity === 'high')
    .slice(0, 4);

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* 1. Hero KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        {/* Critical Alerts */}
        <div className="rounded-2xl border border-red-500/30 bg-gradient-to-br from-red-950/50 via-slate-900/60 to-slate-900/80 p-4 shadow-lg backdrop-blur-md relative overflow-hidden group">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[11px] font-bold uppercase tracking-wider text-red-300">
              Urgent Critical
            </span>
            <div className="p-2 rounded-xl bg-red-500/20 text-red-300 border border-red-500/30">
              <AlertOctagon className="w-4 h-4 animate-pulse" />
            </div>
          </div>
          <div className="text-3xl font-black text-white tracking-tight">{criticalNewCount}</div>
          <div className="mt-1 flex items-center text-xs text-red-200/70 font-medium">
            <span>{criticalAlerts} Total Critical in System</span>
          </div>
          <div className="absolute -bottom-6 -right-6 w-20 h-20 rounded-full bg-red-500/10 blur-xl group-hover:scale-150 transition-transform" />
        </div>

        {/* Total Risk Alerts */}
        <div className="rounded-2xl border border-amber-500/30 bg-gradient-to-br from-amber-950/40 via-slate-900/60 to-slate-900/80 p-4 shadow-lg backdrop-blur-md relative overflow-hidden group">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[11px] font-bold uppercase tracking-wider text-amber-300">
              Total Risk Alerts
            </span>
            <div className="p-2 rounded-xl bg-amber-500/20 text-amber-300 border border-amber-500/30">
              <Activity className="w-4 h-4" />
            </div>
          </div>
          <div className="text-3xl font-black text-white tracking-tight">{totalAlerts}</div>
          <div className="mt-1 flex items-center text-xs text-amber-200/70 font-medium">
            <span>{newAlerts} Pending Review</span>
          </div>
          <div className="absolute -bottom-6 -right-6 w-20 h-20 rounded-full bg-amber-500/10 blur-xl group-hover:scale-150 transition-transform" />
        </div>

        {/* Authorized Students */}
        <div className="rounded-2xl border border-cyan-500/30 bg-gradient-to-br from-cyan-950/40 via-slate-900/60 to-slate-900/80 p-4 shadow-lg backdrop-blur-md relative overflow-hidden group">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[11px] font-bold uppercase tracking-wider text-cyan-300">
              Enrolled Students
            </span>
            <div className="p-2 rounded-xl bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
              <Users className="w-4 h-4" />
            </div>
          </div>
          <div className="text-3xl font-black text-white tracking-tight">{students.length}</div>
          <div className="mt-1 flex items-center text-xs text-cyan-200/70 font-medium">
            <span>Monitored Profiles</span>
          </div>
          <div className="absolute -bottom-6 -right-6 w-20 h-20 rounded-full bg-cyan-500/10 blur-xl group-hover:scale-150 transition-transform" />
        </div>

        {/* FERPA Audit Logs */}
        <div className="rounded-2xl border border-purple-500/30 bg-gradient-to-br from-purple-950/40 via-slate-900/60 to-slate-900/80 p-4 shadow-lg backdrop-blur-md relative overflow-hidden group">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[11px] font-bold uppercase tracking-wider text-purple-300">
              FERPA Audits
            </span>
            <div className="p-2 rounded-xl bg-purple-500/20 text-purple-300 border border-purple-500/30">
              <ShieldCheck className="w-4 h-4" />
            </div>
          </div>
          <div className="text-3xl font-black text-white tracking-tight">{auditLogsCount || 'Active'}</div>
          <div className="mt-1 flex items-center text-xs text-purple-200/70 font-medium">
            <span>Access Audit Trail</span>
          </div>
          <div className="absolute -bottom-6 -right-6 w-20 h-20 rounded-full bg-purple-500/10 blur-xl group-hover:scale-150 transition-transform" />
        </div>

        {/* Resolution Rate */}
        <div className="rounded-2xl border border-emerald-500/30 bg-gradient-to-br from-emerald-950/40 via-slate-900/60 to-slate-900/80 p-4 shadow-lg backdrop-blur-md relative overflow-hidden group">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[11px] font-bold uppercase tracking-wider text-emerald-300">
              Resolution Rate
            </span>
            <div className="p-2 rounded-xl bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
              <CheckCircle2 className="w-4 h-4" />
            </div>
          </div>
          <div className="text-3xl font-black text-white tracking-tight">{resolutionRate}%</div>
          <div className="mt-1 flex items-center text-xs text-emerald-200/70 font-medium">
            <span>{resolvedCount} Case{resolvedCount !== 1 ? 's' : ''} Handled</span>
          </div>
          <div className="absolute -bottom-6 -right-6 w-20 h-20 rounded-full bg-emerald-500/10 blur-xl group-hover:scale-150 transition-transform" />
        </div>
      </div>

      {/* 2. Middle Section: Severity Breakdown & Quick Launch Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Severity Distribution */}
        <div className="rounded-2xl border border-slate-700/80 bg-slate-900/70 p-5 shadow-xl backdrop-blur-md lg:col-span-1">
          <h2 className="text-sm font-bold uppercase tracking-wider text-purple-200 flex items-center space-x-2 mb-4">
            <TrendingUp className="w-4 h-4 text-pink-400" />
            <span>Alert Severity Distribution</span>
          </h2>

          <div className="space-y-3.5">
            {[
              { label: 'Critical Risk', count: criticalAlerts, color: 'bg-red-500', bar: 'bg-red-500/30', border: 'border-red-500/40' },
              { label: 'High Risk', count: highAlerts, color: 'bg-orange-500', bar: 'bg-orange-500/30', border: 'border-orange-500/40' },
              { label: 'Moderate Stress', count: moderateAlerts, color: 'bg-yellow-500', bar: 'bg-yellow-500/30', border: 'border-yellow-500/40' },
              { label: 'Low / Normal', count: Math.max(0, totalAlerts - criticalAlerts - highAlerts - moderateAlerts), color: 'bg-emerald-500', bar: 'bg-emerald-500/30', border: 'border-emerald-500/40' },
            ].map((item) => {
              const pct = totalAlerts > 0 ? Math.round((item.count / totalAlerts) * 100) : 0;
              return (
                <div key={item.label} className="space-y-1">
                  <div className="flex items-center justify-between text-xs font-semibold">
                    <span className="text-slate-300 flex items-center space-x-1.5">
                      <span className={`w-2 h-2 rounded-full ${item.color}`} />
                      <span>{item.label}</span>
                    </span>
                    <span className="text-white font-mono">{item.count} ({pct}%)</span>
                  </div>
                  <div className="h-2 w-full rounded-full bg-slate-800 overflow-hidden">
                    <div
                      className={`h-full ${item.color} rounded-full transition-all duration-500`}
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>

          <button
            type="button"
            onClick={() => setActiveTab('alerts')}
            className="mt-6 w-full flex items-center justify-center space-x-2 rounded-xl bg-purple-950/60 hover:bg-purple-900/60 border border-purple-500/30 hover:border-purple-400 text-xs font-semibold text-purple-200 hover:text-white py-2.5 transition-all cursor-pointer"
          >
            <span>Open Triage Desk</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Quick-Launch Administrative Actions */}
        <div className="rounded-2xl border border-slate-700/80 bg-slate-900/70 p-5 shadow-xl backdrop-blur-md lg:col-span-2">
          <h2 className="text-sm font-bold uppercase tracking-wider text-purple-200 flex items-center space-x-2 mb-4">
            <ClipboardList className="w-4 h-4 text-pink-400" />
            <span>Console Action Center</span>
          </h2>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div
              onClick={() => setActiveTab('alerts')}
              className="p-3.5 rounded-xl border border-slate-800 hover:border-red-500/40 bg-slate-800/40 hover:bg-red-950/20 cursor-pointer transition-all group flex items-start space-x-3"
            >
              <div className="p-2.5 rounded-xl bg-red-500/10 text-red-400 border border-red-500/20 group-hover:scale-105 transition-transform">
                <AlertOctagon className="w-5 h-5" />
              </div>
              <div className="flex-1 min-w-0">
                <h3 className="text-sm font-bold text-white group-hover:text-red-200 transition-colors">
                  Mental Health Triage
                </h3>
                <p className="text-xs text-slate-400 mt-0.5 line-clamp-2">
                  Review student distress signals, flagged messages, and add clinical notes.
                </p>
              </div>
              <ChevronRight className="w-4 h-4 text-slate-500 group-hover:text-red-300 group-hover:translate-x-0.5 transition-all mt-1" />
            </div>

            <div
              onClick={() => setActiveTab('students')}
              className="p-3.5 rounded-xl border border-slate-800 hover:border-cyan-500/40 bg-slate-800/40 hover:bg-cyan-950/20 cursor-pointer transition-all group flex items-start space-x-3"
            >
              <div className="p-2.5 rounded-xl bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 group-hover:scale-105 transition-transform">
                <UserPlus className="w-5 h-5" />
              </div>
              <div className="flex-1 min-w-0">
                <h3 className="text-sm font-bold text-white group-hover:text-cyan-200 transition-colors">
                  Authorized Students
                </h3>
                <p className="text-xs text-slate-400 mt-0.5 line-clamp-2">
                  Manage student credentials, registration IDs, and department enrollments.
                </p>
              </div>
              <ChevronRight className="w-4 h-4 text-slate-500 group-hover:text-cyan-300 group-hover:translate-x-0.5 transition-all mt-1" />
            </div>

            <div
              onClick={() => setActiveTab('records')}
              className="p-3.5 rounded-xl border border-slate-800 hover:border-purple-500/40 bg-slate-800/40 hover:bg-purple-950/20 cursor-pointer transition-all group flex items-start space-x-3"
            >
              <div className="p-2.5 rounded-xl bg-purple-500/10 text-purple-400 border border-purple-500/20 group-hover:scale-105 transition-transform">
                <ClipboardList className="w-5 h-5" />
              </div>
              <div className="flex-1 min-w-0">
                <h3 className="text-sm font-bold text-white group-hover:text-purple-200 transition-colors">
                  Academic & Billing Studio
                </h3>
                <p className="text-xs text-slate-400 mt-0.5 line-clamp-2">
                  Update student CGPA, semester credit progress, course marks, and tuition dues.
                </p>
              </div>
              <ChevronRight className="w-4 h-4 text-slate-500 group-hover:text-purple-300 group-hover:translate-x-0.5 transition-all mt-1" />
            </div>

            <div
              onClick={() => setActiveTab('audits')}
              className="p-3.5 rounded-xl border border-slate-800 hover:border-indigo-500/40 bg-slate-800/40 hover:bg-indigo-950/20 cursor-pointer transition-all group flex items-start space-x-3"
            >
              <div className="p-2.5 rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 group-hover:scale-105 transition-transform">
                <ShieldCheck className="w-5 h-5" />
              </div>
              <div className="flex-1 min-w-0">
                <h3 className="text-sm font-bold text-white group-hover:text-indigo-200 transition-colors">
                  FERPA Audit Logs
                </h3>
                <p className="text-xs text-slate-400 mt-0.5 line-clamp-2">
                  Inspect data access logs, unauthorized attempts, and FERPA compliance records.
                </p>
              </div>
              <ChevronRight className="w-4 h-4 text-slate-500 group-hover:text-indigo-300 group-hover:translate-x-0.5 transition-all mt-1" />
            </div>
          </div>
        </div>
      </div>

      {/* 3. Priority Review Feed */}
      <div className="rounded-2xl border border-slate-700/80 bg-slate-900/70 p-5 shadow-xl backdrop-blur-md">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-2">
            <AlertTriangle className="w-4 h-4 text-amber-400" />
            <h2 className="text-sm font-bold uppercase tracking-wider text-white">
              Urgent Attention Required
            </h2>
          </div>
          <button
            type="button"
            onClick={() => setActiveTab('alerts')}
            className="text-xs font-semibold text-purple-300 hover:text-white flex items-center space-x-1 cursor-pointer"
          >
            <span>View All ({totalAlerts})</span>
            <ChevronRight className="w-3.5 h-3.5" />
          </button>
        </div>

        {priorityAlerts.length === 0 ? (
          <div className="py-8 text-center text-slate-400 text-sm">
            <CheckCircle2 className="w-8 h-8 text-emerald-400 mx-auto mb-2" />
            <p>All clear! No pending critical or high-risk student alerts.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {priorityAlerts.map((alert) => (
              <div
                key={alert.id}
                className="p-3.5 rounded-xl border border-slate-800 bg-slate-800/50 hover:border-purple-500/40 transition-all flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span
                      className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded-md border ${
                        alert.severity === 'critical'
                          ? 'bg-red-500/20 text-red-200 border-red-500/40'
                          : 'bg-orange-500/20 text-orange-200 border-orange-500/40'
                      }`}
                    >
                      {alert.severity}
                    </span>
                    <span className="text-[11px] text-slate-400 font-mono">
                      {new Date(alert.created_at).toLocaleDateString()}
                    </span>
                  </div>

                  <h3 className="text-sm font-bold text-white truncate">
                    {alert.student_name || alert.reg_id || 'Student ID: ' + alert.reg_id}
                  </h3>
                  <p className="text-xs text-purple-200/80 mt-1 line-clamp-1 italic">
                    "{alert.question_sample || alert.summary || 'Risk detected'}"
                  </p>
                </div>

                <div className="mt-3 pt-2.5 border-t border-slate-700/60 flex items-center justify-between">
                  <span className="text-[11px] text-slate-400 capitalize">
                    Status: <strong className="text-slate-200">{alert.status}</strong>
                  </span>
                  <button
                    type="button"
                    onClick={() => {
                      onSelectAlert(alert);
                      setActiveTab('alerts');
                    }}
                    className="text-xs font-semibold text-pink-400 hover:text-pink-300 flex items-center space-x-1 cursor-pointer"
                  >
                    <span>Review Case</span>
                    <ArrowRight className="w-3 h-3" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default OverviewTab;
