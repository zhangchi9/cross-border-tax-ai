import React from 'react';

interface QuickReplyProps {
  options: string[];
  onOptionClick: (option: string) => void;
  disabled?: boolean;
}

export const QuickReply: React.FC<QuickReplyProps> = ({ options, onOptionClick, disabled = false }) => {
  if (options.length === 0) {
    return null;
  }

  return (
    <div className="quick-reply-container">
      <div className="quick-reply-title">Quick replies:</div>
      <div className="quick-reply-buttons">
        {options.map((option, index) => (
          <button
            key={index}
            className="quick-reply-button"
            onClick={() => onOptionClick(option)}
            disabled={disabled}
          >
            {option}
          </button>
        ))}
      </div>
    </div>
  );
};