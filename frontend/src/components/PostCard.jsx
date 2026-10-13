import { useState } from 'react';
import { postService } from '../services/postService';
import { Edit3, RefreshCw, Copy, Trash2, Check, Clock, ChevronDown, ChevronUp } from 'lucide-react';
import ValidationBadge from './ValidationBadge';

const PLATFORM_COLORS = {
  linkedin: 'bg-blue-600',
  x: 'bg-black',
  instagram: 'bg-gradient-to-r from-orange-400 to-pink-600',
  facebook: 'bg-blue-500',
  short_video: 'bg-red-500',
};

const PLATFORM_LABELS = {
  linkedin: 'LinkedIn',
  x: 'X (Twitter)',
  instagram: 'Instagram',
  facebook: 'Facebook',
  short_video: 'Short Video',
};

export default function PostCard({ post, onUpdate, onDelete }) {
  const [editing, setEditing] = useState(false);
  const [editText, setEditText] = useState(post.post_text);
  const [editCta, setEditCta] = useState(post.call_to_action || '');
  const [saving, setSaving] = useState(false);
  const [regenerating, setRegenerating] = useState(false);
  const [copied, setCopied] = useState(false);
  const [expanded, setExpanded] = useState(false);

  const colorClass = PLATFORM_COLORS[post.platform] || 'bg-slate-600';
  const label = PLATFORM_LABELS[post.platform] || post.platform;

  const handleSave = async () => {
    setSaving(true);
    try {
      const res = await postService.update(post.id, {
        post_text: editText,
        call_to_action: editCta,
      });
      onUpdate(res.data);
      setEditing(false);
    } catch (e) {
      alert('Save failed: ' + (e.response?.data?.detail || e.message));
    } finally {
      setSaving(false);
    }
  };

  const handleRegenerate = async () => {
    if (!confirm('Regenerate this post? The current version will be saved to history.')) return;
    setRegenerating(true);
    try {
      const res = await postService.regenerate(post.id);
      onUpdate(res.data);
    } catch (e) {
      alert('Regeneration failed: ' + (e.response?.data?.detail || e.message));
    } finally {
      setRegenerating(false);
    }
  };

  const handleCopy = async () => {
    await navigator.clipboard.writeText(post.post_text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDelete = async () => {
    if (!confirm('Delete this post? This cannot be undone.')) return;
    try {
      await postService.delete(post.id);
      onDelete(post.id);
    } catch (e) {
      alert('Delete failed');
    }
  };

  const markReady = async () => {
    const res = await postService.update(post.id, { status: post.status === 'ready' ? 'draft' : 'ready' });
    onUpdate(res.data);
  };

  const isLong = post.post_text?.length > 300;

  return (
    <div className="bg-white rounded-xl border border-slate-100 shadow-sm overflow-hidden card-hover">
      {/* Platform header */}
      <div className={`${colorClass} px-4 py-2 flex items-center justify-between`}>
        <span className="text-white text-xs font-semibold uppercase tracking-wide">{label}</span>
        <div className="flex items-center gap-1.5">
          <ValidationBadge status={post.validation_status} warnings={post.validation_warnings || []} />
          <span className={`text-xs px-2 py-0.5 rounded-full font-medium
            ${post.status === 'ready' ? 'bg-emerald-100 text-emerald-700' : 'bg-white/20 text-white'}`}>
            {post.status}
          </span>
        </div>
      </div>

      <div className="p-4">
        {/* Title */}
        {post.title && (
          <p className="font-semibold text-slate-800 text-sm mb-2">{post.title}</p>
        )}

        {/* Post text */}
        {editing ? (
          <textarea
            value={editText}
            onChange={(e) => setEditText(e.target.value)}
            className="w-full border border-indigo-300 rounded-lg p-3 text-sm text-slate-700 resize-y min-h-[120px] focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        ) : (
          <div>
            <p className={`text-sm text-slate-700 leading-relaxed whitespace-pre-line ${!expanded && isLong ? 'line-clamp-4' : ''}`}>
              {post.post_text}
            </p>
            {isLong && (
              <button
                onClick={() => setExpanded(!expanded)}
                className="text-xs text-indigo-600 hover:text-indigo-800 flex items-center gap-0.5 mt-1"
              >
                {expanded ? <><ChevronUp className="w-3 h-3" /> Show less</> : <><ChevronDown className="w-3 h-3" /> Show more</>}
              </button>
            )}
          </div>
        )}

        {/* Hashtags */}
        {post.hashtags?.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-2">
            {post.hashtags.map((tag, i) => (
              <span key={i} className="text-xs bg-indigo-50 text-indigo-600 px-2 py-0.5 rounded-full">
                {tag.startsWith('#') ? tag : `#${tag}`}
              </span>
            ))}
          </div>
        )}

        {/* CTA */}
        {editing ? (
          <input
            value={editCta}
            onChange={(e) => setEditCta(e.target.value)}
            placeholder="Call to action…"
            className="w-full border border-slate-200 rounded-lg px-3 py-1.5 text-sm mt-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        ) : post.call_to_action ? (
          <p className="text-xs text-slate-500 mt-2 italic">📣 {post.call_to_action}</p>
        ) : null}

        {/* Visual suggestion */}
        {post.visual_suggestion && (
          <p className="text-xs text-slate-400 mt-1">🖼️ {post.visual_suggestion}</p>
        )}

        {/* Metrics */}
        <div className="flex items-center gap-3 mt-3 pt-3 border-t border-slate-50">
          <span className="text-xs text-slate-400">{post.character_count} chars</span>
          <span className="text-xs text-slate-400">{post.word_count} words</span>
          <span className="flex-1" />

          {/* Actions */}
          {editing ? (
            <div className="flex gap-2">
              <button
                onClick={() => setEditing(false)}
                className="text-xs px-3 py-1 rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-50"
              >
                Cancel
              </button>
              <button
                onClick={handleSave}
                disabled={saving}
                className="text-xs px-3 py-1 rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-60"
              >
                {saving ? 'Saving…' : 'Save'}
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-1">
              <button onClick={markReady} title={post.status === 'ready' ? 'Mark as draft' : 'Mark as ready'}
                className={`p-1.5 rounded-lg transition-colors ${post.status === 'ready' ? 'text-emerald-500 bg-emerald-50' : 'text-slate-400 hover:text-emerald-500 hover:bg-emerald-50'}`}>
                <Check className="w-3.5 h-3.5" />
              </button>
              <button onClick={handleCopy} title="Copy text"
                className="p-1.5 rounded-lg text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 transition-colors">
                {copied ? <Check className="w-3.5 h-3.5 text-emerald-500" /> : <Copy className="w-3.5 h-3.5" />}
              </button>
              <button onClick={() => setEditing(true)} title="Edit"
                className="p-1.5 rounded-lg text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 transition-colors">
                <Edit3 className="w-3.5 h-3.5" />
              </button>
              <button onClick={handleRegenerate} disabled={regenerating} title="Regenerate"
                className="p-1.5 rounded-lg text-slate-400 hover:text-violet-600 hover:bg-violet-50 transition-colors disabled:opacity-40">
                <RefreshCw className={`w-3.5 h-3.5 ${regenerating ? 'animate-spin' : ''}`} />
              </button>
              <button onClick={handleDelete} title="Delete"
                className="p-1.5 rounded-lg text-slate-400 hover:text-red-500 hover:bg-red-50 transition-colors">
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
