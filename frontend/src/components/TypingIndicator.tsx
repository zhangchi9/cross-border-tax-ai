import React from 'react';

export const TypingIndicator: React.FC = () => {
  return (
    <div className="message assistant">
      <div className="message-avatar">AI</div>
      <div className="message-content">
        <div className="typing-indicator">
          <div className="typing-dot"></div>
          <div className="typing-dot"></div>
          <div className="typing-dot"></div>
        </div>
      </div>
    </div>
  );
};