import { useState, useEffect } from 'react';
import { employeeAPI, timeoffAPI, tripAPI, assetAPI } from '../services/api';

export function EmployeeDetailModal({ employee, onClose }) {
  const [activeTab, setActiveTab] = useState('overview');
  const [employeeDetail, setEmployeeDetail] = useState(null);
  const [requestsHistory, setRequestsHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Performance evaluation state
  const [showNewEvaluation, setShowNewEvaluation] = useState(false);
  const [newEvaluation, setNewEvaluation] = useState({
    evaluation_text: '',
    rating: '',
    goals: []
  });
  const [newGoal, setNewGoal] = useState('');

  // Follow-up state
  const [followUpEvalId, setFollowUpEvalId] = useState(null);
  const [followUpNote, setFollowUpNote] = useState('');
  const [followUpRating, setFollowUpRating] = useState('');

  useEffect(() => {
    if (employee) {
      fetchEmployeeDetails();
    }
  }, [employee]);

  useEffect(() => {
    if (activeTab === 'requests' && employee) {
      fetchRequestsHistory();
    }
  }, [activeTab, employee]);

  const fetchEmployeeDetails = async () => {
    try {
      setLoading(true);
      const data = await employeeAPI.getOne(employee.email);
      setEmployeeDetail(data);
      setError(null);
    } catch (err) {
      setError(`Failed to load employee details: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const fetchRequestsHistory = async () => {
    try {
      setLoading(true);
      const currentYear = new Date().getFullYear();

      // Fetch all request types in parallel
      const [timeoffData, tripData, assetData] = await Promise.all([
        timeoffAPI.getEmployeeHistory(employee.email, currentYear).catch(() => []),
        tripAPI.getMy().catch(() => []), // Note: tripAPI doesn't have getEmployeeHistory, so filter by email
        assetAPI.getMy().catch(() => []) // Note: assetAPI doesn't have getEmployeeHistory, so filter by email
      ]);

      // Combine and tag all requests with type
      const allRequests = [
        ...(Array.isArray(timeoffData) ? timeoffData : []).map(req => ({ ...req, request_type: 'timeoff' })),
        ...(Array.isArray(tripData) ? tripData : [])
          .filter(item => {
            const req = Array.isArray(item) ? item[1] : item;
            return req.employee_email === employee.email;
          })
          .map(item => {
            const [id, req] = Array.isArray(item) ? item : [item.request_id, item];
            return { ...req, request_id: id, request_type: 'trip' };
          }),
        ...(Array.isArray(assetData) ? assetData : [])
          .filter(item => {
            const req = Array.isArray(item) ? item[1] : item;
            return req.employee_email === employee.email;
          })
          .map(item => {
            const [id, req] = Array.isArray(item) ? item : [item.request_id, item];
            return { ...req, request_id: id, request_type: 'asset' };
          }),
      ];

      // Sort by date (most recent first)
      allRequests.sort((a, b) => {
        const dateA = new Date(a.start_date || a.created_at);
        const dateB = new Date(b.start_date || b.created_at);
        return dateB - dateA;
      });

      setRequestsHistory(allRequests);
      setError(null);
    } catch (err) {
      setError(`Failed to load request history: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleAddEvaluation = async (e) => {
    e.preventDefault();
    try {
      setLoading(true);
      await employeeAPI.addEvaluation(employee.email, newEvaluation);
      await fetchEmployeeDetails();
      setShowNewEvaluation(false);
      setNewEvaluation({ evaluation_text: '', rating: '', goals: [] });
      setError(null);
    } catch (err) {
      setError(`Failed to add evaluation: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleAddFollowUp = async (evaluationId) => {
    try {
      setLoading(true);
      await employeeAPI.addEvaluationFollowUp(employee.email, evaluationId, {
        note: followUpNote,
        progress_rating: followUpRating ? parseInt(followUpRating) : null
      });
      await fetchEmployeeDetails();
      setFollowUpEvalId(null);
      setFollowUpNote('');
      setFollowUpRating('');
      setError(null);
    } catch (err) {
      setError(`Failed to add follow-up: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const addGoal = () => {
    if (newGoal.trim()) {
      setNewEvaluation({
        ...newEvaluation,
        goals: [...newEvaluation.goals, newGoal.trim()]
      });
      setNewGoal('');
    }
  };

  const removeGoal = (index) => {
    setNewEvaluation({
      ...newEvaluation,
      goals: newEvaluation.goals.filter((_, i) => i !== index)
    });
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const getStatusBadgeColor = (status) => {
    switch (status) {
      case 'approved': return '#28a745';
      case 'manager_approved': return '#ffc107';
      case 'pending': return '#17a2b8';
      case 'rejected': return '#dc3545';
      default: return '#6c757d';
    }
  };

  const getStatusLabel = (status) => {
    switch (status) {
      case 'manager_approved': return 'Manager Approved';
      case 'pending': return 'Pending';
      case 'approved': return 'Approved';
      case 'rejected': return 'Rejected';
      default: return status;
    }
  };

  if (!employee) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content large-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>{employeeDetail?.display_name || employee.full_name || employee.email}</h2>
          <button onClick={onClose} className="close-btn" style={{ background: 'none', border: 'none', fontSize: '24px', cursor: 'pointer' }}>×</button>
        </div>

        <div className="info-message" style={{ background: '#e3f2fd', padding: '12px', borderRadius: '4px', marginBottom: '16px', fontSize: '14px' }}>
          ℹ️ As a manager, you can view your team members' information but cannot edit basic details. Only HR admins can modify employee data.
        </div>

        {error && (
          <div className="error-message" style={{ background: '#f8d7da', color: '#721c24', padding: '12px', borderRadius: '4px', marginBottom: '16px' }}>
            {error}
          </div>
        )}

        <div className="tabs">
          <button
            className={`tab ${activeTab === 'overview' ? 'active' : ''}`}
            onClick={() => setActiveTab('overview')}
          >
            Overview
          </button>
          <button
            className={`tab ${activeTab === 'requests' ? 'active' : ''}`}
            onClick={() => setActiveTab('requests')}
          >
            Requests History
          </button>
          <button
            className={`tab ${activeTab === 'performance' ? 'active' : ''}`}
            onClick={() => setActiveTab('performance')}
          >
            Performance
          </button>
          <button
            className={`tab ${activeTab === 'contract' ? 'active' : ''}`}
            onClick={() => setActiveTab('contract')}
          >
            Contract Info
          </button>
        </div>

        <div className="tab-content">
          {activeTab === 'overview' && employeeDetail && (
            <div className="employee-view-only">
              <div className="form-group">
                <label>Email</label>
                <input type="text" value={employeeDetail.email || 'Not set'} disabled style={{ background: '#f5f5f5' }} />
              </div>
              <div className="form-group">
                <label>Organizational Unit</label>
                <input type="text" value={employeeDetail.organizational_unit || 'Not set'} disabled style={{ background: '#f5f5f5' }} />
              </div>
              <div className="form-group">
                <label>Department / Team</label>
                <input type="text" value={employeeDetail.department || 'Not set'} disabled style={{ background: '#f5f5f5' }} />
              </div>
              <div className="form-group">
                <label>Job Title</label>
                <input type="text" value={employeeDetail.job_title || 'Not set'} disabled style={{ background: '#f5f5f5' }} />
              </div>
              <div className="form-group">
                <label>Location</label>
                <input type="text" value={employeeDetail.location || 'Not set'} disabled style={{ background: '#f5f5f5' }} />
              </div>
              <div className="form-group">
                <label>Working Address</label>
                <textarea value={employeeDetail.working_address || 'Not set'} disabled style={{ background: '#f5f5f5', minHeight: '60px' }} />
              </div>
              <div className="form-group">
                <label>Country</label>
                <input type="text" value={employeeDetail.country || 'Not set'} disabled style={{ background: '#f5f5f5' }} />
              </div>
              <div className="form-group">
                <label>Region</label>
                <input type="text" value={employeeDetail.region || 'Not set'} disabled style={{ background: '#f5f5f5' }} />
              </div>
              <div className="form-group">
                <label>Vacation Days per Year</label>
                <input type="text" value={employeeDetail.vacation_days_per_year || '20'} disabled style={{ background: '#f5f5f5' }} />
              </div>
            </div>
          )}

          {activeTab === 'requests' && (
            <div className="requests-history">
              {loading ? (
                <p>Loading request history...</p>
              ) : requestsHistory.length === 0 ? (
                <p style={{ textAlign: 'center', color: '#666', padding: '20px' }}>No requests for this year.</p>
              ) : (
                <table className="timeoff-table">
                  <thead>
                    <tr>
                      <th>Request Type</th>
                      <th>Details</th>
                      <th>Start Date</th>
                      <th>End Date</th>
                      <th>Days</th>
                      <th>Status</th>
                      <th>Notes</th>
                    </tr>
                  </thead>
                  <tbody>
                    {requestsHistory.map((request) => (
                      <tr key={request.request_id}>
                        <td>
                          <span style={{
                            padding: '4px 8px',
                            borderRadius: '12px',
                            fontSize: '12px',
                            fontWeight: 'bold',
                            background: '#f0f0f0',
                            display: 'inline-block'
                          }}>
                            {request.request_type === 'timeoff' && '🏖️ Time Off'}
                            {request.request_type === 'trip' && '🌍 Business Trip'}
                            {request.request_type === 'asset' && '💻 Equipment'}
                          </span>
                        </td>
                        <td style={{ fontSize: '13px' }}>
                          {request.request_type === 'timeoff' && (
                            <span style={{ textTransform: 'capitalize' }}>{request.timeoff_type?.replace('_', ' ')}</span>
                          )}
                          {request.request_type === 'trip' && (
                            <div>
                              <strong>{request.destination}</strong>
                              <div style={{ fontSize: '12px', color: '#666' }}>Budget: {request.estimated_budget} {request.currency}</div>
                            </div>
                          )}
                          {request.request_type === 'asset' && (
                            <div>
                              <strong>{request.category?.replace('_', ' ').toUpperCase()}</strong>
                              {request.is_misc && request.custom_description && (
                                <div style={{ fontSize: '12px', color: '#666' }}>{request.custom_description}</div>
                              )}
                            </div>
                          )}
                        </td>
                        <td>{formatDate(request.start_date)}</td>
                        <td>{formatDate(request.end_date)}</td>
                        <td>{request.working_days_count || request.days_count || '-'}</td>
                        <td>
                          <span style={{
                            padding: '4px 8px',
                            borderRadius: '4px',
                            color: 'white',
                            fontSize: '12px',
                            fontWeight: 'bold',
                            background: getStatusBadgeColor(request.status)
                          }}>
                            {getStatusLabel(request.status)}
                          </span>
                        </td>
                        <td style={{ fontSize: '13px', color: '#666', maxWidth: '200px' }}>
                          {request.request_type === 'timeoff' && (request.notes || '-')}
                          {request.request_type === 'trip' && (request.purpose || '-')}
                          {request.request_type === 'asset' && (request.business_justification || '-')}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          )}

          {activeTab === 'performance' && employeeDetail && (
            <div className="performance-section">
              <div className="section-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                <h3>Performance Evaluations</h3>
                <button
                  onClick={() => setShowNewEvaluation(!showNewEvaluation)}
                  className="primary-btn"
                  disabled={loading}
                >
                  {showNewEvaluation ? 'Cancel' : '+ Add Evaluation'}
                </button>
              </div>

              {showNewEvaluation && (
                <form onSubmit={handleAddEvaluation} className="new-evaluation-form" style={{ background: '#f8f9fa', padding: '16px', borderRadius: '4px', marginBottom: '20px' }}>
                  <div className="form-group">
                    <label>Evaluation Text *</label>
                    <textarea
                      value={newEvaluation.evaluation_text}
                      onChange={(e) => setNewEvaluation({ ...newEvaluation, evaluation_text: e.target.value })}
                      required
                      rows="4"
                      placeholder="Enter evaluation comments..."
                    />
                  </div>
                  <div className="form-group">
                    <label>Rating (1-5)</label>
                    <select
                      value={newEvaluation.rating}
                      onChange={(e) => setNewEvaluation({ ...newEvaluation, rating: e.target.value })}
                    >
                      <option value="">Select rating...</option>
                      <option value="1">1 - Needs Improvement</option>
                      <option value="2">2 - Below Expectations</option>
                      <option value="3">3 - Meets Expectations</option>
                      <option value="4">4 - Exceeds Expectations</option>
                      <option value="5">5 - Outstanding</option>
                    </select>
                  </div>
                  <div className="form-group">
                    <label>Goals & Objectives</label>
                    <div style={{ display: 'flex', gap: '8px', marginBottom: '8px' }}>
                      <input
                        type="text"
                        value={newGoal}
                        onChange={(e) => setNewGoal(e.target.value)}
                        placeholder="Add a goal..."
                        onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addGoal())}
                      />
                      <button type="button" onClick={addGoal} className="secondary-btn">Add</button>
                    </div>
                    {newEvaluation.goals.length > 0 && (
                      <ul style={{ listStyle: 'none', padding: 0 }}>
                        {newEvaluation.goals.map((goal, idx) => (
                          <li key={idx} style={{ display: 'flex', justifyContent: 'space-between', padding: '8px', background: 'white', marginBottom: '4px', borderRadius: '4px' }}>
                            <span>{goal}</span>
                            <button type="button" onClick={() => removeGoal(idx)} style={{ background: 'none', border: 'none', color: '#dc3545', cursor: 'pointer' }}>✕</button>
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                  <button type="submit" className="primary-btn" disabled={loading}>
                    {loading ? 'Saving...' : 'Save Evaluation'}
                  </button>
                </form>
              )}

              {employeeDetail.evaluations && employeeDetail.evaluations.length > 0 ? (
                <div className="evaluations-list">
                  {employeeDetail.evaluations.map((evaluation, idx) => (
                    <div key={evaluation.id || idx} className="evaluation-card" style={{ border: '1px solid #dee2e6', borderRadius: '4px', padding: '16px', marginBottom: '16px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px' }}>
                        <div>
                          <strong>{evaluation.evaluator_name || evaluation.evaluator_email}</strong>
                          <span style={{ color: '#666', fontSize: '14px', marginLeft: '12px' }}>
                            {formatDate(evaluation.date)}
                          </span>
                        </div>
                        {evaluation.rating && (
                          <span style={{
                            padding: '4px 12px',
                            borderRadius: '4px',
                            background: '#ffc107',
                            color: '#000',
                            fontWeight: 'bold',
                            fontSize: '14px'
                          }}>
                            Rating: {evaluation.rating}/5
                          </span>
                        )}
                      </div>
                      <p style={{ marginBottom: '12px', lineHeight: '1.6' }}>{evaluation.evaluation_text}</p>

                      {evaluation.goals && evaluation.goals.length > 0 && (
                        <div style={{ marginBottom: '12px' }}>
                          <strong style={{ fontSize: '14px' }}>Goals:</strong>
                          <ul style={{ marginTop: '8px', marginLeft: '20px' }}>
                            {evaluation.goals.map((goal, goalIdx) => (
                              <li key={goalIdx} style={{ marginBottom: '4px' }}>{goal}</li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {evaluation.follow_ups && evaluation.follow_ups.length > 0 && (
                        <div className="follow-ups" style={{ marginTop: '16px', paddingTop: '16px', borderTop: '1px solid #dee2e6' }}>
                          <strong style={{ fontSize: '14px' }}>Follow-ups:</strong>
                          {evaluation.follow_ups.map((followUp, fuIdx) => (
                            <div key={fuIdx} style={{ marginTop: '12px', padding: '12px', background: '#f8f9fa', borderRadius: '4px' }}>
                              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                                <span style={{ fontSize: '13px', color: '#666' }}>
                                  {followUp.author_name || followUp.author_email} - {formatDate(followUp.date)}
                                </span>
                                {followUp.progress_rating && (
                                  <span style={{ fontSize: '13px', fontWeight: 'bold' }}>
                                    Progress: {followUp.progress_rating}/5
                                  </span>
                                )}
                              </div>
                              <p style={{ fontSize: '14px', margin: 0 }}>{followUp.note}</p>
                            </div>
                          ))}
                        </div>
                      )}

                      <div style={{ marginTop: '12px' }}>
                        {followUpEvalId === (evaluation.id || idx) ? (
                          <div className="follow-up-form" style={{ marginTop: '12px', padding: '12px', background: '#f8f9fa', borderRadius: '4px' }}>
                            <textarea
                              value={followUpNote}
                              onChange={(e) => setFollowUpNote(e.target.value)}
                              placeholder="Add follow-up note..."
                              rows="3"
                              style={{ width: '100%', marginBottom: '8px' }}
                            />
                            <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                              <select
                                value={followUpRating}
                                onChange={(e) => setFollowUpRating(e.target.value)}
                                style={{ flex: '1' }}
                              >
                                <option value="">Progress rating (optional)</option>
                                <option value="1">1 - No Progress</option>
                                <option value="2">2 - Some Progress</option>
                                <option value="3">3 - Good Progress</option>
                                <option value="4">4 - Excellent Progress</option>
                                <option value="5">5 - Goal Achieved</option>
                              </select>
                              <button
                                onClick={() => handleAddFollowUp(evaluation.id || idx)}
                                className="primary-btn"
                                disabled={!followUpNote.trim() || loading}
                              >
                                Save
                              </button>
                              <button
                                onClick={() => {
                                  setFollowUpEvalId(null);
                                  setFollowUpNote('');
                                  setFollowUpRating('');
                                }}
                                className="secondary-btn"
                              >
                                Cancel
                              </button>
                            </div>
                          </div>
                        ) : (
                          <button
                            onClick={() => setFollowUpEvalId(evaluation.id || idx)}
                            className="secondary-btn"
                            style={{ fontSize: '14px' }}
                          >
                            + Add Follow-up
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p style={{ textAlign: 'center', color: '#666', padding: '20px' }}>No performance evaluations yet.</p>
              )}
            </div>
          )}

          {activeTab === 'contract' && employeeDetail && (
            <div className="employee-view-only">
              <div className="form-group">
                <label>Contract Type</label>
                <input
                  type="text"
                  value={employeeDetail.contract_type ? employeeDetail.contract_type.charAt(0).toUpperCase() + employeeDetail.contract_type.slice(1) : 'Not set'}
                  disabled
                  style={{ background: '#f5f5f5' }}
                />
              </div>
              <div className="form-group">
                <label>Contract Start Date</label>
                <input type="text" value={formatDate(employeeDetail.contract_start_date) || 'Not set'} disabled style={{ background: '#f5f5f5' }} />
              </div>
              <div className="form-group">
                <label>Contract End Date</label>
                <input type="text" value={formatDate(employeeDetail.contract_end_date) || 'Not set'} disabled style={{ background: '#f5f5f5' }} />
              </div>
              <div className="info-message" style={{ background: '#fff3cd', padding: '12px', borderRadius: '4px', marginTop: '16px', fontSize: '14px' }}>
                ⚠️ Contract documents and compensation details are restricted to HR administrators only.
              </div>
            </div>
          )}
        </div>

        <div className="modal-actions" style={{ marginTop: '20px', paddingTop: '20px', borderTop: '1px solid #dee2e6' }}>
          <button onClick={onClose} className="cancel-btn">
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
