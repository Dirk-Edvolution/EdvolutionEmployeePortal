import { authAPI } from '../services/api'
import './LoginPage.css'

export default function LoginPage() {
  return (
    <div className="login-page">
      <div className="login-container">
        <div className="login-header">
          <h1>🏢 Employee Portal</h1>
          <p>Vacation & Time-off Management</p>
        </div>
        <div className="login-content">
          <h2>Welcome!</h2>
          <p>Sign in with your company Google account to manage your time off requests.</p>
          <button onClick={authAPI.login} className="google-login-btn">
            <svg width="18" height="18" xmlns="http://www.w3.org/2000/svg">
              <g fill="none" fillRule="evenodd">
                <path d="M17.6 9.2l-.1-1.8H9v3.4h4.8C13.6 12 13 13 12 13.6v2.2h3a8.8 8.8 0 0 0 2.6-6.6z" fill="#4285F4"/>
                <path d="M9 18c2.4 0 4.5-.8 6-2.2l-3-2.2a5.4 5.4 0 0 1-8-2.9H1V13a9 9 0 0 0 8 5z" fill="#34A853"/>
                <path d="M4 10.7a5.4 5.4 0 0 1 0-3.4V5H1a9 9 0 0 0 0 8l3-2.3z" fill="#FBBC05"/>
                <path d="M9 3.6c1.3 0 2.5.4 3.4 1.3L15 2.3A9 9 0 0 0 1 5l3 2.4a5.4 5.4 0 0 1 5-3.7z" fill="#EA4335"/>
              </g>
            </svg>
            Sign in with Google
          </button>
        </div>
      </div>
    </div>
  )
}
