import { useAuth } from '../context/AuthContext';
import { Zap, User, Mail, Calendar } from 'lucide-react';

export default function SettingsPage() {
  const { user } = useAuth();

  return (
    <div className="max-w-2xl fade-in">
      <h1 className="text-2xl font-bold text-slate-900 mb-8">Settings</h1>

      <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-6 mb-6">
        <h2 className="font-semibold text-slate-900 mb-4 flex items-center gap-2">
          <User className="w-4 h-4 text-indigo-600" /> Profile
        </h2>
        <div className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1 uppercase tracking-wide">Name</label>
            <div className="px-4 py-2.5 bg-slate-50 rounded-xl text-slate-800 text-sm">{user?.name}</div>
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1 uppercase tracking-wide">Email</label>
            <div className="px-4 py-2.5 bg-slate-50 rounded-xl text-slate-800 text-sm flex items-center gap-2">
              <Mail className="w-3.5 h-3.5 text-slate-400" />
              {user?.email}
            </div>
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1 uppercase tracking-wide">Member Since</label>
            <div className="px-4 py-2.5 bg-slate-50 rounded-xl text-slate-800 text-sm flex items-center gap-2">
              <Calendar className="w-3.5 h-3.5 text-slate-400" />
              {user?.created_at ? new Date(user.created_at).toLocaleDateString() : '—'}
            </div>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-6">
        <h2 className="font-semibold text-slate-900 mb-4 flex items-center gap-2">
          <Zap className="w-4 h-4 text-indigo-600" /> About ContentFlow AI
        </h2>
        <div className="prose prose-sm text-slate-600 space-y-3">
          <p>ContentFlow AI is an academic engineering project that demonstrates AI-powered content repurposing using the Google Gemini API.</p>
          <p>The system uses a 7-stage pipeline: article preprocessing, structured analysis, weekly planning, platform-specific generation, source verification, programmatic validation, and persistence.</p>
          <p className="text-xs text-slate-400">Aligned with <strong>SDG 9 — Industry, Innovation and Infrastructure</strong>. All generated content requires human review before publication.</p>
        </div>
      </div>
    </div>
  );
}
