import api from './api';

export const postService = {
  listByCalendar: (calendarId, params) =>
    api.get(`/api/calendars/${calendarId}/posts`, { params }),
  get: (id) => api.get(`/api/posts/${id}`),
  update: (id, data) => api.patch(`/api/posts/${id}`, data),
  delete: (id) => api.delete(`/api/posts/${id}`),
  regenerate: (id) => api.post(`/api/posts/${id}/regenerate`),
  getVersions: (id) => api.get(`/api/posts/${id}/versions`),
  restoreVersion: (postId, versionId) =>
    api.post(`/api/posts/${postId}/restore/${versionId}`),
};
