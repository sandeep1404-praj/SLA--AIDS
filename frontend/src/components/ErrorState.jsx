import { AlertCircle } from 'lucide-react';

export default function ErrorState({ message = 'Something went wrong', retry }) {
  return (
    <div className="flex flex-col items-center justify-center py-20 text-slate-500">
      <AlertCircle className="w-12 h-12 text-red-400 mb-4" />
      <p className="text-sm font-medium text-slate-700">{message}</p>
      {retry && (
        <button
          onClick={retry}
          className="mt-4 px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm hover:bg-indigo-700 transition-colors"
        >
          Try again
        </button>
      )}
    </div>
  );
}
