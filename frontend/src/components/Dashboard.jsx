import { useState, useEffect } from 'react'
import { employeeAPI, timeoffAPI, tripAPI, assetAPI } from '../services/api'
import { EmployeeDetailModal } from './EmployeeDetailModal'
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
  const [workingDaysPreview, setWorkingDaysPreview] = useState(null)
  const [showPreview, setShowPreview] = useState(false)
  const [pendingRequestData, setPendingRequestData] = useState(null)
  const [requestType, setRequestType] = useState('timeoff')

  useEffect(() => {
    loadData()
    // Load employees for admins and managers
    // The backend will filter appropriately based on permissions
    loadEmployees()
    loadHolidayRegions()
  }, [])

  async function loadData() {
    try {
      const [summary, myTimeoffRequests, myTripRequests, myAssetRequests, timeoffApprovals, tripApprovals, assetApprovals] = await Promise.all([
        timeoffAPI.getVacationSummary().catch(() => null),
        timeoffAPI.getMy().catch(() => []),
        tripAPI.getMy().catch(() => []),
        assetAPI.getMy().catch(() => []),
        timeoffAPI.getPendingApprovals().catch(() => []),
        tripAPI.getPendingApprovals().catch(() => []),
        assetAPI.getPendingApprovals().catch(() => []),
      ])
      setVacationSummary(summary)

      // Combine all my requests and add request type
      const allRequests = [
        ...(Array.isArray(myTimeoffRequests) ? myTimeoffRequests : []).map(item => {
          const [id, req] = Array.isArray(item) ? item : [item.request_id || Math.random(), item];
          return [id, { ...req, request_type: 'timeoff' }];
        }),
        ...(Array.isArray(myTripRequests) ? myTripRequests : []).map(item => {
          const [id, req] = Array.isArray(item) ? item : [item.request_id || Math.random(), item];
          return [id, { ...req, request_type: 'trip' }];
        }),
        ...(Array.isArray(myAssetRequests) ? myAssetRequests : []).map(item => {
          const [id, req] = Array.isArray(item) ? item : [item.request_id || Math.random(), item];
          return [id, { ...req, request_type: 'asset' }];
        }),
      ]
      setRequests(allRequests)

      // Combine all pending approvals and add request type
      const allApprovals = [
        ...(Array.isArray(timeoffApprovals) ? timeoffApprovals : []).map(item => ({
          ...item,
          request_type: 'timeoff'
        })),
        ...(Array.isArray(tripApprovals) ? tripApprovals : []).map(item => ({
          ...item,
          request_type: 'trip'
        })),
        ...(Array.isArray(assetApprovals) ? assetApprovals : []).map(item => ({
          ...item,
          request_type: 'asset'
        })),
      ]
      setPendingApprovals(allApprovals)
    } catch (error) {
      showMessage('Failed to load data: ' + error.message, 'error')
    }
  }

  function showMessage(text, type = 'success') {
    setMessage({ text, type })
    setTimeout(() => setMessage(null), 5000)
  }

  async function handlePreviewRequest(e) {
    e.preventDefault()
    setLoading(true)
    try {
      const formData = new FormData(e.target)
      const requestData = {
        start_date: formData.get('start_date'),
        end_date: formData.get('end_date'),
        timeoff_type: formData.get('timeoff_type'),
        notes: formData.get('notes'),
      }

      // Get working days preview
      const preview = await timeoffAPI.previewWorkingDays({
        start_date: requestData.start_date,
        end_date: requestData.end_date,
      })

      setWorkingDaysPreview(preview)
      setPendingRequestData(requestData)
      setShowPreview(true)
    } catch (error) {
      showMessage('Failed to preview request: ' + error.message, 'error')
    } finally {
      setLoading(false)
    }
  }

  async function handleConfirmRequest() {
    setLoading(true)
    try {
      await timeoffAPI.create(pendingRequestData)
      showMessage('Time-off request submitted successfully!')
      setShowPreview(false)
      setWorkingDaysPreview(null)
      setPendingRequestData(null)
      await loadData()
      setView('my-requests')
    } catch (error) {
      showMessage('Failed to create request: ' + error.message, 'error')
    } finally {
      setLoading(false)
    }
  }

  function handleCancelPreview() {
    setShowPreview(false)
    setWorkingDaysPreview(null)
    setPendingRequestData(null)
  }

  async function handleSubmitTripRequest(e) {
    e.preventDefault()
    setLoading(true)
    try {
      const formData = new FormData(e.target)
      const requestData = {
        destination: formData.get('destination'),
        start_date: formData.get('start_date'),
        end_date: formData.get('end_date'),
        purpose: formData.get('purpose'),
        expected_goal: formData.get('expected_goal'),
        estimated_budget: parseFloat(formData.get('estimated_budget')),
        currency: formData.get('currency'),
        needs_advance_funding: formData.get('needs_advance_funding') === 'on',
        advance_amount: formData.get('advance_amount') ? parseFloat(formData.get('advance_amount')) : null,
      }

      await tripAPI.create(requestData)
      showMessage('Trip request submitted successfully!')
      await loadData()
      setView('my-requests')
      e.target.reset()
    } catch (error) {
      showMessage('Failed to create trip request: ' + error.message, 'error')
    } finally {
      setLoading(false)
    }
  }

  async function handleSubmitAssetRequest(e) {
    e.preventDefault()
    setLoading(true)
    try {
      const formData = new FormData(e.target)
      const category = formData.get('category')
      const requestData = {
        category,
        business_justification: formData.get('business_justification'),
      }

      // Add MISC-specific fields if category is misc
      if (category === 'misc') {
        requestData.custom_description = formData.get('custom_description')
        requestData.purchase_url = formData.get('purchase_url')
        requestData.estimated_cost = parseFloat(formData.get('estimated_cost'))
      }

      await assetAPI.create(requestData)
      showMessage('Asset request submitted successfully!')
      await loadData()
      setView('my-requests')
      e.target.reset()
    } catch (error) {
      showMessage('Failed to create asset request: ' + error.message, 'error')
    } finally {
      setLoading(false)
    }
  }

  async function handleApprove(requestId, isManager, requestType = 'timeoff') {
    setLoading(true)
    try {
      const api = requestType === 'trip' ? tripAPI : requestType === 'asset' ? assetAPI : timeoffAPI

      if (isManager) {
        await api.approveManager(requestId)
        showMessage('Approved as manager! Waiting for admin approval.')
      } else {
        await api.approveAdmin(requestId)
        showMessage('Request fully approved!')
      }
      await loadData()
    } catch (error) {
      showMessage('Failed to approve: ' + error.message, 'error')
    } finally {
      setLoading(false)
    }
  }

  async function handleReject(requestId, requestType = 'timeoff') {
    const reason = prompt('Enter rejection reason:')
    if (!reason) return

    setLoading(true)
    try {
      const api = requestType === 'trip' ? tripAPI : requestType === 'asset' ? assetAPI : timeoffAPI
      await api.reject(requestId, reason)
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
          <div className="logo-container">
            <img src="/logo-edvolution.svg" alt="PAPEPE Logo" className="app-logo" />
            <div className="app-title">
              <h2>PAPEPE</h2>
              <p className="app-subtitle">Portal de Autoservicio Para el Personal Edvolution</p>
            </div>
          </div>
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
          {pendingApprovals.length > 0 && (
            <li className={view === 'approvals' ? 'active' : ''} onClick={() => setView('approvals')}>
              ⏳ Approvals ({pendingApprovals.length})
            </li>
          )}
          {employees.length > 0 && (
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
              <h2>My Requests</h2>
              {!Array.isArray(requests) || requests.length === 0 ? (
                <p>No requests yet. <a href="#" onClick={() => setView('new-request')}>Create your first request</a></p>
              ) : (
                <div className="requests-table">
                  {requests.map((item) => {
                    const [id, req] = Array.isArray(item) ? item : [item.request_id || Math.random(), item];
                    const requestType = req.request_type || 'timeoff';

                    return (
                      <div key={id} className="request-row">
                        <div className="request-info">
                          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                            <span className="request-type-badge" style={{ fontSize: '14px', padding: '2px 8px', borderRadius: '12px', background: '#f0f0f0' }}>
                              {requestType === 'timeoff' && '🏖️ Time Off'}
                              {requestType === 'trip' && '🌍 Business Trip'}
                              {requestType === 'asset' && '💻 Equipment'}
                            </span>
                          </div>

                          {requestType === 'timeoff' && (
                            <>
                              <strong>{new Date(req.start_date).toLocaleDateString()} - {new Date(req.end_date).toLocaleDateString()}</strong>
                              <span>{req.timeoff_type.replace('_', ' ')} - {req.working_days_count ?? req.days_count} working days</span>
                              {req.notes && <p className="notes"><strong>Your notes:</strong> {req.notes}</p>}
                            </>
                          )}

                          {requestType === 'trip' && (
                            <>
                              <strong>{req.destination}</strong>
                              <span>{new Date(req.start_date).toLocaleDateString()} - {new Date(req.end_date).toLocaleDateString()}</span>
                              <p className="notes"><strong>Purpose:</strong> {req.purpose}</p>
                              <p className="notes"><strong>Budget:</strong> {req.estimated_budget} {req.currency}</p>
                              {req.requires_advance_funding && <p className="notes" style={{ color: '#856404', background: '#fff3cd', padding: '4px 8px', borderRadius: '4px' }}>⚠️ Requires advance funding</p>}
                              {req.drive_folder_url && (
                                <p className="notes">
                                  <strong>📁 Drive Folder:</strong> <a href={req.drive_folder_url} target="_blank" rel="noopener noreferrer">Open folder</a>
                                </p>
                              )}
                              {req.spreadsheet_url && (
                                <p className="notes">
                                  <strong>📊 Expense Sheet:</strong> <a href={req.spreadsheet_url} target="_blank" rel="noopener noreferrer">Open spreadsheet</a>
                                </p>
                              )}
                            </>
                          )}

                          {requestType === 'asset' && (
                            <>
                              <strong>{req.category.replace('_', ' ').toUpperCase()}</strong>
                              {req.is_misc && req.custom_description && <span>{req.custom_description}</span>}
                              {!req.is_misc && <span>{req.category.replace('_', ' ')} request</span>}
                              <p className="notes"><strong>Justification:</strong> {req.business_justification}</p>
                              {req.is_misc && req.estimated_cost && <p className="notes"><strong>Estimated Cost:</strong> ${req.estimated_cost}</p>}
                            </>
                          )}

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
                          {requestType === 'timeoff' && req.status === 'pending' && (
                            <>
                              <button onClick={() => setEditingRequest({ id, ...req })} className="action-btn" style={{ background: '#667eea' }}>
                                ✏️ Edit
                              </button>
                              <button onClick={() => handleDeleteRequest(id)} className="action-btn" style={{ background: '#dc3545' }}>
                                🗑️ Delete
                              </button>
                            </>
                          )}
                          {requestType === 'timeoff' && req.status === 'approved' && !req.calendar_event_id && (
                            <button onClick={() => handleSyncCalendar(id)} className="action-btn">
                              📅 Sync Calendar
                            </button>
                          )}
                          {requestType === 'timeoff' && req.status === 'approved' && req.calendar_event_id && !req.autoresponder_enabled && (
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
          </div>
        )}

        {view === 'new-request' && (
          <div className="view-content">
            <h1>New Request</h1>

            <div className="request-type-selector" style={{ marginBottom: '32px' }}>
              <label style={{ display: 'block', marginBottom: '12px', fontWeight: '600' }}>What would you like to request?</label>
              <div style={{ display: 'flex', gap: '16px' }}>
                <button
                  onClick={() => { setRequestType('timeoff'); setShowPreview(false); }}
                  className={requestType === 'timeoff' ? 'submit-btn' : 'cancel-btn'}
                  style={{ flex: 1 }}
                >
                  ✈️ Time Off
                </button>
                <button
                  onClick={() => { setRequestType('trip'); setShowPreview(false); }}
                  className={requestType === 'trip' ? 'submit-btn' : 'cancel-btn'}
                  style={{ flex: 1 }}
                >
                  🌍 Business Trip
                </button>
                <button
                  onClick={() => { setRequestType('asset'); setShowPreview(false); }}
                  className={requestType === 'asset' ? 'submit-btn' : 'cancel-btn'}
                  style={{ flex: 1 }}
                >
                  💻 Equipment/Asset
                </button>
              </div>
            </div>

            {requestType === 'timeoff' && !showPreview && (
              <form onSubmit={handlePreviewRequest} className="request-form">
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
                  {loading ? 'Calculating...' : 'Preview Request'}
                </button>
              </form>
            )}

            {requestType === 'timeoff' && showPreview && (
              <div className="preview-section">
                <h2>Request Preview</h2>
                <div className="preview-info">
                  <p><strong>Your time-off calendar is set to: {workingDaysPreview?.holiday_region_name || 'Mexico'}</strong></p>
                  <p>You selected <strong>{workingDaysPreview?.calendar_days || 0} calendar days</strong> ({new Date(workingDaysPreview?.start_date).toLocaleDateString()} - {new Date(workingDaysPreview?.end_date).toLocaleDateString()})</p>
                </div>

                {workingDaysPreview?.non_working_days && workingDaysPreview.non_working_days.length > 0 && (
                  <div className="non-working-days">
                    <h3>Non-Working Days in Your Selected Range:</h3>
                    <ul>
                      {workingDaysPreview.non_working_days.map((day, idx) => (
                        <li key={idx} className={`day-${day.type}`}>
                          <strong>{new Date(day.date).toLocaleDateString()}</strong> - {day.reason}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                <div className="working-days-summary">
                  <p className="highlight">
                    Only <strong>{workingDaysPreview?.working_days || 0} working days</strong> will be deducted from your vacation balance.
                  </p>
                  {vacationSummary && (
                    <p className="balance-info">
                      Current balance: {vacationSummary.remaining_days} days available
                      {workingDaysPreview?.working_days && (
                        <> → After this request: {vacationSummary.remaining_days - workingDaysPreview.working_days} days remaining</>
                      )}
                    </p>
                  )}
                </div>

                <div className="preview-actions">
                  <button onClick={handleConfirmRequest} disabled={loading} className="submit-btn">
                    {loading ? 'Submitting...' : 'Confirm & Submit Request'}
                  </button>
                  <button onClick={handleCancelPreview} disabled={loading} className="cancel-btn">
                    Go Back & Edit
                  </button>
                </div>
              </div>
            )}

            {requestType === 'trip' && (
              <form onSubmit={handleSubmitTripRequest} className="request-form">
                <div className="form-group">
                  <label>Destination</label>
                  <input type="text" name="destination" placeholder="e.g., Mexico City" required />
                </div>
                <div className="form-group">
                  <label>Start Date</label>
                  <input type="date" name="start_date" required />
                </div>
                <div className="form-group">
                  <label>End Date</label>
                  <input type="date" name="end_date" required />
                </div>
                <div className="form-group">
                  <label>Purpose</label>
                  <input type="text" name="purpose" placeholder="e.g., Client meeting, Conference" required />
                </div>
                <div className="form-group">
                  <label>Expected Goal/Outcome</label>
                  <textarea name="expected_goal" rows="3" placeholder="e.g., Sign contract with Client X, Attend AWS Summit..." required></textarea>
                </div>
                <div className="form-group">
                  <label>Estimated Budget</label>
                  <input type="number" name="estimated_budget" step="0.01" placeholder="0.00" required />
                </div>
                <div className="form-group">
                  <label>Currency</label>
                  <select name="currency" required>
                    <option value="MXN">MXN (Mexican Peso)</option>
                    <option value="USD">USD (US Dollar)</option>
                    <option value="EUR">EUR (Euro)</option>
                    <option value="COP">COP (Colombian Peso)</option>
                    <option value="CLP">CLP (Chilean Peso)</option>
                  </select>
                </div>
                <div className="form-group">
                  <label>
                    <input type="checkbox" name="needs_advance_funding" />
                    {' '}I will need funding before the trip
                  </label>
                </div>
                <div className="form-group">
                  <label>Advance Amount (if needed)</label>
                  <input type="number" name="advance_amount" step="0.01" placeholder="0.00" />
                </div>
                <button type="submit" disabled={loading} className="submit-btn">
                  {loading ? 'Submitting...' : 'Submit Trip Request'}
                </button>
              </form>
            )}

            {requestType === 'asset' && (
              <form onSubmit={handleSubmitAssetRequest} className="request-form">
                <div className="form-group">
                  <label>Category</label>
                  <select name="category" required onChange={(e) => {
                    const miscFields = document.querySelectorAll('.misc-only');
                    miscFields.forEach(field => {
                      field.style.display = e.target.value === 'misc' ? 'block' : 'none';
                    });
                  }}>
                    <option value="">Select category...</option>
                    <option value="keyboard">Keyboard</option>
                    <option value="mouse">Mouse</option>
                    <option value="laptop">Laptop</option>
                    <option value="microphone">Microphone</option>
                    <option value="headphones">Headphones (for video conferences)</option>
                    <option value="license">Software License</option>
                    <option value="misc">Miscellaneous (Other)</option>
                  </select>
                </div>
                <div className="form-group misc-only" style={{ display: 'none' }}>
                  <label>Item Description</label>
                  <input type="text" name="custom_description" placeholder="Describe the item" />
                </div>
                <div className="form-group misc-only" style={{ display: 'none' }}>
                  <label>Purchase URL</label>
                  <input type="url" name="purchase_url" placeholder="https://example.com/product" />
                </div>
                <div className="form-group misc-only" style={{ display: 'none' }}>
                  <label>Estimated Cost</label>
                  <input type="number" name="estimated_cost" step="0.01" placeholder="0.00" />
                </div>
                <div className="form-group">
                  <label>Business Justification</label>
                  <textarea name="business_justification" rows="4" placeholder="Why do you need this asset? How will it help your work?" required></textarea>
                </div>
                <button type="submit" disabled={loading} className="submit-btn">
                  {loading ? 'Submitting...' : 'Submit Asset Request'}
                </button>
              </form>
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
                  const requestType = req.request_type || 'timeoff';

                  return (
                    <div key={id} className="approval-card">
                      <div className="approval-header">
                        <strong>{req.employee_email}</strong>
                        <span className={`status-badge status-${req.status}`}>{req.status.replace('_', ' ')}</span>
                        <span className="request-type-badge">
                          {requestType === 'timeoff' && '🏖️ Time Off'}
                          {requestType === 'trip' && '🌍 Business Trip'}
                          {requestType === 'asset' && '💻 Equipment'}
                        </span>
                      </div>
                      <div className="approval-details">
                        {requestType === 'timeoff' && (
                          <>
                            <p><strong>Dates:</strong> {new Date(req.start_date).toLocaleDateString()} - {new Date(req.end_date).toLocaleDateString()} ({req.working_days_count ?? req.days_count} working days)</p>
                            <p><strong>Type:</strong> {req.timeoff_type.replace('_', ' ')}</p>
                            {req.notes && <p><strong>Notes:</strong> {req.notes}</p>}
                          </>
                        )}
                        {requestType === 'trip' && (
                          <>
                            <p><strong>Destination:</strong> {req.destination}</p>
                            <p><strong>Dates:</strong> {new Date(req.start_date).toLocaleDateString()} - {new Date(req.end_date).toLocaleDateString()}</p>
                            <p><strong>Purpose:</strong> {req.purpose}</p>
                            <p><strong>Expected Goal:</strong> {req.expected_goal}</p>
                            <p><strong>Budget:</strong> {req.estimated_budget} {req.currency}</p>
                            {req.requires_advance_funding && <p><strong>⚠️ Requires advance funding</strong></p>}
                          </>
                        )}
                        {requestType === 'asset' && (
                          <>
                            <p><strong>Category:</strong> {req.category.replace('_', ' ').toUpperCase()}</p>
                            {req.is_misc && req.custom_description && <p><strong>Description:</strong> {req.custom_description}</p>}
                            {req.is_misc && req.purchase_url && <p><strong>URL:</strong> <a href={req.purchase_url} target="_blank" rel="noopener noreferrer">{req.purchase_url}</a></p>}
                            {req.is_misc && req.estimated_cost && <p><strong>Estimated Cost:</strong> ${req.estimated_cost}</p>}
                            <p><strong>Justification:</strong> {req.business_justification}</p>
                          </>
                        )}
                      </div>
                      <div className="approval-actions">
                        {req.status === 'pending' && (
                          <button onClick={() => handleApprove(id, true, requestType)} className="approve-btn" disabled={loading}>
                            ✅ Approve (Manager)
                          </button>
                        )}
                        {req.status === 'manager_approved' && user.is_admin && (
                          <button onClick={() => handleApprove(id, false, requestType)} className="approve-btn" disabled={loading}>
                            ✅ Approve (Admin)
                          </button>
                        )}
                        <button onClick={() => handleReject(id, requestType)} className="reject-btn" disabled={loading}>
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

        {view === 'team' && employees.length > 0  && (
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
              <EmployeeDetailModal
                employee={editingEmployee}
                onClose={() => setEditingEmployee(null)}
              />
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
