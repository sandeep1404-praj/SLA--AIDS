import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import LoadingState from '../components/LoadingState';
import {
  FileText, Calendar, Hash, Layers, Plus, ArrowRight,
  TrendingUp, Clock, CheckCircle
} from 'lucide-react';

function StatCard({ icon: Icon, label, value, color }) {
  return (
    <div className="bg-white rounded-2xl border border-slate-100 p-6 shadow-sm">
      <div className={`w-10 h-10 rounded-xl flex items-center justify-center mb-4 ${color}`}>
        <Icon className="w-5 h-5" />
      </div>
      <p className="text-3xl font-bold text-slate-900">{value ?? '—'}</p>
      <p className="text-sm text-slate-500 mt-1">{label}</p>
    </div>
  );
}

function StatusBadge({ status }) {
  const colors = {
    completed: 'bg-emerald-100 text-emerald-700',
    processing: 'bg-amber-100 text-amber-700',
    pending: 'bg-slate-100 text-slate-600',
    failed: 'bg-red-100 text-red-600',
    partial: 'bg-orange-100 text-orange-700',
  };
  return (
    <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${colors[status] || 'bg-slate-100 text-slate-500'}`}>
      {status}
    </span>
  );
}

export default function DashboardPage() {
  const { user } = useAuth();
  const [stats, setStats] = useState(null);
  const [recent, setRecent] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.get('/api/dashboard/stats'),
      api.get('/api/dashboard/recent'),
    ])
      .then(([s, r]) => {
        setStats(s.data);
        setRecent(r.data);
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <LoadingState message="Loading your dashboard…" />;

  return (
    <div className="fade-in">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">
            Welcome back, {user?.name?.split(' ')[0]} 👋
          </h1>
          <p className="text-slate-500 text-sm mt-1">Here's what's happening with your content.</p>
        </div>
        <Link
          to="/create"
          className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2.5 rounded-xl text-sm font-medium transition-colors shadow-sm"
        >
          <Plus className="w-4 h-4" />
          New Calendar
        </Link>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4 mb-8">
        <StatCard icon={FileText} label="Articles" value={stats?.total_articles} color="bg-indigo-50 text-indigo-600" />
        <StatCard icon={Calendar} label="Calendars" value={stats?.total_calendars} color="bg-violet-50 text-violet-600" />
        <StatCard icon={CheckCircle} label="Completed" value={stats?.completed_calendars} color="bg-emerald-50 text-emerald-600" />
        <StatCard icon={Hash} label="Total Posts" value={stats?.total_posts} color="bg-cyan-50 text-cyan-600" />
        <StatCard icon={Layers} label="Drafts" value={stats?.draft_posts} color="bg-amber-50 text-amber-600" />
        <StatCard icon={TrendingUp} label="Ready" value={stats?.ready_posts} color="bg-rose-50 text-rose-600" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Calendars */}
        <div className="bg-white rounded-2xl border border-slate-100 shadow-sm">
          <div className="flex items-center justify-between px-6 py-4 border-b border-slate-50">
            <h2 className="font-semibold text-slate-900">Recent Calendars</h2>
            <Link to="/calendars" className="text-xs text-indigo-600 hover:text-indigo-800 flex items-center gap-1">
              View all <ArrowRight className="w-3 h-3" />
            </Link>
          </div>
          <div className="divide-y divide-slate-50">
            {!recent?.recent_calendars?.length ? (
              <div className="px-6 py-8 text-center">
                <Calendar className="w-8 h-8 text-slate-200 mx-auto mb-2" />
                <p className="text-sm text-slate-400">No calendars yet.</p>
                <Link to="/create" className="text-xs text-indigo-600 hover:underline mt-1 block">
                  Create your first calendar →
                </Link>
              </div>
            ) : (
              recent.recent_calendars.map((cal) => (
                <Link
                  key={cal.id}
                  to={`/calendars/${cal.id}`}
                  className="flex items-center justify-between px-6 py-3.5 hover:bg-slate-50 transition-colors"
                >
                  <div>
                    <p className="text-sm font-medium text-slate-800">{cal.title}</p>
                    <p className="text-xs text-slate-400 mt-0.5">
                      {cal.selected_platforms?.join(', ')} · {cal.start_date}
                    </p>
                  </div>
                  <StatusBadge status={cal.generation_status} />
                </Link>
              ))
            )}
          </div>
        </div>

        {/* Recent Articles */}
        <div className="bg-white rounded-2xl border border-slate-100 shadow-sm">
          <div className="flex items-center justify-between px-6 py-4 border-b border-slate-50">
            <h2 className="font-semibold text-slate-900">Recent Articles</h2>
            <Link to="/articles" className="text-xs text-indigo-600 hover:text-indigo-800 flex items-center gap-1">
              View all <ArrowRight className="w-3 h-3" />
            </Link>
          </div>
          <div className="divide-y divide-slate-50">
            {!recent?.recent_articles?.length ? (
              <div className="px-6 py-8 text-center">
                <FileText className="w-8 h-8 text-slate-200 mx-auto mb-2" />
                <p className="text-sm text-slate-400">No articles yet.</p>
                <Link to="/create" className="text-xs text-indigo-600 hover:underline mt-1 block">
                  Add your first article →
                </Link>
              </div>
            ) : (
              recent.recent_articles.map((art) => (
                <Link
                  key={art.id}
                  to={`/articles/${art.id}`}
                  className="flex items-center justify-between px-6 py-3.5 hover:bg-slate-50 transition-colors"
                >
                  <div>
                    <p className="text-sm font-medium text-slate-800 line-clamp-1">{art.title}</p>
                    <p className="text-xs text-slate-400 mt-0.5 flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {art.language}
                      {art.extracted_analysis ? ' · Analyzed' : ''}
                    </p>
                  </div>
                  <ArrowRight className="w-4 h-4 text-slate-300" />
                </Link>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
