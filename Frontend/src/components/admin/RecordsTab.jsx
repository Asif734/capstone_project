import React, { useState, useEffect } from 'react';
import {
  GraduationCap,
  DollarSign,
  Plus,
  Trash2,
  Save,
  RotateCcw,
  AlertCircle,
  CheckCircle2,
  BookOpen,
  TrendingUp,
  CreditCard,
  User,
  Search,
  Award
} from 'lucide-react';

export default function RecordsTab({
  students = [],
  selectedStudent,
  onSelectStudent,
  recordData,
  onSaveRecords,
  isSaving = false,
  isLoading = false
}) {
  const [activeRegId, setActiveRegId] = useState(selectedStudent?.reg_id || '');
  const [searchTerm, setSearchTerm] = useState('');

  // Form state
  const [academic, setAcademic] = useState({
    semester: '',
    cgpa: '',
    credits_completed: '',
  });

  const [financial, setFinancial] = useState({
    tuition_fee: '',
    paid_amount: '',
    due_amount: '',
    pending_fees: '',
  });

  const [cgpaRecords, setCgpaRecords] = useState([]);
  const [courses, setCourses] = useState([]);
  const [formError, setFormError] = useState('');

  // Sync state when selectedStudent or recordData changes
  useEffect(() => {
    if (selectedStudent?.reg_id) {
      setActiveRegId(selectedStudent.reg_id);
    }
  }, [selectedStudent]);

  useEffect(() => {
    if (recordData) {
      setAcademic({
        semester: recordData.academic?.semester || '',
        cgpa: recordData.academic?.cgpa ?? '',
        credits_completed: recordData.academic?.credits_completed ?? '',
      });

      setFinancial({
        tuition_fee: recordData.financial?.tuition_fee ?? '',
        paid_amount: recordData.financial?.paid_amount ?? '',
        due_amount: recordData.financial?.due_amount ?? '',
        pending_fees: recordData.financial?.pending_fees ?? '',
      });

      setCgpaRecords(
        (recordData.cgpa_records || []).map((r) => ({
          semester: r.semester || '',
          cgpa: r.cgpa ?? '',
        }))
      );

      setCourses(
        (recordData.courses || []).map((c) => ({
          course_name: c.course_name || '',
          marks: c.marks ?? '',
        }))
      );
      setFormError('');
    }
  }, [recordData]);

  // Handle student selection change
  const handleStudentSelect = (regId) => {
    setActiveRegId(regId);
    onSelectStudent(regId);
  };

  // Row operations for CGPA
  const handleAddCgpaRow = () => {
    const nextNum = cgpaRecords.length + 1;
    setCgpaRecords([...cgpaRecords, { semester: `Semester ${nextNum}`, cgpa: '' }]);
  };

  const handleUpdateCgpaRow = (index, field, value) => {
    const updated = [...cgpaRecords];
    updated[index] = { ...updated[index], [field]: value };
    setCgpaRecords(updated);
  };

  const handleRemoveCgpaRow = (index) => {
    setCgpaRecords(cgpaRecords.filter((_, i) => i !== index));
  };

  // Row operations for Courses
  const handleAddCourseRow = () => {
    setCourses([...courses, { course_name: '', marks: '' }]);
  };

  const handleUpdateCourseRow = (index, field, value) => {
    const updated = [...courses];
    updated[index] = { ...updated[index], [field]: value };
    setCourses(updated);
  };

  const handleRemoveCourseRow = (index) => {
    setCourses(courses.filter((_, i) => i !== index));
  };

  // Financial calculations
  const tuition = Number(financial.tuition_fee) || 0;
  const paid = Number(financial.paid_amount) || 0;
  const due = Number(financial.due_amount) || 0;
  const pending = Number(financial.pending_fees) || 0;
  const paidPercent = tuition > 0 ? Math.min(100, Math.max(0, Math.round((paid / tuition) * 100))) : 0;

  // Save handler
  const handleFormSubmit = (e) => {
    e.preventDefault();
    setFormError('');

    if (!activeRegId) {
      setFormError('Please select a student record to update.');
      return;
    }

    // Validate CGPA records
    for (let i = 0; i < cgpaRecords.length; i++) {
      const item = cgpaRecords[i];
      if (!item.semester.trim()) {
        setFormError(`Semester name is required in row ${i + 1} of CGPA history.`);
        return;
      }
      const val = Number(item.cgpa);
      if (item.cgpa === '' || Number.isNaN(val) || val < 0 || val > 4.0) {
        setFormError(`Valid CGPA (0.00 - 4.00) is required for "${item.semester}".`);
        return;
      }
    }

    // Validate Course records
    for (let i = 0; i < courses.length; i++) {
      const item = courses[i];
      if (!item.course_name.trim()) {
        setFormError(`Course name is required in row ${i + 1} of Course Marks.`);
        return;
      }
      if (item.marks !== '' && (Number.isNaN(Number(item.marks)) || Number(item.marks) < 0 || Number(item.marks) > 100)) {
        setFormError(`Marks must be between 0 and 100 for "${item.course_name}".`);
        return;
      }
    }

    const payload = {
      academic: {
        semester: academic.semester.trim() || null,
        cgpa: academic.cgpa !== '' ? Number(academic.cgpa) : null,
        credits_completed: academic.credits_completed !== '' ? Number(academic.credits_completed) : null,
      },
      financial: {
        tuition_fee: financial.tuition_fee !== '' ? Number(financial.tuition_fee) : null,
        paid_amount: financial.paid_amount !== '' ? Number(financial.paid_amount) : null,
        due_amount: financial.due_amount !== '' ? Number(financial.due_amount) : null,
        pending_fees: financial.pending_fees !== '' ? Number(financial.pending_fees) : null,
      },
      cgpa_records: cgpaRecords.map((r) => ({
        semester: r.semester.trim(),
        cgpa: Number(r.cgpa),
      })),
      courses: courses.map((c) => ({
        course_name: c.course_name.trim(),
        marks: c.marks !== '' ? Number(c.marks) : null,
      })),
    };

    onSaveRecords(activeRegId, payload);
  };

  const filteredStudents = students.filter(
    (s) =>
      s.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      s.reg_id?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      s.department?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* Student Selector Card */}
      <div className="rounded-2xl border border-purple-500/20 bg-slate-800/80 p-5 shadow-lg backdrop-blur-md">
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <GraduationCap className="h-5 w-5 text-purple-400" />
              Academic & Financial Profile Editor
            </h2>
            <p className="text-xs text-purple-300/70">
              Select an authorized student to view and manage their semester grade history, course marks, and billing status.
            </p>
          </div>

          <div className="flex flex-col sm:flex-row items-center gap-3 w-full md:w-auto">
            {/* Search filter for dropdown */}
            <div className="relative w-full sm:w-64">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-purple-300/50" />
              <input
                type="text"
                placeholder="Search student..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full rounded-xl border border-purple-500/30 bg-slate-900/80 py-2 pl-9 pr-3 text-xs text-white placeholder-purple-300/40 focus:border-purple-400 focus:outline-none"
              />
            </div>

            {/* Selector */}
            <select
              value={activeRegId}
              onChange={(e) => handleStudentSelect(e.target.value)}
              className="w-full sm:w-64 rounded-xl border border-purple-500/30 bg-slate-900/80 px-3 py-2 text-xs font-medium text-white focus:border-purple-400 focus:outline-none"
            >
              <option value="">-- Choose Student Record --</option>
              {filteredStudents.map((s) => (
                <option key={s.reg_id} value={s.reg_id}>
                  {s.reg_id} • {s.name} ({s.department})
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Selected Student Banner */}
        {selectedStudent && (
          <div className="mt-4 pt-4 border-t border-purple-500/10 flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-xl bg-purple-500/20 border border-purple-500/30 flex items-center justify-center font-bold text-purple-300">
                {selectedStudent.name?.charAt(0) || 'S'}
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-bold text-white text-sm">{selectedStudent.name}</span>
                  <span className="text-[11px] font-mono px-2 py-0.5 rounded-full bg-purple-500/15 text-purple-300 border border-purple-500/20">
                    {selectedStudent.reg_id}
                  </span>
                </div>
                <div className="text-xs text-purple-300/70 flex items-center gap-3 mt-0.5">
                  <span>Dept: <strong className="text-white">{selectedStudent.department || 'N/A'}</strong></span>
                  <span>Batch: <strong className="text-white">{selectedStudent.batch || 'N/A'}</strong></span>
                  <span>Intake: <strong className="text-white">{selectedStudent.intake || 'N/A'}</strong></span>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-4 text-xs">
              <div className="rounded-xl bg-slate-900/60 border border-purple-500/20 px-3 py-2">
                <span className="text-purple-300/70 block text-[10px] uppercase font-semibold">Current CGPA</span>
                <span className="text-white font-bold text-sm">
                  {academic.cgpa ? Number(academic.cgpa).toFixed(2) : 'N/A'}
                </span>
              </div>
              <div className="rounded-xl bg-slate-900/60 border border-purple-500/20 px-3 py-2">
                <span className="text-purple-300/70 block text-[10px] uppercase font-semibold">Credits</span>
                <span className="text-white font-bold text-sm">
                  {academic.credits_completed ? academic.credits_completed : '0'}
                </span>
              </div>
              <div className="rounded-xl bg-slate-900/60 border border-purple-500/20 px-3 py-2">
                <span className="text-purple-300/70 block text-[10px] uppercase font-semibold">Tuition Status</span>
                <span className={`font-bold text-sm ${paidPercent === 100 ? 'text-emerald-400' : 'text-amber-400'}`}>
                  {paidPercent}% Paid
                </span>
              </div>
            </div>
          </div>
        )}
      </div>

      {formError && (
        <div className="rounded-xl border border-red-500/40 bg-red-500/10 p-3 text-xs text-red-200 flex items-center gap-2">
          <AlertCircle className="h-4 w-4 shrink-0 text-red-400" />
          <span>{formError}</span>
        </div>
      )}

      {/* Main Edit Form */}
      <form onSubmit={handleFormSubmit} className="space-y-6">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Section 1: Academic Standing */}
          <div className="rounded-2xl border border-purple-500/20 bg-slate-800/80 p-5 shadow-lg backdrop-blur-md space-y-4">
            <div className="flex items-center justify-between border-b border-purple-500/10 pb-3">
              <div className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5 text-purple-400" />
                <h3 className="font-bold text-white text-sm">Academic Standing</h3>
              </div>
              <span className="text-[11px] text-purple-300/60">Primary metrics</span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div>
                <label className="block text-[11px] font-medium text-purple-200 mb-1">Current Semester</label>
                <input
                  type="text"
                  placeholder="e.g. Semester 6"
                  value={academic.semester}
                  onChange={(e) => setAcademic({ ...academic, semester: e.target.value })}
                  className="w-full rounded-xl border border-purple-500/30 bg-slate-900/80 px-3 py-2 text-xs text-white placeholder-purple-300/40 focus:border-purple-400 focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-[11px] font-medium text-purple-200 mb-1">Cumulative CGPA</label>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  max="4"
                  placeholder="e.g. 3.75"
                  value={academic.cgpa}
                  onChange={(e) => setAcademic({ ...academic, cgpa: e.target.value })}
                  className="w-full rounded-xl border border-purple-500/30 bg-slate-900/80 px-3 py-2 text-xs text-white placeholder-purple-300/40 focus:border-purple-400 focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-[11px] font-medium text-purple-200 mb-1">Credits Completed</label>
                <input
                  type="number"
                  step="0.5"
                  min="0"
                  placeholder="e.g. 84.0"
                  value={academic.credits_completed}
                  onChange={(e) => setAcademic({ ...academic, credits_completed: e.target.value })}
                  className="w-full rounded-xl border border-purple-500/30 bg-slate-900/80 px-3 py-2 text-xs text-white placeholder-purple-300/40 focus:border-purple-400 focus:outline-none"
                />
              </div>
            </div>

            {/* Semester CGPA History Dynamic Rows */}
            <div className="pt-2">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-semibold text-purple-200">Semester CGPA Breakdown</span>
                <button
                  type="button"
                  onClick={handleAddCgpaRow}
                  className="inline-flex items-center gap-1 text-[11px] font-medium text-purple-300 hover:text-white bg-purple-500/20 hover:bg-purple-500/30 px-2.5 py-1 rounded-lg border border-purple-500/30 transition-all"
                >
                  <Plus className="h-3 w-3" /> Add Semester
                </button>
              </div>

              {cgpaRecords.length === 0 ? (
                <div className="rounded-xl border border-dashed border-purple-500/20 p-4 text-center text-xs text-purple-300/50">
                  No individual semester records added yet. Click "+ Add Semester" above.
                </div>
              ) : (
                <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
                  {cgpaRecords.map((row, idx) => (
                    <div
                      key={idx}
                      className="flex items-center gap-2 rounded-xl bg-slate-900/60 border border-purple-500/20 p-2"
                    >
                      <input
                        type="text"
                        placeholder="Semester (e.g. sem1)"
                        value={row.semester}
                        onChange={(e) => handleUpdateCgpaRow(idx, 'semester', e.target.value)}
                        className="flex-1 rounded-lg border border-purple-500/20 bg-slate-800 px-2.5 py-1.5 text-xs text-white placeholder-purple-300/40 focus:border-purple-400 focus:outline-none"
                      />
                      <div className="w-24">
                        <input
                          type="number"
                          step="0.01"
                          min="0"
                          max="4"
                          placeholder="CGPA"
                          value={row.cgpa}
                          onChange={(e) => handleUpdateCgpaRow(idx, 'cgpa', e.target.value)}
                          className="w-full rounded-lg border border-purple-500/20 bg-slate-800 px-2.5 py-1.5 text-xs text-white placeholder-purple-300/40 focus:border-purple-400 focus:outline-none"
                        />
                      </div>
                      <button
                        type="button"
                        onClick={() => handleRemoveCgpaRow(idx)}
                        className="rounded-lg p-1.5 text-red-400 hover:bg-red-500/20 hover:text-red-300 transition-colors"
                        title="Remove row"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Section 2: Tuition & Financial Record */}
          <div className="rounded-2xl border border-purple-500/20 bg-slate-800/80 p-5 shadow-lg backdrop-blur-md space-y-4">
            <div className="flex items-center justify-between border-b border-purple-500/10 pb-3">
              <div className="flex items-center gap-2">
                <CreditCard className="h-5 w-5 text-emerald-400" />
                <h3 className="font-bold text-white text-sm">Tuition & Financial Status</h3>
              </div>
              <span className={`text-[11px] font-bold px-2 py-0.5 rounded-full ${
                paidPercent === 100
                  ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                  : paidPercent > 0
                  ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                  : 'bg-red-500/20 text-red-300 border border-red-500/30'
              }`}>
                {paidPercent === 100 ? 'Fully Cleared' : paidPercent > 0 ? 'Partial Payment' : 'Unpaid'}
              </span>
            </div>

            {/* Visual Progress Bar */}
            <div className="space-y-1.5 bg-slate-900/60 p-3 rounded-xl border border-purple-500/10">
              <div className="flex justify-between text-xs">
                <span className="text-purple-300/80 font-medium">Payment Ratio</span>
                <span className="font-bold text-white">{paidPercent}% ({paid.toLocaleString()} / {tuition.toLocaleString()} BDT)</span>
              </div>
              <div className="h-2.5 w-full rounded-full bg-slate-800 overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-emerald-500 to-teal-400 rounded-full transition-all duration-500"
                  style={{ width: `${paidPercent}%` }}
                />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="block text-[11px] font-medium text-purple-200 mb-1">Total Tuition Fee (BDT)</label>
                <input
                  type="number"
                  min="0"
                  placeholder="e.g. 120000"
                  value={financial.tuition_fee}
                  onChange={(e) => setFinancial({ ...financial, tuition_fee: e.target.value })}
                  className="w-full rounded-xl border border-purple-500/30 bg-slate-900/80 px-3 py-2 text-xs text-white placeholder-purple-300/40 focus:border-purple-400 focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-[11px] font-medium text-purple-200 mb-1">Paid Amount (BDT)</label>
                <input
                  type="number"
                  min="0"
                  placeholder="e.g. 120000"
                  value={financial.paid_amount}
                  onChange={(e) => setFinancial({ ...financial, paid_amount: e.target.value })}
                  className="w-full rounded-xl border border-purple-500/30 bg-slate-900/80 px-3 py-2 text-xs text-white placeholder-purple-300/40 focus:border-purple-400 focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-[11px] font-medium text-purple-200 mb-1">Due Amount (BDT)</label>
                <input
                  type="number"
                  min="0"
                  placeholder="e.g. 0"
                  value={financial.due_amount}
                  onChange={(e) => setFinancial({ ...financial, due_amount: e.target.value })}
                  className="w-full rounded-xl border border-purple-500/30 bg-slate-900/80 px-3 py-2 text-xs text-white placeholder-purple-300/40 focus:border-purple-400 focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-[11px] font-medium text-purple-200 mb-1">Pending Fees (Misc/Late)</label>
                <input
                  type="number"
                  min="0"
                  placeholder="e.g. 0"
                  value={financial.pending_fees}
                  onChange={(e) => setFinancial({ ...financial, pending_fees: e.target.value })}
                  className="w-full rounded-xl border border-purple-500/30 bg-slate-900/80 px-3 py-2 text-xs text-white placeholder-purple-300/40 focus:border-purple-400 focus:outline-none"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Section 3: Course Marks Dynamic Row Builder */}
        <div className="rounded-2xl border border-purple-500/20 bg-slate-800/80 p-5 shadow-lg backdrop-blur-md space-y-4">
          <div className="flex items-center justify-between border-b border-purple-500/10 pb-3">
            <div className="flex items-center gap-2">
              <BookOpen className="h-5 w-5 text-purple-400" />
              <div>
                <h3 className="font-bold text-white text-sm">Enrolled Courses & Marks Record</h3>
                <p className="text-xs text-purple-300/60">Individual course evaluations, midterm/final scores.</p>
              </div>
            </div>
            <button
              type="button"
              onClick={handleAddCourseRow}
              className="inline-flex items-center gap-1 text-xs font-semibold text-purple-200 hover:text-white bg-purple-600/30 hover:bg-purple-600/50 px-3 py-1.5 rounded-xl border border-purple-500/40 transition-all"
            >
              <Plus className="h-3.5 w-3.5" /> Add Course
            </button>
          </div>

          {courses.length === 0 ? (
            <div className="rounded-xl border border-dashed border-purple-500/20 p-6 text-center text-xs text-purple-300/50">
              No individual course marks entered yet. Click "+ Add Course" to record course marks.
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-h-72 overflow-y-auto pr-1">
              {courses.map((row, idx) => (
                <div
                  key={idx}
                  className="flex items-center gap-2 rounded-xl bg-slate-900/60 border border-purple-500/20 p-2.5"
                >
                  <input
                    type="text"
                    placeholder="Course name (e.g. Data Structures)"
                    value={row.course_name}
                    onChange={(e) => handleUpdateCourseRow(idx, 'course_name', e.target.value)}
                    className="flex-1 rounded-lg border border-purple-500/20 bg-slate-800 px-3 py-1.5 text-xs text-white placeholder-purple-300/40 focus:border-purple-400 focus:outline-none"
                  />
                  <div className="w-24">
                    <input
                      type="number"
                      min="0"
                      max="100"
                      placeholder="Marks"
                      value={row.marks}
                      onChange={(e) => handleUpdateCourseRow(idx, 'marks', e.target.value)}
                      className="w-full rounded-lg border border-purple-500/20 bg-slate-800 px-2.5 py-1.5 text-xs text-white placeholder-purple-300/40 focus:border-purple-400 focus:outline-none text-center"
                    />
                  </div>
                  <button
                    type="button"
                    onClick={() => handleRemoveCourseRow(idx)}
                    className="rounded-lg p-1.5 text-red-400 hover:bg-red-500/20 hover:text-red-300 transition-colors"
                    title="Remove course"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Sticky Actions Bar */}
        <div className="flex items-center justify-between rounded-2xl border border-purple-500/20 bg-slate-800/90 p-4 shadow-xl backdrop-blur-md">
          <button
            type="button"
            onClick={() => {
              if (selectedStudent?.reg_id) onSelectStudent(selectedStudent.reg_id);
            }}
            disabled={isLoading || isSaving}
            className="inline-flex items-center gap-2 rounded-xl border border-purple-500/30 bg-slate-700/60 px-4 py-2 text-xs font-semibold text-purple-200 hover:bg-slate-700 hover:text-white transition-all disabled:opacity-50"
          >
            <RotateCcw className="h-3.5 w-3.5" /> Revert Changes
          </button>

          <button
            type="submit"
            disabled={isSaving || !activeRegId}
            className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-purple-600 to-pink-600 px-6 py-2.5 text-xs font-bold text-white shadow-lg shadow-purple-600/30 hover:from-purple-500 hover:to-pink-500 transition-all disabled:opacity-50"
          >
            {isSaving ? (
              <>
                <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                <span>Saving Records...</span>
              </>
            ) : (
              <>
                <Save className="h-4 w-4" />
                <span>Save All Records</span>
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
