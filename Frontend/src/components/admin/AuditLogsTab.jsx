import React, { useState, useMemo } from 'react';
import {
  ShieldAlert,
  ShieldCheck,
  Search,
  Filter,
  RefreshCw,
  Clock,
  UserCheck,
  AlertTriangle,
  Lock,
  ChevronRight,
  Database,
  Terminal,
  Activity
} from 'lucide-react';

const ACTION_LABELS = {
  READ_CGPA: 'Read CGPA',
  READ_IDENTITY: 'Read Identity',
  READ_FEE_STATUS: 'Read Fee Status',
  UNAUTHORIZED_ATTEMPT: 'Unauthorized Attempt',
};

const STATUS_BADGES = {
  AUTHORIZED: {
    bg: 'bg-emerald-500/15',
    text: 'text-emerald-300',
    border: 'border-emerald-500/30',
    dot: 'bg-emerald-400',
    label: 'Authorized',
  },
  DENIED_FORBIDDEN: {
    bg: 'bg-rose-500/20',
    text: 'text-rose-300',
    border: 'border-rose-500/30',
    dot: 'bg-rose-400',
    label: 'Denied (Forbidden)',
  },
  DENIED_UNAUTHENTICATED: {
    bg: 'bg-amber-500/20',
    text: 'text-amber-300',
    border: 'border-amber-500/30',
    dot: 'bg-amber-400',
    label: 'Unauthenticated',
  },
};

export default function AuditLogsTab({
  logs = [],
  totalLogs = 0,
  onRefresh,
  isLoading = false,
  onViewStudentProfile
}) {
  const [searchTerm, setSearchTerm] = useState('');
  const [actionFilter, setActionFilter] = useState('ALL');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [limit, setLimit] = useState(50);

  // Compute summary metrics
  const metrics = useMemo(() => {
    let authorized = 0;
    let denied = 0;
    let crossAccess = 0;

    logs.forEach((log) => {
      if (log.auth_status === 'AUTHORIZED') authorized++;
      else denied++;

      if (
        log.actor_student_id &&
        log.target_student_id &&
        log.actor_student_id !== log.target_student_id
      ) {
        crossAccess++;
      }
    });

    return {
      total: totalLogs || logs.length,
      authorized,
      denied,
      crossAccess,
    };
  }, [logs, totalLogs]);

  // Client-side filtering
  const filteredLogs = useMemo(() => {
    return logs.filter((log) => {
      const matchesSearch =
        !searchTerm ||
        log.actor_student_id?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        log.target_student_id?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        log.agent_node?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        log.client_ip?.toLowerCase().includes(searchTerm.toLowerCase());

      const matchesAction = actionFilter === 'ALL' || log.action_type === actionFilter;
      const matchesStatus = statusFilter === 'ALL' || log.auth_status === statusFilter;

      return matchesSearch && matchesAction && matchesStatus;
    });
  }, [logs, searchTerm, actionFilter, statusFilter]);

  const formatTimestamp = (isoString) => {
    if (!isoString) return 'N/A';
    try {
      const d = new Date(isoString);
      return d.toLocaleString(undefined, {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
      });
    } catch {
      return isoString;
    }
  };

  return (
    <div className="space-y-6">
      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="rounded-2xl border border-purple-500/20 bg-slate-800/80 p-4 shadow-lg backdrop-blur-md">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-[11px] font-semibold text-purple-300/70 uppercase">Total Access Logs</p>
              <p className="text-2xl font-bold text-white mt-1">{metrics.total}</p>
            </div>
            <div className="h-10 w-10 rounded-xl bg-purple-500/20 border border-purple-500/30 flex items-center justify-center text-purple-300">
              <Activity className="h-5 w-5" />
            </div>
          </div>
          <p className="text-[11px] text-purple-300/50 mt-2">Recorded audit entries</p>
        </div>

        <div className="rounded-2xl border border-emerald-500/20 bg-slate-800/80 p-4 shadow-lg backdrop-blur-md">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-[11px] font-semibold text-emerald-300/70 uppercase">Authorized Operations</p>
              <p className="text-2xl font-bold text-emerald-400 mt-1">{metrics.authorized}</p>
            </div>
            <div className="h-10 w-10 rounded-xl bg-emerald-500/20 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
              <ShieldCheck className="h-5 w-5" />
            </div>
          </div>
          <p className="text-[11px] text-emerald-300/50 mt-2">Verified identity tokens</p>
        </div>

        <div className="rounded-2xl border border-rose-500/20 bg-slate-800/80 p-4 shadow-lg backdrop-blur-md">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-[11px] font-semibold text-rose-300/70 uppercase">Denied Access Attempts</p>
              <p className="text-2xl font-bold text-rose-400 mt-1">{metrics.denied}</p>
            </div>
            <div className="h-10 w-10 rounded-xl bg-rose-500/20 border border-rose-500/30 flex items-center justify-center text-rose-400">
              <ShieldAlert className="h-5 w-5" />
            </div>
          </div>
          <p className="text-[11px] text-rose-300/50 mt-2">FERPA violations prevented</p>
        </div>

        <div className="rounded-2xl border border-amber-500/20 bg-slate-800/80 p-4 shadow-lg backdrop-blur-md">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-[11px] font-semibold text-amber-300/70 uppercase">Cross-Student Inquiries</p>
              <p className="text-2xl font-bold text-amber-400 mt-1">{metrics.crossAccess}</p>
            </div>
            <div className="h-10 w-10 rounded-xl bg-amber-500/20 border border-amber-500/30 flex items-center justify-center text-amber-400">
              <AlertTriangle className="h-5 w-5" />
            </div>
          </div>
          <p className="text-[11px] text-amber-300/50 mt-2">Actor requested another ID</p>
        </div>
      </div>

      {/* Control Bar */}
      <div className="rounded-2xl border border-purple-500/20 bg-slate-800/80 p-4 shadow-lg backdrop-blur-md">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex flex-1 flex-col sm:flex-row gap-3">
            {/* Search */}
            <div className="relative flex-1">
              <Search className="absolute left-3.5 top-2.5 h-4 w-4 text-purple-300/50" />
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search by student ID, agent node, or client IP..."
                className="w-full rounded-xl border border-purple-500/30 bg-slate-900/80 py-2 pl-10 pr-4 text-xs text-white placeholder-purple-300/40 focus:border-purple-400 focus:outline-none"
              />
            </div>

            {/* Action Filter */}
            <select
              value={actionFilter}
              onChange={(e) => setActionFilter(e.target.value)}
              className="rounded-xl border border-purple-500/30 bg-slate-900/80 px-3 py-2 text-xs font-medium text-white focus:border-purple-400 focus:outline-none"
            >
              <option value="ALL">All Actions</option>
              <option value="READ_CGPA">Read CGPA</option>
              <option value="READ_IDENTITY">Read Identity</option>
              <option value="READ_FEE_STATUS">Read Fee Status</option>
              <option value="UNAUTHORIZED_ATTEMPT">Unauthorized Attempt</option>
            </select>

            {/* Status Filter */}
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="rounded-xl border border-purple-500/30 bg-slate-900/80 px-3 py-2 text-xs font-medium text-white focus:border-purple-400 focus:outline-none"
            >
              <option value="ALL">All Statuses</option>
              <option value="AUTHORIZED">Authorized</option>
              <option value="DENIED_FORBIDDEN">Denied (Forbidden)</option>
              <option value="DENIED_UNAUTHENTICATED">Unauthenticated</option>
            </select>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => onRefresh && onRefresh()}
              disabled={isLoading}
              className="inline-flex items-center gap-1.5 rounded-xl border border-purple-500/30 bg-purple-500/10 hover:bg-purple-500/20 px-3 py-2 text-xs font-semibold text-purple-200 transition-all disabled:opacity-50"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${isLoading ? 'animate-spin' : ''}`} />
              <span>Refresh Logs</span>
            </button>
          </div>
        </div>
      </div>

      {/* Audit Log Table */}
      <div className="overflow-hidden rounded-2xl border border-purple-500/20 bg-slate-800/80 shadow-xl backdrop-blur-md">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-900/80 text-[11px] uppercase tracking-wider text-purple-300/70 border-b border-purple-500/20">
              <tr>
                <th className="px-4 py-3.5">Timestamp</th>
                <th className="px-4 py-3.5">Actor / Target Student</th>
                <th className="px-4 py-3.5">Agent Node</th>
                <th className="px-4 py-3.5">Action Type</th>
                <th className="px-4 py-3.5">Auth Status</th>
                <th className="px-4 py-3.5">Client IP / Token</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-purple-500/10">
              {filteredLogs.length === 0 ? (
                <tr>
                  <td colSpan={6} className="p-8 text-center text-purple-300/60">
                    <Database className="mx-auto h-8 w-8 text-purple-400/40 mb-2" />
                    <p className="font-medium text-sm">No access audit logs match the current criteria.</p>
                  </td>
                </tr>
              ) : (
                filteredLogs.map((log) => {
                  const badge = STATUS_BADGES[log.auth_status] || {
                    bg: 'bg-slate-700',
                    text: 'text-slate-300',
                    border: 'border-slate-600',
                    dot: 'bg-slate-400',
                    label: log.auth_status,
                  };

                  const isCrossAccess =
                    log.actor_student_id &&
                    log.target_student_id &&
                    log.actor_student_id !== log.target_student_id;

                  return (
                    <tr
                      key={log.id}
                      className="hover:bg-purple-500/[0.04] transition-colors"
                    >
                      {/* Timestamp */}
                      <td className="px-4 py-3.5 whitespace-nowrap text-purple-200">
                        <div className="flex items-center gap-1.5">
                          <Clock className="h-3.5 w-3.5 text-purple-400" />
                          <span className="font-mono text-[11px]">{formatTimestamp(log.timestamp)}</span>
                        </div>
                      </td>

                      {/* Actor vs Target */}
                      <td className="px-4 py-3.5">
                        <div className="space-y-1">
                          <div className="flex items-center gap-1.5">
                            <span className="text-[10px] text-purple-300/60 uppercase">Actor:</span>
                            {log.actor_student_id ? (
                              <button
                                onClick={() => onViewStudentProfile && onViewStudentProfile(log.actor_student_id)}
                                className="font-mono font-medium text-purple-300 hover:text-white hover:underline"
                              >
                                {log.actor_student_id}
                              </button>
                            ) : (
                              <span className="text-slate-400 italic">None (Anonymous)</span>
                            )}
                          </div>

                          <div className="flex items-center gap-1.5">
                            <span className="text-[10px] text-purple-300/60 uppercase">Target:</span>
                            {log.target_student_id ? (
                              <span className={`font-mono font-medium ${isCrossAccess ? 'text-amber-400 font-bold' : 'text-slate-200'}`}>
                                {log.target_student_id}
                              </span>
                            ) : (
                              <span className="text-slate-400 italic">N/A</span>
                            )}

                            {isCrossAccess && (
                              <span
                                title="Cross-student record query violation"
                                className="text-[10px] px-1.5 py-0.2 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30"
                              >
                                Cross-Access
                              </span>
                            )}
                          </div>
                        </div>
                      </td>

                      {/* Agent Node */}
                      <td className="px-4 py-3.5 whitespace-nowrap">
                        <span className="inline-flex items-center gap-1 rounded-lg bg-slate-900/60 border border-purple-500/20 px-2 py-1 text-[11px] font-mono text-purple-200">
                          <Terminal className="h-3 w-3 text-purple-400" />
                          {log.agent_node}
                        </span>
                      </td>

                      {/* Action Type */}
                      <td className="px-4 py-3.5 whitespace-nowrap">
                        <span className="font-semibold text-white">
                          {ACTION_LABELS[log.action_type] || log.action_type}
                        </span>
                      </td>

                      {/* Auth Status */}
                      <td className="px-4 py-3.5 whitespace-nowrap">
                        <span
                          className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-[11px] font-semibold border ${badge.bg} ${badge.text} ${badge.border}`}
                        >
                          <span className={`h-1.5 w-1.5 rounded-full ${badge.dot}`} />
                          {badge.label}
                        </span>
                      </td>

                      {/* Client IP & Token */}
                      <td className="px-4 py-3.5 whitespace-nowrap text-purple-300/70">
                        <div className="font-mono text-[11px]">
                          <div>{log.client_ip || '127.0.0.1'}</div>
                          {log.token_jti && (
                            <div className="text-[10px] text-purple-400/60 truncate max-w-[120px]" title={log.token_jti}>
                              jti: {log.token_jti}
                            </div>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
