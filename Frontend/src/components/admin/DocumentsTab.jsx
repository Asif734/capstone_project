import React, { useState, useRef } from 'react';
import {
  FileText,
  UploadCloud,
  Trash2,
  RefreshCw,
  Search,
  Database,
  Layers,
  Clock,
  AlertCircle,
  CheckCircle2,
  FileCheck,
  FileType,
  Info
} from 'lucide-react';

export default function DocumentsTab({
  documents = [],
  totalDocuments = 0,
  onRefresh,
  onUploadDocument,
  onDeleteDocument,
  isLoading = false,
  isUploading = false,
  isDeleting = false
}) {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const [docToDelete, setDocToDelete] = useState(null);
  const [uploadError, setUploadError] = useState('');
  const fileInputRef = useRef(null);

  const filteredDocuments = documents.filter((doc) => {
    const name = doc.document_name || doc.source_name || doc.document_id || '';
    return name.toLowerCase().includes(searchTerm.toLowerCase());
  });

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    validateAndSetFile(file);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files?.[0];
    validateAndSetFile(file);
  };

  const validateAndSetFile = (file) => {
    setUploadError('');
    if (!file) return;

    const allowedExtensions = ['.pdf', '.docx', '.txt'];
    const lowerName = file.name.toLowerCase();
    const isAllowed = allowedExtensions.some((ext) => lowerName.endsWith(ext));

    if (!isAllowed) {
      setUploadError('Only .pdf, .docx, and .txt files are supported.');
      return;
    }

    if (file.size > 20 * 1024 * 1024) {
      setUploadError('File size exceeds the 20MB limit.');
      return;
    }

    setSelectedFile(file);
  };

  const handleUploadSubmit = async () => {
    if (!selectedFile) return;
    try {
      await onUploadDocument(selectedFile);
      setSelectedFile(null);
      if (fileInputRef.current) fileInputRef.current.value = '';
    } catch (err) {
      setUploadError(err.message || 'Failed to upload document.');
    }
  };

  const confirmDelete = async () => {
    if (!docToDelete) return;
    try {
      const docName = docToDelete.document_name || docToDelete.document_id;
      await onDeleteDocument(docName);
      setDocToDelete(null);
    } catch (err) {
      console.error(err);
    }
  };

  const formatFileSize = (bytes) => {
    if (!bytes) return null;
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const formatTimestamp = (isoString) => {
    if (!isoString) return 'Previously Indexed';
    try {
      const d = new Date(isoString);
      return d.toLocaleDateString(undefined, {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
      });
    } catch {
      return isoString;
    }
  };

  const getFileBadgeColor = (name) => {
    const lower = (name || '').toLowerCase();
    if (lower.endsWith('.pdf')) return 'bg-rose-500/20 text-rose-300 border-rose-500/30';
    if (lower.endsWith('.docx')) return 'bg-blue-500/20 text-blue-300 border-blue-500/30';
    return 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30';
  };

  return (
    <div className="space-y-6">
      {/* Informational Hero Banner */}
      <div className="rounded-2xl border border-purple-500/20 bg-slate-800/80 p-5 shadow-lg backdrop-blur-md">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div className="space-y-1">
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <Database className="h-5 w-5 text-purple-400" />
              Knowledge Base & Vector Store Manager
            </h2>
            <p className="text-xs text-purple-300/70 max-w-2xl">
              Documents stored here are chunked, embedded, and indexed in FAISS to power the BUP Academic Assistant's retrieval-augmented generation (RAG) system with verified university answers.
            </p>
          </div>

          <div className="flex items-center gap-3 w-full md:w-auto justify-end">
            <div className="rounded-xl bg-purple-500/10 border border-purple-500/20 px-3 py-2 text-center">
              <span className="text-[10px] uppercase font-bold text-purple-300/60 block">Indexed Files</span>
              <span className="text-base font-bold text-white">{totalDocuments || documents.length}</span>
            </div>
            <button
              onClick={() => onRefresh && onRefresh()}
              disabled={isLoading}
              className="inline-flex items-center gap-1.5 rounded-xl border border-purple-500/30 bg-purple-500/20 hover:bg-purple-500/30 px-3 py-2.5 text-xs font-semibold text-white transition-all disabled:opacity-50"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${isLoading ? 'animate-spin' : ''}`} />
              <span>Refresh Store</span>
            </button>
          </div>
        </div>
      </div>

      {/* Upload Dropzone */}
      <div className="rounded-2xl border border-purple-500/20 bg-slate-800/80 p-5 shadow-lg backdrop-blur-md">
        <h3 className="text-sm font-bold text-white mb-2 flex items-center gap-2">
          <UploadCloud className="h-4 w-4 text-purple-400" /> Ingest New Academic Document
        </h3>

        {uploadError && (
          <div className="mb-3 rounded-xl border border-red-500/30 bg-red-500/10 p-3 text-xs text-red-200 flex items-center gap-2">
            <AlertCircle className="h-4 w-4 shrink-0 text-red-400" />
            <span>{uploadError}</span>
          </div>
        )}

        <div
          onDragOver={(e) => {
            e.preventDefault();
            setDragOver(true);
          }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
          className={`border-2 border-dashed rounded-2xl p-6 text-center transition-all ${
            dragOver
              ? 'border-purple-400 bg-purple-500/15'
              : 'border-purple-500/30 bg-slate-900/60 hover:border-purple-500/50'
          }`}
        >
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            accept=".pdf,.docx,.txt"
            className="hidden"
          />

          {selectedFile ? (
            <div className="flex flex-col items-center justify-center space-y-3">
              <div className="h-12 w-12 rounded-2xl bg-purple-500/20 border border-purple-500/30 flex items-center justify-center text-purple-300">
                <FileCheck className="h-6 w-6 text-emerald-400" />
              </div>
              <div>
                <p className="text-sm font-bold text-white">{selectedFile.name}</p>
                <p className="text-xs text-purple-300/70">{formatFileSize(selectedFile.size)}</p>
              </div>
              <div className="flex items-center gap-2 pt-1">
                <button
                  type="button"
                  onClick={() => setSelectedFile(null)}
                  className="rounded-xl border border-purple-500/30 bg-slate-800 px-3 py-1.5 text-xs text-purple-200 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleUploadSubmit}
                  disabled={isUploading}
                  className="inline-flex items-center gap-1.5 rounded-xl bg-gradient-to-r from-purple-600 to-pink-600 px-4 py-1.5 text-xs font-bold text-white shadow-lg shadow-purple-600/30 hover:from-purple-500 hover:to-pink-500 disabled:opacity-50"
                >
                  {isUploading ? (
                    <>
                      <div className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-white border-t-transparent" />
                      <span>Chunking & Indexing...</span>
                    </>
                  ) : (
                    <>
                      <UploadCloud className="h-3.5 w-3.5" />
                      <span>Upload & Ingest to FAISS</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center space-y-2 cursor-pointer" onClick={() => fileInputRef.current?.click()}>
              <div className="h-12 w-12 rounded-2xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-purple-300">
                <UploadCloud className="h-6 w-6 text-purple-400" />
              </div>
              <p className="text-xs text-white font-medium">
                Drag and drop your file here, or <span className="text-purple-400 underline font-semibold">browse files</span>
              </p>
              <p className="text-[11px] text-purple-300/50">Supported formats: .DOCX, .PDF, .TXT (Max 20MB)</p>
            </div>
          )}
        </div>
      </div>

      {/* Documents List Header & Filter */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
        <div className="relative w-full sm:w-72">
          <Search className="absolute left-3.5 top-2.5 h-4 w-4 text-purple-300/50" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search indexed documents..."
            className="w-full rounded-xl border border-purple-500/30 bg-slate-900/80 py-2 pl-10 pr-4 text-xs text-white placeholder-purple-300/40 focus:border-purple-400 focus:outline-none"
          />
        </div>
        <p className="text-xs text-purple-300/60">
          Showing {filteredDocuments.length} of {documents.length} document{documents.length !== 1 ? 's' : ''}
        </p>
      </div>

      {/* Documents Grid / Table */}
      {filteredDocuments.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-purple-500/20 bg-slate-800/40 p-12 text-center">
          <Database className="mx-auto h-10 w-10 text-purple-400/40 mb-3" />
          <p className="text-sm font-semibold text-white">No documents found</p>
          <p className="text-xs text-purple-300/60 mt-1 max-w-sm mx-auto">
            Upload your BUP academic curriculum, degree catalogs, or admission circulars above to expand the AI's verified knowledge.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredDocuments.map((doc, idx) => {
            const name = doc.document_name || doc.source_name || doc.document_id || 'Untitled Document';
            const chunkCount = doc.chunks_count ?? doc.chunk_count ?? 'N/A';
            const date = formatTimestamp(doc.ingested_at);
            const badgeColor = getFileBadgeColor(name);

            return (
              <div
                key={doc.document_id || idx}
                className="group relative flex flex-col justify-between rounded-2xl border border-purple-500/20 bg-slate-800/80 p-5 shadow-lg backdrop-blur-md hover:border-purple-500/40 hover:bg-slate-800 transition-all"
              >
                <div>
                  <div className="flex items-start justify-between gap-2 mb-3">
                    <div className="h-10 w-10 rounded-xl bg-purple-500/20 border border-purple-500/30 flex items-center justify-center text-purple-300 shrink-0">
                      <FileText className="h-5 w-5 text-purple-300" />
                    </div>
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${badgeColor}`}>
                      {name.split('.').pop()?.toUpperCase() || 'DOC'}
                    </span>
                  </div>

                  <h4 className="font-bold text-white text-sm break-words line-clamp-2" title={name}>
                    {name}
                  </h4>

                  <div className="mt-3 space-y-1.5 text-xs text-purple-300/70 border-t border-purple-500/10 pt-3">
                    <div className="flex items-center justify-between">
                      <span className="flex items-center gap-1.5 text-[11px]">
                        <Layers className="h-3.5 w-3.5 text-purple-400" /> Chunks Indexed
                      </span>
                      <span className="font-mono font-bold text-white bg-slate-900/60 px-2 py-0.5 rounded-md border border-purple-500/20">
                        {chunkCount}
                      </span>
                    </div>

                    <div className="flex items-center justify-between">
                      <span className="flex items-center gap-1.5 text-[11px]">
                        <Clock className="h-3.5 w-3.5 text-purple-400" /> Ingested Date
                      </span>
                      <span className="text-[11px] text-purple-200">{date}</span>
                    </div>
                  </div>
                </div>

                <div className="mt-4 pt-3 border-t border-purple-500/10 flex items-center justify-end">
                  <button
                    type="button"
                    onClick={() => setDocToDelete(doc)}
                    className="inline-flex items-center gap-1 text-xs text-red-400 hover:text-red-300 bg-red-500/10 hover:bg-red-500/20 px-2.5 py-1.5 rounded-xl border border-red-500/20 transition-all"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                    <span>Delete Document</span>
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {docToDelete && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-2xl border border-red-500/30 bg-slate-800 p-6 shadow-2xl">
            <div className="mb-4 flex items-center gap-3">
              <div className="rounded-xl bg-red-500/20 p-2.5 text-red-400">
                <Trash2 className="h-6 w-6" />
              </div>
              <div>
                <h3 className="text-base font-bold text-white">Delete Document</h3>
                <p className="text-xs text-purple-300/70">Confirm removal from FAISS vector store</p>
              </div>
            </div>

            <p className="text-xs text-purple-200 mb-4 leading-relaxed">
              Are you sure you want to delete <strong className="text-white">{docToDelete.document_name || docToDelete.document_id}</strong>? All associated text chunks and vector embeddings will be permanently purged from the knowledge base.
            </p>

            <div className="flex items-center justify-end gap-3">
              <button
                type="button"
                onClick={() => setDocToDelete(null)}
                className="rounded-xl border border-purple-500/30 bg-slate-700/60 px-4 py-2 text-xs font-semibold text-purple-200 hover:bg-slate-700 hover:text-white"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={confirmDelete}
                disabled={isDeleting}
                className="inline-flex items-center gap-1.5 rounded-xl bg-red-600 px-4 py-2 text-xs font-bold text-white shadow-lg shadow-red-600/30 hover:bg-red-500 disabled:opacity-50"
              >
                {isDeleting ? (
                  <>
                    <div className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-white border-t-transparent" />
                    <span>Deleting...</span>
                  </>
                ) : (
                  <>
                    <Trash2 className="h-3.5 w-3.5" />
                    <span>Delete Forever</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
