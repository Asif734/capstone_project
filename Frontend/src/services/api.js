// // API Base URL - Update this with your backend URL
// const API_BASE_URL = 'http://localhost:8000/api';

// // Helper function for API calls
// const apiCall = async (endpoint, options = {}) => {
//   const url = `${API_BASE_URL}${endpoint}`;
//   const token = localStorage.getItem('authToken');

//   const config = {
//     headers: {
//       'Content-Type': 'application/json',
//       ...(token && { Authorization: `Bearer ${token}` }),
//       ...options.headers,
//     },
//     ...options,
//   };

//   try {
//     const response = await fetch(url, config);
//     const data = await response.json();

//     if (!response.ok) {
//       throw new Error(data.message || 'API request failed');
//     }

//     return data;
//   } catch (error) {
//     console.error('API Error:', error);
//     throw error;
//   }
// };

// // Auth API endpoints
// export const authAPI = {
//   // Sign In
//   signIn: async (credentials) => {
//     return apiCall('/auth/signin', {
//       method: 'POST',
//       body: JSON.stringify(credentials),
//     });
//   },

//   // Sign Up Step 1 - Send OTP
//   sendOTP: async (data) => {
//     return apiCall('/auth/send-otp', {
//       method: 'POST',
//       body: JSON.stringify(data),
//     });
//   },

//   // Sign Up Step 2 - Verify OTP and Create Account
//   signUp: async (data) => {
//     return apiCall('/auth/signup', {
//       method: 'POST',
//       body: JSON.stringify(data),
//     });
//   },

//   // Verify token
//   verifyToken: async () => {
//     return apiCall('/auth/verify', {
//       method: 'GET',
//     });
//   },
// };

// // Chat API endpoints
// export const chatAPI = {
//   // Send message
//   sendMessage: async (message) => {
//     return apiCall('/chat/send', {
//       method: 'POST',
//       body: JSON.stringify({ message }),
//     });
//   },

//   // Get chat history
//   getChatHistory: async () => {
//     return apiCall('/chat/history', {
//       method: 'GET',
//     });
//   },
// };

// export default { authAPI, chatAPI };



// API Base URL - FastAPI backend
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const API_TIMEOUT_MS = Number(import.meta.env.VITE_API_TIMEOUT_MS || 180000); // 3 minutes timeout for local LLM inference

// Helper function for API calls
const apiCall = async (endpoint, options = {}) => {
  const url = `${API_BASE_URL}${endpoint}`;
  const token = localStorage.getItem('authToken');
  const controller = new AbortController();
  const timeoutId = window.setTimeout(() => controller.abort(), API_TIMEOUT_MS);
  const hasJsonBody = options.body && !(options.body instanceof FormData);

  const config = {
    ...options,
    signal: controller.signal,
    headers: {
      ...(hasJsonBody && { 'Content-Type': 'application/json' }),
      ...(token && { 'X-User-Token': token }),
      ...options.headers,
    },
  };

  try {
    const response = await fetch(url, config);
    const responseText = await response.text();
    let data = {};
    if (responseText) {
      try {
        data = JSON.parse(responseText);
      } catch {
        data = { detail: responseText };
      }
    }

    if (!response.ok) {
      throw new Error(data.detail || data.message || 'API request failed');
    }

    return data;
  } catch (error) {
    if (error.name === 'AbortError') {
      throw new Error('The server took too long to respond. Please try again.');
    }
    throw error;
  } finally {
    window.clearTimeout(timeoutId);
  }
};

// ==============================
// AUTH API ENDPOINTS
// ==============================
export const authAPI = {
  // Step 1: Sign Up (send reg_id and email)
  signUp: async (data) => {
    return apiCall('/signup', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  // Step 2: Verify OTP (confirm password)
  verifyOTP: async (data) => {
    return apiCall('/verify-otp', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  // Step 3: Sign In (login)
  signIn: async (credentials) => {
    return apiCall('/login', {
      method: 'POST',
      body: JSON.stringify(credentials),
    });
  },

  getCurrentUser: async () => apiCall('/me', { method: 'GET' }),
};

// ==============================
// CHATBOT / QUERY API ENDPOINTS
// ==============================
export const chatAPI = {
  // Send a message (ask a question)
  sendMessage: async (payload, tokenOverride = null) => {
    // payload example: { user_id: "abc123", question: "What is thermodynamics?" }
    return apiCall('/query', {
      method: 'POST',
      headers: tokenOverride ? { 'X-User-Token': tokenOverride } : {},
      body: JSON.stringify(payload),
    });
  },
};

// ==============================
// ADMIN API ENDPOINTS
// ==============================
const adminHeaders = (adminToken) => ({
  'X-Admin-Token': adminToken,
});

export const adminAPI = {
  getSummary: async (adminToken) => {
    return apiCall('/admin/mental-health-summary', {
      method: 'GET',
      headers: adminHeaders(adminToken),
    });
  },

  getAlerts: async (adminToken) => {
    return apiCall('/admin/mental-health-alerts', {
      method: 'GET',
      headers: adminHeaders(adminToken),
    });
  },

  updateAlert: async (adminToken, alertId, data) => {
    return apiCall(`/admin/mental-health-alerts/${alertId}`, {
      method: 'PATCH',
      headers: adminHeaders(adminToken),
      body: JSON.stringify(data),
    });
  },

  deleteAlert: async (adminToken, alertId) => {
    return apiCall(`/admin/mental-health-alerts/${alertId}`, {
      method: 'DELETE',
      headers: adminHeaders(adminToken),
    });
  },

  clearAlerts: async (adminToken) => {
    return apiCall('/admin/mental-health-alerts', {
      method: 'DELETE',
      headers: adminHeaders(adminToken),
    });
  },

  getStudents: async (adminToken) => {
    return apiCall('/admin/authorized-students', {
      method: 'GET',
      headers: adminHeaders(adminToken),
    });
  },

  addStudent: async (adminToken, data) => {
    return apiCall('/admin/authorized-students', {
      method: 'POST',
      headers: adminHeaders(adminToken),
      body: JSON.stringify(data),
    });
  },

  updateStudent: async (adminToken, studentId, data) => {
    return apiCall(`/admin/authorized-students/${studentId}`, {
      method: 'PATCH',
      headers: adminHeaders(adminToken),
      body: JSON.stringify(data),
    });
  },

  deleteStudent: async (adminToken, studentId) => {
    return apiCall(`/admin/authorized-students/${studentId}`, {
      method: 'DELETE',
      headers: adminHeaders(adminToken),
    });
  },

  getStudentMentalHealth: async (adminToken, regId) => {
    return apiCall(`/admin/students/${regId}/mental-health`, {
      method: 'GET',
      headers: adminHeaders(adminToken),
    });
  },

  getStudentRecords: async (adminToken, regId) => {
    return apiCall(`/admin/students/${regId}/records`, {
      method: 'GET',
      headers: adminHeaders(adminToken),
    });
  },

  updateStudentRecords: async (adminToken, regId, data) => {
    return apiCall(`/admin/students/${regId}/records`, {
      method: 'PATCH',
      headers: adminHeaders(adminToken),
      body: JSON.stringify(data),
    });
  },

  login: async (email, password) => {
    return apiCall('/admin/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
  },

  getAuditLogs: async (adminToken, params = {}) => {
    const query = new URLSearchParams();
    if (params.limit) query.set('limit', params.limit);
    if (params.offset !== undefined) query.set('offset', params.offset);
    if (params.actor_student_id) query.set('actor_student_id', params.actor_student_id);
    if (params.target_student_id) query.set('target_student_id', params.target_student_id);
    if (params.action_type) query.set('action_type', params.action_type);
    if (params.auth_status) query.set('auth_status', params.auth_status);
    if (params.agent_node) query.set('agent_node', params.agent_node);
    const queryString = query.toString() ? `?${query.toString()}` : '';

    return apiCall(`/admin/audit-logs${queryString}`, {
      method: 'GET',
      headers: adminHeaders(adminToken),
    });
  },

  getDocuments: async (adminToken) => {
    return apiCall('/documents', {
      method: 'GET',
      headers: adminHeaders(adminToken),
    });
  },

  uploadDocument: async (adminToken, file) => {
    const formData = new FormData();
    formData.append('file', file);
    return apiCall('/upload', {
      method: 'POST',
      headers: adminHeaders(adminToken),
      body: formData,
    });
  },

  deleteDocument: async (adminToken, documentName) => {
    return apiCall(`/documents/${encodeURIComponent(documentName)}`, {
      method: 'DELETE',
      headers: adminHeaders(adminToken),
    });
  },
};

export default { authAPI, chatAPI, adminAPI };
