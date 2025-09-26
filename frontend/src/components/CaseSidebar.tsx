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
          <h3>Case Summary</h3>
          <p>Start a conversation to see your case information here.</p>
        </div>
      </div>
    );
  }

  const { user_profile, conversation_phase, potential_issues } = caseFile;

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
        <h3>Case Summary</h3>

        {user_profile.countries_involved.length > 0 && (
          <div className="summary-section">
            <h4>Countries</h4>
            <ul className="summary-list">
              {user_profile.countries_involved.map((country, index) => (
                <li key={index}>{country}</li>
              ))}
            </ul>
          </div>
        )}

        {user_profile.tax_year && (
          <div className="summary-section">
            <h4>Tax Year</h4>
            <ul className="summary-list">
              <li>{user_profile.tax_year}</li>
            </ul>
          </div>
        )}

        {user_profile.sources_of_income.length > 0 && (
          <div className="summary-section">
            <h4>Income Sources</h4>
            <ul className="summary-list">
              {user_profile.sources_of_income.map((source, index) => (
                <li key={index}>{source}</li>
              ))}
            </ul>
          </div>
        )}

        {user_profile.foreign_assets.length > 0 && (
          <div className="summary-section">
            <h4>Foreign Assets</h4>
            <ul className="summary-list">
              {user_profile.foreign_assets.map((asset, index) => (
                <li key={index}>{asset}</li>
              ))}
            </ul>
          </div>
        )}

        {user_profile.tax_residency_status && (
          <div className="summary-section">
            <h4>Tax Residency</h4>
            <ul className="summary-list">
              <li>{user_profile.tax_residency_status}</li>
            </ul>
          </div>
        )}

        {user_profile.filing_status && (
          <div className="summary-section">
            <h4>Filing Status</h4>
            <ul className="summary-list">
              <li>{user_profile.filing_status}</li>
            </ul>
          </div>
        )}

        {potential_issues.length > 0 && (
          <div className="summary-section">
            <h4>Potential Issues</h4>
            <ul className="summary-list">
              {potential_issues.map((issue, index) => (
                <li key={index}>{issue}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
};