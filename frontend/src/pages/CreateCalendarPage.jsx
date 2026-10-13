import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { articleService } from '../services/articleService';
import { calendarService } from '../services/calendarService';
import { Sparkles, ChevronRight, ChevronLeft, AlertCircle, Check } from 'lucide-react';
import { formatApiError } from '../utils/apiError';

const PLATFORMS = [
  { id: 'linkedin', label: 'LinkedIn', emoji: '💼', desc: 'Professional posts & insights' },
  { id: 'x', label: 'X (Twitter)', emoji: '𝕏', desc: 'Posts & threads, 280 chars' },
  { id: 'instagram', label: 'Instagram', emoji: '📸', desc: 'Captions & carousel outlines' },
  { id: 'facebook', label: 'Facebook', emoji: '👥', desc: 'Discussion-oriented posts' },
  { id: 'short_video', label: 'Short Video', emoji: '🎬', desc: 'YouTube Shorts / Reels scripts' },
];

const TONES = ['professional', 'conversational', 'educational', 'informative', 'persuasive', 'storytelling', 'inspirational', 'humorous'];
const OBJECTIVES = ['education', 'brand_awareness', 'audience_engagement', 'lead_generation', 'thought_leadership', 'community_building'];

export default function CreateCalendarPage() {
  const navigate = useNavigate();
  const { register, handleSubmit, watch, formState: { errors } } = useForm({
    defaultValues: {
      tone: 'professional',
      content_objective: 'education',
      language: 'English',
      start_date: new Date().toISOString().split('T')[0],
    }
  });

  const [step, setStep] = useState(1);
  const [selectedPlatforms, setSelectedPlatforms] = useState([]);
  const [apiError, setApiError] = useState('');
  const [loading, setLoading] = useState(false);

  const articleText = watch('article_text', '');

  const togglePlatform = (id) => {
    setSelectedPlatforms((prev) =>
      prev.includes(id) ? prev.filter((p) => p !== id) : [...prev, id]
    );
  };

  const onSubmit = async (data) => {
    if (selectedPlatforms.length === 0) {
      setApiError('Please select at least one platform.');
      return;
    }
    setLoading(true);
    setApiError('');
    try {
      // Step 1: create article
      const artRes = await articleService.create({
        title: data.title,
        article_text: data.article_text,
        source_url: data.source_url || null,
        language: data.language,
      });

      // Step 2: generate calendar
      const calRes = await calendarService.generate({
        article_id: artRes.data.id,
        title: data.title,
        target_audience: data.target_audience,
        industry: data.industry,
        content_objective: data.content_objective,
        tone: data.tone,
        start_date: data.start_date,
        platforms: selectedPlatforms,
      });

      navigate(`/calendars/${calRes.data.calendar_id}`);
    } catch (e) {
      setApiError(formatApiError(e, 'Generation failed. Please try again.'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto fade-in">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-900">Create Content Calendar</h1>
        <p className="text-slate-500 text-sm mt-1">Transform an article into a 7-day social media strategy.</p>
      </div>

      {/* Progress */}
      <div className="flex items-center gap-2 mb-8">
        {[1, 2, 3].map((s) => (
          <div key={s} className="flex items-center gap-2">
            <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold border-2 transition-colors
              ${step >= s ? 'bg-indigo-600 border-indigo-600 text-white' : 'border-slate-200 text-slate-400'}`}>
              {step > s ? <Check className="w-3.5 h-3.5" /> : s}
            </div>
            <span className={`text-sm ${step === s ? 'font-medium text-slate-900' : 'text-slate-400'}`}>
              {s === 1 ? 'Article' : s === 2 ? 'Settings' : 'Generate'}
            </span>
            {s < 3 && <div className={`h-px w-8 ${step > s ? 'bg-indigo-400' : 'bg-slate-200'}`} />}
          </div>
        ))}
      </div>

      {apiError && (
        <div className="flex items-center gap-2 bg-red-50 border border-red-100 rounded-xl px-4 py-3 mb-6 text-red-600 text-sm">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          {apiError}
        </div>
      )}

      <form onSubmit={handleSubmit(onSubmit)}>
        {/* Step 1: Article */}
        {step === 1 && (
          <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-6 space-y-5">
            <h2 className="font-semibold text-slate-900 text-lg">Article Details</h2>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1.5">Article Title *</label>
              <input
                {...register('title', { required: 'Title is required' })}
                className="w-full border border-slate-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                placeholder="e.g. The Future of Remote Work"
              />
              {errors.title && <p className="text-xs text-red-500 mt-1">{errors.title.message}</p>}
            </div>

            <div>
              <div className="flex justify-between items-center mb-1.5">
                <label className="text-sm font-medium text-slate-700">Article Text *</label>
                <span className="text-xs text-slate-400">{articleText.length} chars</span>
              </div>
              <textarea
                {...register('article_text', {
                  required: 'Article text is required',
                  minLength: { value: 100, message: 'At least 100 characters required' },
                })}
                rows={10}
                className="w-full border border-slate-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-y"
                placeholder="Paste your full article text here…"
              />
              {errors.article_text && <p className="text-xs text-red-500 mt-1">{errors.article_text.message}</p>}
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">Source URL (optional)</label>
                <input
                  {...register('source_url')}
                  className="w-full border border-slate-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  placeholder="https://…"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">Language</label>
                <input
                  {...register('language')}
                  className="w-full border border-slate-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  placeholder="English"
                />
              </div>
            </div>

            <button
              type="button"
              onClick={() => setStep(2)}
              className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-2.5 rounded-xl text-sm font-medium transition-colors ml-auto"
            >
              Next: Settings <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        )}

        {/* Step 2: Settings */}
        {step === 2 && (
          <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-6 space-y-5">
            <h2 className="font-semibold text-slate-900 text-lg">Calendar Settings</h2>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">Target Audience *</label>
                <input
                  {...register('target_audience', { required: 'Required' })}
                  className="w-full border border-slate-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  placeholder="e.g. Marketing professionals"
                />
                {errors.target_audience && <p className="text-xs text-red-500 mt-1">{errors.target_audience.message}</p>}
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">Industry / Topic *</label>
                <input
                  {...register('industry', { required: 'Required' })}
                  className="w-full border border-slate-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  placeholder="e.g. Technology"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">Tone</label>
              <div className="flex flex-wrap gap-2">
                {TONES.map((t) => {
                  const selected = watch('tone') === t;
                  return (
                    <label key={t} className={`cursor-pointer px-3 py-1.5 rounded-full text-xs font-medium border transition-colors
                      ${selected ? 'bg-indigo-600 text-white border-indigo-600' : 'bg-white text-slate-600 border-slate-200 hover:border-indigo-300'}`}>
                      <input {...register('tone')} type="radio" value={t} className="hidden" />
                      {t.charAt(0).toUpperCase() + t.slice(1)}
                    </label>
                  );
                })}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">Content Objective</label>
              <div className="flex flex-wrap gap-2">
                {OBJECTIVES.map((o) => {
                  const selected = watch('content_objective') === o;
                  return (
                    <label key={o} className={`cursor-pointer px-3 py-1.5 rounded-full text-xs font-medium border transition-colors
                      ${selected ? 'bg-violet-600 text-white border-violet-600' : 'bg-white text-slate-600 border-slate-200 hover:border-violet-300'}`}>
                      <input {...register('content_objective')} type="radio" value={o} className="hidden" />
                      {o.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase())}
                    </label>
                  );
                })}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1.5">Calendar Start Date</label>
              <input
                type="date"
                {...register('start_date')}
                className="w-full border border-slate-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-3">
                Target Platforms * <span className="text-slate-400 text-xs">(select one or more)</span>
              </label>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {PLATFORMS.map(({ id, label, emoji, desc }) => {
                  const sel = selectedPlatforms.includes(id);
                  return (
                    <button
                      type="button"
                      key={id}
                      onClick={() => togglePlatform(id)}
                      className={`flex items-center gap-3 p-3 rounded-xl border text-left transition-all
                        ${sel ? 'border-indigo-500 bg-indigo-50' : 'border-slate-200 hover:border-indigo-200 hover:bg-slate-50'}`}
                    >
                      <span className="text-xl">{emoji}</span>
                      <div className="flex-1">
                        <p className="text-sm font-medium text-slate-800">{label}</p>
                        <p className="text-xs text-slate-400">{desc}</p>
                      </div>
                      {sel && <Check className="w-4 h-4 text-indigo-600" />}
                    </button>
                  );
                })}
              </div>
            </div>

            <div className="flex items-center justify-between pt-2">
              <button
                type="button"
                onClick={() => setStep(1)}
                className="flex items-center gap-2 text-slate-600 hover:text-slate-900 text-sm font-medium"
              >
                <ChevronLeft className="w-4 h-4" /> Back
              </button>
              <button
                type="button"
                onClick={() => {
                  if (selectedPlatforms.length === 0) {
                    setApiError('Please select at least one platform.');
                    return;
                  }
                  setApiError('');
                  setStep(3);
                }}
                className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-2.5 rounded-xl text-sm font-medium transition-colors"
              >
                Review & Generate <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}

        {/* Step 3: Review */}
        {step === 3 && (
          <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-6 space-y-5">
            <h2 className="font-semibold text-slate-900 text-lg">Ready to Generate</h2>

            <div className="bg-slate-50 rounded-xl p-4 space-y-2 text-sm text-slate-700">
              <div className="flex justify-between"><span className="text-slate-500">Article:</span><span className="font-medium">{watch('title')}</span></div>
              <div className="flex justify-between"><span className="text-slate-500">Audience:</span><span className="font-medium">{watch('target_audience')}</span></div>
              <div className="flex justify-between"><span className="text-slate-500">Tone:</span><span className="font-medium capitalize">{watch('tone')}</span></div>
              <div className="flex justify-between"><span className="text-slate-500">Objective:</span><span className="font-medium">{watch('content_objective')?.replace(/_/g, ' ')}</span></div>
              <div className="flex justify-between"><span className="text-slate-500">Platforms:</span><span className="font-medium">{selectedPlatforms.join(', ')}</span></div>
              <div className="flex justify-between"><span className="text-slate-500">Estimated posts:</span><span className="font-medium">{selectedPlatforms.length * 7}</span></div>
            </div>

            <div className="bg-amber-50 border border-amber-100 rounded-xl p-4 text-xs text-amber-700">
              ⏱ Generation may take 1-3 minutes. The calendar will be ready in the background — you'll be redirected to track progress.
            </div>

            <div className="flex items-center justify-between pt-2">
              <button type="button" onClick={() => setStep(2)}
                className="flex items-center gap-2 text-slate-600 hover:text-slate-900 text-sm font-medium">
                <ChevronLeft className="w-4 h-4" /> Back
              </button>
              <button
                type="submit"
                disabled={loading}
                className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white px-8 py-3 rounded-xl text-sm font-semibold transition-colors disabled:opacity-60 shadow-lg shadow-indigo-200"
              >
                {loading ? (
                  <><div className="spinner w-4 h-4" /> Generating…</>
                ) : (
                  <><Sparkles className="w-4 h-4" /> Generate Calendar</>
                )}
              </button>
            </div>
          </div>
        )}
      </form>
    </div>
  );
}
