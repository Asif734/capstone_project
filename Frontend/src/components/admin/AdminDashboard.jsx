import React, { useEffect, useMemo, useState } from 'react';
import {
  Activity,
  AlertOctagon,
  BookOpen,
  CheckCircle2,
  Database,
  FileText,
  GraduationCap,
  Layers,
  Lock,
  Mail,
  RefreshCw,
  ShieldAlert,
  ShieldCheck,
  TrendingUp,
  UserCheck,
  Users,
  X,
  AlertTriangle
} from 'lucide-react';
import { adminAPI } from '../../services/api';
import AdminHeader from './AdminHeader';
import OverviewTab from './OverviewTab';
import AlertsTab from './AlertsTab';
import StudentsTab from './StudentsTab';
import RecordsTab from './RecordsTab';
import AuditLogsTab from './AuditLogsTab';
import DocumentsTab from './DocumentsTab';

const severityOrder = {
  critical: 0,
  high: 1,
  moderate: 2,
  low: 3,
};

const sortAlerts = (items = []) => {
  return [...items].sort((a, b) => {
    const diff = (severityOrder[a.severity] ?? 99) - (severityOrder[b.severity] ?? 99);
    if (diff !== 0) return diff;
    return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
  });
};

export default function AdminDashboard({
  isAdminAuthenticated,
  onAdminAuth,
  onAdminLogout,
  onBackToChat,
}) {
  // Auth state
  const [activeToken, setActiveToken] = useState(() => {
    return sessionStorage.getItem('adminToken') || localStorage.getItem('adminToken') || '';
  });
  const [isAuthorized, setIsAuthorized] = useState(Boolean(activeToken) || Boolean(isAdminAuthenticated));
  const [adminEmail, setAdminEmail] = useState('');
  const [adminPassword, setAdminPassword] = useState('');

  // Active navigation tab
  const [activeTab, setActiveTab] = useState('overview');

  // Core data states
  const [summary, setSummary] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [students, setStudents] = useState([]);
  const [auditLogs, setAuditLogs] = useState([]);
  const [totalAuditLogs, setTotalAuditLogs] = useState(0);
  const [documents, setDocuments] = useState([]);
  const [totalDocuments, setTotalDocuments] = useState(0);

  // Detail / Interaction states
  const [selectedAlert, setSelectedAlert] = useState(null);
  const [noteDraft, setNoteDraft] = useState('');
  const [selectedRecordStudent, setSelectedRecordStudent] = useState(null);
  const [recordData, setRecordData] = useState(null);
  const [studentDetail, setStudentDetail] = useState(null);

  // Status flags
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [uploadingDoc, setUploadingDoc] = useState(false);
  const [deletingDoc, setDeletingDoc] = useState(false);
  const [toast, setToast] = useState({ show: false, message: '', type: 'success' });

  const showToast = (message, type = 'success') => {
    setToast({ show: true, message, type });
    setTimeout(() => {
      setToast((current) => ({ ...current, show: false }));
    }, 4500);
  };

  const criticalNewCount = useMemo(() => {
    return alerts.filter((a) => a.severity === 'critical' && a.status === 'new').length;
  }, [alerts]);

  const unresolvedAlertsCount = useMemo(() => {
    return alerts.filter((a) => a.status === 'new' || a.status === 'reviewed').length;
  }, [alerts]);

  // Load complete dashboard data
  const loadDashboard = async (tokenToUse = activeToken) => {
    let token = tokenToUse;
    if (!token && (!adminEmail.trim() || !adminPassword)) {
      showToast('Enter the admin email and password.', 'error');
      return;
    }

    setLoading(true);
    try {
      if (!token) {
        const loginResponse = await adminAPI.login(adminEmail.trim(), adminPassword);
        token = loginResponse.access_token;
      }

      if (!token?.trim()) {
        throw new Error('Invalid admin credentials.');
      }

      const [summaryData, alertData, studentData, auditData, docData] = await Promise.all([
        adminAPI.getSummary(token).catch(() => ({})),
        adminAPI.getAlerts(token).catch(() => []),
        adminAPI.getStudents(token).catch(() => []),
        adminAPI.getAuditLogs(token, { limit: 100 }).catch(() => ({ items: [], total: 0 })),
        adminAPI.getDocuments(token).catch(() => ({ documents: [], total_documents: 0 })),
      ]);

      setSummary(summaryData);
      setAlerts(sortAlerts(alertData));
      setStudents(studentData);
      setAuditLogs(auditData.items || []);
      setTotalAuditLogs(auditData.total || (auditData.items || []).length);
      setDocuments(docData.documents || []);
      setTotalDocuments(docData.total_documents || (docData.documents || []).length);

      setActiveToken(token);
      sessionStorage.setItem('adminToken', token);
      localStorage.setItem('adminToken', token);
      setAdminPassword('');
      setIsAuthorized(true);
      if (onAdminAuth) onAdminAuth(token);
    } catch (err) {
      setIsAuthorized(false);
      showToast(err.message || 'Unable to authenticate as admin.', 'error');
      setActiveToken('');
      sessionStorage.removeItem('adminToken');
      localStorage.removeItem('adminToken');
    } finally {
      setLoading(false);
    }
  };

  // Initial authentication check
  useEffect(() => {
    const storedToken = sessionStorage.getItem('adminToken') || localStorage.getItem('adminToken');
    if (storedToken && !summary && !loading) {
      loadDashboard(storedToken);
    }
  }, []);

  const handleLoginSubmit = (e) => {
    e.preventDefault();
    loadDashboard();
  };

  const handleLogout = () => {
    sessionStorage.removeItem('adminToken');
    localStorage.removeItem('adminToken');
    setActiveToken('');
    setIsAuthorized(false);
    setAdminEmail('');
    setAdminPassword('');
    setSummary(null);
    setAlerts([]);
    setStudents([]);
    setAuditLogs([]);
    setDocuments([]);
    setSelectedAlert(null);
    setSelectedRecordStudent(null);
    setRecordData(null);
    setStudentDetail(null);
    if (onAdminLogout) onAdminLogout();
    showToast('Logged out successfully.', 'success');
  };

  // Alerts actions
  const handleSelectAlert = (alert) => {
    setSelectedAlert(alert);
    setNoteDraft(alert?.admin_notes || '');
  };

  const handleCloseAlertDrawer = () => {
    setSelectedAlert(null);
    setNoteDraft('');
  };

  const handleUpdateAlert = async (status, notes = noteDraft) => {
    if (!selectedAlert) return;
    setSaving(true);
    try {
      const updated = await adminAPI.updateAlert(activeToken, selectedAlert.id, {
        status,
        admin_notes: notes,
      });
      setSelectedAlert(updated);
      setAlerts((current) =>
        sortAlerts(current.map((a) => (a.id === updated.id ? updated : a)))
      );
      showToast(`Alert updated to "${status}".`, 'success');
    } catch (err) {
      showToast(err.message || 'Failed to update alert.', 'error');
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteAlert = async (alert) => {
    if (!window.confirm(`Delete mental health alert #${alert.id} for ${alert.student_name || alert.reg_id || 'this student'}?`)) {
      return;
    }
    setSaving(true);
    try {
      await adminAPI.deleteAlert(activeToken, alert.id);
      setAlerts((current) => current.filter((a) => a.id !== alert.id));
      if (selectedAlert?.id === alert.id) {
        setSelectedAlert(null);
        setNoteDraft('');
      }
      showToast('Mental health alert deleted.', 'success');
    } catch (err) {
      showToast(err.message || 'Failed to delete alert.', 'error');
    } finally {
      setSaving(false);
    }
  };

  const handleClearAlerts = async () => {
    if (!window.confirm('Clear all mental health alerts from the database? This cannot be undone.')) {
      return;
    }
    setSaving(true);
    try {
      await adminAPI.clearAlerts(activeToken);
      setAlerts([]);
      setSelectedAlert(null);
      setNoteDraft('');
      showToast('All mental health alerts cleared.', 'success');
    } catch (err) {
      showToast(err.message || 'Failed to clear alerts.', 'error');
    } finally {
      setSaving(false);
    }
  };

  // Students actions
  const handleSaveStudent = async (studentForm, editingStudent = null) => {
    setSaving(true);
    const payload = {
      reg_id: studentForm.reg_id.trim(),
      name: studentForm.name.trim(),
      email: studentForm.email.trim(),
      department: studentForm.department?.trim() || null,
      year: studentForm.year ? Number(studentForm.year) : null,
      semester: studentForm.semester ? Number(studentForm.semester) : null,
      status: studentForm.status || 'active',
    };

    try {
      if (editingStudent) {
        const updated = await adminAPI.updateStudent(activeToken, editingStudent.id, payload);
        setStudents((current) =>
          current
            .map((s) => (s.id === updated.id ? updated : s))
            .sort((a, b) => a.reg_id.localeCompare(b.reg_id))
        );
        showToast('Authorized student updated.', 'success');
      } else {
        const created = await adminAPI.addStudent(activeToken, payload);
        setStudents((current) =>
          [...current, created].sort((a, b) => a.reg_id.localeCompare(b.reg_id))
        );
        showToast('New student added successfully.', 'success');
      }
    } catch (err) {
      showToast(err.message || 'Failed to save student.', 'error');
      throw err;
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteStudent = async (student) => {
    if (!window.confirm(`Delete ${student.name || student.reg_id}? This cannot be undone.`)) {
      return;
    }
    setSaving(true);
    try {
      await adminAPI.deleteStudent(activeToken, student.id);
      setStudents((current) => current.filter((s) => s.id !== student.id));
      if (selectedRecordStudent?.reg_id === student.reg_id) {
        setSelectedRecordStudent(null);
        setRecordData(null);
      }
      showToast('Student removed from registry.', 'success');
    } catch (err) {
      showToast(err.message || 'Failed to remove student.', 'error');
    } finally {
      setSaving(false);
    }
  };

  // Load Student 360 profile
  const handleLoadStudentProfile = async (regId) => {
    if (!regId) return;
    setLoading(true);
    try {
      const detail = await adminAPI.getStudentMentalHealth(activeToken, regId);
      setStudentDetail({
        ...detail,
        alerts: sortAlerts(detail.alerts),
      });
    } catch (err) {
      showToast(err.message || 'Failed to load student profile.', 'error');
    } finally {
      setLoading(false);
    }
  };

  // Records actions
  const handleSelectRecordStudent = async (regId) => {
    if (!regId) {
      setSelectedRecordStudent(null);
      setRecordData(null);
      return;
    }
    const student = students.find((s) => s.reg_id === regId) || { reg_id: regId };
    setSelectedRecordStudent(student);
    setLoading(true);
    try {
      const records = await adminAPI.getStudentRecords(activeToken, regId);
      setRecordData(records);
      setSelectedRecordStudent(records.student || student);
    } catch (err) {
      showToast(err.message || 'Failed to fetch student records.', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleEditStudentRecordsFromDirectory = async (regId) => {
    setActiveTab('records');
    await handleSelectRecordStudent(regId);
  };

  const handleSaveRecords = async (regId, payload) => {
    setSaving(true);
    try {
      const updated = await adminAPI.updateStudentRecords(activeToken, regId, payload);
      setRecordData(updated);
      setSelectedRecordStudent(updated.student);
      showToast('Academic and billing records updated successfully.', 'success');
    } catch (err) {
      showToast(err.message || 'Failed to save academic records.', 'error');
    } finally {
      setSaving(false);
    }
  };

  // Audit Logs refresh
  const handleRefreshAuditLogs = async () => {
    setLoading(true);
    try {
      const res = await adminAPI.getAuditLogs(activeToken, { limit: 100 });
      setAuditLogs(res.items || []);
      setTotalAuditLogs(res.total || (res.items || []).length);
      showToast('Access audit logs refreshed.', 'success');
    } catch (err) {
      showToast(err.message || 'Failed to refresh audit logs.', 'error');
    } finally {
      setLoading(false);
    }
  };

  // Documents actions
  const handleRefreshDocuments = async () => {
    setLoading(true);
    try {
      const res = await adminAPI.getDocuments(activeToken);
      setDocuments(res.documents || []);
      setTotalDocuments(res.total_documents || (res.documents || []).length);
      showToast('Knowledge base index refreshed.', 'success');
    } catch (err) {
      showToast(err.message || 'Failed to refresh documents.', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleUploadDocument = async (file) => {
    setUploadingDoc(true);
    try {
      const res = await adminAPI.uploadDocument(activeToken, file);
      showToast(res.message || 'Document indexed into FAISS successfully.', 'success');
      await handleRefreshDocuments();
    } catch (err) {
      showToast(err.message || 'Failed to upload document.', 'error');
      throw err;
    } finally {
      setUploadingDoc(false);
    }
  };

  const handleDeleteDocument = async (documentName) => {
    setDeletingDoc(true);
    try {
      const res = await adminAPI.deleteDocument(activeToken, documentName);
      showToast(res.message || 'Document purged from FAISS store.', 'success');
      await handleRefreshDocuments();
    } catch (err) {
      showToast(err.message || 'Failed to delete document.', 'error');
    } finally {
      setDeletingDoc(false);
    }
  };

  // Unauthenticated login view
  if (!isAuthorized) {
    return (
      <main className="flex-1 overflow-y-auto px-4 py-12 flex items-center justify-center min-h-[85vh]">
        <div className="w-full max-w-md rounded-3xl border border-purple-500/30 bg-slate-900/90 p-8 shadow-2xl backdrop-blur-xl">
          <div className="mb-6 flex flex-col items-center text-center">
            <div className="h-16 w-16 rounded-2xl bg-gradient-to-tr from-purple-600 via-pink-600 to-amber-500 flex items-center justify-center text-white shadow-xl shadow-purple-500/25 mb-4">
              <ShieldCheck className="h-8 w-8" />
            </div>
            <h1 className="text-2xl font-black text-white">BUP Admin Console</h1>
            <p className="text-xs text-purple-200/70 mt-1 max-w-xs">
              Enter your administrative credentials to access student well-being triage, compliance, and academic records.
            </p>
          </div>

          <form onSubmit={handleLoginSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-purple-200 mb-1.5">Admin Email</label>
              <div className="relative">
                <Mail className="absolute left-3.5 top-3 h-4 w-4 text-purple-300/50" />
                <input
                  type="email"
                  value={adminEmail}
                  onChange={(e) => setAdminEmail(e.target.value)}
                  className="w-full rounded-xl border border-purple-500/30 bg-slate-800/80 py-2.5 pl-10 pr-4 text-xs text-white placeholder-purple-300/40 focus:border-purple-400 focus:outline-none"
                  placeholder="admin@bup.edu.bd"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-purple-200 mb-1.5">Password</label>
              <div className="relative">
                <Lock className="absolute left-3.5 top-3 h-4 w-4 text-purple-300/50" />
                <input
                  type="password"
                  value={adminPassword}
                  onChange={(e) => setAdminPassword(e.target.value)}
                  className="w-full rounded-xl border border-purple-500/30 bg-slate-800/80 py-2.5 pl-10 pr-4 text-xs text-white placeholder-purple-300/40 focus:border-purple-400 focus:outline-none"
                  placeholder="••••••••••••"
                  required
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full mt-2 flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-purple-600 to-pink-600 py-3 text-xs font-bold text-white shadow-lg shadow-purple-600/30 hover:from-purple-500 hover:to-pink-500 transition-all disabled:opacity-50"
            >
              {loading ? (
                <>
                  <RefreshCw className="h-4 w-4 animate-spin" />
                  <span>Signing In...</span>
                </>
              ) : (
                <>
                  <ShieldCheck className="h-4 w-4" />
                  <span>Authenticate to Console</span>
                </>
              )}
            </button>
          </form>

          {onBackToChat && (
            <div className="mt-6 text-center">
              <button
                type="button"
                onClick={onBackToChat}
                className="text-xs text-purple-300/70 hover:text-white underline transition-colors"
              >
                Return to Student Chat Assistant
              </button>
            </div>
          )}
        </div>
      </main>
    );
  }

  return (
    <main className="flex-1 overflow-y-auto px-4 sm:px-6 py-6 max-w-7xl mx-auto space-y-6">
      {/* Toast Notification */}
      {toast.show && (
        <div
          className={`fixed bottom-6 right-6 z-50 flex items-center gap-2 rounded-2xl border px-4 py-3 text-xs font-semibold shadow-2xl backdrop-blur-md transition-all animate-bounce ${
            toast.type === 'error'
              ? 'border-red-500/40 bg-red-950/90 text-red-200 shadow-red-500/20'
              : 'border-emerald-500/40 bg-emerald-950/90 text-emerald-200 shadow-emerald-500/20'
          }`}
        >
          {toast.type === 'error' ? (
            <AlertTriangle className="h-4 w-4 text-red-400" />
          ) : (
            <CheckCircle2 className="h-4 w-4 text-emerald-400" />
          )}
          <span>{toast.message}</span>
          <button
            onClick={() => setToast((t) => ({ ...t, show: false }))}
            className="ml-2 rounded p-1 hover:bg-white/10"
          >
            <X className="h-3 w-3" />
          </button>
        </div>
      )}

      {/* Header */}
      <AdminHeader
        loading={loading}
        criticalNewCount={criticalNewCount}
        onRefresh={() => loadDashboard()}
        onLogout={handleLogout}
        onBackToChat={onBackToChat}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
      />

      {/* Segmented Navigation Tabs */}
      <nav className="flex flex-wrap items-center gap-2 rounded-2xl border border-purple-500/20 bg-slate-900/70 p-1.5 shadow-lg backdrop-blur-md">
        <button
          onClick={() => setActiveTab('overview')}
          className={`flex items-center gap-2 rounded-xl px-4 py-2 text-xs font-semibold transition-all cursor-pointer ${
            activeTab === 'overview'
              ? 'bg-gradient-to-r from-purple-600 to-pink-600 text-white shadow-md shadow-purple-600/30 font-bold'
              : 'text-purple-300/70 hover:text-white hover:bg-slate-800/60'
          }`}
        >
          <Activity className="h-4 w-4" />
          <span>Executive Overview</span>
        </button>

        <button
          onClick={() => setActiveTab('alerts')}
          className={`flex items-center gap-2 rounded-xl px-4 py-2 text-xs font-semibold transition-all cursor-pointer ${
            activeTab === 'alerts'
              ? 'bg-gradient-to-r from-purple-600 to-pink-600 text-white shadow-md shadow-purple-600/30 font-bold'
              : 'text-purple-300/70 hover:text-white hover:bg-slate-800/60'
          }`}
        >
          <ShieldAlert className="h-4 w-4" />
          <span>Mental Health Triage</span>
          {unresolvedAlertsCount > 0 && (
            <span
              className={`rounded-full px-2 py-0.2 text-[10px] font-bold ${
                criticalNewCount > 0
                  ? 'bg-red-500 text-white animate-pulse'
                  : 'bg-purple-500/40 text-purple-200'
              }`}
            >
              {unresolvedAlertsCount}
            </span>
          )}
        </button>

        <button
          onClick={() => setActiveTab('students')}
          className={`flex items-center gap-2 rounded-xl px-4 py-2 text-xs font-semibold transition-all cursor-pointer ${
            activeTab === 'students'
              ? 'bg-gradient-to-r from-purple-600 to-pink-600 text-white shadow-md shadow-purple-600/30 font-bold'
              : 'text-purple-300/70 hover:text-white hover:bg-slate-800/60'
          }`}
        >
          <Users className="h-4 w-4" />
          <span>Student Directory</span>
          <span className="rounded-full bg-slate-800 px-2 py-0.2 text-[10px] text-purple-300/70">
            {students.length}
          </span>
        </button>

        <button
          onClick={() => setActiveTab('records')}
          className={`flex items-center gap-2 rounded-xl px-4 py-2 text-xs font-semibold transition-all cursor-pointer ${
            activeTab === 'records'
              ? 'bg-gradient-to-r from-purple-600 to-pink-600 text-white shadow-md shadow-purple-600/30 font-bold'
              : 'text-purple-300/70 hover:text-white hover:bg-slate-800/60'
          }`}
        >
          <GraduationCap className="h-4 w-4" />
          <span>Academic & Billing Records</span>
        </button>

        <button
          onClick={() => setActiveTab('audits')}
          className={`flex items-center gap-2 rounded-xl px-4 py-2 text-xs font-semibold transition-all cursor-pointer ${
            activeTab === 'audits'
              ? 'bg-gradient-to-r from-purple-600 to-pink-600 text-white shadow-md shadow-purple-600/30 font-bold'
              : 'text-purple-300/70 hover:text-white hover:bg-slate-800/60'
          }`}
        >
          <ShieldCheck className="h-4 w-4" />
          <span>FERPA Audit Trail</span>
          <span className="rounded-full bg-slate-800 px-2 py-0.2 text-[10px] text-purple-300/70">
            {totalAuditLogs}
          </span>
        </button>

        <button
          onClick={() => setActiveTab('documents')}
          className={`flex items-center gap-2 rounded-xl px-4 py-2 text-xs font-semibold transition-all cursor-pointer ${
            activeTab === 'documents'
              ? 'bg-gradient-to-r from-purple-600 to-pink-600 text-white shadow-md shadow-purple-600/30 font-bold'
              : 'text-purple-300/70 hover:text-white hover:bg-slate-800/60'
          }`}
        >
          <Database className="h-4 w-4" />
          <span>Knowledge Base</span>
          <span className="rounded-full bg-slate-800 px-2 py-0.2 text-[10px] text-purple-300/70">
            {totalDocuments}
          </span>
        </button>
      </nav>

      {/* Tab Panels */}
      {activeTab === 'overview' && (
        <OverviewTab
          summary={summary}
          students={students}
          alerts={alerts}
          auditLogsCount={totalAuditLogs}
          documentsCount={totalDocuments}
          criticalNewCount={criticalNewCount}
          setActiveTab={setActiveTab}
          onSelectAlert={(alert) => {
            handleSelectAlert(alert);
            setActiveTab('alerts');
          }}
        />
      )}

      {activeTab === 'alerts' && (
        <AlertsTab
          alerts={alerts}
          selectedAlert={selectedAlert}
          noteDraft={noteDraft}
          saving={saving}
          onSelectAlert={handleSelectAlert}
          onCloseAlert={handleCloseAlertDrawer}
          onNoteDraftChange={setNoteDraft}
          onUpdateAlert={handleUpdateAlert}
          onDeleteAlert={handleDeleteAlert}
          onClearAlerts={handleClearAlerts}
          onLoadStudentProfile={handleLoadStudentProfile}
        />
      )}

      {activeTab === 'students' && (
        <StudentsTab
          students={students}
          saving={saving}
          onSaveStudent={handleSaveStudent}
          onDeleteStudent={handleDeleteStudent}
          onLoadStudentMentalHealth={handleLoadStudentProfile}
          onLoadStudentRecords={handleEditStudentRecordsFromDirectory}
          studentDetail={studentDetail}
          onCloseStudentDetail={() => setStudentDetail(null)}
        />
      )}

      {activeTab === 'records' && (
        <RecordsTab
          students={students}
          selectedStudent={selectedRecordStudent}
          onSelectStudent={handleSelectRecordStudent}
          recordData={recordData}
          onSaveRecords={handleSaveRecords}
          isSaving={saving}
          isLoading={loading}
        />
      )}

      {activeTab === 'audits' && (
        <AuditLogsTab
          logs={auditLogs}
          totalLogs={totalAuditLogs}
          onRefresh={handleRefreshAuditLogs}
          isLoading={loading}
          onViewStudentProfile={handleLoadStudentProfile}
        />
      )}

      {activeTab === 'documents' && (
        <DocumentsTab
          documents={documents}
          totalDocuments={totalDocuments}
          onRefresh={handleRefreshDocuments}
          onUploadDocument={handleUploadDocument}
          onDeleteDocument={handleDeleteDocument}
          isLoading={loading}
          isUploading={uploadingDoc}
          isDeleting={deletingDoc}
        />
      )}
    </main>
  );
}
