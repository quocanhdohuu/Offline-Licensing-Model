import client from './client'

export const authApi = {
  login: async (username, password) => {
    const res = await client.post('/auth/login', { username, password })
    return res.data
  },
  getMe: async () => {
    const res = await client.get('/auth/me')
    return res.data
  },
}

export const licenseApi = {
  getLicenses: async (params = {}) => {
    const res = await client.get('/licenses', { params })
    return res.data
  },
  getLicenseDetail: async (id) => {
    const res = await client.get(`/licenses/${id}`)
    return res.data
  },
  checkDf: async (df) => {
    const res = await client.get(`/licenses/check-df/${encodeURIComponent(df)}`)
    return res.data
  },
  createLicense: async (data) => {
    const res = await client.post('/licenses', data)
    return res.data
  },
  upgradeLicense: async (id, data) => {
    const res = await client.post(`/licenses/${id}/upgrade`, data)
    return res.data
  },
  getStats: async () => {
    const res = await client.get('/stats')
    return res.data
  },
  getDownloadQrUrl: (id) => `/api/licenses/${id}/download-qr`,
  getDownloadLicUrl: (id) => `/api/licenses/${id}/download-lic`,
}

