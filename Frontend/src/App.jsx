// import React, { useState } from 'react';
// import Header from './components/layout/Header';
// import ChatArea from './components/chat/ChatArea';
// import MessageInput from './components/chat/MessageInput';
// import AuthModal from './components/auth/AuthModal';

// function App() {
//   const [showAuthModal, setShowAuthModal] = useState(false);
//   const [authMode, setAuthMode] = useState('signin');
//   const [messages, setMessages] = useState([]);

//   const handleOpenAuth = (mode) => {
//     setAuthMode(mode);
//     setShowAuthModal(true);
//   };

//   const handleCloseAuth = () => {
//     setShowAuthModal(false);
//   };

//   const handleSendMessage = (message) => {
//     // Add user message
//     setMessages([...messages, { text: message, isUser: true }]);
    
//     // TODO: Send to API and get response
//     // Simulate bot response
//     setTimeout(() => {
//       setMessages(prev => [...prev, { 
//         text: 'This is a simulated response. Connect to your backend API for real responses.', 
//         isUser: false 
//       }]);
//     }, 1000);
//   };

//   return (
//     <div className="flex flex-col h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
//       <Header onOpenAuth={handleOpenAuth} />
//       <ChatArea messages={messages} />
//       <MessageInput onSendMessage={handleSendMessage} />
//       <AuthModal 
//         isOpen={showAuthModal} 
//         onClose={handleCloseAuth}
//         initialMode={authMode}
//       />
//     </div>
//   );
// }

// export default App;

import React, { useState } from 'react';
import Header from './components/layout/Header';
import ChatArea from './components/chat/ChatArea';
import MessageInput from './components/chat/MessageInput';
import AuthModal from './components/auth/AuthModal';
import AdminDashboard from './components/admin/AdminDashboard';
import { chatAPI } from './services/api';
import { useAuth } from './hooks/useAuth';

function App() {
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [authMode, setAuthMode] = useState('signin');
  const [messages, setMessages] = useState([]);
  const [activeView, setActiveView] = useState('chat');
  const [isAdminAuthenticated, setIsAdminAuthenticated] = useState(false);
  const { user, signIn, sendOTP, verifyOTP, signOut, error } = useAuth();

  const handleOpenAuth = (mode) => {
    console.log('Opening auth with mode:', mode); // Debug log
    setAuthMode(mode);
    setShowAuthModal(true);
  };

  const handleCloseAuth = () => {
    setShowAuthModal(false);
  };

  const handleAuthSuccess = () => {
    setActiveView('chat');
    setShowAuthModal(false);
  };

  const handleAdminAuth = () => {
    setIsAdminAuthenticated(true);
    setActiveView('admin');
  };

  const handleAdminLogout = () => {
    setIsAdminAuthenticated(false);
    setActiveView('chat');
  };

  const handleSendMessage = (message) => {
    // Add user message
    setMessages([...messages, { text: message, isUser: true }]);
    
    chatAPI.sendMessage(
      { user_id: 'student_001', question: message, top_k: 3 },
      user?.token || null
    )
    .then((data) => {
      setMessages(prev => [...prev, { 
        text: data.answer || 'No response', 
        isUser: false 
      }]);
    })
    .catch((error) => {
      console.error('Chat request failed:', error);
      const message = error?.message
        ? `Unable to reach backend. ${error.message}`
        : 'Unable to reach backend. Check that it is running on http://localhost:8000';
      setMessages(prev => [...prev, { 
        text: message,
        isUser: false 
      }]);
    });
  };

  return (
    <div className="flex flex-col h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      <Header
        onOpenAuth={handleOpenAuth}
        user={user}
        onLogout={signOut}
        onOpenAdmin={() => setActiveView('admin')}
        onOpenChat={() => setActiveView('chat')}
        isAdminView={activeView === 'admin'}
        isAdminAuthenticated={isAdminAuthenticated}
      />
      {activeView === 'admin' ? (
        <AdminDashboard
          isAdminAuthenticated={isAdminAuthenticated}
          onAdminAuth={handleAdminAuth}
          onAdminLogout={handleAdminLogout}
        />
      ) : (
        <>
          <ChatArea messages={messages} />
          <MessageInput onSendMessage={handleSendMessage} />
        </>
      )}
      <AuthModal 
        isOpen={showAuthModal} 
        onClose={handleCloseAuth}
        onSuccess={handleAuthSuccess}
        initialMode={authMode}
        signIn={signIn}
        sendOTP={sendOTP}
        verifyOTP={verifyOTP}
        error={error}
      />
    </div>
  );
}

export default App;
