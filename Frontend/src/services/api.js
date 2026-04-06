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

// Helper function for API calls
const apiCall = async (endpoint, options = {}) => {
  const url = `${API_BASE_URL}${endpoint}`;
  const token = localStorage.getItem('authToken');

  const config = {
    headers: {
      'Content-Type': 'application/json',
      ...(token && { 'X-User-Token': token }),
      ...options.headers,
    },
    ...options,
  };

  try {
    const response = await fetch(url, config);
    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || data.message || 'API request failed');
    }

    return data;
  } catch (error) {
    console.error('API Error:', error);
    throw error;
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

export default { authAPI, chatAPI };
