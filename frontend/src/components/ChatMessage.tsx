import React, { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { ChatMessage as ChatMessageType } from '../types';

interface ChatMessageProps {
  message: ChatMessageType;
  onEdit?: (messageId: string, newContent: string) => void;
  canEdit?: boolean;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({ message, onEdit, canEdit = true }) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editContent, setEditContent] = useState(message.content);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const getAvatar = (role: string) => {
    switch (role) {
      case 'user':
        return 'You';
      case 'assistant':
        return 'AI';
      case 'system':
        return 'ℹ️';
      default:
        return '?';
    }
  };

  const handleEditStart = () => {
    setIsEditing(true);
    setEditContent(message.content);
  };

  const handleEditCancel = () => {
    setIsEditing(false);
    setEditContent(message.content);
  };

  const handleEditSave = () => {
    if (onEdit && editContent.trim() !== message.content) {
      // Generate ID if missing (for backward compatibility)
      const messageId = message.id || crypto.randomUUID();
      onEdit(messageId, editContent.trim());
    }
    setIsEditing(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      handleEditSave();
    } else if (e.key === 'Escape') {
      e.preventDefault();
      handleEditCancel();
    }
  };

  const adjustTextareaHeight = () => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = `${textarea.scrollHeight}px`;
    }
  };

  useEffect(() => {
    if (isEditing) {
      adjustTextareaHeight();
      textareaRef.current?.focus();
    }
  }, [isEditing, editContent]);

  return (
    <div className={`message ${message.role}`}>
      <div className="message-avatar">
        {getAvatar(message.role)}
      </div>
      <div className="message-content">
        {isEditing ? (
          <div className="message-edit">
            <textarea
              ref={textareaRef}
              className="message-edit-textarea"
              value={editContent}
              onChange={(e) => {
                setEditContent(e.target.value);
                adjustTextareaHeight();
              }}
              onKeyDown={handleKeyDown}
              placeholder="Edit your message..."
              rows={1}
              style={{
                resize: 'none',
                overflow: 'hidden',
                minHeight: '44px',
              }}
            />
            <div className="message-edit-actions">
              <button
                className="message-edit-button save"
                onClick={handleEditSave}
                disabled={!editContent.trim()}
                title="Save (Ctrl+Enter)"
              >
                ✓
              </button>
              <button
                className="message-edit-button cancel"
                onClick={handleEditCancel}
                title="Cancel (Esc)"
              >
                ✕
              </button>
            </div>
          </div>
        ) : (
          <>
            <div className="markdown">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  a: ({ href, children, ...props }) => (
                    <a href={href} target="_blank" rel="noopener noreferrer" {...props}>
                      {children}
                    </a>
                  ),
                }}
              >
                {message.content}
              </ReactMarkdown>
            </div>
            {onEdit && canEdit && (
              <button
                className="message-edit-trigger"
                onClick={handleEditStart}
                title="Edit message"
              >
                ✏️
              </button>
            )}
          </>
        )}
      </div>
    </div>
  );
};