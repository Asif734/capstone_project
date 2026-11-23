import React, { useState } from 'react';
import {
  Bot,
  GraduationCap,
  BookOpen,
  Briefcase,
  Shield,
  Cpu,
  HeartPulse,
  Sparkles,
  ChevronDown,
  ChevronUp,
  Clock,
  Calendar,
  Award,
  Users,
  FileText,
  ArrowRight,
  HelpCircle,
  School,
  CheckCircle2,
} from 'lucide-react';

// Faculty configuration mapping for iconography and accent colors
const FACULTY_CONFIG = {
  FBS: {
    name: 'Faculty of Business Studies',
    bnName: 'ব্যবসায় শিক্ষা অনুষদ',
    short: 'FBS',
    icon: Briefcase,
    color: 'from-blue-500/20 via-indigo-500/10 to-transparent',
    borderColor: 'border-blue-500/40',
    textColor: 'text-blue-300',
    badgeColor: 'bg-blue-500/20 text-blue-200 border-blue-500/30',
  },
  FASS: {
    name: 'Faculty of Arts & Social Sciences',
    bnName: 'কলা ও সামাজিক বিজ্ঞান অনুষদ',
    short: 'FASS',
    icon: BookOpen,
    color: 'from-amber-500/20 via-orange-500/10 to-transparent',
    borderColor: 'border-amber-500/40',
    textColor: 'text-amber-300',
    badgeColor: 'bg-amber-500/20 text-amber-200 border-amber-500/30',
  },
  FST: {
    name: 'Faculty of Science & Technology',
    bnName: 'বিজ্ঞান ও প্রযুক্তি অনুষদ',
    short: 'FST',
    icon: Cpu,
    color: 'from-cyan-500/20 via-emerald-500/10 to-transparent',
    borderColor: 'border-cyan-500/40',
    textColor: 'text-cyan-300',
    badgeColor: 'bg-cyan-500/20 text-cyan-200 border-cyan-500/30',
  },
  FSSS: {
    name: 'Faculty of Security & Strategic Studies',
    bnName: 'নিরাপত্তা ও কৌশলগত অধ্যয়ন অনুষদ',
    short: 'FSSS',
    icon: Shield,
    color: 'from-purple-500/20 via-violet-500/10 to-transparent',
    borderColor: 'border-purple-500/40',
    textColor: 'text-purple-300',
    badgeColor: 'bg-purple-500/20 text-purple-200 border-purple-500/30',
  },
  FMS: {
    name: 'Faculty of Medical Studies',
    bnName: 'চিকিৎসা শিক্ষা অনুষদ',
    short: 'FMS',
    icon: HeartPulse,
    color: 'from-rose-500/20 via-pink-500/10 to-transparent',
    borderColor: 'border-rose-500/40',
    textColor: 'text-rose-300',
    badgeColor: 'bg-rose-500/20 text-rose-200 border-rose-500/30',
  },
};

// Identify if a line represents a Faculty heading
const detectFacultyKey = (line) => {
  const normalized = line.toUpperCase();
  const isFacultyLine =
    normalized.includes('FACULTY') ||
    normalized.includes('অনুষদ') ||
    normalized.includes('ফ্যাকাল্টি') ||
    normalized.includes('SCHOOL OF') ||
    /^\s*[*#•-]*\s*(FBS|FASS|FST|FSSS|FMS)\b/.test(normalized);
  if (!isFacultyLine) return null;

  if (normalized.includes('BUSINESS') || normalized.includes('FBS') || normalized.includes('ব্যবসায়') || normalized.includes('বিজনেস')) return 'FBS';
  if (normalized.includes('ARTS') || normalized.includes('SOCIAL') || normalized.includes('FASS') || normalized.includes('কলা') || normalized.includes('সামাজিক')) return 'FASS';
  if (normalized.includes('SCIENCE') || normalized.includes('TECHNOLOGY') || normalized.includes('FST') || normalized.includes('বিজ্ঞান') || normalized.includes('প্রযুক্তি')) return 'FST';
  if (normalized.includes('SECURITY') || normalized.includes('STRATEGIC') || normalized.includes('FSSS') || normalized.includes('নিরাপত্তা') || normalized.includes('কৌশল')) return 'FSSS';
  if (normalized.includes('MEDICAL') || normalized.includes('FMS') || normalized.includes('AFMI') || normalized.includes('চিকিৎসা') || normalized.includes('মেডিকেল')) return 'FMS';
  return null;
};

// Clean raw markdown artifact tokens
const cleanTextToken = (text) => {
  if (!text) return '';
  return text
    .replace(/^#+\s*/, '')
    .replace(/^\s*[•*+-]\s*/, '')
    .replace(/^\d+[\.)]\s*/, '')
    .replace(/^[*_]+|[*_]+$/g, '')
    .trim();
};

// Extract modality badges from degree program names
const parseProgramBadges = (rawName) => {
  const badges = [];
  const lower = rawName.toLowerCase();

  if (lower.includes('professional') || lower.includes('পেশাদার') || lower.includes('প্রফেশনাল')) {
    badges.push({ label: 'Professional', color: 'bg-purple-500/30 text-purple-200 border-purple-400/40' });
  }
  if (lower.includes('regular') || lower.includes('সাধারণ') || lower.includes('রেগুলার')) {
    badges.push({ label: 'Regular', color: 'bg-emerald-500/30 text-emerald-200 border-emerald-400/40' });
  }
  if (lower.includes('weekend') || lower.includes('fri & sat') || lower.includes('শুক্র') || lower.includes('উইকেন্ড')) {
    badges.push({ label: 'Weekend', color: 'bg-amber-500/30 text-amber-200 border-amber-400/40' });
  }
  if (lower.includes('evening') || lower.includes('ইভনিং')) {
    badges.push({ label: 'Evening', color: 'bg-blue-500/30 text-blue-200 border-blue-400/40' });
  }

  let cleanName = rawName
    .replace(/^[*•\s\d.-]+/, '')
    .replace(/^[*_]+|[*_]+$/g, '')
    .trim();

  return { cleanName, badges };
};

// Rich structured assistant message renderer
const StructuredMessage = ({ text, onSendMessage }) => {
  if (!text) return null;

  const rawLines = text.split('\n');
  const blocks = [];
  let currentFaculty = null;
  let currentFacultyItems = [];
  let specGridItems = [];
  let overviewText = '';
  let questionBlock = null;

  for (let i = 0; i < rawLines.length; i++) {
    const trimmed = rawLines[i].trim();
    if (!trimmed) continue;

    // 1. Check if line is a course specification key-value pair
    const specMatch = trimmed.match(
      /^\s*[*•-]?\s*\*\*?(Program Overview|Overview|Duration|Schedule|Credit Requirements|Total Credits|Credits|Eligibility\/Target Audience|Admission Eligibility|Eligibility|Target Audience|Tuition Fees?|Type|Degree Level)\*\*?:?\s*(.*)$/i
    );
    if (specMatch) {
      const key = specMatch[1].trim();
      const val = specMatch[2].trim().replace(/^[*_]+|[*_]+$/g, '');
      if (key.toLowerCase().includes('overview')) {
        overviewText = val;
      } else {
        specGridItems.push({ key, val });
      }
      continue;
    }

    // 2. Check if line is a faculty heading (MUST check before bullet check)
    const facultyKey = detectFacultyKey(trimmed);
    if (facultyKey) {
      if (currentFaculty && currentFacultyItems.length > 0) {
        blocks.push({ type: 'faculty', key: currentFaculty, items: [...currentFacultyItems] });
        currentFacultyItems = [];
      }
      currentFaculty = facultyKey;
      continue;
    }

    // 3. Check if line is the closing advisor triage question
    const isTriage =
      (trimmed.endsWith('?') ||
        trimmed.includes('interests you most') ||
        trimmed.includes('looking for a Regular') ||
        trimmed.includes('আগ্রহী') ||
        trimmed.includes('জানতে চান')) &&
      !facultyKey;
    if (isTriage && i >= rawLines.length - 4) {
      questionBlock = cleanTextToken(trimmed);
      continue;
    }

    // 4. Check if line is a main title
    const isMainTitle =
      (trimmed.includes('Degree Programs') ||
        trimmed.includes('Programs at Bangladesh University') ||
        trimmed.includes('Courses at Bangladesh University') ||
        trimmed.includes('ডিগ্রি প্রোগ্রাম')) &&
      !facultyKey;
    if (isMainTitle) {
      if (currentFaculty && currentFacultyItems.length > 0) {
        blocks.push({ type: 'faculty', key: currentFaculty, items: [...currentFacultyItems] });
        currentFaculty = null;
        currentFacultyItems = [];
      }
      blocks.push({ type: 'title', text: cleanTextToken(trimmed) });
      continue;
    }

    // 5. Check if line is a bullet / numbered degree item
    const isBulletRegex = /^\s*([•+-]|\*(?!\*))\s+/;
    const isNumberRegex = /^\s*\d+[\.)]\s+/;
    const isBullet = isBulletRegex.test(trimmed) || isNumberRegex.test(trimmed);

    if (isBullet) {
      const cleanLine = trimmed
        .replace(/^[*•\s\d.-]+/, '')
        .replace(/^[*_]+|[*_]+$/g, '')
        .trim();
      if (currentFaculty) {
        currentFacultyItems.push(cleanLine);
      } else {
        blocks.push({ type: 'bullet', text: cleanLine });
      }
      continue;
    }

    // 6. Generic heading
    if (
      trimmed.startsWith('###') ||
      trimmed.startsWith('##') ||
      trimmed.startsWith('#') ||
      (trimmed.startsWith('**') && trimmed.endsWith('**') && trimmed.length < 80)
    ) {
      const heading = cleanTextToken(trimmed);
      if (currentFaculty && currentFacultyItems.length > 0) {
        blocks.push({ type: 'faculty', key: currentFaculty, items: [...currentFacultyItems] });
        currentFaculty = null;
        currentFacultyItems = [];
      }
      blocks.push({ type: 'heading', text: heading });
      continue;
    }

    // 7. Regular paragraph
    if (currentFaculty && currentFacultyItems.length > 0) {
      blocks.push({ type: 'faculty', key: currentFaculty, items: [...currentFacultyItems] });
      currentFaculty = null;
      currentFacultyItems = [];
    }
    blocks.push({ type: 'paragraph', text: trimmed });
  }

  // Flush remaining faculty items
  if (currentFaculty && currentFacultyItems.length > 0) {
    blocks.push({ type: 'faculty', key: currentFaculty, items: [...currentFacultyItems] });
  }

  // Quick reply options for prospective students
  const suggestionChips = [
    { label: 'Business / MBA (FBS)', query: 'Tell me about Master programs in Business Studies (MBA)' },
    { label: 'Computer Science (FST)', query: 'Tell me about Master of Computer Science & Engineering (MCSE)' },
    { label: 'Development Studies (MDS)', query: 'Tell me about Master of Development Studies (MDS)' },
    { label: 'Law (LLM)', query: 'Tell me about Master of Laws (LLM)' },
    { label: 'Weekend Professional', query: 'Which programs are offered on weekends for working professionals?' },
    { label: 'Regular Weekday', query: 'Which Master programs are full-time regular on weekdays?' },
  ];

  return (
    <div className="space-y-4 text-slate-100">
      {/* 1. Overview Callout if Program Deep Dive */}
      {overviewText && (
        <div className="bg-gradient-to-r from-purple-950/60 via-purple-900/30 to-slate-900/60 border border-purple-500/30 rounded-2xl p-4 shadow-inner">
          <div className="flex items-center space-x-2 text-purple-300 font-semibold mb-1">
            <BookOpen className="w-4 h-4 text-pink-400" />
            <span className="text-xs uppercase tracking-wider font-bold">Program Overview</span>
          </div>
          <p className="text-slate-200 text-sm leading-relaxed">{overviewText}</p>
        </div>
      )}

      {/* 2. Program Specification Grid (When Deep-Dive details exist) */}
      {specGridItems.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 my-3">
          {specGridItems.map((spec, i) => {
            const isDuration = spec.key.toLowerCase().includes('duration');
            const isSchedule = spec.key.toLowerCase().includes('schedule');
            const isCredit = spec.key.toLowerCase().includes('credit');
            const Icon = isDuration ? Clock : isSchedule ? Calendar : isCredit ? Award : Users;
            const accent = isDuration
              ? 'text-amber-400 bg-amber-400/10 border-amber-400/20'
              : isSchedule
              ? 'text-emerald-400 bg-emerald-400/10 border-emerald-400/20'
              : isCredit
              ? 'text-cyan-400 bg-cyan-400/10 border-cyan-400/20'
              : 'text-purple-400 bg-purple-400/10 border-purple-400/20';

            return (
              <div
                key={i}
                className="bg-slate-900/70 border border-slate-700/80 rounded-xl p-3 shadow-sm hover:border-slate-600 transition-all"
              >
                <div className="flex items-center space-x-2 mb-1">
                  <div className={`p-1.5 rounded-lg border ${accent}`}>
                    <Icon className="w-3.5 h-3.5" />
                  </div>
                  <span className="text-xs font-semibold text-slate-300 uppercase tracking-wide">
                    {spec.key}
                  </span>
                </div>
                <div className="text-sm font-medium text-white pl-7">{spec.val}</div>
              </div>
            );
          })}
        </div>
      )}

      {/* 3. Render Sequence of Blocks (Titles, Headings, Paragraphs, Faculty Cards) */}
      {blocks.map((block, idx) => {
        if (block.type === 'title') {
          return (
            <div
              key={idx}
              className="flex items-center space-x-3 pb-3 mb-2 border-b border-purple-500/30"
            >
              <div className="p-2 rounded-xl bg-gradient-to-tr from-purple-500 to-pink-500 text-white shadow-md">
                <School className="w-5 h-5" />
              </div>
              <div>
                <span className="text-[11px] font-bold uppercase tracking-wider text-purple-300 block">
                  Academic Degree Directory
                </span>
                <h2 className="text-base sm:text-lg font-bold text-white tracking-tight">
                  {block.text}
                </h2>
              </div>
            </div>
          );
        }

        if (block.type === 'heading') {
          return (
            <div key={idx} className="flex items-center space-x-2 pt-2 border-b border-purple-500/20 pb-1.5">
              <GraduationCap className="w-5 h-5 text-pink-400 flex-shrink-0" />
              <h3 className="text-sm sm:text-base font-bold text-purple-200">
                {block.text}
              </h3>
            </div>
          );
        }

        if (block.type === 'paragraph') {
          const formatted = block.text.split(/\*\*(.*?)\*\*/g).map((part, i) =>
            i % 2 === 1 ? (
              <strong key={i} className="font-bold text-purple-200">
                {part}
              </strong>
            ) : (
              part
            )
          );
          return (
            <p key={idx} className="text-sm sm:text-base text-slate-200 leading-relaxed">
              {formatted}
            </p>
          );
        }

        if (block.type === 'faculty') {
          const cfg = FACULTY_CONFIG[block.key] || {
            name: block.key,
            bnName: block.key,
            short: block.key,
            icon: GraduationCap,
            color: 'from-slate-700/50 to-slate-800/50',
            borderColor: 'border-slate-600',
            textColor: 'text-purple-300',
            badgeColor: 'bg-purple-500/20 text-purple-200 border-purple-500/30',
          };
          const IconComponent = cfg.icon;

          return (
            <div
              key={idx}
              className={`rounded-2xl border ${cfg.borderColor} bg-gradient-to-br ${cfg.color} p-4 shadow-md backdrop-blur-sm transition-all hover:border-purple-400/50 my-2.5`}
            >
              {/* Faculty Card Header */}
              <div className="flex items-center justify-between mb-3 border-b border-slate-700/50 pb-2.5">
                <div className="flex items-center space-x-2.5">
                  <div
                    className={`p-2 rounded-xl bg-slate-900/80 border ${cfg.borderColor} ${cfg.textColor} shadow-inner`}
                  >
                    <IconComponent className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className={`font-bold text-sm sm:text-base ${cfg.textColor} leading-tight`}>
                      {cfg.name}
                    </h3>
                    <span className="text-xs text-slate-400 font-mono">
                      {block.items.length} Programs Available
                    </span>
                  </div>
                </div>
                <span className={`text-xs px-2.5 py-1 rounded-full font-bold border ${cfg.badgeColor}`}>
                  {cfg.short}
                </span>
              </div>

              {/* Grid of clean program pills */}
              <div className="grid grid-cols-1 gap-2">
                {block.items.map((rawItem, itemIdx) => {
                  const { cleanName, badges } = parseProgramBadges(rawItem);
                  return (
                    <div
                      key={itemIdx}
                      onClick={() => onSendMessage && onSendMessage(`Tell me more about ${cleanName}`)}
                      className="group flex items-center justify-between p-2.5 rounded-xl bg-slate-900/70 hover:bg-purple-950/70 border border-slate-800 hover:border-purple-500/40 cursor-pointer transition-all shadow-sm"
                      title={`Click to explore ${cleanName}`}
                    >
                      <div className="flex items-center space-x-2.5 flex-1 min-w-0 pr-2">
                        <CheckCircle2 className="w-3.5 h-3.5 text-pink-400 flex-shrink-0 group-hover:scale-110 transition-transform" />
                        <span className="text-xs sm:text-sm text-slate-200 group-hover:text-white font-medium truncate">
                          {cleanName}
                        </span>
                      </div>
                      <div className="flex items-center space-x-1.5 flex-shrink-0">
                        {badges.map((b, bIdx) => (
                          <span
                            key={bIdx}
                            className={`text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-md border ${b.color}`}
                          >
                            {b.label}
                          </span>
                        ))}
                        <ArrowRight className="w-3.5 h-3.5 text-slate-500 group-hover:text-pink-400 group-hover:translate-x-0.5 transition-all ml-1" />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          );
        }

        if (block.type === 'bullet') {
          return (
            <div key={idx} className="flex items-start space-x-2.5 ml-2 my-1">
              <span className="text-pink-400 mt-1 flex-shrink-0 font-bold">•</span>
              <span className="text-sm text-slate-200">{block.text}</span>
            </div>
          );
        }

        return null;
      })}

      {/* 4. Advisor Triage / Guidance Card with Interactive Quick-Reply Chips */}
      {questionBlock && (
        <div className="mt-4 rounded-2xl border border-pink-500/40 bg-gradient-to-r from-purple-950/60 via-pink-950/30 to-purple-950/60 p-4 shadow-xl">
          <div className="flex items-start space-x-3 mb-3">
            <div className="p-2 rounded-xl bg-pink-500/20 text-pink-300 border border-pink-500/30 flex-shrink-0">
              <Sparkles className="w-5 h-5 animate-pulse text-pink-300" />
            </div>
            <div>
              <span className="text-xs font-bold uppercase tracking-wider text-pink-300 block mb-0.5">
                BUP Academic Advisor Guidance
              </span>
              <p className="text-sm sm:text-base font-medium text-white leading-snug">
                {questionBlock}
              </p>
            </div>
          </div>

          {/* Quick-Reply Action Chips */}
          <div className="pt-2.5 border-t border-purple-500/20">
            <span className="text-xs text-purple-200/80 mb-2 block font-medium">
              Click a program category to explore specific details:
            </span>
            <div className="flex flex-wrap gap-2">
              {suggestionChips.map((chip, i) => (
                <button
                  key={i}
                  type="button"
                  onClick={() => onSendMessage && onSendMessage(chip.query)}
                  className="px-3 py-1.5 rounded-xl bg-slate-900/80 hover:bg-gradient-to-r hover:from-purple-600 hover:to-pink-600 border border-purple-500/30 hover:border-transparent text-xs text-slate-200 hover:text-white font-medium transition-all shadow-sm active:scale-95 cursor-pointer"
                >
                  {chip.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Main ChatArea Container
const ChatArea = ({ messages = [], onSendMessage, isSending = false }) => {
  const [sourcesOpenMap, setSourcesOpenMap] = useState({});

  const toggleSources = (idx) => {
    setSourcesOpenMap((prev) => ({ ...prev, [idx]: !prev[idx] }));
  };

  const uniqueSources = (sources = []) => {
    const seen = new Set();
    return sources.filter((source) => {
      const key = `${source.doc_id}:${source.chunk_index}`;
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    });
  };

  const starterQuestions = [
    "What Master's degree programs does BUP offer?",
    "What undergraduate bachelor courses are available?",
    'Tell me about the Master of Development Studies (MDS)',
    'What are the MBA weekend programs for professionals?',
  ];

  return (
    <div className="flex-1 overflow-y-auto px-4 py-6">
      <div className="max-w-3xl mx-auto space-y-6">
        {messages.length === 0 ? (
          // Welcome Screen
          <div className="flex flex-col items-center justify-center min-h-[60vh] text-center px-4">
            <div className="bg-gradient-to-br from-purple-500/20 via-pink-500/10 to-transparent backdrop-blur-md border border-purple-500/30 rounded-3xl p-8 max-w-xl shadow-2xl">
              <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-purple-500 to-pink-500 flex items-center justify-center mx-auto mb-4 shadow-lg shadow-purple-500/30">
                <GraduationCap className="w-8 h-8 text-white" />
              </div>
              <h2 className="text-2xl sm:text-3xl font-extrabold text-white mb-2 tracking-tight">
                BUP Student Assistant
              </h2>
              <p className="text-purple-200/80 text-sm sm:text-base leading-relaxed mb-6">
                Your official academic guide to degree programs, admissions, faculty details, and student services at Bangladesh University of Professionals.
              </p>

              {/* Starter Question Chips */}
              <div className="space-y-2 text-left">
                <span className="text-xs font-semibold text-purple-300 uppercase tracking-wider block">
                  Frequently Asked Questions
                </span>
                <div className="grid grid-cols-1 gap-2">
                  {starterQuestions.map((q, i) => (
                    <button
                      key={i}
                      onClick={() => onSendMessage && onSendMessage(q)}
                      className="w-full text-left p-3 rounded-xl bg-slate-800/60 hover:bg-purple-900/40 border border-purple-500/20 hover:border-purple-500/50 text-xs sm:text-sm text-slate-200 hover:text-white transition-all flex items-center justify-between group cursor-pointer"
                    >
                      <span className="truncate pr-2">{q}</span>
                      <ArrowRight className="w-4 h-4 text-purple-400 group-hover:translate-x-1 transition-transform flex-shrink-0" />
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>
        ) : (
          // Message Thread
          messages.map((msg, idx) => {
            const sources = uniqueSources(msg.sources);
            const isSourcesOpen = Boolean(sourcesOpenMap[idx]);

            return (
              <div
                key={idx}
                className={`flex ${msg.isUser ? 'justify-end' : 'justify-start'} animate-fadeIn`}
              >
                {msg.isUser ? (
                  // User Message
                  <div className="max-w-xl px-5 py-3.5 rounded-3xl rounded-tr-sm bg-gradient-to-r from-purple-600 to-pink-600 text-white shadow-lg text-sm sm:text-base font-medium leading-relaxed">
                    {msg.text}
                  </div>
                ) : (
                  // Assistant Message
                  <div className="w-full max-w-2xl bg-slate-800/90 border border-slate-700/80 backdrop-blur-md rounded-3xl rounded-tl-sm p-5 sm:p-6 shadow-2xl transition-all">
                    {/* Assistant Header */}
                    <div className="flex items-center space-x-2.5 pb-3 mb-3 border-b border-slate-700/60">
                      <div className="w-7 h-7 rounded-lg bg-gradient-to-tr from-purple-500 to-pink-500 flex items-center justify-center shadow-md">
                        <Bot className="w-4 h-4 text-white" />
                      </div>
                      <span className="text-xs font-bold tracking-wide text-transparent bg-clip-text bg-gradient-to-r from-purple-300 to-pink-300">
                        BUP Academic Assistant
                      </span>
                    </div>

                    {/* Rich Structured Message */}
                    <StructuredMessage text={msg.text} onSendMessage={onSendMessage} />

                    {/* Sources Collapsible Card */}
                    {sources.length > 0 && (
                      <div className="mt-4 pt-3 border-t border-slate-700/60">
                        <button
                          type="button"
                          onClick={() => toggleSources(idx)}
                          className="flex items-center justify-between w-full text-xs font-semibold text-slate-400 hover:text-purple-300 transition-colors py-1 cursor-pointer"
                        >
                          <span className="flex items-center space-x-1.5">
                            <FileText className="w-3.5 h-3.5 text-purple-400" />
                            <span>Verified Sources ({sources.length})</span>
                          </span>
                          {isSourcesOpen ? (
                            <ChevronUp className="w-3.5 h-3.5" />
                          ) : (
                            <ChevronDown className="w-3.5 h-3.5" />
                          )}
                        </button>

                        {isSourcesOpen && (
                          <div className="mt-2 space-y-1.5 pl-2 border-l-2 border-purple-500/30">
                            {sources.map((s, sIdx) => (
                              <div
                                key={sIdx}
                                className="text-[11px] text-slate-400 font-mono bg-slate-900/60 rounded-md p-1.5 flex items-center justify-between"
                              >
                                <span className="text-purple-300 truncate max-w-[80%]">
                                  {s.title || s.source_name || s.doc_id}
                                </span>
                                <span className="text-slate-500">chunk {s.chunk_index}</span>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })
        )}

        {/* Loading / Generating State */}
        {isSending && (
          <div className="flex justify-start animate-fadeIn">
            <div className="bg-slate-800/90 border border-slate-700/80 rounded-2xl rounded-tl-sm px-4 py-3 flex items-center space-x-3 shadow-lg">
              <div className="w-6 h-6 rounded-lg bg-gradient-to-tr from-purple-500 to-pink-500 flex items-center justify-center animate-pulse">
                <Bot className="w-3.5 h-3.5 text-white" />
              </div>
              <div className="flex items-center space-x-1.5">
                <span className="w-2 h-2 rounded-full bg-purple-400 animate-bounce" style={{ animationDelay: '0ms' }} />
                <span className="w-2 h-2 rounded-full bg-pink-400 animate-bounce" style={{ animationDelay: '150ms' }} />
                <span className="w-2 h-2 rounded-full bg-purple-300 animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
              <span className="text-xs text-slate-400 font-medium ml-1">
                BUP Assistant is thinking...
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ChatArea;
