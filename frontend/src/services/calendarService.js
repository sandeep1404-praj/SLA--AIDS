import api from './api';

export const calendarService = {
  generate: (data) => api.post('/api/calendars/generate', data),
  list: (params) => api.get('/api/calendars', { params }),
  get: (id) => api.get(`/api/calendars/${id}`),
  update: (id, data) => api.patch(`/api/calendars/${id}`, data),
  delete: (id) => api.delete(`/api/calendars/${id}`),
  getStatus: (id) => api.get(`/api/calendars/${id}/generation-status`),
  regenerateDay: (id, day) => api.post(`/api/calendars/${id}/regenerate-day/${day}`),
  exportJson: (id) => api.get(`/api/calendars/${id}/export/json`, { responseType: 'blob' }),
  exportCsv: (id) => api.get(`/api/calendars/${id}/export/csv`, { responseType: 'blob' }),
  exportMarkdown: (id) => api.get(`/api/calendars/${id}/export/markdown`, { responseType: 'blob' }),
};
