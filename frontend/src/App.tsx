import React, { useEffect, useRef, useState } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ChatMessage } from './components/ChatMessage';
import { ChatInput } from './components/ChatInput';
import { CaseSidebar } from './components/CaseSidebar';
import { TypingIndicator } from './components/TypingIndicator';
import { useTaxConsultant } from './hooks/useTaxConsultant';
import './styles/index.css';

const queryClient = new QueryClient();

const AppContent: React.FC = () => {
  const {
    caseFile,
    isLoading,
    isStreaming,
    error,
    currentStreamingMessage,
    quickReplyOptions,
    sendMessage,
    editMessage,
    forceFinalSuggestions,
    canForceFinal,
    startNewSession,
  } = useTaxConsultant();

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [caseFile?.messages, currentStreamingMessage]);

  const handleSendMessage = (message: string) => {
    sendMessage(message);
  };

  const handleForceFinal = () => {
    forceFinalSuggestions();
  };

  if (isLoading && !caseFile) {
    return (
      <div className="app">
        <div className="chat-container">
          <div className="chat-header">
            <h1>Cross-Border Tax Consultant</h1>
          </div>
          <div className="messages-container">
            <div className="message system">
              <div className="message-avatar">ℹ️</div>
              <div className="message-content">
                <div className="markdown">
                  <p>Initializing your tax consultation session...</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error && !caseFile) {
    return (
      <div className="app">
        <div className="chat-container">
          <div className="chat-header">
            <h1>Cross-Border Tax Consultant</h1>
          </div>
          <div className="messages-container">
            <div className="message system">
              <div className="message-avatar">⚠️</div>
              <div className="message-content">
                <div className="markdown">
                  <p>Error: {error}</p>
                  <p>Please refresh the page to try again.</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="app">
      <div className="chat-container">
        <div className="chat-header">
          <h1>Cross-Border Tax Consultant</h1>
          <button
            className="new-session-button"
            onClick={startNewSession}
            disabled={isStreaming}
            title="Start a new consultation session"
          >
            New Session
          </button>
        </div>

        <div className="disclaimer">
          <strong>Disclaimer:</strong> This is general information, not legal or tax advice.
          Consult a qualified professional for specific guidance on your tax situation.
        </div>

        <div className="messages-container">
          {caseFile?.messages.map((message, index) => {
            // Add ID if missing (for backward compatibility)
            if (!message.id) {
              message.id = crypto.randomUUID();
            }
            return (
              <ChatMessage
                key={message.id || index}
                message={message}
                onEdit={message.role === 'user' ? editMessage : undefined}
                canEdit={!isStreaming}
              />
            );
          })}

          {isStreaming && (
            <>
              {currentStreamingMessage ? (
                <div className="message assistant">
                  <div className="message-avatar">AI</div>
                  <div className="message-content">
                    <div className="markdown">
                      {currentStreamingMessage}
                    </div>
                  </div>
                </div>
              ) : (
                <TypingIndicator />
              )}
            </>
          )}

          {error && (
            <div className="message system">
              <div className="message-avatar">⚠️</div>
              <div className="message-content">
                <div className="markdown">
                  <p>Error: {error}</p>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        <ChatInput
          onSendMessage={handleSendMessage}
          disabled={isStreaming}
          quickReplyOptions={quickReplyOptions}
        />
      </div>

      <CaseSidebar
        caseFile={caseFile}
        onForceFinal={handleForceFinal}
        canForceFinal={canForceFinal}
        isLoading={isStreaming}
      />
    </div>
  );
};

const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <AppContent />
    </QueryClientProvider>
  );
};

export default App;