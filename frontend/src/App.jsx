import { useState, useEffect } from 'react'
import './App.css'
import { authAPI, employeeAPI, timeoffAPI } from './services/api'
import Dashboard from './components/Dashboard'
import LoginPage from './components/LoginPage'

function App() {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    checkAuth()
  }, [])

  async function checkAuth() {
    try {
      const status = await authAPI.checkStatus()
      console.log('Auth status:', status)
      if (status.authenticated) {
        try {
          const profile = await employeeAPI.getMe()
          console.log('Profile:', profile)
          setUser({ ...status.user, ...profile })
        } catch (profileError) {
          console.warn('Profile fetch failed, using basic user info:', profileError)
          setUser(status.user)
        }
      }
    } catch (error) {
      console.error('Auth check failed:', error)
      setError(error.message)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="loading-screen">
        <div className="spinner"></div>
        <p>Loading Employee Portal...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="loading-screen">
        <h2>Error Loading Portal</h2>
        <p>{error}</p>
        <button onClick={() => window.location.reload()}>Retry</button>
      </div>
    )
  }

  if (!user) {
    return <LoginPage />
  }

  return <Dashboard user={user} onLogout={() => authAPI.logout()} />
}

export default App
