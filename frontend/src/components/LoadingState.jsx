export default function LoadingState({ message = 'Loading…' }) {
  return (
    <div className="flex flex-col items-center justify-center py-20 text-slate-500">
      <div className="spinner w-10 h-10 mb-4" />
      <p className="text-sm">{message}</p>
    </div>
  );
}
