/**
 * Normalize FastAPI / axios error payloads into a user-visible string.
 */
export function formatApiError(error, fallback = 'Something went wrong. Please try again.') {
  const detail = error?.response?.data?.detail;
  if (typeof detail === 'string' && detail.trim()) {
    return detail;
  }
  if (Array.isArray(detail)) {
    const parts = detail
      .map((item) => {
        if (typeof item === 'string') return item;
        if (item?.msg) return item.msg;
        if (item?.message) return item.message;
        return null;
      })
      .filter(Boolean);
    if (parts.length) return parts.join(' ');
  }
  if (error?.message && !error.message.includes('Network Error')) {
    return error.message;
  }
  if (!error?.response) {
    return 'Cannot reach the server. Make sure the backend is running on port 8000.';
  }
  return fallback;
}
