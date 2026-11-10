import React, { createContext, useContext, useState, useEffect } from 'react'
import { authApi } from '../api/licenseApi'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [token, setToken] = useState(localStorage.getItem('olm_access_token'))
  const [loading, setLoading] = useState(true)

  // Khôi phục phiên làm việc khi load lại trang
  useEffect(() => {
    async function loadUser() {
      const savedToken = localStorage.getItem('olm_access_token')
      if (savedToken) {
        try {
          const userData = await authApi.getMe()
          setUser(userData)
          setToken(savedToken)
        } catch (err) {
          console.error('Không thể khôi phục phiên:', err)
          localStorage.removeItem('olm_access_token')
          setUser(null)
          setToken(null)
        }
      }
      setLoading(false)
    }

    const handleUnauthorized = () => {
      setUser(null)
      setToken(null)
    }
    window.addEventListener('auth:unauthorized', handleUnauthorized)

    loadUser()

    return () => {
      window.removeEventListener('auth:unauthorized', handleUnauthorized)
    }
  }, [])

  const login = async (username, password) => {
    const data = await authApi.login(username, password)
    localStorage.setItem('olm_access_token', data.access_token)
    setToken(data.access_token)
    setUser(data.user)
    return data.user
  }

  const logout = () => {
    localStorage.removeItem('olm_access_token')
    setToken(null)
    setUser(null)
  }

  const isAdmin = user?.role === 'ADMIN'
  const isSale = user?.role === 'SALE'

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        loading,
        isAuthenticated: !!user,
        isAdmin,
        isSale,
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

