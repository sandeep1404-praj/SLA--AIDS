import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
  Zap, ArrowRight, CheckCircle, FileText, Calendar, Sparkles,
  Shield, ChevronRight
} from 'lucide-react';

const FEATURES = [
  {
    icon: Sparkles,
    title: 'AI-Powered Analysis',
    desc: 'Gemini extracts themes, facts, statistics, and key takeaways from your article with precision.',
    color: 'bg-indigo-50 text-indigo-600',
  },
  {
    icon: Calendar,
    title: '7-Day Strategic Calendar',
    desc: 'Each day gets a unique content angle — hook, insight, how-to, evidence, problem/solution, discussion, and summary.',
    color: 'bg-violet-50 text-violet-600',
  },
  {
    icon: FileText,
    title: 'Platform-Specific Posts',
    desc: 'LinkedIn, X, Instagram, Facebook, and short-video scripts — each tailored to platform norms and limits.',
    color: 'bg-cyan-50 text-cyan-600',
  },
  {
    icon: Shield,
    title: 'Responsible AI',
    desc: 'Source-grounded generation. Claims verified against your article. Warnings flag unsupported content.',
    color: 'bg-emerald-50 text-emerald-600',
  },
];

const STEPS = [
  { step: '01', title: 'Paste Your Article', desc: 'Input any long-form article, blog post, or research piece.' },
  { step: '02', title: 'Configure & Generate', desc: 'Choose platforms, tone, audience, and let Gemini build your 7-day calendar.' },
  { step: '03', title: 'Edit & Export', desc: 'Review AI posts, make edits, and export as JSON, CSV, or Markdown.' },
];

const FAQ = [
  { q: 'Does ContentFlow AI publish posts automatically?', a: 'No. ContentFlow AI generates and organizes content for your review. You export or copy posts and publish them yourself.' },
  { q: 'Can I edit the AI-generated posts?', a: 'Yes. Every post is editable inline, and full version history is preserved so you can restore previous versions.' },
  { q: 'How does source grounding work?', a: 'The AI is instructed to use only facts from your article. A verification step flags claims that may lack source support.' },
  { q: 'What platforms are supported?', a: 'LinkedIn, X (Twitter), Instagram, Facebook, and short-video scripts (YouTube Shorts / Instagram Reels).' },
  { q: 'Is my data secure?', a: 'Articles and calendars are stored under your account. JWT authentication ensures only you can access your data.' },
];

const PREVIEW_DAYS = [
  { day: 1, theme: 'Hook & Introduction', platform: 'LinkedIn', snippet: 'Most companies create content. Few create strategic content. Here\'s the difference that matters…' },
  { day: 2, theme: 'Key Insight', platform: 'X', snippet: 'The biggest content mistake? Posting the same thing everywhere. Platform-native content wins every time. 🧵' },
  { day: 3, theme: 'Practical Tips', platform: 'Instagram', snippet: '3 steps to repurpose one article into a week of content 📱✨ Save this for later!' },
  { day: 4, theme: 'Evidence & Data', platform: 'Facebook', snippet: 'What does the research actually say about content repurposing? Here\'s what we found in the article…' },
  { day: 5, theme: 'Problem & Solution', platform: 'LinkedIn', snippet: 'Content creators waste 80% of their writing. This AI-powered system changes that completely.' },
];

export default function LandingPage() {
  const { user } = useAuth();
  const [openFaq, setOpenFaq] = useState(null);

  return (
    <div className="min-h-screen bg-white">
      {/* Navbar */}
      <nav className="sticky top-0 z-50 bg-white/90 backdrop-blur border-b border-slate-100">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex items-center justify-between h-16">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center">
              <Zap className="w-4 h-4 text-white" />
            </div>
            <span className="font-bold text-slate-900 text-lg">ContentFlow AI</span>
          </div>

          <div className="hidden md:flex items-center gap-8 text-sm text-slate-600">
            <a href="#features" className="hover:text-indigo-600 transition-colors">Features</a>
            <a href="#how-it-works" className="hover:text-indigo-600 transition-colors">How It Works</a>
            <a href="#platforms" className="hover:text-indigo-600 transition-colors">Platforms</a>
            <a href="#about" className="hover:text-indigo-600 transition-colors">About</a>
            <a href="#faq" className="hover:text-indigo-600 transition-colors">FAQ</a>
          </div>

          <div className="flex items-center gap-3">
            {user ? (
              <Link to="/dashboard" className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors">
                Dashboard <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            ) : (
              <>
                <Link to="/login" className="text-sm text-slate-600 hover:text-indigo-600 font-medium">Login</Link>
                <Link to="/register" className="bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors">
                  Get Started
                </Link>
              </>
            )}
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative overflow-hidden bg-gradient-to-b from-slate-50 to-white pt-20 pb-24">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_rgba(99,102,241,0.08)_0%,_transparent_60%)]" />
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 text-center relative">
          <div className="inline-flex items-center gap-2 bg-indigo-50 text-indigo-700 text-xs font-medium px-3 py-1.5 rounded-full mb-6 border border-indigo-100">
            <Sparkles className="w-3 h-3" />
            Powered by Google Gemini
          </div>

          <h1 className="text-5xl sm:text-6xl font-bold text-slate-900 mb-6 leading-tight">
            One Article.{' '}
            <span className="gradient-text">Seven Days</span>
            {' '}of Content.
          </h1>

          <p className="text-xl text-slate-500 max-w-2xl mx-auto mb-10 leading-relaxed">
            Transform your long-form content into a strategic, platform-specific social media calendar with AI.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link
              to={user ? '/create' : '/register'}
              className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold px-8 py-3.5 rounded-xl transition-colors text-base shadow-lg shadow-indigo-200"
            >
              Generate My Calendar <ArrowRight className="w-4 h-4" />
            </Link>
            <a href="#features" className="flex items-center gap-2 text-slate-700 hover:text-indigo-600 font-medium px-6 py-3.5 rounded-xl border border-slate-200 hover:border-indigo-200 transition-colors text-base">
              Explore Features
            </a>
          </div>

          {/* Calendar preview */}
          <div className="mt-16 bg-white rounded-2xl shadow-2xl border border-slate-100 overflow-hidden max-w-4xl mx-auto">
            <div className="bg-gradient-to-r from-indigo-600 to-violet-600 px-6 py-3 flex items-center gap-2">
              <div className="flex gap-1.5">
                {[0,1,2].map(i => <div key={i} className="w-2.5 h-2.5 rounded-full bg-white/30" />)}
              </div>
              <span className="text-white/80 text-sm ml-2">7-Day Content Calendar Preview</span>
            </div>
            <div className="p-6">
              <div className="grid grid-cols-1 sm:grid-cols-5 gap-3">
                {PREVIEW_DAYS.map((item) => (
                  <div key={item.day} className="bg-slate-50 rounded-xl p-3 text-left border border-slate-100">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs font-bold text-indigo-600">Day {item.day}</span>
                      <span className="text-xs bg-white text-slate-500 px-1.5 py-0.5 rounded-full border border-slate-200">{item.platform}</span>
                    </div>
                    <p className="text-xs font-semibold text-slate-700 mb-1">{item.theme}</p>
                    <p className="text-xs text-slate-500 line-clamp-3">{item.snippet}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="py-20 bg-white">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-14">
            <h2 className="text-3xl sm:text-4xl font-bold text-slate-900 mb-4">Everything you need to repurpose content</h2>
            <p className="text-slate-500 max-w-xl mx-auto">Intelligent content planning powered by Google Gemini — not a simple rewriting tool.</p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {FEATURES.map(({ icon: Icon, title, desc, color }) => (
              <div key={title} className="p-6 rounded-2xl border border-slate-100 hover:border-indigo-100 hover:shadow-md transition-all">
                <div className={`w-10 h-10 rounded-xl flex items-center justify-center mb-4 ${color}`}>
                  <Icon className="w-5 h-5" />
                </div>
                <h3 className="font-semibold text-slate-900 mb-2">{title}</h3>
                <p className="text-sm text-slate-500 leading-relaxed">{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How it works */}
      <section id="how-it-works" className="py-20 bg-slate-50">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-14">
            <h2 className="text-3xl sm:text-4xl font-bold text-slate-900 mb-4">Three steps to a full week of content</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {STEPS.map(({ step, title, desc }) => (
              <div key={step} className="text-center">
                <div className="w-12 h-12 rounded-2xl bg-indigo-600 text-white font-bold text-lg flex items-center justify-center mx-auto mb-4">{step}</div>
                <h3 className="font-semibold text-slate-900 text-lg mb-2">{title}</h3>
                <p className="text-slate-500 text-sm leading-relaxed">{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Platforms */}
      <section id="platforms" className="py-20 bg-white">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl sm:text-4xl font-bold text-slate-900 mb-4">Supported Platforms</h2>
          <p className="text-slate-500 mb-12">Platform-native content respecting each channel's character limits and culture.</p>
          <div className="flex flex-wrap justify-center gap-6">
            {[
              { name: 'LinkedIn', color: 'bg-blue-600', detail: 'Professional posts, polls, insight threads' },
              { name: 'X (Twitter)', color: 'bg-black', detail: 'Single posts & threaded content, 280 char limit' },
              { name: 'Instagram', color: 'bg-gradient-to-r from-orange-400 to-pink-600', detail: 'Captions, carousel outlines, hashtag sets' },
              { name: 'Facebook', color: 'bg-blue-500', detail: 'Discussion posts, community questions' },
              { name: 'Short Video', color: 'bg-red-500', detail: 'YouTube Shorts & Reels scripts, hooks, visual cues' },
            ].map(({ name, color, detail }) => (
              <div key={name} className="flex flex-col items-center gap-2 w-36">
                <div className={`w-14 h-14 rounded-2xl ${color} flex items-center justify-center text-white font-bold text-xl shadow-lg`}>{name[0]}</div>
                <p className="font-semibold text-slate-800 text-sm">{name}</p>
                <p className="text-xs text-slate-400 text-center">{detail}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Responsible AI */}
      <section id="about" className="py-20 bg-indigo-600 text-white">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <Shield className="w-12 h-12 mx-auto mb-6 text-indigo-200" />
          <h2 className="text-3xl font-bold mb-4">Responsible AI Generation</h2>
          <p className="text-indigo-100 text-lg leading-relaxed max-w-2xl mx-auto mb-8">
            ContentFlow AI uses source-grounded generation. The model is instructed to use only information from your article. A verification step flags claims that may lack source support. Human review remains essential before publication.
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 text-left">
            {[
              { title: 'Source Grounded', desc: 'Gemini only generates content supported by your article.' },
              { title: 'Claim Verification', desc: 'A second AI pass flags potentially unsupported claims for review.' },
              { title: 'Human Review Required', desc: 'All AI-generated content requires your review before any use.' },
            ].map(({ title, desc }) => (
              <div key={title} className="bg-white/10 rounded-xl p-4 border border-white/10">
                <CheckCircle className="w-5 h-5 text-indigo-200 mb-2" />
                <p className="font-semibold text-white mb-1">{title}</p>
                <p className="text-indigo-200 text-sm">{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section id="faq" className="py-20 bg-white">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl font-bold text-slate-900 text-center mb-12">Frequently Asked Questions</h2>
          <div className="space-y-3">
            {FAQ.map(({ q, a }, i) => (
              <div key={i} className="border border-slate-100 rounded-xl overflow-hidden">
                <button
                  onClick={() => setOpenFaq(openFaq === i ? null : i)}
                  className="w-full flex items-center justify-between px-5 py-4 text-left font-medium text-slate-800 hover:bg-slate-50 transition-colors"
                >
                  {q}
                  <ChevronRight className={`w-4 h-4 text-slate-400 transition-transform flex-shrink-0 ml-2 ${openFaq === i ? 'rotate-90' : ''}`} />
                </button>
                {openFaq === i && (
                  <div className="px-5 pb-4 text-sm text-slate-500 leading-relaxed border-t border-slate-50">{a}</div>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 bg-gradient-to-r from-indigo-600 to-violet-600">
        <div className="max-w-3xl mx-auto px-4 text-center text-white">
          <h2 className="text-3xl font-bold mb-4">Ready to transform your content strategy?</h2>
          <p className="text-indigo-100 mb-8">Generate your first 7-day content calendar in minutes.</p>
          <Link to={user ? '/create' : '/register'}
            className="inline-flex items-center gap-2 bg-white text-indigo-700 font-semibold px-8 py-3.5 rounded-xl hover:bg-indigo-50 transition-colors shadow-lg">
            Get Started Free <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-slate-900 text-slate-400 py-12">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 rounded-lg bg-indigo-600 flex items-center justify-center">
                <Zap className="w-3.5 h-3.5 text-white" />
              </div>
              <span className="font-bold text-white">ContentFlow AI</span>
            </div>
            <div className="flex items-center gap-6 text-sm">
              <a href="#features" className="hover:text-white transition-colors">Features</a>
              <a href="#how-it-works" className="hover:text-white transition-colors">How It Works</a>
              <a href="#faq" className="hover:text-white transition-colors">FAQ</a>
              <Link to="/login" className="hover:text-white transition-colors">Login</Link>
            </div>
            <p className="text-sm text-center">Academic project · SDG 9 — Industry, Innovation &amp; Infrastructure</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
