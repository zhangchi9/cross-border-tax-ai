import React from 'react';
import { CaseFile } from '../types';

interface CaseSidebarProps {
  caseFile: CaseFile | null;
  onForceFinal: () => void;
  canForceFinal: boolean;
  isLoading: boolean;
}

export const CaseSidebar: React.FC<CaseSidebarProps> = ({
  caseFile,
  onForceFinal,
  canForceFinal,
  isLoading
}) => {
  if (!caseFile) {
    return (
      <div className="sidebar">
        <div className="case-summary">
          <h3>Identified Tags</h3>
          <p>Start a conversation to see identified tax tags here.</p>
        </div>
      </div>
    );
  }

  const { assigned_tags, conversation_phase } = caseFile;

  return (
    <div className="sidebar">
      <div className="phase-indicator">
        <div className={`phase-badge ${conversation_phase}`}>
          {conversation_phase.replace('_', ' ')}
        </div>
        {canForceFinal && conversation_phase !== 'final_suggestions' && (
          <button
            className="final-button"
            onClick={onForceFinal}
            disabled={isLoading}
          >
            {isLoading ? 'Loading...' : 'Get Final Suggestions'}
          </button>
        )}
      </div>

      <div className="case-summary">
        <h3>Identified Tags</h3>

        {assigned_tags.length > 0 ? (
          <div className="summary-section">
            <div className="tags-container">
              {assigned_tags.map((tag, index) => (
                <div key={index} className="tag-item">
                  <span className="tag-badge">
                    {tag}
                  </span>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="summary-section">
            <p className="no-tags-message">
              Answer questions to identify relevant tax tags for your situation.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};