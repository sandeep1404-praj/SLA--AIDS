import { useState } from 'react';
import { calendarService } from '../services/calendarService';
import { Download, FileJson, FileText, FileCode } from 'lucide-react';

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export default function ExportMenu({ calendarId, calendarTitle }) {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(null);

  const handleExport = async (format) => {
    setLoading(format);
    try {
      let res;
      let ext;
      if (format === 'json') {
        res = await calendarService.exportJson(calendarId);
        ext = 'json';
      } else if (format === 'csv') {
        res = await calendarService.exportCsv(calendarId);
        ext = 'csv';
      } else {
        res = await calendarService.exportMarkdown(calendarId);
        ext = 'md';
      }
      const name = `${calendarTitle?.replace(/\s+/g, '_') || 'calendar'}.${ext}`;
      downloadBlob(res.data, name);
    } catch (e) {
      alert('Export failed: ' + (e.response?.data?.detail || e.message));
    } finally {
      setLoading(null);
      setOpen(false);
    }
  };

  return (
    <div className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 px-3 py-2 rounded-lg border border-slate-200 text-slate-700 hover:bg-slate-50 text-sm font-medium transition-colors"
      >
        <Download className="w-4 h-4" />
        Export
      </button>

      {open && (
        <div className="absolute right-0 top-full mt-2 w-44 bg-white rounded-xl shadow-xl border border-slate-100 py-1 z-50">
          {[
            { format: 'json', icon: FileJson, label: 'Export JSON' },
            { format: 'csv', icon: FileCode, label: 'Export CSV' },
            { format: 'markdown', icon: FileText, label: 'Export Markdown' },
          ].map(({ format, icon: Icon, label }) => (
            <button
              key={format}
              onClick={() => handleExport(format)}
              disabled={loading === format}
              className="w-full flex items-center gap-2.5 px-4 py-2 text-sm text-slate-700 hover:bg-slate-50 transition-colors disabled:opacity-50"
            >
              <Icon className="w-4 h-4 text-slate-400" />
              {loading === format ? 'Downloading…' : label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
