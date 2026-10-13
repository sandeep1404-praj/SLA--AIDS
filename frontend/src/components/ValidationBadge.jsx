import { CheckCircle, AlertTriangle, XCircle } from 'lucide-react';

const CONFIG = {
  valid: { icon: CheckCircle, color: 'text-emerald-500', bg: 'bg-emerald-50', label: 'Valid' },
  warning: { icon: AlertTriangle, color: 'text-amber-500', bg: 'bg-amber-50', label: 'Warning' },
  invalid: { icon: XCircle, color: 'text-red-500', bg: 'bg-red-50', label: 'Invalid' },
};

export default function ValidationBadge({ status, warnings = [] }) {
  const cfg = CONFIG[status] || CONFIG.valid;
  const Icon = cfg.icon;

  return (
    <div className="relative group inline-block">
      <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${cfg.bg} ${cfg.color}`}>
        <Icon className="w-3 h-3" />
        {cfg.label}
      </span>
      {warnings.length > 0 && (
        <div className="absolute bottom-full left-0 mb-2 hidden group-hover:block z-50 w-72 bg-slate-900 text-white text-xs rounded-lg p-3 shadow-xl">
          <ul className="space-y-1">
            {warnings.map((w, i) => (
              <li key={i} className="flex gap-1.5">
                <span className="text-amber-400 flex-shrink-0">⚠</span>
                {w}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
