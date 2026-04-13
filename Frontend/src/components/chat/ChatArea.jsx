import React from 'react';
import { Bot } from 'lucide-react';

const ChatArea = ({ messages = [] }) => {
  // Simple markdown renderer for common formatting
  const renderMarkdown = (text) => {
    if (!text) return '';
    
    // Split by lines to preserve line breaks
    const lines = text.split('\n');
    const elements = [];
    
    lines.forEach((line, idx) => {
      const trimmed = line.trim();
      
      // Headers (###)
      if (trimmed.startsWith('###')) {
        const title = trimmed.replace(/^#+\s*/, '');
        elements.push(
          <h3 key={idx} className="text-lg font-bold text-purple-300 mt-3 mb-2">
            {title}
          </h3>
        );
      }
      // Bullet points
      else if (trimmed.startsWith('*')) {
        const content = trimmed.replace(/^\*\s*/, '');
        elements.push(
          <div key={idx} className="ml-4 mb-1 flex items-start">
            <span className="text-pink-400 mr-2">•</span>
            <span className="text-white">{content}</span>
          </div>
        );
      }
      // Bold text inline
      else if (trimmed.length > 0) {
        const formatted = trimmed.split(/\*\*(.*?)\*\*/g).map((part, i) => 
          i % 2 === 1 ? <span key={i} className="font-bold text-purple-300">{part}</span> : part
        );
        elements.push(
          <p key={idx} className="mb-2 text-white leading-relaxed">
            {formatted}
          </p>
        );
      } else {
        elements.push(<div key={idx} className="mb-1"></div>);
      }
    });
    
    return elements;
  };

  return (
    <div className="flex-1 overflow-y-auto px-4 py-8">
      <div className="max-w-3xl mx-auto">
        {messages.length === 0 ? (
          // Welcome Message
          <div className="flex justify-center mb-8">
            <div className="bg-gradient-to-br from-purple-500/20 to-pink-500/20 backdrop-blur-sm border border-purple-500/30 rounded-2xl p-8 text-center max-w-2xl">
              <div className="bg-gradient-to-br from-purple-500 to-pink-500 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                <Bot className="w-8 h-8 text-white" />
              </div>
              <h2 className="text-2xl font-bold text-white mb-2">Welcome to SmartBot</h2>
              <p className="text-purple-200">Your intelligent assistant is ready to help. Start a conversation below!</p>
            </div>
          </div>
        ) : (
          // Messages will be displayed here
          <div className="space-y-4">
            {messages.map((msg, idx) => (
              <div key={idx} className={`flex ${msg.isUser ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-2xl px-4 py-3 rounded-2xl ${
                  msg.isUser 
                    ? 'bg-gradient-to-r from-purple-500 to-pink-500 text-white' 
                    : 'bg-slate-700 text-white'
                }`}>
                  {msg.isUser ? msg.text : renderMarkdown(msg.text)}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default ChatArea;