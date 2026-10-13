import { useEffect, useState, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import { calendarService } from '../services/calendarService';
import { postService } from '../services/postService';
import PostCard from '../components/PostCard';
import LoadingState from '../components/LoadingState';
import ErrorState from '../components/ErrorState';
import ExportMenu from '../components/ExportMenu';
import {
  ArrowLeft, RefreshCw, Calendar, Filter, AlertTriangle, Clock
} from 'lucide-react';
import { formatApiError } from '../utils/apiError';

const STATUS_MESSAGES = {
  pending: 'Gemini is analyzing your article…',
  processing: 'Generating platform posts — this may take 1-3 minutes…',
  partial: 'Some posts were generated. Others may have failed.',
  failed: 'Generation failed. Please try again.',
  completed: null,
};

export default function CalendarDetailsPage() {
  const { id } = useParams();
  const [calendar, setCalendar] = useState(null);
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [filterPlatform, setFilterPlatform] = useState('all');
  const [filterDay, setFilterDay] = useState('all');
  const [polling, setPolling] = useState(false);

  const fetchCalendar = useCallback(async () => {
    try {
      const [calRes, postsRes] = await Promise.all([
        calendarService.get(id),
        postService.listByCalendar(id),
      ]);
      setCalendar(calRes.data);
      setPosts(postsRes.data);

      // Keep polling if still generating
      const needsPoll = ['pending', 'processing'].includes(calRes.data.generation_status);
      setPolling(needsPoll);
    } catch (e) {
      setError(formatApiError(e, 'Failed to load calendar'));
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchCalendar();
  }, [fetchCalendar]);

  // Poll status while generating
  useEffect(() => {
    if (!polling) return;
    const interval = setInterval(fetchCalendar, 5000);
    return () => clearInterval(interval);
  }, [polling, fetchCalendar]);

  const handlePostUpdate = (updated) => {
    setPosts((prev) => prev.map((p) => (p.id === updated.id ? updated : p)));
  };

  const handlePostDelete = (deletedId) => {
    setPosts((prev) => prev.filter((p) => p.id !== deletedId));
  };

  const handleRegenerateDay = async (dayNum) => {
    if (!confirm(`Regenerate all posts for Day ${dayNum}? Existing posts will be replaced.`)) return;
    await calendarService.regenerateDay(id, dayNum);
    setPolling(true);
    fetchCalendar();
  };

  if (loading) return <LoadingState message="Loading your calendar…" />;
  if (error) return <ErrorState message={error} retry={fetchCalendar} />;
  if (!calendar) return null;

  const platforms = calendar.selected_platforms || [];
  const days = calendar.weekly_plan || [];

  // Filter posts
  const filtered = posts.filter((p) => {
    const platformOk = filterPlatform === 'all' || p.platform === filterPlatform;
    const dayOk = filterDay === 'all' || String(p.day_number) === filterDay;
    return platformOk && dayOk;
  });

  // Group by day
  const byDay = {};
  filtered.forEach((p) => {
    byDay[p.day_number] = byDay[p.day_number] || [];
    byDay[p.day_number].push(p);
  });

  const statusMsg =
    calendar.generation_status === 'failed' && calendar.generation_error
      ? calendar.generation_error
      : STATUS_MESSAGES[calendar.generation_status];
  const isGenerating = ['pending', 'processing'].includes(calendar.generation_status);

  return (
    <div className="fade-in">
      {/* Header */}
      <div className="flex items-start justify-between mb-6 gap-4">
        <div>
          <Link to="/calendars" className="inline-flex items-center gap-1.5 text-slate-500 hover:text-indigo-600 text-sm mb-2">
            <ArrowLeft className="w-3.5 h-3.5" /> All Calendars
          </Link>
          <h1 className="text-2xl font-bold text-slate-900">{calendar.title}</h1>
          <div className="flex items-center gap-3 mt-1 text-sm text-slate-400">
            <span className="flex items-center gap-1"><Calendar className="w-3.5 h-3.5" /> {calendar.start_date}</span>
            <span>·</span>
            <span className="capitalize">{calendar.tone}</span>
            <span>·</span>
            <span>{calendar.selected_platforms?.length} platforms</span>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <ExportMenu calendarId={id} calendarTitle={calendar.title} />
        </div>
      </div>

      {/* Generation status */}
      {statusMsg && (
        <div className={`flex items-center gap-3 rounded-xl px-4 py-3 mb-6 text-sm border
          ${calendar.generation_status === 'failed' ? 'bg-red-50 border-red-100 text-red-700' : 'bg-amber-50 border-amber-100 text-amber-700'}`}>
          {isGenerating ? <div className="spinner w-4 h-4 border-amber-400" /> : <AlertTriangle className="w-4 h-4" />}
          <span className="flex-1">{statusMsg}</span>
          {calendar.generation_errors?.length > 0 && (
            <details className="text-xs ml-2">
              <summary className="cursor-pointer underline">Details</summary>
              <ul className="mt-2 list-disc pl-4 space-y-1">
                {calendar.generation_errors.slice(0, 5).map((err, i) => (
                  <li key={i}>{err}</li>
                ))}
              </ul>
            </details>
          )}
          {isGenerating && <span className="text-xs ml-auto text-amber-500">Auto-refreshing…</span>}
        </div>
      )}

      {/* Filters */}
      {posts.length > 0 && (
        <div className="flex flex-wrap items-center gap-3 mb-6">
          <div className="flex items-center gap-2 text-sm text-slate-500">
            <Filter className="w-3.5 h-3.5" />
            <span>Filter:</span>
          </div>
          <select
            value={filterPlatform}
            onChange={(e) => setFilterPlatform(e.target.value)}
            className="border border-slate-200 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="all">All Platforms</option>
            {platforms.map((p) => <option key={p} value={p}>{p}</option>)}
          </select>
          <select
            value={filterDay}
            onChange={(e) => setFilterDay(e.target.value)}
            className="border border-slate-200 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="all">All Days</option>
            {[1,2,3,4,5,6,7].map((d) => <option key={d} value={String(d)}>Day {d}</option>)}
          </select>
          <span className="text-xs text-slate-400">{filtered.length} post{filtered.length !== 1 ? 's' : ''}</span>
        </div>
      )}

      {/* Calendar grid by day */}
      {Object.keys(byDay).length === 0 && !isGenerating ? (
        <div className="text-center py-20 text-slate-400">
          <Calendar className="w-12 h-12 mx-auto mb-3 text-slate-200" />
          <p>No posts found. Try adjusting filters or wait for generation to complete.</p>
        </div>
      ) : (
        <div className="space-y-8">
          {[1,2,3,4,5,6,7].map((dayNum) => {
            const dayPosts = byDay[dayNum] || [];
            const dayPlan = days.find((d) => d.day_number === dayNum);
            if (!dayPosts.length && filterDay !== 'all') return null;

            return (
              <div key={dayNum} className="rounded-2xl border border-slate-100 overflow-hidden bg-white shadow-sm">
                {/* Day header */}
                <div className="flex items-center justify-between px-5 py-3.5 bg-gradient-to-r from-slate-50 to-indigo-50 border-b border-slate-100">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="bg-indigo-600 text-white text-xs font-bold px-2.5 py-0.5 rounded-full">Day {dayNum}</span>
                      {dayPlan && <span className="text-sm font-semibold text-slate-800">{dayPlan.theme}</span>}
                    </div>
                    {dayPlan && (
                      <p className="text-xs text-slate-500 mt-0.5">{dayPlan.content_angle}</p>
                    )}
                  </div>
                  <button
                    onClick={() => handleRegenerateDay(dayNum)}
                    className="flex items-center gap-1.5 text-xs text-slate-500 hover:text-indigo-600 border border-slate-200 hover:border-indigo-200 px-3 py-1.5 rounded-lg transition-colors"
                  >
                    <RefreshCw className="w-3 h-3" /> Regenerate Day
                  </button>
                </div>

                {/* Posts */}
                <div className="p-4">
                  {dayPosts.length === 0 ? (
                    <div className="flex items-center gap-2 text-xs text-slate-400 py-4 px-2">
                      <Clock className="w-4 h-4" />
                      {isGenerating ? 'Generating…' : 'No posts for this day'}
                    </div>
                  ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                      {dayPosts.map((post) => (
                        <PostCard
                          key={post.id}
                          post={post}
                          onUpdate={handlePostUpdate}
                          onDelete={handlePostDelete}
                        />
                      ))}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
