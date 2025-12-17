const API_BASE = '';

async function fetchAPI(url, options = {}) {
  const response = await fetch(API_BASE + url, {
    ...options,
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: 'Request failed' }));
    throw new Error(error.error || `HTTP ${response.status}`);
  }

  return response.json();
}

export const authAPI = {
  checkStatus: () => fetchAPI('/auth/status'),
  login: () => window.location.href = '/auth/login',
  logout: () => window.location.href = '/auth/logout',
};

export const employeeAPI = {
  getMe: () => fetchAPI('/api/employees/me'),
  list: () => fetchAPI('/api/employees/'),
  listAll: () => fetchAPI('/api/employees/'),
  getOne: (email) => fetchAPI(`/api/employees/${email}`),
  updateMe: (data) => fetchAPI('/api/employees/me', {
    method: 'PUT',
    body: JSON.stringify(data),
  }),
  update: (email, data) => fetchAPI(`/api/employees/${email}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  }),
  changeOU: (email, ou_key) => fetchAPI(`/api/employees/${email}/change-ou`, {
    method: 'POST',
    body: JSON.stringify({ ou_key }),
  }),
  sync: () => fetchAPI('/api/employees/sync', { method: 'POST' }),
  getTeam: () => fetchAPI('/api/employees/team'),
  getHolidayRegions: () => fetchAPI('/api/employees/holiday-regions'),
  getRegionHolidays: (regionCode, year) => fetchAPI(`/api/employees/holiday-regions/${regionCode}/holidays/${year}`),
};

export const timeoffAPI = {
  create: (data) => fetchAPI('/api/timeoff/requests', {
    method: 'POST',
    body: JSON.stringify(data),
  }),
  getMy: (year) => fetchAPI(`/api/timeoff/requests/my${year ? `?year=${year}` : ''}`),
  getOne: (id) => fetchAPI(`/api/timeoff/requests/${id}`),
  update: (id, data) => fetchAPI(`/api/timeoff/requests/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  }),
  delete: (id) => fetchAPI(`/api/timeoff/requests/${id}`, {
    method: 'DELETE',
  }),
  getPendingApprovals: () => fetchAPI('/api/timeoff/requests/pending-approval'),
  approveManager: (id) => fetchAPI(`/api/timeoff/requests/${id}/approve-manager`, {
    method: 'POST',
  }),
  approveAdmin: (id) => fetchAPI(`/api/timeoff/requests/${id}/approve-admin`, {
    method: 'POST',
  }),
  reject: (id, reason) => fetchAPI(`/api/timeoff/requests/${id}/reject`, {
    method: 'POST',
    body: JSON.stringify({ reason }),
  }),
  syncCalendar: (id) => fetchAPI(`/api/timeoff/requests/${id}/sync-calendar`, {
    method: 'POST',
  }),
  enableAutoresponder: (id) => fetchAPI(`/api/timeoff/requests/${id}/enable-autoresponder`, {
    method: 'POST',
  }),
  getVacationSummary: (year) => fetchAPI(`/api/timeoff/vacation-summary${year ? `?year=${year}` : ''}`),
};
