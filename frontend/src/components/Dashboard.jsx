import { useState, useEffect } from 'react'
import { employeeAPI, timeoffAPI } from '../services/api'
import './Dashboard.css'

export default function Dashboard({ user, onLogout }) {
  const [view, setView] = useState('overview')
  const [vacationSummary, setVacationSummary] = useState(null)
  const [requests, setRequests] = useState([])
  const [pendingApprovals, setPendingApprovals] = useState([])
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState(null)
  const [employees, setEmployees] = useState([])
  const [editingEmployee, setEditingEmployee] = useState(null)
  const [editingRequest, setEditingRequest] = useState(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [filterDepartment, setFilterDepartment] = useState('')
  const [holidayRegions, setHolidayRegions] = useState([])

  useEffect(() => {
    loadData()
    // Load employees for admins and managers
    // The backend will filter appropriately based on permissions
    loadEmployees()
    loadHolidayRegions()
  }, [])

  async function loadData() {
    try {
      const [summary, myRequests, approvals] = await Promise.all([
        timeoffAPI.getVacationSummary().catch(() => null),
        timeoffAPI.getMy().catch(() => []),
        timeoffAPI.getPendingApprovals().catch(() => []),
      ])
      setVacationSummary(summary)
      setRequests(Array.isArray(myRequests) ? myRequests : [])
      setPendingApprovals(Array.isArray(approvals) ? approvals : [])
    } catch (error) {
      showMessage('Failed to load data: ' + error.message, 'error')
    }
  }

  function showMessage(text, type = 'success') {
    setMessage({ text, type })
    setTimeout(() => setMessage(null), 5000)
  }

  async function handleCreateRequest(e) {
    e.preventDefault()
    setLoading(true)
    try {
      const formData = new FormData(e.target)
      await timeoffAPI.create({
        start_date: formData.get('start_date'),
        end_date: formData.get('end_date'),
        timeoff_type: formData.get('timeoff_type'),
        notes: formData.get('notes'),
      })
      showMessage('Time-off request submitted successfully!')
      e.target.reset()
      await loadData()
      setView('my-requests')
    } catch (error) {
      showMessage('Failed to create request: ' + error.message, 'error')
    } finally {
      setLoading(false)
    }
  }

  async function handleApprove(requestId, isManager) {
    setLoading(true)
    try {
      if (isManager) {
        await timeoffAPI.approveManager(requestId)
        showMessage('Approved as manager! Waiting for admin approval.')
      } else {
        await timeoffAPI.approveAdmin(requestId)
        showMessage('Request fully approved!')
      }
      await loadData()
    } catch (error) {
      showMessage('Failed to approve: ' + error.message, 'error')
    } finally {
      setLoading(false)
    }
  }

  async function handleReject(requestId) {
    const reason = prompt('Enter rejection reason:')
    if (!reason) return

    setLoading(true)
    try {
      await timeoffAPI.reject(requestId, reason)
      showMessage('Request rejected')
      await loadData()
    } catch (error) {
      showMessage('Failed to reject: ' + error.message, 'error')
    } finally {
      setLoading(false)
    }
  }

  async function handleSyncCalendar(requestId) {
    setLoading(true)
    try {
      await timeoffAPI.syncCalendar(requestId)
      showMessage('Synced to Google Calendar!')
      await loadData()
    } catch (error) {
      showMessage('Failed to sync calendar: ' + error.message, 'error')
    } finally {
      setLoading(false)
    }
  }

  async function handleEnableAutoresponder(requestId) {
    setLoading(true)
    try {
      await timeoffAPI.enableAutoresponder(requestId)
      showMessage('Gmail auto-responder enabled!')
      await loadData()
    } catch (error) {
      showMessage('Failed to enable auto-responder: ' + error.message, 'error')
    } finally {
      setLoading(false)
    }
  }

  async function loadEmployees() {
    try {
      const allEmployees = await employeeAPI.list()
      setEmployees(allEmployees)
    } catch (error) {
      showMessage('Failed to load employees: ' + error.message, 'error')
    }
  }

  async function loadHolidayRegions() {
    try {
      const data = await employeeAPI.getHolidayRegions()
      setHolidayRegions(data.regions || [])
    } catch (error) {
      console.error('Failed to load holiday regions:', error)
      // Don't show error to user, this is optional data
    }
  }

  async function handleUpdateEmployee(email, updates) {
    setLoading(true)
    try {
      await employeeAPI.update(email, updates)
      showMessage('Employee updated successfully!')
      setEditingEmployee(null)
      await loadEmployees()
    } catch (error) {
      showMessage('Failed to update employee: ' + error.message, 'error')
    } finally {
      setLoading(false)
    }
  }

  async function handleUpdateRequest(requestId, updates) {
    setLoading(true)
    try {
      await timeoffAPI.update(requestId, updates)
      showMessage('Request updated successfully!')
      setEditingRequest(null)
      await loadData()
    } catch (error) {
      showMessage('Failed to update request: ' + error.message, 'error')
    } finally {
      setLoading(false)
    }
  }

  async function handleDeleteRequest(requestId) {
    if (!confirm('Are you sure you want to delete this request?')) {
      return
    }

    setLoading(true)
    try {
      await timeoffAPI.delete(requestId)
      showMessage('Request deleted successfully!')
      await loadData()
    } catch (error) {
      showMessage('Failed to delete request: ' + error.message, 'error')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="dashboard">
      <nav className="sidebar">
        <div className="sidebar-header">
          <h2>🏢 Employee Portal</h2>
          <div className="user-info">
            {user.photo_url && <img src={user.photo_url} alt={user.name} />}
            <div>
              <strong>{user.name}</strong>
              <span>{user.email}</span>
            </div>
          </div>
        </div>
        <ul className="nav-menu">
          <li className={view === 'overview' ? 'active' : ''} onClick={() => setView('overview')}>
            📊 Overview
          </li>
          <li className={view === 'new-request' ? 'active' : ''} onClick={() => setView('new-request')}>
            ✉️ New Request
          </li>
          <li className={view === 'my-requests' ? 'active' : ''} onClick={() => setView('my-requests')}>
            📝 My Requests
          </li>
          {pendingApprovals.length > 0 && (
            <li className={view === 'approvals' ? 'active' : ''} onClick={() => setView('approvals')}>
              ⏳ Approvals ({pendingApprovals.length})
            </li>
          )}
          {employees.length > 0 && !user.is_admin && (
            <li className={view === 'team' ? 'active' : ''} onClick={() => setView('team')}>
              👥 My Team ({employees.length})
            </li>
          )}
          {user.is_admin && (
            <li className={view === 'admin' ? 'active' : ''} onClick={() => setView('admin')}>
              ⚙️ HR Admin
            </li>
          )}
        </ul>
        <button onClick={onLogout} className="logout-btn">🚪 Logout</button>
      </nav>

      <main className="main-content">
        {message && (
          <div className={`message ${message.type}`}>
            {message.text}
          </div>
        )}

        {view === 'overview' && (
          <div className="view-content">
            <h1>Welcome, {user.given_name}!</h1>

            {vacationSummary && (
              <div className="vacation-summary">
                <h2>Vacation Summary {vacationSummary.year}</h2>
                <div className="summary-cards">
                  <div className="card">
                    <div className="card-value">{vacationSummary.total_days}</div>
                    <div className="card-label">Total Days</div>
                  </div>
                  <div className="card">
                    <div className="card-value">{vacationSummary.used_days}</div>
                    <div className="card-label">Used</div>
                  </div>
                  <div className="card highlight">
                    <div className="card-value">{vacationSummary.remaining_days}</div>
                    <div className="card-label">Remaining</div>
                  </div>
                </div>
              </div>
            )}

            <div className="recent-requests">
              <h2>Recent Requests</h2>
              {!Array.isArray(requests) || requests.length === 0 ? (
                <p>No requests yet. <a href="#" onClick={() => setView('new-request')}>Create your first request</a></p>
              ) : (
                <div className="requests-list">
                  {requests.slice(0, 3).map((item) => {
                    const [id, req] = Array.isArray(item) ? item : [item.request_id || Math.random(), item];
                    return (
                      <div key={id} className="request-card">
                        <span className={`status-badge status-${req.status}`}>{req.status}</span>
                        <strong>{new Date(req.start_date).toLocaleDateString()} - {new Date(req.end_date).toLocaleDateString()}</strong>
                        <span>{req.timeoff_type.replace('_', ' ')} ({req.days_count} days)</span>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
        )}

        {view === 'new-request' && (
          <div className="view-content">
            <h1>New Time-off Request</h1>
            <form onSubmit={handleCreateRequest} className="request-form">
              <div className="form-group">
                <label>Start Date</label>
                <input type="date" name="start_date" required />
              </div>
              <div className="form-group">
                <label>End Date</label>
                <input type="date" name="end_date" required />
              </div>
              <div className="form-group">
                <label>Type</label>
                <select name="timeoff_type" required>
                  <option value="vacation">Vacation</option>
                  <option value="sick_leave">Sick Leave</option>
                  <option value="day_off">Day Off</option>
                </select>
              </div>
              <div className="form-group">
                <label>Notes (optional)</label>
                <textarea name="notes" rows="4" placeholder="Any additional information..."></textarea>
              </div>
              <button type="submit" disabled={loading} className="submit-btn">
                {loading ? 'Submitting...' : 'Submit Request'}
              </button>
            </form>
          </div>
        )}

        {view === 'my-requests' && (
          <div className="view-content">
            <h1>My Requests</h1>
            {!Array.isArray(requests) || requests.length === 0 ? (
              <p>No requests found.</p>
            ) : (
              <div className="requests-table">
                {requests.map((item) => {
                  const [id, req] = Array.isArray(item) ? item : [item.request_id || Math.random(), item];
                  return (
                    <div key={id} className="request-row">
                      <div className="request-info">
                        <strong>{new Date(req.start_date).toLocaleDateString()} - {new Date(req.end_date).toLocaleDateString()}</strong>
                        <span>{req.timeoff_type.replace('_', ' ')} - {req.days_count} days</span>
                        {req.notes && <p className="notes"><strong>Your notes:</strong> {req.notes}</p>}
                        {req.status === 'rejected' && req.rejection_reason && (
                          <p className="notes" style={{ color: '#dc3545', background: '#ffe6e6', padding: '8px', borderRadius: '4px', marginTop: '8px' }}>
                            <strong>Rejection reason:</strong> {req.rejection_reason}
                          </p>
                        )}
                        {req.status === 'rejected' && req.rejected_by && (
                          <p className="notes" style={{ fontSize: '12px', color: '#666' }}>
                            Rejected by: {req.rejected_by}
                          </p>
                        )}
                      </div>
                      <div className="request-status">
                        <span className={`status-badge status-${req.status}`}>{req.status.replace('_', ' ')}</span>
                        {req.status === 'pending' && (
                          <>
                            <button onClick={() => setEditingRequest({ id, ...req })} className="action-btn" style={{ background: '#667eea' }}>
                              ✏️ Edit
                            </button>
                            <button onClick={() => handleDeleteRequest(id)} className="action-btn" style={{ background: '#dc3545' }}>
                              🗑️ Delete
                            </button>
                          </>
                        )}
                        {req.status === 'approved' && !req.calendar_event_id && (
                          <button onClick={() => handleSyncCalendar(id)} className="action-btn">
                            📅 Sync Calendar
                          </button>
                        )}
                        {req.status === 'approved' && req.calendar_event_id && !req.autoresponder_enabled && (
                          <button onClick={() => handleEnableAutoresponder(id)} className="action-btn">
                            📧 Enable Auto-reply
                          </button>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}

        {view === 'approvals' && (
          <div className="view-content">
            <h1>Pending Approvals</h1>
            {!Array.isArray(pendingApprovals) || pendingApprovals.length === 0 ? (
              <p>No pending approvals.</p>
            ) : (
              <div className="approvals-list">
                {pendingApprovals.map((item) => {
                  const id = item.request_id || item[0];
                  const req = item.request_id ? item : item[1];
                  return (
                    <div key={id} className="approval-card">
                      <div className="approval-header">
                        <strong>{req.employee_email}</strong>
                        <span className={`status-badge status-${req.status}`}>{req.status.replace('_', ' ')}</span>
                      </div>
                      <div className="approval-details">
                        <p><strong>Dates:</strong> {new Date(req.start_date).toLocaleDateString()} - {new Date(req.end_date).toLocaleDateString()} ({req.days_count} days)</p>
                        <p><strong>Type:</strong> {req.timeoff_type.replace('_', ' ')}</p>
                        {req.notes && <p><strong>Notes:</strong> {req.notes}</p>}
                      </div>
                      <div className="approval-actions">
                        {req.status === 'pending' && (
                          <button onClick={() => handleApprove(id, true)} className="approve-btn" disabled={loading}>
                            ✅ Approve (Manager)
                          </button>
                        )}
                        {req.status === 'manager_approved' && user.is_admin && (
                          <button onClick={() => handleApprove(id, false)} className="approve-btn" disabled={loading}>
                            ✅ Approve (Admin)
                          </button>
                        )}
                        <button onClick={() => handleReject(id)} className="reject-btn" disabled={loading}>
                          ❌ Reject
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}

        {view === 'team' && employees.length > 0 && !user.is_admin && (
          <div className="view-content">
            <h1>My Team</h1>

            <div className="employees-section">
              <div className="employees-header">
                <h2>Team Members</h2>
                <div className="employees-stats">
                  <div className="stat-card">
                    <div className="stat-value">{employees.length}</div>
                    <div className="stat-label">Direct Reports</div>
                  </div>
                  <div className="stat-card">
                    <div className="stat-value">{[...new Set(employees.map(e => e.department).filter(Boolean))].length}</div>
                    <div className="stat-label">Departments</div>
                  </div>
                  <div className="stat-card">
                    <div className="stat-value">{[...new Set(employees.map(e => e.country).filter(Boolean))].length}</div>
                    <div className="stat-label">Countries</div>
                  </div>
                </div>
              </div>

              <div className="employees-filters">
                <input
                  type="text"
                  placeholder="Search by name or email..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="search-input"
                />
                <select
                  value={filterDepartment}
                  onChange={(e) => setFilterDepartment(e.target.value)}
                  className="filter-select"
                >
                  <option value="">All Departments</option>
                  {[...new Set(employees.map(e => e.department).filter(Boolean))].map(dept => (
                    <option key={dept} value={dept}>{dept}</option>
                  ))}
                </select>
              </div>

              <div className="employees-table">
                {employees
                  .filter(emp => {
                    const matchesSearch = !searchTerm ||
                      emp.full_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                      emp.email?.toLowerCase().includes(searchTerm.toLowerCase());
                    const matchesDept = !filterDepartment || emp.department === filterDepartment;
                    return matchesSearch && matchesDept;
                  })
                  .map((emp) => (
                    <div key={emp.email} className="employee-card">
                      <div className="employee-info">
                        <strong>{emp.display_name || emp.full_name || emp.email}</strong>
                        {emp.job_title && <span className="job-title">{emp.job_title}</span>}
                      </div>
                      <div className="employee-details">
                        <div className="detail-row">
                          <span className="detail-label">Organization:</span>
                          <span>{emp.organizational_unit || 'Not set'}</span>
                        </div>
                        <div className="detail-row">
                          <span className="detail-label">Department:</span>
                          <span>{emp.department || 'Not set'}</span>
                        </div>
                        <div className="detail-row">
                          <span className="detail-label">Location:</span>
                          <span>{emp.location || emp.country || 'Not set'}</span>
                        </div>
                        {emp.vacation_summary && (
                          <div className="detail-row">
                            <span className="detail-label">Vacation Days:</span>
                            <span style={{
                              fontWeight: 'bold',
                              color: emp.vacation_summary.remaining_days < (emp.vacation_summary.total_days * 0.25) ? '#dc3545' :
                                     emp.vacation_summary.remaining_days < (emp.vacation_summary.total_days * 0.5) ? '#ffc107' :
                                     '#28a745'
                            }}>
                              {emp.vacation_summary.remaining_days} / {emp.vacation_summary.total_days} remaining
                            </span>
                            <span style={{ fontSize: '12px', color: '#666', marginLeft: '8px' }}>
                              ({emp.vacation_summary.used_days} used)
                            </span>
                          </div>
                        )}
                        <div className="detail-row">
                          <span className="detail-label">Country:</span>
                          <span>{emp.country || 'Not set'}</span>
                        </div>
                        <div className="detail-row">
                          <span className="detail-label">Region:</span>
                          <span>{emp.region || 'Not set'}</span>
                        </div>
                      </div>
                      <button
                        onClick={() => setEditingEmployee(emp)}
                        className="edit-btn"
                        disabled={loading}
                      >
                        👁️ View
                      </button>
                    </div>
                  ))}
              </div>
            </div>

            {editingEmployee && (
              <div className="modal-overlay" onClick={() => setEditingEmployee(null)}>
                <div className="modal-content" onClick={(e) => e.stopPropagation()}>
                  <h2>View Team Member: {editingEmployee.full_name || editingEmployee.email}</h2>
                  <div className="info-message" style={{ background: '#e3f2fd', padding: '12px', borderRadius: '4px', marginBottom: '16px', fontSize: '14px' }}>
                    ℹ️ As a manager, you can view your team members' information but cannot edit it. Only HR admins can modify employee data.
                  </div>
                  <div className="employee-view-only">
                    <div className="form-group">
                      <label>Organizational Unit (from Google Workspace)</label>
                      <input
                        type="text"
                        value={editingEmployee.organizational_unit || 'Not set'}
                        disabled
                        style={{ background: '#f5f5f5', cursor: 'not-allowed' }}
                      />
                    </div>
                    <div className="form-group">
                      <label>Department / Team</label>
                      <input
                        type="text"
                        value={editingEmployee.department || 'Not set'}
                        disabled
                        style={{ background: '#f5f5f5', cursor: 'not-allowed' }}
                      />
                    </div>
                    <div className="form-group">
                      <label>Job Title</label>
                      <input
                        type="text"
                        value={editingEmployee.job_title || 'Not set'}
                        disabled
                        style={{ background: '#f5f5f5', cursor: 'not-allowed' }}
                      />
                    </div>
                    <div className="form-group">
                      <label>Location</label>
                      <input
                        type="text"
                        value={editingEmployee.location || 'Not set'}
                        disabled
                        style={{ background: '#f5f5f5', cursor: 'not-allowed' }}
                      />
                    </div>
                    <div className="form-group">
                      <label>Country</label>
                      <input
                        type="text"
                        value={editingEmployee.country || 'Not set'}
                        disabled
                        style={{ background: '#f5f5f5', cursor: 'not-allowed' }}
                      />
                    </div>
                    <div className="form-group">
                      <label>Region</label>
                      <input
                        type="text"
                        value={editingEmployee.region || 'Not set'}
                        disabled
                        style={{ background: '#f5f5f5', cursor: 'not-allowed' }}
                      />
                    </div>
                    <div className="modal-actions">
                      <button
                        type="button"
                        onClick={() => setEditingEmployee(null)}
                        className="cancel-btn"
                      >
                        Close
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {view === 'admin' && user.is_admin && (
          <div className="view-content">
            <h1>HR Admin Panel</h1>
            <div className="admin-actions">
              <button onClick={async () => {
                setLoading(true)
                try {
                  const result = await employeeAPI.sync()
                  showMessage(`Synced ${result.synced_count} employees from Workspace!`)
                  await loadData()
                  await loadEmployees()
                } catch (error) {
                  showMessage('Sync failed: ' + error.message, 'error')
                } finally {
                  setLoading(false)
                }
              }} disabled={loading} className="admin-btn">
                🔄 Sync Employees from Workspace
              </button>
            </div>

            <div className="employees-section">
              <div className="employees-header">
                <h2>Employee Management</h2>
                <div className="employees-stats">
                  <div className="stat-card">
                    <div className="stat-value">{employees.length}</div>
                    <div className="stat-label">Total Users</div>
                  </div>
                  <div className="stat-card">
                    <div className="stat-value">{employees.filter(e => e.organizational_unit?.includes('Employees')).length}</div>
                    <div className="stat-label">Employees</div>
                  </div>
                  <div className="stat-card">
                    <div className="stat-value">{employees.filter(e => !e.organizational_unit?.includes('Employees')).length}</div>
                    <div className="stat-label">Externals</div>
                  </div>
                  <div className="stat-card">
                    <div className="stat-value">{[...new Set(employees.map(e => e.department).filter(Boolean))].length}</div>
                    <div className="stat-label">Departments</div>
                  </div>
                </div>
              </div>

              <div className="employees-filters">
                <input
                  type="text"
                  placeholder="Search by name or email..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="search-input"
                />
                <select
                  value={filterDepartment}
                  onChange={(e) => setFilterDepartment(e.target.value)}
                  className="filter-select"
                >
                  <option value="">All Departments</option>
                  {[...new Set(employees.map(e => e.department).filter(Boolean))].map(dept => (
                    <option key={dept} value={dept}>{dept}</option>
                  ))}
                </select>
              </div>

              <div className="employees-table">
                {employees
                  .filter(emp => {
                    const matchesSearch = !searchTerm ||
                      emp.full_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                      emp.email?.toLowerCase().includes(searchTerm.toLowerCase());
                    const matchesDept = !filterDepartment || emp.department === filterDepartment;
                    return matchesSearch && matchesDept;
                  })
                  .map((emp) => (
                    <div key={emp.email} className="employee-card">
                      <div className="employee-info">
                        <strong>{emp.display_name || emp.full_name || emp.email}</strong>
                        {emp.job_title && <span className="job-title">{emp.job_title}</span>}
                      </div>
                      <div className="employee-details">
                        <div className="detail-row">
                          <span className="detail-label">Manager:</span>
                          <span>{emp.manager_email || 'Not set'}</span>
                        </div>
                        <div className="detail-row">
                          <span className="detail-label">Organization:</span>
                          <span>{emp.organizational_unit || 'Not set'}</span>
                        </div>
                        <div className="detail-row">
                          <span className="detail-label">Department:</span>
                          <span>{emp.department || 'Not set'}</span>
                        </div>
                        <div className="detail-row">
                          <span className="detail-label">Location:</span>
                          <span>{emp.location || emp.country || 'Not set'}</span>
                        </div>
                        {emp.vacation_summary && (
                          <div className="detail-row">
                            <span className="detail-label">Vacation Days:</span>
                            <span style={{
                              fontWeight: 'bold',
                              color: emp.vacation_summary.remaining_days < (emp.vacation_summary.total_days * 0.25) ? '#dc3545' :
                                     emp.vacation_summary.remaining_days < (emp.vacation_summary.total_days * 0.5) ? '#ffc107' :
                                     '#28a745'
                            }}>
                              {emp.vacation_summary.remaining_days} / {emp.vacation_summary.total_days} remaining
                            </span>
                            <span style={{ fontSize: '12px', color: '#666', marginLeft: '8px' }}>
                              ({emp.vacation_summary.used_days} used in {emp.vacation_summary.year})
                            </span>
                          </div>
                        )}
                        <div className="detail-row">
                          <span className="detail-label">Admin:</span>
                          <span className={emp.is_admin ? 'badge-yes' : 'badge-no'}>
                            {emp.is_admin ? 'Yes' : 'No'}
                          </span>
                        </div>
                      </div>
                      <button
                        onClick={() => setEditingEmployee(emp)}
                        className="edit-btn"
                        disabled={loading}
                      >
                        ✏️ Edit
                      </button>
                    </div>
                  ))}
              </div>
            </div>

            {editingEmployee && (() => {
              // Get filtered employees list for navigation
              const filteredEmployees = employees.filter(emp => {
                const matchesSearch = !searchTerm ||
                  emp.full_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                  emp.email?.toLowerCase().includes(searchTerm.toLowerCase());
                const matchesDept = !filterDepartment || emp.department === filterDepartment;
                return matchesSearch && matchesDept;
              });
              const currentIndex = filteredEmployees.findIndex(e => e.email === editingEmployee.email);
              const hasPrevious = currentIndex > 0;
              const hasNext = currentIndex < filteredEmployees.length - 1;

              // Get target employee for navigation
              const getTargetEmployee = (direction) => {
                const targetIndex = direction === 'previous' ? currentIndex - 1 : currentIndex + 1;
                if (targetIndex >= 0 && targetIndex < filteredEmployees.length) {
                  return filteredEmployees[targetIndex];
                }
                return null;
              };

              // Check if form has unsaved changes
              const checkDirty = () => {
                const form = document.getElementById('employee-edit-form');
                if (!form) return false;
                const formData = new FormData(form);
                const orig = editingEmployee;

                // Compare key fields
                if ((formData.get('manager_email') || '') !== (orig.manager_email || '')) return true;
                if ((formData.get('department') || '') !== (orig.department || '')) return true;
                if ((formData.get('job_title') || '') !== (orig.job_title || '')) return true;
                if ((formData.get('location') || '') !== (orig.location || '')) return true;
                if ((formData.get('country') || '') !== (orig.country || '')) return true;
                if ((formData.get('region') || '') !== (orig.region || '')) return true;
                if ((formData.get('holiday_region') || '') !== (orig.holiday_region || '')) return true;
                if (String(formData.get('vacation_days_per_year') || '20') !== String(orig.vacation_days_per_year || 20)) return true;
                if ((formData.get('contract_type') || '') !== (orig.contract_type || '')) return true;
                if ((formData.get('salary') || '') !== String(orig.salary || '')) return true;
                if ((formData.get('has_bonus') === 'on') !== (orig.has_bonus || false)) return true;
                if ((formData.get('has_commission') === 'on') !== (orig.has_commission || false)) return true;

                return false;
              };

              // Handle navigation with dirty check
              const handleNavigate = async (direction) => {
                const targetEmployee = getTargetEmployee(direction);
                if (!targetEmployee) return;

                if (checkDirty()) {
                  const wantToSave = window.confirm(
                    'You have unsaved changes!\n\nClick OK to SAVE changes first.\nClick Cancel to DISCARD changes and continue.'
                  );

                  if (wantToSave) {
                    // Save first, then navigate
                    const saved = await doSave();
                    if (!saved) return; // Save failed, don't navigate
                  }
                  // If user clicked Cancel or save succeeded, navigate to target
                }

                // Navigate to target employee
                setEditingEmployee(targetEmployee);
              };

              // Save employee data - returns true on success, false on failure
              const doSave = async () => {
                const form = document.getElementById('employee-edit-form');
                if (!form) return false;

                const formData = new FormData(form);
                const updates = {
                  manager_email: formData.get('manager_email') || null,
                  department: formData.get('department'),
                  job_title: formData.get('job_title'),
                  location: formData.get('location'),
                  country: formData.get('country'),
                  region: formData.get('region'),
                  holiday_region: formData.get('holiday_region') || null,
                  vacation_days_per_year: parseInt(formData.get('vacation_days_per_year')) || 20,
                  contract_type: formData.get('contract_type'),
                  contract_start_date: formData.get('contract_start_date') || null,
                  contract_end_date: formData.get('contract_end_date') || null,
                  contract_document_url: formData.get('contract_document_url') || null,
                  salary: formData.get('salary') ? parseFloat(formData.get('salary')) : null,
                  salary_currency: formData.get('salary_currency'),
                  has_bonus: formData.get('has_bonus') === 'on',
                  bonus_type: formData.get('bonus_type') || null,
                  bonus_percentage: formData.get('bonus_percentage') ? parseFloat(formData.get('bonus_percentage')) : null,
                  has_commission: formData.get('has_commission') === 'on',
                  commission_notes: formData.get('commission_notes') || null,
                  personal_address: formData.get('personal_address') || null,
                  working_address: formData.get('working_address') || null,
                  spouse_partner_name: formData.get('spouse_partner_name') || null,
                  spouse_partner_phone: formData.get('spouse_partner_phone') || null,
                  spouse_partner_email: formData.get('spouse_partner_email') || null,
                };

                setLoading(true);
                try {
                  await employeeAPI.update(editingEmployee.email, updates);
                  showMessage('Employee saved successfully!');

                  // Refresh the employee list
                  const updatedEmployees = await employeeAPI.list();
                  setEmployees(updatedEmployees);

                  return true;
                } catch (error) {
                  showMessage('Failed to save: ' + error.message, 'error');
                  return false;
                } finally {
                  setLoading(false);
                }
              };

              // Handle save button click (just save, no navigation)
              const handleSaveClick = async () => {
                const saved = await doSave();
                if (saved) {
                  // Update the editing employee with fresh data
                  const updatedEmployees = await employeeAPI.list();
                  const updatedEmployee = updatedEmployees.find(e => e.email === editingEmployee.email);
                  if (updatedEmployee) {
                    setEditingEmployee(updatedEmployee);
                  }
                }
              };

              return (
                <div className="modal-overlay" onClick={() => setEditingEmployee(null)}>
                  <div className="modal-content modal-large" onClick={(e) => e.stopPropagation()}>
                    {/* Header: [PREV] {NAME} [NEXT][SAVE] */}
                    <div style={{
                      display: 'grid',
                      gridTemplateColumns: '80px 1fr auto',
                      alignItems: 'center',
                      gap: '1rem',
                      marginBottom: '1rem',
                      paddingBottom: '1rem',
                      borderBottom: '1px solid #e0e0e0'
                    }}>
                      {/* Left: PREV */}
                      <button
                        type="button"
                        onClick={() => handleNavigate('previous')}
                        disabled={!hasPrevious || loading}
                        style={{
                          padding: '10px 16px',
                          background: hasPrevious ? '#667eea' : '#ccc',
                          color: 'white',
                          border: 'none',
                          borderRadius: '6px',
                          cursor: hasPrevious ? 'pointer' : 'not-allowed',
                          fontSize: '14px',
                          fontWeight: '500'
                        }}
                      >
                        ← Prev
                      </button>

                      {/* Center: Name + counter */}
                      <div style={{ textAlign: 'center', overflow: 'hidden' }}>
                        <h2 style={{
                          margin: 0,
                          whiteSpace: 'nowrap',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          fontSize: '1.3rem'
                        }}>
                          {editingEmployee.full_name || editingEmployee.email}
                        </h2>
                        <span style={{ fontSize: '12px', color: '#666' }}>
                          {currentIndex + 1} of {filteredEmployees.length}
                        </span>
                      </div>

                      {/* Right: NEXT + SAVE */}
                      <div style={{ display: 'flex', gap: '0.5rem' }}>
                        <button
                          type="button"
                          onClick={() => handleNavigate('next')}
                          disabled={!hasNext || loading}
                          style={{
                            padding: '10px 16px',
                            background: hasNext ? '#667eea' : '#ccc',
                            color: 'white',
                            border: 'none',
                            borderRadius: '6px',
                            cursor: hasNext ? 'pointer' : 'not-allowed',
                            fontSize: '14px',
                            fontWeight: '500'
                          }}
                        >
                          Next →
                        </button>
                        <button
                          type="button"
                          onClick={() => handleSaveClick()}
                          disabled={loading}
                          style={{
                            padding: '10px 20px',
                            background: '#28a745',
                            color: 'white',
                            border: 'none',
                            borderRadius: '6px',
                            cursor: loading ? 'not-allowed' : 'pointer',
                            fontSize: '14px',
                            fontWeight: '500'
                          }}
                        >
                          {loading ? 'Saving...' : '💾 Save'}
                        </button>
                      </div>
                    </div>
                    <form key={editingEmployee.email} id="employee-edit-form" onSubmit={(e) => {
                      e.preventDefault()
                      const formData = new FormData(e.target)
                      const updates = {
                        manager_email: formData.get('manager_email') || null,
                        department: formData.get('department'),
                        job_title: formData.get('job_title'),
                        location: formData.get('location'),
                        country: formData.get('country'),
                        region: formData.get('region'),
                        holiday_region: formData.get('holiday_region') || null,
                        vacation_days_per_year: parseInt(formData.get('vacation_days_per_year')),
                        contract_type: formData.get('contract_type'),
                        contract_start_date: formData.get('contract_start_date') || null,
                        contract_end_date: formData.get('contract_end_date') || null,
                        contract_document_url: formData.get('contract_document_url') || null,
                        salary: formData.get('salary') ? parseFloat(formData.get('salary')) : null,
                        salary_currency: formData.get('salary_currency'),
                        has_bonus: formData.get('has_bonus') === 'on',
                        bonus_type: formData.get('bonus_type') || null,
                        bonus_percentage: formData.get('bonus_percentage') ? parseFloat(formData.get('bonus_percentage')) : null,
                        has_commission: formData.get('has_commission') === 'on',
                        commission_notes: formData.get('commission_notes') || null,
                        personal_address: formData.get('personal_address') || null,
                        working_address: formData.get('working_address') || null,
                        spouse_partner_name: formData.get('spouse_partner_name') || null,
                        spouse_partner_phone: formData.get('spouse_partner_phone') || null,
                        spouse_partner_email: formData.get('spouse_partner_email') || null,
                      }
                      handleUpdateEmployee(editingEmployee.email, updates)
                    }}>
                      <h3 style={{ marginTop: '1rem', marginBottom: '0.5rem', color: '#667eea' }}>Basic Information</h3>
                      <div className="form-group">
                        <label>Manager</label>
                        <select name="manager_email" defaultValue={editingEmployee.manager_email || ''}>
                          <option value="">No Manager</option>
                          {employees
                            .filter(e => e.email !== editingEmployee.email)
                            .map(e => (
                              <option key={e.email} value={e.email}>{e.full_name || e.email}</option>
                            ))
                          }
                        </select>
                      </div>
                      <div className="form-group">
                        <label>Organizational Unit</label>
                        <select
                          name="ou_type"
                          defaultValue={
                            editingEmployee.organizational_unit === 'Employees' ? 'employees' :
                              editingEmployee.organizational_unit === 'External' ? 'external' :
                                editingEmployee.organizational_unit === 'Others' ? 'others' :
                                  'employees'
                          }
                          onChange={async (e) => {
                            if (confirm(`Move ${editingEmployee.email} to /${e.target.options[e.target.selectedIndex].text} in Google Workspace?`)) {
                              try {
                                setLoading(true)
                                await employeeAPI.changeOU(editingEmployee.email, e.target.value)
                                showMessage(`Successfully moved to /${e.target.options[e.target.selectedIndex].text}`)
                                await loadEmployees()
                                setEditingEmployee(null)
                              } catch (error) {
                                showMessage('Failed to change OU: ' + error.message, 'error')
                              } finally {
                                setLoading(false)
                              }
                            } else {
                              e.target.value = e.target.defaultValue
                            }
                          }}
                        >
                          <option value="employees">Employees</option>
                          <option value="external">External</option>
                          <option value="others">Others</option>
                        </select>
                        <small style={{ color: '#666', fontSize: '12px' }}>
                          Changes the user's Organizational Unit in Google Workspace immediately.
                          <br />Current: /{editingEmployee.organizational_unit || 'Unknown'}
                        </small>
                      </div>
                      <div className="form-group">
                        <label>Department / Team</label>
                        <input
                          type="text"
                          name="department"
                          defaultValue={editingEmployee.department || ''}
                          placeholder="e.g., Backend Team, Customer Success, Product Design"
                        />
                      </div>
                      <div className="form-group">
                        <label>Job Title</label>
                        <input
                          type="text"
                          name="job_title"
                          defaultValue={editingEmployee.job_title || ''}
                        />
                      </div>
                      <div className="form-group">
                        <label>Location</label>
                        <input
                          type="text"
                          name="location"
                          defaultValue={editingEmployee.location || ''}
                          placeholder="e.g., New York Office, Remote"
                        />
                      </div>
                      <div className="form-group">
                        <label>Country</label>
                        <input
                          type="text"
                          name="country"
                          defaultValue={editingEmployee.country || ''}
                          placeholder="e.g., United States"
                        />
                      </div>
                      <div className="form-group">
                        <label>Region</label>
                        <input
                          type="text"
                          name="region"
                          defaultValue={editingEmployee.region || ''}
                          placeholder="e.g., North America, EMEA, APAC"
                        />
                      </div>
                      <div className="form-group">
                        <label>Holiday Region (for day-off calculations)</label>
                        <select name="holiday_region" defaultValue={editingEmployee.holiday_region || ''}>
                          <option value="">Not set (no regional holidays)</option>
                          {holidayRegions.map(region => (
                            <option key={region.code} value={region.code}>
                              {region.name}
                            </option>
                          ))}
                        </select>
                        <small style={{ color: '#666', fontSize: '12px' }}>
                          Defines which regional holidays are excluded from working days calculations.
                        </small>
                      </div>
                      <div className="form-group">
                        <label>Vacation Days Per Year</label>
                        <input
                          type="number"
                          name="vacation_days_per_year"
                          defaultValue={editingEmployee.vacation_days_per_year || 20}
                          min="0"
                        />
                      </div>
                      <div className="form-group">
                        <label>HR Admin Status</label>
                        <input
                          type="text"
                          value={editingEmployee.is_admin ? 'Yes - HR Admin' : 'No - Regular Employee'}
                          disabled
                          style={{ background: '#f5f5f5', cursor: 'not-allowed' }}
                        />
                        <small style={{ color: '#666', fontSize: '12px' }}>Admin status is controlled by the ADMIN_USERS environment variable and cannot be changed here.</small>
                      </div>

                      <h3 style={{ marginTop: '1.5rem', marginBottom: '0.5rem', color: '#667eea' }}>Contract Information</h3>
                      <div className="form-group">
                        <label>Contract Type</label>
                        <select name="contract_type" defaultValue={editingEmployee.contract_type || ''}>
                          <option value="">Not set</option>
                          <option value="permanent">Permanent</option>
                          <option value="temporary">Temporary</option>
                          <option value="contractor">Contractor</option>
                          <option value="intern">Intern</option>
                        </select>
                      </div>
                      <div className="form-group">
                        <label>Contract Start Date</label>
                        <input
                          type="date"
                          name="contract_start_date"
                          defaultValue={editingEmployee.contract_start_date || ''}
                        />
                      </div>
                      <div className="form-group">
                        <label>Contract End Date</label>
                        <input
                          type="date"
                          name="contract_end_date"
                          defaultValue={editingEmployee.contract_end_date || ''}
                        />
                      </div>
                      <div className="form-group">
                        <label>Contract Document URL (Google Drive)</label>
                        <input
                          type="url"
                          name="contract_document_url"
                          defaultValue={editingEmployee.contract_document_url || ''}
                          placeholder="https://drive.google.com/..."
                        />
                      </div>

                      <h3 style={{ marginTop: '1.5rem', marginBottom: '0.5rem', color: '#667eea' }}>Compensation</h3>
                      <div className="form-group">
                        <label>Salary</label>
                        <input
                          type="number"
                          name="salary"
                          step="0.01"
                          defaultValue={editingEmployee.salary || ''}
                          placeholder="e.g., 75000"
                        />
                      </div>
                      <div className="form-group">
                        <label>Currency</label>
                        <select name="salary_currency" defaultValue={editingEmployee.salary_currency || 'USD'}>
                          <option value="USD">USD</option>
                          <option value="EUR">EUR</option>
                          <option value="GBP">GBP</option>
                          <option value="CAD">CAD</option>
                          <option value="AUD">AUD</option>
                          <option value="MXN">MXN</option>
                        </select>
                      </div>
                      <div className="form-group">
                        <label>
                          <input
                            type="checkbox"
                            name="has_bonus"
                            defaultChecked={editingEmployee.has_bonus}
                          />
                          Has Bonus
                        </label>
                      </div>
                      <div className="form-group">
                        <label>Bonus Type</label>
                        <select name="bonus_type" defaultValue={editingEmployee.bonus_type || ''}>
                          <option value="">Not applicable</option>
                          <option value="quarterly">Quarterly</option>
                          <option value="annual">Annual</option>
                        </select>
                      </div>
                      <div className="form-group">
                        <label>Bonus Percentage</label>
                        <input
                          type="number"
                          name="bonus_percentage"
                          step="0.1"
                          defaultValue={editingEmployee.bonus_percentage || ''}
                          placeholder="e.g., 10 for 10%"
                        />
                      </div>
                      <div className="form-group">
                        <label>
                          <input
                            type="checkbox"
                            name="has_commission"
                            defaultChecked={editingEmployee.has_commission}
                          />
                          Has Commission
                        </label>
                      </div>
                      <div className="form-group">
                        <label>Commission Notes</label>
                        <textarea
                          name="commission_notes"
                          rows="3"
                          defaultValue={editingEmployee.commission_notes || ''}
                          placeholder="Details about commission structure..."
                        ></textarea>
                      </div>

                      <h3 style={{ marginTop: '1.5rem', marginBottom: '0.5rem', color: '#667eea' }}>Addresses</h3>
                      <div className="form-group">
                        <label>Personal Address</label>
                        <textarea
                          name="personal_address"
                          rows="2"
                          defaultValue={editingEmployee.personal_address || ''}
                          placeholder="Home address..."
                        ></textarea>
                      </div>
                      <div className="form-group">
                        <label>Working Address</label>
                        <textarea
                          name="working_address"
                          rows="2"
                          defaultValue={editingEmployee.working_address || ''}
                          placeholder="Office or working location address..."
                        ></textarea>
                      </div>

                      <h3 style={{ marginTop: '1.5rem', marginBottom: '0.5rem', color: '#667eea' }}>Emergency Contact</h3>
                      <div className="form-group">
                        <label>Spouse/Partner Name</label>
                        <input
                          type="text"
                          name="spouse_partner_name"
                          defaultValue={editingEmployee.spouse_partner_name || ''}
                        />
                      </div>
                      <div className="form-group">
                        <label>Spouse/Partner Phone</label>
                        <input
                          type="tel"
                          name="spouse_partner_phone"
                          defaultValue={editingEmployee.spouse_partner_phone || ''}
                        />
                      </div>
                      <div className="form-group">
                        <label>Spouse/Partner Email</label>
                        <input
                          type="email"
                          name="spouse_partner_email"
                          defaultValue={editingEmployee.spouse_partner_email || ''}
                        />
                      </div>

                      <div className="modal-actions">
                        <button type="submit" className="submit-btn" disabled={loading}>
                          {loading ? 'Saving...' : 'Save Changes'}
                        </button>
                        <button
                          type="button"
                          onClick={() => setEditingEmployee(null)}
                          className="cancel-btn"
                        >
                          Cancel
                        </button>
                      </div>
                    </form>
                  </div>
                </div >
              )
            })()}

            {
              editingRequest && (
                <div className="modal-overlay" onClick={() => setEditingRequest(null)}>
                  <div className="modal-content" onClick={(e) => e.stopPropagation()}>
                    <h2>Edit Time-off Request</h2>
                    <form onSubmit={(e) => {
                      e.preventDefault()
                      const formData = new FormData(e.target)
                      handleUpdateRequest(editingRequest.id, {
                        start_date: formData.get('start_date'),
                        end_date: formData.get('end_date'),
                        timeoff_type: formData.get('timeoff_type'),
                        notes: formData.get('notes')
                      })
                    }}>
                      <div className="form-group">
                        <label>Start Date</label>
                        <input
                          type="date"
                          name="start_date"
                          defaultValue={editingRequest.start_date}
                          required
                        />
                      </div>
                      <div className="form-group">
                        <label>End Date</label>
                        <input
                          type="date"
                          name="end_date"
                          defaultValue={editingRequest.end_date}
                          required
                        />
                      </div>
                      <div className="form-group">
                        <label>Type</label>
                        <select name="timeoff_type" defaultValue={editingRequest.timeoff_type} required>
                          <option value="vacation">Vacation</option>
                          <option value="sick_leave">Sick Leave</option>
                          <option value="day_off">Day Off</option>
                        </select>
                      </div>
                      <div className="form-group">
                        <label>Notes (optional)</label>
                        <textarea
                          name="notes"
                          rows="4"
                          defaultValue={editingRequest.notes || ''}
                          placeholder="Any additional information..."
                        ></textarea>
                      </div>
                      <div className="modal-actions">
                        <button type="submit" className="submit-btn" disabled={loading}>
                          {loading ? 'Saving...' : 'Save Changes'}
                        </button>
                        <button
                          type="button"
                          onClick={() => setEditingRequest(null)}
                          className="cancel-btn"
                        >
                          Cancel
                        </button>
                      </div>
                    </form>
                  </div>
                </div>
              )
            }
          </div >
        )}
      </main >
    </div >
  )
}
