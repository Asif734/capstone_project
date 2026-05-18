import React, { useMemo, useState } from 'react';
import {
  AlertTriangle,
  CheckCircle2,
  ClipboardList,
  Eye,
  Plus,
  RefreshCw,
  ShieldCheck,
  UserPlus,
} from 'lucide-react';
import { adminAPI } from '../../services/api';

const blankStudentForm = {
  reg_id: '',
  name: '',
  email: '',
  department: '',
  year: '',
  semester: '',
  status: 'active',
};

const severityOrder = {
  critical: 0,
  high: 1,
  moderate: 2,
  low: 3,
};

const statusOptions = ['new', 'reviewed', 'contacted', 'closed'];

const severityClasses = {
  critical: 'border-red-400/60 bg-red-500/20 text-red-100',
  high: 'border-orange-400/60 bg-orange-500/20 text-orange-100',
  moderate: 'border-yellow-400/60 bg-yellow-500/20 text-yellow-100',
  low: 'border-emerald-400/60 bg-emerald-500/20 text-emerald-100',
};

const sortAlerts = (items = []) => {
  return [...items].sort((a, b) => {
    const severityDiff =
      (severityOrder[a.severity] ?? 99) - (severityOrder[b.severity] ?? 99);
    if (severityDiff !== 0) return severityDiff;
    return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
  });
};

const formatDate = (value) => {
  if (!value) return 'N/A';
  return new Date(value).toLocaleString();
};

const formatConfidence = (value) => {
  if (value === null || value === undefined) return 'N/A';
  return `${Math.round(value * 100)}%`;
};

const AdminDashboard = ({ isAdminAuthenticated, onAdminAuth, onAdminLogout }) => {
  const [adminEmail, setAdminEmail] = useState('');
  const [adminPassword, setAdminPassword] = useState('');
  const [activeToken, setActiveToken] = useState('');
  const [isAuthorized, setIsAuthorized] = useState(false);
  const [activeTab, setActiveTab] = useState('alerts');
  const [summary, setSummary] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [students, setStudents] = useState([]);
  const [selectedAlert, setSelectedAlert] = useState(null);
  const [noteDraft, setNoteDraft] = useState('');
  const [studentForm, setStudentForm] = useState(blankStudentForm);
  const [editingStudent, setEditingStudent] = useState(null);
  const [studentDetail, setStudentDetail] = useState(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const criticalNewCount = useMemo(() => {
    return alerts.filter(
      (alert) => alert.severity === 'critical' && alert.status === 'new'
    ).length;
  }, [alerts]);

  const loadDashboard = async (tokenToUse = activeToken) => {
    let token = tokenToUse;
    if (!token && (!adminEmail.trim() || !adminPassword)) {
      setError('Enter the admin email and password.');
      return;
    }

    setLoading(true);
    setError('');
    setSuccess('');
    try {
      if (!token) {
        const loginResponse = await adminAPI.login(adminEmail.trim(), adminPassword);
        token = loginResponse.access_token;
      }

      if (!token?.trim()) {
        throw new Error('Invalid admin login response.');
      }

      const [summaryData, alertData, studentData] = await Promise.all([
        adminAPI.getSummary(token),
        adminAPI.getAlerts(token),
        adminAPI.getStudents(token),
      ]);

      setSummary(summaryData);
      setAlerts(sortAlerts(alertData));
      setStudents(studentData);
      setActiveToken(token);
      setIsAuthorized(true);
      if (onAdminAuth) onAdminAuth();
    } catch (err) {
      setIsAuthorized(false);
      setError(err.message || 'Unable to load admin dashboard.');
      setActiveToken('');
    } finally {
      setLoading(false);
    }
  };

  const handleLoginSubmit = (event) => {
    event.preventDefault();
    loadDashboard();
  };

  const selectAlert = (alert) => {
    setSelectedAlert(alert);
    setNoteDraft(alert.admin_notes || '');
  };

  const refreshSelectedAlert = (updatedAlert) => {
    setSelectedAlert(updatedAlert);
    setNoteDraft(updatedAlert.admin_notes || '');
    setAlerts((current) =>
      sortAlerts(current.map((alert) => (alert.id === updatedAlert.id ? updatedAlert : alert)))
    );
  };

  const updateSelectedAlert = async (status = selectedAlert?.status) => {
    if (!selectedAlert) return;

    setSaving(true);
    setError('');
    setSuccess('');
    try {
      const updatedAlert = await adminAPI.updateAlert(activeToken, selectedAlert.id, {
        status,
        admin_notes: noteDraft,
      });
      refreshSelectedAlert(updatedAlert);
      setSuccess('Alert updated.');
    } catch (err) {
      setError(err.message || 'Unable to update alert.');
    } finally {
      setSaving(false);
    }
  };

  const handleStudentFormChange = (event) => {
    const { name, value } = event.target;
    setStudentForm((current) => ({ ...current, [name]: value }));
  };

  const resetStudentForm = () => {
    setStudentForm(blankStudentForm);
    setEditingStudent(null);
  };

  const handleSaveStudent = async (event) => {
    event.preventDefault();
    setSaving(true);
    setError('');
    setSuccess('');

    const payload = {
      reg_id: studentForm.reg_id,
      name: studentForm.name,
      email: studentForm.email,
      department: studentForm.department || null,
      year: studentForm.year ? Number(studentForm.year) : null,
      semester: studentForm.semester ? Number(studentForm.semester) : null,
      status: studentForm.status || 'active',
    };

    try {
      if (editingStudent) {
        const updated = await adminAPI.updateStudent(activeToken, editingStudent.id, payload);
        setStudents((current) =>
          current
            .map((student) => (student.id === updated.id ? updated : student))
            .sort((a, b) => a.reg_id.localeCompare(b.reg_id))
        );
        setSuccess('Student updated.');
      } else {
        const created = await adminAPI.addStudent(activeToken, payload);
        setStudents((current) =>
          [...current, created].sort((a, b) => a.reg_id.localeCompare(b.reg_id))
        );
        setSuccess('Authorized student added.');
      }
      resetStudentForm();
    } catch (err) {
      setError(err.message || 'Unable to save student.');
    } finally {
      setSaving(false);
    }
  };

  const handleEditStudent = (student) => {
    setEditingStudent(student);
    setStudentForm({
      reg_id: student.reg_id || '',
      name: student.name || '',
      email: student.email || '',
      department: student.department || '',
      year: student.year ?? '',
      semester: student.semester ?? '',
      status: student.status || 'active',
    });
  };

  const handleDeleteStudent = async (student) => {
    if (!window.confirm(`Delete ${student.name || student.reg_id}? This cannot be undone.`)) {
      return;
    }

    setSaving(true);
    setError('');
    setSuccess('');
    try {
      await adminAPI.deleteStudent(activeToken, student.id);
      setStudents((current) => current.filter((item) => item.id !== student.id));
      if (editingStudent?.id === student.id) {
        resetStudentForm();
      }
      if (studentDetail?.student?.reg_id === student.reg_id) {
        setStudentDetail(null);
      }
      setSuccess('Student removed.');
    } catch (err) {
      setError(err.message || 'Unable to remove student.');
    } finally {
      setSaving(false);
    }
  };

  const handleAdminLogout = () => {
    setActiveToken('');
    setIsAuthorized(false);
    setAdminEmail('');
    setAdminPassword('');
    setSummary(null);
    setAlerts([]);
    setStudents([]);
    setSelectedAlert(null);
    setNoteDraft('');
    setStudentDetail(null);
    resetStudentForm();
    if (onAdminLogout) onAdminLogout();
  };

  const loadStudentMentalHealth = async (regId) => {
    setLoading(true);
    setError('');
    setSuccess('');
    try {
      const detail = await adminAPI.getStudentMentalHealth(activeToken, regId);
      setStudentDetail({
        ...detail,
        alerts: sortAlerts(detail.alerts),
      });
      setActiveTab('students');
    } catch (err) {
      setError(err.message || 'Unable to load student mental-health profile.');
    } finally {
      setLoading(false);
    }
  };

  if (!isAuthorized) {
    return (
      <main className="flex-1 overflow-y-auto px-4 py-10">
        <div className="mx-auto max-w-md rounded-2xl border border-purple-500/30 bg-slate-800/80 p-8 shadow-2xl">
          <div className="mb-6 flex items-center space-x-3">
            <div className="rounded-xl bg-purple-500/20 p-3 text-purple-200">
              <ShieldCheck className="h-6 w-6" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-white">Admin Dashboard</h1>
              <p className="text-sm text-purple-200">Enter the admin email and password.</p>
            </div>
          </div>

          {error && (
            <div className="mb-4 rounded-lg border border-red-400/40 bg-red-500/10 px-3 py-2 text-sm text-red-200">
              {error}
            </div>
          )}

          <form onSubmit={handleLoginSubmit} className="space-y-4">
            <input
              type="email"
              value={adminEmail}
              onChange={(event) => setAdminEmail(event.target.value)}
              className="w-full rounded-lg border border-purple-500/30 bg-slate-700 px-4 py-3 text-white placeholder-purple-300/50 focus:border-purple-500 focus:outline-none"
              placeholder="Admin email"
            />
            <input
              type="password"
              value={adminPassword}
              onChange={(event) => setAdminPassword(event.target.value)}
              className="w-full rounded-lg border border-purple-500/30 bg-slate-700 px-4 py-3 text-white placeholder-purple-300/50 focus:border-purple-500 focus:outline-none"
              placeholder="Password"
            />
            <button
              type="submit"
              disabled={loading}
              className="flex w-full items-center justify-center space-x-2 rounded-lg bg-gradient-to-r from-purple-500 to-pink-500 px-4 py-3 font-medium text-white transition-all hover:from-purple-600 hover:to-pink-600 disabled:cursor-not-allowed disabled:opacity-60"
            >
              <ShieldCheck className="h-4 w-4" />
              <span>{loading ? 'Loading...' : 'Open Dashboard'}</span>
            </button>
          </form>
        </div>
      </main>
    );
  }

  return (
    <main className="flex-1 overflow-y-auto px-4 py-6">
      <div className="mx-auto max-w-7xl space-y-5">
        <section className="rounded-xl border border-purple-500/20 bg-slate-800/70 p-5 shadow-xl">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <div className="flex items-center space-x-3">
                <ShieldCheck className="h-6 w-6 text-purple-200" />
                <h1 className="text-2xl font-bold text-white">Admin Dashboard</h1>
              </div>
              <p className="mt-1 text-sm text-purple-200">
                New critical alerts are surfaced first for review.
              </p>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={() => loadDashboard(activeToken)}
                disabled={loading}
                className="flex items-center justify-center space-x-2 rounded-lg border border-purple-500/30 px-4 py-2 text-purple-100 transition-colors hover:bg-purple-500/10 disabled:opacity-60"
              >
                <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
                <span>Refresh</span>
              </button>
              <button
                onClick={handleAdminLogout}
                disabled={loading}
                className="flex items-center justify-center space-x-2 rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-2 text-red-200 hover:bg-red-500/20 disabled:opacity-60"
              >
                <span>Logout</span>
              </button>
            </div>
          </div>

          <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-6">
            {[
              ['New Critical', criticalNewCount],
              ['Total Alerts', summary?.total_alerts ?? 0],
              ['New', summary?.new_alerts ?? 0],
              ['Critical', summary?.critical_alerts ?? 0],
              ['High', summary?.high_alerts ?? 0],
              ['Moderate', summary?.moderate_alerts ?? 0],
            ].map(([label, value]) => (
              <div key={label} className="rounded-lg border border-slate-600/70 bg-slate-900/50 p-3">
                <p className="text-xs uppercase tracking-wide text-purple-200/70">{label}</p>
                <p className="mt-1 text-2xl font-bold text-white">{value}</p>
              </div>
            ))}
          </div>
        </section>

        {(error || success) && (
          <div
            className={`rounded-lg border px-4 py-3 text-sm ${
              error
                ? 'border-red-400/40 bg-red-500/10 text-red-200'
                : 'border-emerald-400/40 bg-emerald-500/10 text-emerald-200'
            }`}
          >
            {error || success}
          </div>
        )}

        <div className="flex rounded-xl border border-purple-500/20 bg-slate-800/60 p-1">
          {[
            ['alerts', 'Alerts', AlertTriangle],
            ['students', 'Authorized Students', UserPlus],
          ].map(([key, label, Icon]) => (
            <button
              key={key}
              onClick={() => setActiveTab(key)}
              className={`flex flex-1 items-center justify-center space-x-2 rounded-lg px-4 py-2 text-sm font-medium transition-colors ${
                activeTab === key
                  ? 'bg-purple-500 text-white'
                  : 'text-purple-200 hover:bg-purple-500/10 hover:text-white'
              }`}
            >
              <Icon className="h-4 w-4" />
              <span>{label}</span>
            </button>
          ))}
        </div>

        {activeTab === 'alerts' ? (
          <section className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_360px]">
            <div className="overflow-hidden rounded-xl border border-purple-500/20 bg-slate-800/70">
              <div className="border-b border-purple-500/20 px-4 py-3">
                <h2 className="font-semibold text-white">Risk Alerts</h2>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full min-w-[860px] text-left text-sm">
                  <thead className="bg-slate-900/60 text-xs uppercase text-purple-200/70">
                    <tr>
                      <th className="px-4 py-3">Severity</th>
                      <th className="px-4 py-3">Student</th>
                      <th className="px-4 py-3">Signal</th>
                      <th className="px-4 py-3">Score</th>
                      <th className="px-4 py-3">Status</th>
                      <th className="px-4 py-3">Created</th>
                      <th className="px-4 py-3">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-700/80">
                    {alerts.length === 0 ? (
                      <tr>
                        <td className="px-4 py-6 text-center text-purple-200" colSpan="7">
                          No mental-health alerts yet.
                        </td>
                      </tr>
                    ) : (
                      alerts.map((alert) => (
                        <tr key={alert.id} className="text-slate-100 hover:bg-slate-700/40">
                          <td className="px-4 py-3">
                            <span
                              className={`rounded-full border px-3 py-1 text-xs font-semibold capitalize ${
                                severityClasses[alert.severity] || 'border-slate-500 bg-slate-700'
                              }`}
                            >
                              {alert.severity}
                            </span>
                          </td>
                          <td className="px-4 py-3">
                            <div className="font-medium text-white">
                              {alert.student_name || alert.reg_id || 'Unknown'}
                            </div>
                            <div className="text-xs text-purple-200/70">
                              {alert.reg_id} {alert.student_email ? `- ${alert.student_email}` : ''}
                            </div>
                          </td>
                          <td className="px-4 py-3">
                            <div>{alert.predicted_class || 'Risk signal'}</div>
                            <div className="text-xs text-purple-200/70">
                              Confidence {formatConfidence(alert.confidence)}
                            </div>
                          </td>
                          <td className="px-4 py-3">{alert.score}</td>
                          <td className="px-4 py-3 capitalize">{alert.status}</td>
                          <td className="px-4 py-3">{formatDate(alert.created_at)}</td>
                          <td className="px-4 py-3">
                            <button
                              onClick={() => selectAlert(alert)}
                              className="inline-flex items-center space-x-1 rounded-lg border border-purple-500/30 px-3 py-1.5 text-purple-100 hover:bg-purple-500/10"
                            >
                              <Eye className="h-4 w-4" />
                              <span>Review</span>
                            </button>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            <aside className="rounded-xl border border-purple-500/20 bg-slate-800/70 p-4">
              {selectedAlert ? (
                <div className="space-y-4">
                  <div>
                    <p className="text-xs uppercase tracking-wide text-purple-200/70">Selected Alert</p>
                    <h3 className="mt-1 text-lg font-bold text-white">
                      {selectedAlert.student_name || selectedAlert.reg_id || 'Student'}
                    </h3>
                    <p className="text-sm text-purple-200">{selectedAlert.reg_id}</p>
                  </div>

                  <div className="rounded-lg bg-slate-900/50 p-3 text-sm text-slate-100">
                    <p className="mb-2 text-xs uppercase tracking-wide text-purple-200/70">
                      Latest flagged message
                    </p>
                    <p>{selectedAlert.question_sample || 'No sample stored.'}</p>
                  </div>

                  <div>
                    <label className="mb-2 block text-sm font-medium text-purple-200">
                      Status
                    </label>
                    <select
                      value={selectedAlert.status}
                      onChange={(event) => updateSelectedAlert(event.target.value)}
                      disabled={saving}
                      className="w-full rounded-lg border border-purple-500/30 bg-slate-700 px-3 py-2 text-white focus:border-purple-500 focus:outline-none"
                    >
                      {statusOptions.map((statusValue) => (
                        <option key={statusValue} value={statusValue}>
                          {statusValue}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="mb-2 block text-sm font-medium text-purple-200">
                      Admin notes
                    </label>
                    <textarea
                      value={noteDraft}
                      onChange={(event) => setNoteDraft(event.target.value)}
                      rows="5"
                      className="w-full rounded-lg border border-purple-500/30 bg-slate-700 px-3 py-2 text-white placeholder-purple-300/50 focus:border-purple-500 focus:outline-none"
                      placeholder="Add review notes or next steps"
                    />
                  </div>

                  <button
                    onClick={() => updateSelectedAlert()}
                    disabled={saving}
                    className="flex w-full items-center justify-center space-x-2 rounded-lg bg-purple-500 px-4 py-2 font-medium text-white hover:bg-purple-600 disabled:opacity-60"
                  >
                    <CheckCircle2 className="h-4 w-4" />
                    <span>{saving ? 'Saving...' : 'Save Review'}</span>
                  </button>

                  {selectedAlert.reg_id && (
                    <button
                      onClick={() => loadStudentMentalHealth(selectedAlert.reg_id)}
                      className="flex w-full items-center justify-center space-x-2 rounded-lg border border-purple-500/30 px-4 py-2 text-purple-100 hover:bg-purple-500/10"
                    >
                      <ClipboardList className="h-4 w-4" />
                      <span>Student Profile</span>
                    </button>
                  )}
                </div>
              ) : (
                <div className="flex h-full min-h-[280px] flex-col items-center justify-center text-center text-purple-200">
                  <AlertTriangle className="mb-3 h-8 w-8" />
                  <p>Select an alert to review the risk signal.</p>
                </div>
              )}
            </aside>
          </section>
        ) : (
          <section className="grid gap-5 lg:grid-cols-[380px_minmax(0,1fr)]">
            <form
              onSubmit={handleSaveStudent}
              className="rounded-xl border border-purple-500/20 bg-slate-800/70 p-4"
            >
              <div className="mb-4 flex items-center space-x-2 text-white">
                <Plus className="h-5 w-5 text-purple-200" />
                <h2 className="font-semibold">{editingStudent ? 'Edit Authorized Student' : 'Add Authorized Student'}</h2>
              </div>

              <div className="space-y-3">
                {[
                  ['name', 'Name', 'Student name'],
                  ['reg_id', 'Student ID', 'Registration ID'],
                  ['email', 'Email', 'student@email.com'],
                  ['department', 'Department', 'Department'],
                  ['year', 'Year', '1'],
                  ['semester', 'Semester', '1'],
                ].map(([name, label, placeholder]) => (
                  <div key={name}>
                    <label className="mb-1 block text-sm text-purple-200">{label}</label>
                    <input
                      name={name}
                      type={name === 'email' ? 'email' : name === 'year' || name === 'semester' ? 'number' : 'text'}
                      value={studentForm[name]}
                      onChange={handleStudentFormChange}
                      required={['name', 'reg_id', 'email'].includes(name)}
                      className="w-full rounded-lg border border-purple-500/30 bg-slate-700 px-3 py-2 text-white placeholder-purple-300/50 focus:border-purple-500 focus:outline-none"
                      placeholder={placeholder}
                    />
                  </div>
                ))}
                <div>
                  <label className="mb-1 block text-sm text-purple-200">Status</label>
                  <select
                    name="status"
                    value={studentForm.status}
                    onChange={handleStudentFormChange}
                    className="w-full rounded-lg border border-purple-500/30 bg-slate-700 px-3 py-2 text-white focus:border-purple-500 focus:outline-none"
                  >
                    {['active', 'graduated', 'inactive'].map((statusOption) => (
                      <option key={statusOption} value={statusOption}>
                        {statusOption}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="mt-4 flex flex-col gap-3">
                <button
                  type="submit"
                  disabled={saving}
                  className="flex w-full items-center justify-center space-x-2 rounded-lg bg-gradient-to-r from-purple-500 to-pink-500 px-4 py-3 font-medium text-white hover:from-purple-600 hover:to-pink-600 disabled:opacity-60"
                >
                  <UserPlus className="h-4 w-4" />
                  <span>{saving ? (editingStudent ? 'Saving...' : 'Adding...') : editingStudent ? 'Save Student' : 'Add Student'}</span>
                </button>
                {editingStudent && (
                  <button
                    type="button"
                    disabled={saving}
                    onClick={resetStudentForm}
                    className="flex w-full items-center justify-center space-x-2 rounded-lg border border-purple-500/30 px-4 py-3 text-purple-100 hover:bg-purple-500/10 disabled:opacity-60"
                  >
                    <RefreshCw className="h-4 w-4" />
                    <span>Cancel Edit</span>
                  </button>
                )}
              </div>
            </form>

            <div className="space-y-5">
              <div className="overflow-hidden rounded-xl border border-purple-500/20 bg-slate-800/70">
                <div className="border-b border-purple-500/20 px-4 py-3">
                  <h2 className="font-semibold text-white">Authorized Students</h2>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full min-w-[820px] text-left text-sm">
                    <thead className="bg-slate-900/60 text-xs uppercase text-purple-200/70">
                      <tr>
                        <th className="px-4 py-3">Student</th>
                        <th className="px-4 py-3">Email</th>
                        <th className="px-4 py-3">Department</th>
                        <th className="px-4 py-3">Semester</th>
                        <th className="px-4 py-3">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-700/80">
                      {students.map((student) => (
                        <tr key={student.id} className="text-slate-100 hover:bg-slate-700/40">
                          <td className="px-4 py-3">
                            <div className="font-medium text-white">{student.name || student.reg_id}</div>
                            <div className="text-xs text-purple-200/70">{student.reg_id}</div>
                          </td>
                          <td className="px-4 py-3">{student.email}</td>
                          <td className="px-4 py-3">{student.department || 'N/A'}</td>
                          <td className="px-4 py-3">{student.semester ? `Semester ${student.semester}` : 'N/A'}</td>
                          <td className="px-4 py-3">
                            <div className="flex flex-col gap-2 sm:flex-row">
                              <button
                                onClick={() => handleEditStudent(student)}
                                className="inline-flex items-center justify-center rounded-lg border border-purple-500/30 px-3 py-1.5 text-purple-100 hover:bg-purple-500/10"
                              >
                                <span>Edit</span>
                              </button>
                              <button
                                onClick={() => handleDeleteStudent(student)}
                                disabled={saving}
                                className="inline-flex items-center justify-center rounded-lg border border-red-400/40 bg-red-500/10 px-3 py-1.5 text-red-200 hover:bg-red-500/20 disabled:opacity-60"
                              >
                                <span>Remove</span>
                              </button>
                              <button
                                onClick={() => loadStudentMentalHealth(student.reg_id)}
                                className="inline-flex items-center justify-center rounded-lg border border-purple-500/30 px-3 py-1.5 text-purple-100 hover:bg-purple-500/10"
                              >
                                <Eye className="h-4 w-4" />
                                <span>Profile</span>
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {studentDetail && (
                <div className="rounded-xl border border-purple-500/20 bg-slate-800/70 p-4">
                  <div className="mb-4">
                    <p className="text-xs uppercase tracking-wide text-purple-200/70">
                      Student Mental-Health Profile
                    </p>
                    <h3 className="mt-1 text-lg font-bold text-white">
                      {studentDetail.student.name || studentDetail.student.reg_id}
                    </h3>
                    <p className="text-sm text-purple-200">
                      {studentDetail.student.reg_id} - {studentDetail.student.email}
                    </p>
                  </div>

                  {studentDetail.alerts.length === 0 ? (
                    <p className="rounded-lg bg-slate-900/50 p-3 text-purple-200">
                      No mental-health alerts recorded for this student.
                    </p>
                  ) : (
                    <div className="space-y-3">
                      {studentDetail.alerts.map((alert) => (
                        <div key={alert.id} className="rounded-lg border border-slate-600/70 bg-slate-900/50 p-3">
                          <div className="flex flex-wrap items-center gap-2">
                            <span
                              className={`rounded-full border px-3 py-1 text-xs font-semibold capitalize ${
                                severityClasses[alert.severity] || 'border-slate-500 bg-slate-700 text-white'
                              }`}
                            >
                              {alert.severity}
                            </span>
                            <span className="text-sm text-purple-200">
                              {alert.predicted_class || 'Risk signal'} - {formatDate(alert.created_at)}
                            </span>
                          </div>
                          <p className="mt-2 text-sm text-slate-100">
                            {alert.question_sample || 'No sample stored.'}
                          </p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          </section>
        )}
      </div>
    </main>
  );
};

export default AdminDashboard;
