import React, { useState, useMemo } from 'react';
import {
  AlertTriangle,
  AlertOctagon,
  Eye,
  CheckCircle2,
  Search,
  Filter,
  X,
  ClipboardList,
  Calendar,
  MessageSquare,
  Sparkles,
  ArrowRight,
  User,
  Trash2,
} from 'lucide-react';

const severityClasses = {
  critical: 'border-red-400/60 bg-red-500/20 text-red-200',
  high: 'border-orange-400/60 bg-orange-500/20 text-orange-200',
  moderate: 'border-yellow-400/60 bg-yellow-500/20 text-yellow-200',
  low: 'border-emerald-400/60 bg-emerald-500/20 text-emerald-200',
};

const statusClasses = {
  new: 'bg-red-500/20 text-red-300 border-red-500/30',
  reviewed: 'bg-amber-500/20 text-amber-300 border-amber-500/30',
  contacted: 'bg-cyan-500/20 text-cyan-300 border-cyan-500/30',
  closed: 'bg-slate-700/60 text-slate-300 border-slate-600',
};

const statusOptions = ['new', 'reviewed', 'contacted', 'closed'];

const AlertsTab = ({
  alerts = [],
  selectedAlert,
  noteDraft,
  saving,
  onSelectAlert,
  onCloseAlert,
  onNoteDraftChange,
  onUpdateAlert,
  onDeleteAlert,
  onClearAlerts,
  onLoadStudentProfile,
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [severityFilter, setSeverityFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');

  // Filtered alerts
  const filteredAlerts = useMemo(() => {
    return alerts.filter((alert) => {
      // Search match
      const q = searchQuery.toLowerCase().trim();
      const nameMatch = (alert.student_name || '').toLowerCase().includes(q);
      const idMatch = (alert.reg_id || '').toLowerCase().includes(q);
      const textMatch = (alert.question_sample || '').toLowerCase().includes(q);
      const summaryMatch = (alert.summary || '').toLowerCase().includes(q);
      const matchesSearch = !q || nameMatch || idMatch || textMatch || summaryMatch;

      // Severity match
      const matchesSeverity =
        severityFilter === 'all' || (alert.severity || '').toLowerCase() === severityFilter;

      // Status match
      const matchesStatus =
        statusFilter === 'all' || (alert.status || 'new').toLowerCase() === statusFilter;

      return matchesSearch && matchesSeverity && matchesStatus;
    });
  }, [alerts, searchQuery, severityFilter, statusFilter]);

  return (
    <div className="space-y-5 animate-fadeIn">
      {/* 1. Filter & Search Control Bar */}
      <div className="rounded-2xl border border-slate-700/80 bg-slate-900/80 p-4 shadow-xl backdrop-blur-md flex flex-col md:flex-row gap-3 items-center justify-between">
        {/* Search Input */}
        <div className="relative w-full md:w-80">
          <Search className="w-4 h-4 text-purple-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search student, ID, or flagged phrase..."
            className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-purple-500/30 bg-slate-800/80 text-xs sm:text-sm text-white placeholder-purple-300/40 focus:border-purple-500 focus:outline-none"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery('')}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-white"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>

        {/* Severity Filter Chips */}
        <div className="flex flex-wrap items-center gap-1.5 w-full md:w-auto">
          <span className="text-xs text-slate-400 font-semibold mr-1 flex items-center space-x-1">
            <Filter className="w-3 h-3 text-pink-400" />
            <span>Severity:</span>
          </span>
          {['all', 'critical', 'high', 'moderate', 'low'].map((sev) => (
            <button
              key={sev}
              type="button"
              onClick={() => setSeverityFilter(sev)}
              className={`px-3 py-1 rounded-xl text-xs font-semibold capitalize transition-all cursor-pointer ${
                severityFilter === sev
                  ? 'bg-purple-600 text-white shadow-md shadow-purple-500/20'
                  : 'bg-slate-800/80 text-slate-300 hover:bg-slate-700 hover:text-white border border-slate-700'
              }`}
            >
              {sev}
            </button>
          ))}
        </div>

        {/* Status Filter Chips */}
        <div className="flex flex-wrap items-center gap-1.5 w-full md:w-auto">
          <span className="text-xs text-slate-400 font-semibold mr-1">Status:</span>
          {['all', 'new', 'reviewed', 'contacted', 'closed'].map((st) => (
            <button
              key={st}
              type="button"
              onClick={() => setStatusFilter(st)}
              className={`px-3 py-1 rounded-xl text-xs font-semibold capitalize transition-all cursor-pointer ${
                statusFilter === st
                  ? 'bg-pink-600 text-white shadow-md shadow-pink-500/20'
                  : 'bg-slate-800/80 text-slate-300 hover:bg-slate-700 hover:text-white border border-slate-700'
              }`}
            >
              {st}
            </button>
          ))}
        </div>
      </div>

      {/* 2. Main Table & Slide-Over Panel Container */}
      <div className="grid grid-cols-1 gap-5 relative">
        <div className="overflow-hidden rounded-2xl border border-slate-700/80 bg-slate-900/80 shadow-xl backdrop-blur-md">
          <div className="border-b border-slate-800 px-5 py-3.5 flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <AlertTriangle className="w-4 h-4 text-pink-400" />
              <h2 className="font-bold text-white text-sm uppercase tracking-wider">
                Mental Health Alerts ({filteredAlerts.length})
              </h2>
            </div>
            <div className="flex items-center gap-3">
              {(severityFilter !== 'all' || statusFilter !== 'all' || searchQuery) && (
                <span className="text-xs text-purple-300 font-mono">Filtered view</span>
              )}
              {alerts.length > 0 && onClearAlerts && (
                <button
                  type="button"
                  onClick={onClearAlerts}
                  disabled={saving}
                  className="inline-flex items-center space-x-1.5 rounded-xl border border-red-500/30 bg-red-950/40 hover:bg-red-900/60 px-3 py-1.5 text-xs font-semibold text-red-200 hover:text-white transition-all disabled:opacity-50 cursor-pointer"
                >
                  <Trash2 className="w-3.5 h-3.5 text-red-400" />
                  <span>Clear All</span>
                </button>
              )}
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full min-w-[880px] text-left text-sm">
              <thead className="bg-slate-950/70 text-[11px] font-bold uppercase tracking-wider text-purple-300/80 border-b border-slate-800">
                <tr>
                  <th className="px-5 py-3.5">Severity</th>
                  <th className="px-5 py-3.5">Student</th>
                  <th className="px-5 py-3.5">Signal & Confidence</th>
                  <th className="px-5 py-3.5">Flagged Student Phrase</th>
                  <th className="px-5 py-3.5">Status</th>
                  <th className="px-5 py-3.5">Timestamp</th>
                  <th className="px-5 py-3.5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/70">
                {filteredAlerts.length === 0 ? (
                  <tr>
                    <td className="px-5 py-12 text-center text-slate-400" colSpan="7">
                      <div className="flex flex-col items-center justify-center">
                        <CheckCircle2 className="w-8 h-8 text-emerald-400 mb-2" />
                        <p className="font-semibold text-white">No alerts match your current filter.</p>
                        <p className="text-xs text-slate-500 mt-1">Try resetting the search or severity filters.</p>
                      </div>
                    </td>
                  </tr>
                ) : (
                  filteredAlerts.map((alert) => {
                    const isSelected = selectedAlert?.id === alert.id;
                    return (
                      <tr
                        key={alert.id}
                        className={`transition-colors ${
                          isSelected
                            ? 'bg-purple-950/40 border-l-4 border-pink-500'
                            : 'hover:bg-slate-800/50 text-slate-200'
                        }`}
                      >
                        {/* Severity */}
                        <td className="px-5 py-4">
                          <span
                            className={`inline-flex items-center space-x-1.5 rounded-full border px-2.5 py-1 text-xs font-bold uppercase tracking-wider ${
                              severityClasses[alert.severity] || 'border-slate-500 bg-slate-700'
                            }`}
                          >
                            <span
                              className={`w-1.5 h-1.5 rounded-full ${
                                alert.severity === 'critical' ? 'bg-red-400 animate-ping' : 'bg-current'
                              }`}
                            />
                            <span>{alert.severity}</span>
                          </span>
                        </td>

                        {/* Student Info */}
                        <td className="px-5 py-4">
                          <div className="font-semibold text-white">
                            {alert.student_name || alert.reg_id || 'Student'}
                          </div>
                          <div className="text-xs text-purple-300 font-mono">
                            {alert.reg_id}
                          </div>
                        </td>

                        {/* Signal & Confidence */}
                        <td className="px-5 py-4">
                          <div className="font-medium text-slate-200">
                            {alert.predicted_class || alert.summary || 'Mental distress'}
                          </div>
                          <div className="text-xs text-slate-400 font-mono mt-0.5">
                            {alert.confidence ? `${Math.round(alert.confidence * 100)}% confidence` : `Score: ${alert.score}`}
                          </div>
                        </td>

                        {/* Flagged Snippet */}
                        <td className="px-5 py-4 max-w-xs">
                          <p className="text-xs text-slate-300 italic truncate" title={alert.question_sample}>
                            "{alert.question_sample || 'No sample stored'}"
                          </p>
                        </td>

                        {/* Workflow Status */}
                        <td className="px-5 py-4">
                          <span
                            className={`inline-block text-[11px] font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-md border ${
                              statusClasses[alert.status] || 'border-slate-600 bg-slate-800 text-slate-300'
                            }`}
                          >
                            {alert.status}
                          </span>
                        </td>

                        {/* Created At */}
                        <td className="px-5 py-4 text-xs text-slate-400 font-mono whitespace-nowrap">
                          {new Date(alert.created_at).toLocaleString([], {
                            month: 'short',
                            day: 'numeric',
                            hour: '2-digit',
                            minute: '2-digit',
                          })}
                        </td>

                        {/* Action Buttons */}
                        <td className="px-5 py-4 text-right">
                          <div className="inline-flex items-center justify-end gap-2">
                            <button
                              type="button"
                              onClick={() => onSelectAlert(alert)}
                              className="inline-flex items-center space-x-1.5 rounded-xl border border-purple-500/30 bg-purple-950/40 hover:bg-purple-900/60 px-3 py-1.5 text-xs font-semibold text-purple-200 hover:text-white transition-all cursor-pointer"
                            >
                              <Eye className="w-3.5 h-3.5 text-pink-400" />
                              <span>Review</span>
                            </button>
                            {onDeleteAlert && (
                              <button
                                type="button"
                                onClick={() => onDeleteAlert(alert)}
                                disabled={saving}
                                title="Delete alert"
                                className="inline-flex items-center space-x-1 rounded-xl border border-red-500/30 bg-red-950/40 hover:bg-red-900/60 px-2.5 py-1.5 text-xs font-semibold text-red-200 hover:text-white transition-all disabled:opacity-50 cursor-pointer"
                              >
                                <Trash2 className="w-3.5 h-3.5 text-red-400" />
                                <span>Delete</span>
                              </button>
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

        {/* 3. Slide-Over Review Drawer (Modal Drawer on Selection) */}
        {selectedAlert && (
          <div className="fixed inset-y-0 right-0 z-50 w-full max-w-lg bg-slate-900/95 border-l border-purple-500/30 p-6 shadow-2xl backdrop-blur-xl overflow-y-auto animate-slideLeft">
            <div className="flex items-center justify-between pb-4 border-b border-slate-800">
              <div className="flex items-center space-x-2.5">
                <div className="p-2 rounded-xl bg-purple-500/20 text-purple-300 border border-purple-500/30">
                  <AlertOctagon className="w-5 h-5 text-pink-400" />
                </div>
                <div>
                  <h3 className="font-bold text-white text-base">Alert Case Review</h3>
                  <span className="text-xs text-purple-300 font-mono">Case #{selectedAlert.id}</span>
                </div>
              </div>
              <button
                type="button"
                onClick={onCloseAlert}
                className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-4 my-5">
              {/* Student Header */}
              <div className="p-4 rounded-xl border border-slate-800 bg-slate-800/40 flex items-center justify-between">
                <div>
                  <div className="font-bold text-white text-base">
                    {selectedAlert.student_name || 'Student Name N/A'}
                  </div>
                  <div className="text-xs text-purple-300 font-mono mt-0.5">
                    Reg ID: {selectedAlert.reg_id}
                  </div>
                  {selectedAlert.student_email && (
                    <div className="text-xs text-slate-400">{selectedAlert.student_email}</div>
                  )}
                </div>
                <span
                  className={`text-xs font-bold uppercase tracking-wider px-3 py-1 rounded-full border ${
                    severityClasses[selectedAlert.severity] || ''
                  }`}
                >
                  {selectedAlert.severity}
                </span>
              </div>

              {/* Signal & Model Assessment */}
              <div className="p-4 rounded-xl border border-purple-500/20 bg-purple-950/20">
                <div className="text-xs font-bold uppercase tracking-wider text-purple-300 mb-1">
                  Clinical Assessment Signal
                </div>
                <div className="text-sm font-semibold text-white">
                  {selectedAlert.predicted_class || 'Distress Pattern'}
                </div>
                {selectedAlert.confidence && (
                  <div className="text-xs text-slate-400 font-mono mt-1">
                    ML Model Confidence: {Math.round(selectedAlert.confidence * 100)}%
                  </div>
                )}
                {selectedAlert.summary && (
                  <p className="text-xs text-slate-200 mt-2 bg-slate-900/60 p-2.5 rounded-lg border border-purple-500/20">
                    {selectedAlert.summary}
                  </p>
                )}
              </div>

              {/* Latest Flagged Interaction */}
              <div className="p-4 rounded-xl border border-slate-800 bg-slate-800/40">
                <div className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-1 flex items-center space-x-1.5">
                  <MessageSquare className="w-3.5 h-3.5 text-pink-400" />
                  <span>Flagged Message Sample</span>
                </div>
                <p className="text-sm text-pink-200/90 font-medium italic bg-slate-900/80 p-3 rounded-lg border border-slate-800">
                  "{selectedAlert.question_sample || 'No sample recorded'}"
                </p>
                <span className="text-[11px] text-slate-500 font-mono mt-1.5 block">
                  Logged: {new Date(selectedAlert.created_at).toLocaleString()}
                </span>
              </div>

              {/* Status Selector */}
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-purple-300 mb-1.5">
                  Workflow Resolution Status
                </label>
                <select
                  value={selectedAlert.status}
                  onChange={(e) => onUpdateAlert(e.target.value)}
                  disabled={saving}
                  className="w-full rounded-xl border border-purple-500/30 bg-slate-800 px-3.5 py-2.5 text-sm text-white focus:border-purple-500 focus:outline-none capitalize"
                >
                  {statusOptions.map((opt) => (
                    <option key={opt} value={opt} className="capitalize">
                      {opt}
                    </option>
                  ))}
                </select>
              </div>

              {/* Counselor / Admin Notes */}
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-purple-300 mb-1.5">
                  Counselor & Triage Notes
                </label>
                <textarea
                  value={noteDraft}
                  onChange={(e) => onNoteDraftChange(e.target.value)}
                  rows="4"
                  placeholder="Record counseling actions, outreach attempts, or clinical follow-ups..."
                  className="w-full rounded-xl border border-purple-500/30 bg-slate-800 px-3.5 py-2.5 text-sm text-white placeholder-purple-300/40 focus:border-purple-500 focus:outline-none"
                />
              </div>

              {/* Action Buttons */}
              <div className="pt-2 flex flex-col gap-2.5">
                <button
                  type="button"
                  onClick={() => onUpdateAlert(selectedAlert.status)}
                  disabled={saving}
                  className="w-full flex items-center justify-center space-x-2 rounded-xl bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500 px-4 py-3 text-sm font-bold text-white shadow-lg shadow-purple-500/25 transition-all disabled:opacity-60 cursor-pointer"
                >
                  <CheckCircle2 className="w-4 h-4" />
                  <span>{saving ? 'Saving...' : 'Save Review & Notes'}</span>
                </button>

                {selectedAlert.reg_id && (
                  <button
                    type="button"
                    onClick={() => onLoadStudentProfile(selectedAlert.reg_id)}
                    className="w-full flex items-center justify-center space-x-2 rounded-xl border border-purple-500/30 bg-purple-950/30 hover:bg-purple-900/50 px-4 py-2.5 text-xs font-semibold text-purple-200 hover:text-white transition-all cursor-pointer"
                  >
                    <ClipboardList className="w-4 h-4 text-pink-400" />
                    <span>View Student 360° Profile</span>
                  </button>
                )}

                {onDeleteAlert && (
                  <button
                    type="button"
                    onClick={() => onDeleteAlert(selectedAlert)}
                    disabled={saving}
                    className="w-full flex items-center justify-center space-x-2 rounded-xl border border-red-500/30 bg-red-950/40 hover:bg-red-900/60 px-4 py-2.5 text-xs font-semibold text-red-200 hover:text-white transition-all disabled:opacity-50 cursor-pointer"
                  >
                    <Trash2 className="w-4 h-4 text-red-400" />
                    <span>Delete Alert</span>
                  </button>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AlertsTab;
