import api from './api';

export const articleService = {
  create: (data) => api.post('/api/articles', data),
  list: (params) => api.get('/api/articles', { params }),
  get: (id) => api.get(`/api/articles/${id}`),
  update: (id, data) => api.patch(`/api/articles/${id}`, data),
  delete: (id) => api.delete(`/api/articles/${id}`),
};
