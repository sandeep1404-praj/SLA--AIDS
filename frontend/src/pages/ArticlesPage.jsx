import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { articleService } from '../services/articleService';
import { calendarService } from '../services/calendarService';
import LoadingState from '../components/LoadingState';
import { FileText, Plus, Trash2, ArrowRight, Calendar } from 'lucide-react';

export default function ArticlesPage() {
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);

  const fetchArticles = async (p = 1) => {
    setLoading(true);
    try {
      const res = await articleService.list({ page: p, page_size: 12 });
      setArticles(res.data.items);
      setTotal(res.data.total);
      setPage(p);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchArticles(); }, []);

  const handleDelete = async (id, title) => {
    if (!confirm(`Delete article "${title}"?`)) return;
    await articleService.delete(id);
    fetchArticles(page);
  };

  return (
    <div className="fade-in">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">My Articles</h1>
          <p className="text-slate-500 text-sm mt-1">{total} article{total !== 1 ? 's' : ''}</p>
        </div>
        <Link
          to="/create"
          className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2.5 rounded-xl text-sm font-medium transition-colors"
        >
          <Plus className="w-4 h-4" /> New Calendar
        </Link>
      </div>

      {loading ? <LoadingState /> : articles.length === 0 ? (
        <div className="text-center py-20">
          <FileText className="w-12 h-12 text-slate-200 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-slate-700 mb-2">No articles yet</h3>
          <p className="text-slate-400 mb-6">Submit an article to generate your first content calendar</p>
          <Link to="/create" className="bg-indigo-600 text-white px-6 py-2.5 rounded-xl text-sm font-medium hover:bg-indigo-700 transition-colors">
            Submit Article
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {articles.map((art) => (
            <div key={art.id} className="bg-white rounded-2xl border border-slate-100 shadow-sm card-hover overflow-hidden">
              <div className="p-5">
                <div className="flex items-start justify-between mb-2">
                  <h3 className="font-semibold text-slate-900 text-sm leading-tight line-clamp-2">{art.title}</h3>
                  {art.extracted_analysis && (
                    <span className="text-xs bg-emerald-50 text-emerald-600 px-2 py-0.5 rounded-full ml-2 flex-shrink-0">Analyzed</span>
                  )}
                </div>
                <p className="text-xs text-slate-400 mb-3">{art.language}</p>
                {art.source_url && (
                  <a href={art.source_url} target="_blank" rel="noopener noreferrer"
                    className="text-xs text-indigo-500 hover:underline truncate block mb-2">
                    {art.source_url}
                  </a>
                )}
              </div>
              <div className="border-t border-slate-50 px-5 py-2 flex justify-between items-center">
                <Link
                  to={`/create?article_id=${art.id}`}
                  className="text-xs text-indigo-600 hover:text-indigo-800 flex items-center gap-1"
                >
                  <Calendar className="w-3 h-3" /> Create Calendar
                </Link>
                <button
                  onClick={() => handleDelete(art.id, art.title)}
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
