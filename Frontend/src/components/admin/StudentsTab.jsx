import React, { useState, useMemo } from 'react';
import {
  Users,
  UserPlus,
  Search,
  Filter,
  Eye,
  ClipboardList,
  Edit2,
  Trash2,
  X,
  CheckCircle2,
  School,
  Mail,
  GraduationCap,
  Calendar,
  AlertTriangle,
  Activity,
} from 'lucide-react';

const blankStudentForm = {
  reg_id: '',
  name: '',
  email: '',
  department: '',
  year: '',
  semester: '',
  status: 'active',
};

const StudentsTab = ({
  students = [],
  saving,
  onSaveStudent,
  onDeleteStudent,
  onLoadStudentMentalHealth,
  onLoadStudentRecords,
  studentDetail,
  onCloseStudentDetail,
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [departmentFilter, setDepartmentFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingStudent, setEditingStudent] = useState(null);
  const [studentForm, setStudentForm] = useState(blankStudentForm);

  // Unique departments for filter pills
  const departments = useMemo(() => {
    const set = new Set();
    students.forEach((s) => {
      if (s.department) set.add(s.department);
    });
    return Array.from(set);
  }, [students]);

  // Filtered students
  const filteredStudents = useMemo(() => {
    return students.filter((s) => {
      const q = searchQuery.toLowerCase().trim();
      const matchSearch =
        !q ||
        (s.name || '').toLowerCase().includes(q) ||
        (s.reg_id || '').toLowerCase().includes(q) ||
        (s.email || '').toLowerCase().includes(q);

      const matchDept = departmentFilter === 'all' || s.department === departmentFilter;
      const matchStatus = statusFilter === 'all' || (s.status || 'active') === statusFilter;

      return matchSearch && matchDept && matchStatus;
    });
  }, [students, searchQuery, departmentFilter, statusFilter]);

  const handleOpenAddModal = () => {
    setEditingStudent(null);
    setStudentForm(blankStudentForm);
    setIsModalOpen(true);
  };

  const handleOpenEditModal = (student) => {
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
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setEditingStudent(null);
    setStudentForm(blankStudentForm);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const success = await onSaveStudent(studentForm, editingStudent);
    if (success) {
      handleCloseModal();
    }
  };

  return (
    <div className="space-y-5 animate-fadeIn">
      {/* 1. Control Toolbar */}
      <div className="rounded-2xl border border-slate-700/80 bg-slate-900/80 p-4 shadow-xl backdrop-blur-md flex flex-col md:flex-row gap-3 items-center justify-between">
        {/* Search */}
        <div className="relative w-full md:w-80">
          <Search className="w-4 h-4 text-purple-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search name, student ID, email..."
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

        {/* Department Filters */}
        <div className="flex flex-wrap items-center gap-1.5 w-full md:w-auto">
          <span className="text-xs text-slate-400 font-semibold mr-1 flex items-center space-x-1">
            <Filter className="w-3 h-3 text-cyan-400" />
            <span>Dept:</span>
          </span>
          <button
            type="button"
            onClick={() => setDepartmentFilter('all')}
            className={`px-3 py-1 rounded-xl text-xs font-semibold capitalize transition-all cursor-pointer ${
              departmentFilter === 'all'
                ? 'bg-cyan-600 text-white shadow-md shadow-cyan-500/20'
                : 'bg-slate-800/80 text-slate-300 hover:bg-slate-700 hover:text-white border border-slate-700'
            }`}
          >
            All
          </button>
          {departments.slice(0, 4).map((dept) => (
            <button
              key={dept}
              type="button"
              onClick={() => setDepartmentFilter(dept)}
              className={`px-3 py-1 rounded-xl text-xs font-semibold capitalize transition-all cursor-pointer truncate max-w-[120px] ${
                departmentFilter === dept
                  ? 'bg-cyan-600 text-white shadow-md shadow-cyan-500/20'
                  : 'bg-slate-800/80 text-slate-300 hover:bg-slate-700 hover:text-white border border-slate-700'
              }`}
            >
              {dept}
            </button>
          ))}
        </div>

        {/* Add Student CTA */}
        <button
          type="button"
          onClick={handleOpenAddModal}
          className="w-full md:w-auto flex items-center justify-center space-x-2 rounded-xl bg-gradient-to-r from-purple-600 via-pink-600 to-purple-600 hover:from-purple-500 hover:to-pink-500 px-4 py-2.5 text-xs sm:text-sm font-bold text-white shadow-lg shadow-purple-500/20 transition-all active:scale-95 cursor-pointer"
        >
          <UserPlus className="w-4 h-4" />
          <span>Add Student</span>
        </button>
      </div>

      {/* 2. Students Directory Table */}
      <div className="overflow-hidden rounded-2xl border border-slate-700/80 bg-slate-900/80 shadow-xl backdrop-blur-md">
        <div className="border-b border-slate-800 px-5 py-3.5 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Users className="w-4 h-4 text-cyan-400" />
            <h2 className="font-bold text-white text-sm uppercase tracking-wider">
              Authorized Student Directory ({filteredStudents.length})
            </h2>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full min-w-[840px] text-left text-sm">
            <thead className="bg-slate-950/70 text-[11px] font-bold uppercase tracking-wider text-purple-300/80 border-b border-slate-800">
              <tr>
                <th className="px-5 py-3.5">Student</th>
                <th className="px-5 py-3.5">Registration ID</th>
                <th className="px-5 py-3.5">Email</th>
                <th className="px-5 py-3.5">Department</th>
                <th className="px-5 py-3.5">Level</th>
                <th className="px-5 py-3.5">Status</th>
                <th className="px-5 py-3.5 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/70">
              {filteredStudents.length === 0 ? (
                <tr>
                  <td className="px-5 py-10 text-center text-slate-400" colSpan="7">
                    No students found matching your search.
                  </td>
                </tr>
              ) : (
                filteredStudents.map((student) => (
                  <tr key={student.id} className="hover:bg-slate-800/40 text-slate-200 transition-colors">
                    {/* Student Name */}
                    <td className="px-5 py-4">
                      <div className="flex items-center space-x-3">
                        <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-cyan-600 to-purple-600 flex items-center justify-center text-xs font-bold text-white shadow-md">
                          {(student.name || 'S').charAt(0).toUpperCase()}
                        </div>
                        <span className="font-bold text-white">{student.name || 'Unnamed'}</span>
                      </div>
                    </td>

                    {/* Reg ID */}
                    <td className="px-5 py-4 font-mono text-purple-300 text-xs">
                      {student.reg_id}
                    </td>

                    {/* Email */}
                    <td className="px-5 py-4 text-xs text-slate-300 font-mono">
                      {student.email}
                    </td>

                    {/* Department */}
                    <td className="px-5 py-4">
                      <span className="text-xs px-2.5 py-1 rounded-lg bg-slate-800 border border-slate-700 text-slate-200 font-medium">
                        {student.department || 'N/A'}
                      </span>
                    </td>

                    {/* Year / Semester */}
                    <td className="px-5 py-4 text-xs text-slate-300">
                      {student.semester ? `Semester ${student.semester}` : student.year ? `Year ${student.year}` : 'N/A'}
                    </td>

                    {/* Status */}
                    <td className="px-5 py-4">
                      <span
                        className={`text-[10px] font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full border ${
                          student.status === 'active'
                            ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30'
                            : 'bg-slate-700 text-slate-300 border-slate-600'
                        }`}
                      >
                        {student.status || 'active'}
                      </span>
                    </td>

                    {/* Actions */}
                    <td className="px-5 py-4 text-right">
                      <div className="flex items-center justify-end space-x-1.5">
                        <button
                          type="button"
                          onClick={() => handleOpenEditModal(student)}
                          className="p-1.5 rounded-lg border border-purple-500/30 bg-purple-950/30 text-purple-200 hover:text-white hover:bg-purple-900/50 transition-colors cursor-pointer"
                          title="Edit Student"
                        >
                          <Edit2 className="w-3.5 h-3.5" />
                        </button>
                        <button
                          type="button"
                          onClick={() => onLoadStudentRecords(student.reg_id)}
                          className="p-1.5 rounded-lg border border-cyan-500/30 bg-cyan-950/30 text-cyan-200 hover:text-white hover:bg-cyan-900/50 transition-colors cursor-pointer"
                          title="View Academic & Billing Records"
                        >
                          <ClipboardList className="w-3.5 h-3.5" />
                        </button>
                        <button
                          type="button"
                          onClick={() => onLoadStudentMentalHealth(student.reg_id)}
                          className="p-1.5 rounded-lg border border-pink-500/30 bg-pink-950/30 text-pink-200 hover:text-white hover:bg-pink-900/50 transition-colors cursor-pointer"
                          title="Student 360 Profile"
                        >
                          <Eye className="w-3.5 h-3.5" />
                        </button>
                        <button
                          type="button"
                          onClick={() => onDeleteStudent(student)}
                          className="p-1.5 rounded-lg border border-red-500/30 bg-red-950/30 text-red-200 hover:text-white hover:bg-red-900/50 transition-colors cursor-pointer"
                          title="Delete Student"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* 3. Add / Edit Student Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-fadeIn">
          <div className="w-full max-w-lg rounded-3xl border border-purple-500/30 bg-slate-900 p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center space-x-2.5">
                <div className="p-2 rounded-xl bg-purple-500/20 text-purple-300 border border-purple-500/30">
                  <UserPlus className="w-5 h-5 text-pink-400" />
                </div>
                <h3 className="font-bold text-white text-base">
                  {editingStudent ? 'Edit Authorized Student' : 'Add New Authorized Student'}
                </h3>
              </div>
              <button
                type="button"
                onClick={handleCloseModal}
                className="text-slate-400 hover:text-white cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-3.5">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-purple-200 mb-1">Full Name *</label>
                  <input
                    type="text"
                    required
                    value={studentForm.name}
                    onChange={(e) => setStudentForm({ ...studentForm, name: e.target.value })}
                    placeholder="e.g. A. Asif"
                    className="w-full px-3.5 py-2 rounded-xl border border-purple-500/30 bg-slate-800 text-sm text-white placeholder-slate-500 focus:border-purple-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-purple-200 mb-1">Registration ID *</label>
                  <input
                    type="text"
                    required
                    value={studentForm.reg_id}
                    onChange={(e) => setStudentForm({ ...studentForm, reg_id: e.target.value })}
                    placeholder="e.g. 24525002013"
                    className="w-full px-3.5 py-2 rounded-xl border border-purple-500/30 bg-slate-800 text-sm text-white placeholder-slate-500 focus:border-purple-500 focus:outline-none"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-purple-200 mb-1">Email Address *</label>
                <input
                  type="email"
                  required
                  value={studentForm.email}
                  onChange={(e) => setStudentForm({ ...studentForm, email: e.target.value })}
                  placeholder="student@bup.edu.bd"
                  className="w-full px-3.5 py-2 rounded-xl border border-purple-500/30 bg-slate-800 text-sm text-white placeholder-slate-500 focus:border-purple-500 focus:outline-none"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-purple-200 mb-1">Department</label>
                  <input
                    type="text"
                    value={studentForm.department}
                    onChange={(e) => setStudentForm({ ...studentForm, department: e.target.value })}
                    placeholder="e.g. CSE / FST"
                    className="w-full px-3.5 py-2 rounded-xl border border-purple-500/30 bg-slate-800 text-sm text-white placeholder-slate-500 focus:border-purple-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-purple-200 mb-1">Year</label>
                  <input
                    type="number"
                    value={studentForm.year}
                    onChange={(e) => setStudentForm({ ...studentForm, year: e.target.value })}
                    placeholder="1-4"
                    className="w-full px-3.5 py-2 rounded-xl border border-purple-500/30 bg-slate-800 text-sm text-white placeholder-slate-500 focus:border-purple-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-purple-200 mb-1">Semester</label>
                  <input
                    type="number"
                    value={studentForm.semester}
                    onChange={(e) => setStudentForm({ ...studentForm, semester: e.target.value })}
                    placeholder="1-8"
                    className="w-full px-3.5 py-2 rounded-xl border border-purple-500/30 bg-slate-800 text-sm text-white placeholder-slate-500 focus:border-purple-500 focus:outline-none"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-purple-200 mb-1">Account Status</label>
                <select
                  value={studentForm.status}
                  onChange={(e) => setStudentForm({ ...studentForm, status: e.target.value })}
                  className="w-full px-3.5 py-2 rounded-xl border border-purple-500/30 bg-slate-800 text-sm text-white focus:border-purple-500 focus:outline-none"
                >
                  <option value="active">Active</option>
                  <option value="graduated">Graduated</option>
                  <option value="inactive">Inactive</option>
                </select>
              </div>

              <div className="pt-3 flex items-center justify-end space-x-2.5">
                <button
                  type="button"
                  onClick={handleCloseModal}
                  className="px-4 py-2.5 rounded-xl border border-slate-700 bg-slate-800 text-xs font-semibold text-slate-300 hover:text-white cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={saving}
                  className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500 text-xs font-bold text-white shadow-lg shadow-purple-500/25 transition-all disabled:opacity-60 cursor-pointer"
                >
                  {saving ? 'Saving...' : editingStudent ? 'Update Student' : 'Add Student'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* 4. Student 360° Profile Modal */}
      {studentDetail && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-fadeIn">
          <div className="w-full max-w-2xl rounded-3xl border border-purple-500/30 bg-slate-900 p-6 shadow-2xl space-y-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center space-x-2.5">
                <div className="p-2 rounded-xl bg-pink-500/20 text-pink-300 border border-pink-500/30">
                  <Activity className="w-5 h-5 text-pink-400" />
                </div>
                <div>
                  <h3 className="font-bold text-white text-base">Student 360° Profile</h3>
                  <span className="text-xs text-purple-300 font-mono">
                    {studentDetail.student.reg_id} • {studentDetail.student.name}
                  </span>
                </div>
              </div>
              <button
                type="button"
                onClick={onCloseStudentDetail}
                className="text-slate-400 hover:text-white cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Profile Overview */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 text-xs">
              <div className="p-3 rounded-xl bg-slate-800/60 border border-slate-800">
                <span className="text-slate-400 block mb-0.5">Email</span>
                <span className="font-mono text-white truncate block">{studentDetail.student.email}</span>
              </div>
              <div className="p-3 rounded-xl bg-slate-800/60 border border-slate-800">
                <span className="text-slate-400 block mb-0.5">Department</span>
                <span className="font-medium text-white">{studentDetail.student.department || 'N/A'}</span>
              </div>
              <div className="p-3 rounded-xl bg-slate-800/60 border border-slate-800">
                <span className="text-slate-400 block mb-0.5">Semester</span>
                <span className="font-medium text-white">{studentDetail.student.semester ? `Semester ${studentDetail.student.semester}` : 'N/A'}</span>
              </div>
              <div className="p-3 rounded-xl bg-slate-800/60 border border-slate-800">
                <span className="text-slate-400 block mb-0.5">Status</span>
                <span className="font-bold text-emerald-400 capitalize">{studentDetail.student.status || 'Active'}</span>
              </div>
            </div>

            {/* Mental Health History */}
            <div className="space-y-2.5 pt-2">
              <h4 className="text-xs font-bold uppercase tracking-wider text-purple-300 flex items-center space-x-1.5">
                <AlertTriangle className="w-3.5 h-3.5 text-pink-400" />
                <span>Mental Health Alert History ({studentDetail.alerts?.length || 0})</span>
              </h4>

              {(!studentDetail.alerts || studentDetail.alerts.length === 0) ? (
                <div className="p-6 rounded-xl bg-slate-800/40 border border-slate-800 text-center text-slate-400 text-xs">
                  No distress alerts or risk signals recorded for this student.
                </div>
              ) : (
                <div className="space-y-2">
                  {studentDetail.alerts.map((alert) => (
                    <div
                      key={alert.id}
                      className="p-3.5 rounded-xl border border-slate-800 bg-slate-800/50 flex flex-col space-y-1.5"
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-md border border-purple-500/30 bg-purple-950/40 text-purple-200">
                          {alert.severity} • {alert.predicted_class || 'Distress'}
                        </span>
                        <span className="text-[11px] text-slate-400 font-mono">
                          {new Date(alert.created_at).toLocaleDateString()}
                        </span>
                      </div>
                      <p className="text-xs text-slate-200 italic">
                        "{alert.question_sample || alert.summary}"
                      </p>
                      {alert.admin_notes && (
                        <p className="text-xs text-purple-300 bg-slate-900/60 p-2 rounded-lg border border-purple-500/20">
                          <strong>Admin Notes:</strong> {alert.admin_notes}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="pt-2 flex justify-end">
              <button
                type="button"
                onClick={() => {
                  onLoadStudentRecords(studentDetail.student.reg_id);
                  onCloseStudentDetail();
                }}
                className="flex items-center space-x-2 px-4 py-2 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-xs font-bold text-white transition-colors cursor-pointer"
              >
                <ClipboardList className="w-3.5 h-3.5" />
                <span>Open Academic & Billing Records</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default StudentsTab;
