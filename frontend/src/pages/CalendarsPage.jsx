import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { calendarService } from '../services/calendarService';
import LoadingState from '../components/LoadingState';
import { Calendar, Plus, Trash2, ArrowRight } from 'lucide-react';

const STATUS_COLORS = {
  completed: 'bg-emerald-100 text-emerald-700',
  processing: 'bg-amber-100 text-amber-700',
  pending: 'bg-slate-100 text-slate-600',
  failed: 'bg-red-100 text-red-600',
  partial: 'bg-orange-100 text-orange-700',
};

export default function CalendarsPage() {
  const [calendars, setCalendars] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);

  const fetchCalendars = async (p = 1) => {
    setLoading(true);
    try {
      const res = await calendarService.list({ page: p, page_size: 12 });
      setCalendars(res.data.items);
      setTotal(res.data.total);
      setPage(p);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchCalendars(); }, []);

  const handleDelete = async (id, title) => {
    if (!confirm(`Delete calendar "${title}"? All posts will be removed.`)) return;
    await calendarService.delete(id);
    fetchCalendars(page);
  };

  return (
    <div className="fade-in">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">My Calendars</h1>
          <p className="text-slate-500 text-sm mt-1">{total} calendar{total !== 1 ? 's' : ''}</p>
        </div>
        <Link
          to="/create"
          className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2.5 rounded-xl text-sm font-medium transition-colors"
        >
          <Plus className="w-4 h-4" /> New Calendar
        </Link>
      </div>

      {loading ? <LoadingState /> : calendars.length === 0 ? (
        <div className="text-center py-20">
          <Calendar className="w-12 h-12 text-slate-200 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-slate-700 mb-2">No calendars yet</h3>
          <p className="text-slate-400 mb-6">Create your first 7-day content calendar</p>
          <Link to="/create" className="bg-indigo-600 text-white px-6 py-2.5 rounded-xl text-sm font-medium hover:bg-indigo-700 transition-colors">
            Create Calendar
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {calendars.map((cal) => (
            <div key={cal.id} className="bg-white rounded-2xl border border-slate-100 shadow-sm card-hover overflow-hidden">
              <Link to={`/calendars/${cal.id}`} className="block p-5">
                <div className="flex items-start justify-between mb-3">
                  <h3 className="font-semibold text-slate-900 text-sm leading-tight">{cal.title}</h3>
                  <span className={`text-xs px-2 py-0.5 rounded-full font-medium ml-2 flex-shrink-0 ${STATUS_COLORS[cal.generation_status] || 'bg-slate-100 text-slate-500'}`}>
                    {cal.generation_status}
                  </span>
                </div>
                <p className="text-xs text-slate-400 mb-3">Start: {cal.start_date} · {cal.duration_days} days</p>
                <div className="flex flex-wrap gap-1 mb-3">
                  {cal.selected_platforms?.map((p) => (
                    <span key={p} className="text-xs bg-indigo-50 text-indigo-600 px-2 py-0.5 rounded-full capitalize">{p}</span>
                  ))}
                </div>
                <div className="flex items-center justify-between text-xs text-slate-400">
                  <span className="capitalize">{cal.tone} · {cal.content_objective?.replace(/_/g, ' ')}</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </div>
              </Link>
              <div className="border-t border-slate-50 px-5 py-2 flex justify-end">
                <button
                  onClick={() => handleDelete(cal.id, cal.title)}
                  className="text-xs text-slate-400 hover:text-red-500 flex items-center gap-1 transition-colors"
                >
                  <Trash2 className="w-3 h-3" /> Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
