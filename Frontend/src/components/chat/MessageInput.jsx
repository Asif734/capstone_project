import React, { useState } from 'react';
import { Send } from 'lucide-react';

const MessageInput = ({ onSendMessage }) => {
  const [message, setMessage] = useState('');

  const handleSend = () => {
    if (message.trim()) {
      onSendMessage(message);
      setMessage('');
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="border-t border-purple-500/20 bg-slate-800/30 backdrop-blur-lg">
      <div className="max-w-3xl mx-auto px-4 py-4">
        <div className="flex items-end space-x-2">
          <div className="flex-1 bg-slate-700/50 rounded-2xl border border-purple-500/30 focus-within:border-purple-500 transition-colors">
            <textarea
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Type your message here..."
              rows="1"
              className="w-full bg-transparent text-white placeholder-purple-300/50 px-4 py-3 rounded-2xl resize-none focus:outline-none"
            />
          </div>
          <button
            onClick={handleSend}
            disabled={!message.trim()}
            className="bg-gradient-to-r from-purple-500 to-pink-500 text-white p-3 rounded-xl hover:from-purple-600 hover:to-pink-600 transition-all shadow-lg hover:shadow-purple-500/50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
        <p className="text-purple-300/50 text-xs text-center mt-2">
          Press Enter to send, Shift + Enter for new line
        </p>
      </div>
    </div>
  );
};

export default MessageInput;