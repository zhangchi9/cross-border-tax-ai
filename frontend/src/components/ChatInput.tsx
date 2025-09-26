import React, { useState, KeyboardEvent, useRef, useEffect } from 'react';
import { QuickReply } from './QuickReply';

interface ChatInputProps {
  onSendMessage: (message: string) => void;
  disabled: boolean;
  quickReplyOptions?: string[];
}

export const ChatInput: React.FC<ChatInputProps> = ({ onSendMessage, disabled, quickReplyOptions = [] }) => {
  const [message, setMessage] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const adjustTextareaHeight = () => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      const newHeight = Math.min(textarea.scrollHeight, 200);
      textarea.style.height = `${newHeight}px`;
      textarea.style.maxHeight = '200px';
      textarea.style.minHeight = 'auto';
    }
  };

  useEffect(() => {
    adjustTextareaHeight();
  }, [message]);

  useEffect(() => {
    // Initial adjustment on mount
    adjustTextareaHeight();
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim() && !disabled) {
      onSendMessage(message.trim());
      setMessage('');
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleQuickReply = (option: string) => {
    if (!disabled) {
      onSendMessage(option);
      setMessage('');
    }
  };

  return (
    <div className="input-container">
      {quickReplyOptions.length > 0 && (
        <QuickReply
          options={quickReplyOptions}
          onOptionClick={handleQuickReply}
          disabled={disabled}
        />
      )}
      <form onSubmit={handleSubmit} className="input-form">
        <div className="input-wrapper">
          <textarea
            ref={textareaRef}
            className="message-input"
            placeholder="Type your tax question here..."
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onInput={adjustTextareaHeight}
            onKeyDown={handleKeyDown}
            disabled={disabled}
            rows={1}
            style={{
              resize: 'none',
              overflow: 'hidden',
              minHeight: '44px',
              maxHeight: '200px',
              height: 'auto'
            }}
          />
        </div>
        <button
          type="submit"
          className="send-button"
          disabled={!message.trim() || disabled}
        >
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M22 2L11 13M22 2L15 22L11 13M22 2L2 9L11 13" />
          </svg>
        </button>
      </form>
    </div>
  );
};