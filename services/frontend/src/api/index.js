import axios from 'axios'

// Хранится в памяти — не в localStorage (XSS).
// Устанавливается при логине/refresh, сбрасывается при logout.
export const tokenRef = { value: null }

const api = axios.create({ withCredentials: true })

// ── Request: добавляем Authorization header ───────────────
api.interceptors.request.use(config => {
  if (tokenRef.value) config.headers.Authorization = `Bearer ${tokenRef.value}`
  return config
})

// Эти эндпоинты возвращают 401 когда пользователь просто не залогинен —
// refresh здесь бессмысленен и создаёт бесконечный цикл.
const NO_REFRESH = ['/auth/api/v1/me', '/auth/api/v1/refresh', '/auth/api/v1/login']

let refreshing = false
let refreshQueue = []

// ── Response: при 401 пробуем refresh один раз ───────────
api.interceptors.response.use(
  res => res,
  async err => {
    const original = err.config
    const url = original?.url ?? ''
    const skip = NO_REFRESH.some(u => url.includes(u))

    if (err.response?.status === 401 && !original._retry && !skip) {
      if (refreshing) {
        return new Promise((resolve, reject) => {
          refreshQueue.push({ resolve, reject })
        }).then(() => api(original)).catch(e => Promise.reject(e))
      }
      original._retry = true
      refreshing = true
      try {
        const { data } = await axios.post('/auth/api/v1/refresh', {}, { withCredentials: true })
        tokenRef.value = data.access_token
        original.headers.Authorization = `Bearer ${data.access_token}`
        refreshQueue.forEach(p => p.resolve())
        refreshQueue = []
        return api(original)
      } catch {
        refreshQueue.forEach(p => p.reject(err))
        refreshQueue = []
        tokenRef.value = null
        return Promise.reject(err)
      } finally {
        refreshing = false
      }
    }
    return Promise.reject(err)
  },
)

// Auth
export const authApi = {
  login:    (username, password) =>
    api.post('/auth/api/v1/login', { username, password }),
  register: (username, email, password) =>
    api.post('/auth/api/v1/registration', { username, email, password }),
  confirm: token => {
    const form = new URLSearchParams()
    form.append('token', token)
    return api.post('/auth/api/v1/confirm', form)
  },
  logout:         () => api.post('/auth/api/v1/logout'),
  me:             () => api.get('/auth/api/v1/me'),
  refresh:        () => axios.post('/auth/api/v1/refresh', {}, { withCredentials: true }),
  changePassword: (userId, currentPassword, newPassword) =>
    api.post(`/auth/api/v1/user/${userId}/password`, {
      current_password: currentPassword,
      new_password: newPassword,
    }),
  // Admin
  listUsers:  () => api.get('/auth/api/v1/users'),
  getUser:    id => api.get(`/auth/api/v1/user/${id}`),
  deleteUser: id => api.delete(`/auth/api/v1/user/${id}`),
  patchUser:  (id, data) => api.patch(`/auth/api/v1/user/${id}`, data),
  addRole:    (id, role) => api.post(`/auth/api/v1/role/${id}`, null, { params: { role } }),
  deleteRole: (id, role) => api.delete(`/auth/api/v1/role/${id}`, { params: { role } }),
}

// Gallery — photos
export const photosApi = {
  list:   (params = {}) => api.get('/api/v1/photos', { params }),
  get:    id            => api.get(`/api/v1/photos/${id}`),
  upload: formData      =>
    api.post('/api/v1/photos', formData, { headers: { 'Content-Type': 'multipart/form-data' } }),
  move:   (id, albumId) => api.patch(`/api/v1/photos/${id}/album`, { album_id: albumId }),
  delete: id            => api.delete(`/api/v1/photos/${id}`),
}

// Gallery — albums
export const albumsApi = {
  list:   ()           => api.get('/api/v1/albums'),
  create: name         => api.post('/api/v1/albums', { name }),
  rename: (id, name)   => api.put(`/api/v1/albums/${id}`, { name }),
  delete: id           => api.delete(`/api/v1/albums/${id}`),
}
