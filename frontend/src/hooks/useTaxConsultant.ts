import { useState, useEffect, useCallback, useRef } from 'react';
import { TaxConsultantAPI } from '../api/client';
import { CaseFile, ChatMessage } from '../types';

export const useTaxConsultant = () => {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [caseFile, setCaseFile] = useState<CaseFile | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentStreamingMessage, setCurrentStreamingMessage] = useState('');
  const [quickReplyOptions, setQuickReplyOptions] = useState<string[]>([]);

  const abortControllerRef = useRef<AbortController | null>(null);

  const initializeSession = useCallback(async (forceNew = false) => {
    try {
      setIsLoading(true);
      setError(null);

      // Check for existing session if not forcing new
      if (!forceNew) {
        const existingSessionId = localStorage.getItem('tax_consultant_session_id');
        if (existingSessionId) {
          try {
            // Try to retrieve existing session
            const response = await TaxConsultantAPI.getSession(existingSessionId);
            setSessionId(existingSessionId);
            setCaseFile(response.case_file);
            setIsLoading(false);
            return;
          } catch (err) {
            // If session doesn't exist or is invalid, create a new one
            localStorage.removeItem('tax_consultant_session_id');
          }
        }
      } else {
        // Clear existing session when forcing new
        localStorage.removeItem('tax_consultant_session_id');
      }

      // Create new session
      const response = await TaxConsultantAPI.createSession();
      setSessionId(response.session_id);
      setCaseFile(response.case_file);

      // Store session ID in localStorage
      localStorage.setItem('tax_consultant_session_id', response.session_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to initialize session');
    } finally {
      setIsLoading(false);
    }
  }, []);

  const sendMessage = useCallback(async (message: string) => {
    if (!sessionId || isStreaming) return;

    try {
      setIsStreaming(true);
      setCurrentStreamingMessage('');
      setQuickReplyOptions([]);
      setError(null);

      // Add user message optimistically
      const userMessage: ChatMessage = {
        id: crypto.randomUUID(),
        role: 'user',
        content: message,
        timestamp: new Date().toISOString(),
      };

      if (caseFile) {
        const updatedCaseFile = {
          ...caseFile,
          messages: [...caseFile.messages, userMessage],
        };
        setCaseFile(updatedCaseFile);
      }

      // Start streaming response
      let fullResponse = '';
      const stream = TaxConsultantAPI.streamChat(sessionId, message);

      for await (const chunk of stream) {
        if (chunk.content) {
          fullResponse += chunk.content;
          setCurrentStreamingMessage(fullResponse);
        }

        if (chunk.is_final) {
          // Handle quick_replies if present
          if (chunk.quick_replies) {
            setQuickReplyOptions(chunk.quick_replies);
          }

          // Add assistant message to case file
          const assistantMessage: ChatMessage = {
            id: crypto.randomUUID(),
            role: 'assistant',
            content: fullResponse,
            timestamp: new Date().toISOString(),
          };

          if (chunk.case_file) {
            setCaseFile(chunk.case_file);
          } else if (caseFile) {
            const finalCaseFile = {
              ...caseFile,
              messages: [...caseFile.messages, userMessage, assistantMessage],
            };
            setCaseFile(finalCaseFile);
          }

          setCurrentStreamingMessage('');
          break;
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to send message');
      setCurrentStreamingMessage('');
    } finally {
      setIsStreaming(false);
    }
  }, [sessionId, caseFile, isStreaming]);

  const forceFinalSuggestions = useCallback(async () => {
    if (!sessionId || isStreaming) return;

    try {
      setIsStreaming(true);
      setCurrentStreamingMessage('');
      setError(null);

      let fullResponse = '';
      const stream = TaxConsultantAPI.forceFinalSuggestions(sessionId);

      for await (const chunk of stream) {
        if (chunk.content) {
          fullResponse += chunk.content;
          setCurrentStreamingMessage(fullResponse);
        }

        if (chunk.is_final) {
          const assistantMessage: ChatMessage = {
            id: crypto.randomUUID(),
            role: 'assistant',
            content: fullResponse,
            timestamp: new Date().toISOString(),
          };

          if (chunk.case_file) {
            setCaseFile(chunk.case_file);
          } else if (caseFile) {
            const finalCaseFile = {
              ...caseFile,
              messages: [...caseFile.messages, assistantMessage],
            };
            setCaseFile(finalCaseFile);
          }

          setCurrentStreamingMessage('');
          break;
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to get final suggestions');
      setCurrentStreamingMessage('');
    } finally {
      setIsStreaming(false);
    }
  }, [sessionId, caseFile, isStreaming]);

  const canForceFinal = useCallback(() => {
    if (!caseFile) return false;

    const { user_profile, conversation_phase } = caseFile;

    // Must have basic info
    const hasCountries = user_profile.countries_involved.length >= 2;
    const hasIncome = user_profile.sources_of_income.length > 0;
    const hasTaxYear = user_profile.tax_year !== undefined;

    // Must have asked questions
    const assistantQuestions = caseFile.messages.filter(
      msg => msg.role === 'assistant' && msg.content.includes('?')
    ).length;

    const hasBasicInfo = hasCountries && hasIncome && hasTaxYear;
    const hasQuestions = assistantQuestions >= 1;

    return hasBasicInfo && hasQuestions && conversation_phase !== 'final_suggestions';
  }, [caseFile]);

  // Initialize session on mount
  useEffect(() => {
    initializeSession();
  }, [initializeSession]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  const editMessage = useCallback(async (messageId: string, newContent: string) => {
    if (!sessionId || isStreaming) return;

    try {
      setIsStreaming(true);
      setCurrentStreamingMessage('');
      setQuickReplyOptions([]);
      setError(null);

      // Start streaming response
      let fullResponse = '';
      const stream = TaxConsultantAPI.editMessage(sessionId, messageId, newContent);

      for await (const chunk of stream) {
        if (chunk.content) {
          fullResponse += chunk.content;
          setCurrentStreamingMessage(fullResponse);
        }

        if (chunk.is_final) {
          // Handle quick_replies if present
          if (chunk.quick_replies) {
            setQuickReplyOptions(chunk.quick_replies);
          }

          // Update the case file with the edited conversation
          if (chunk.case_file) {
            setCaseFile(chunk.case_file);
          }

          setCurrentStreamingMessage('');
          break;
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to edit message');
      setCurrentStreamingMessage('');
    } finally {
      setIsStreaming(false);
    }
  }, [sessionId, isStreaming]);

  const startNewSession = useCallback(() => {
    // Clear state
    setSessionId(null);
    setCaseFile(null);
    setCurrentStreamingMessage('');
    setQuickReplyOptions([]);
    setError(null);

    // Initialize new session
    initializeSession(true);
  }, [initializeSession]);

  return {
    sessionId,
    caseFile,
    isLoading,
    isStreaming,
    error,
    currentStreamingMessage,
    quickReplyOptions,
    sendMessage,
    editMessage,
    forceFinalSuggestions,
    canForceFinal: canForceFinal(),
    initializeSession,
    startNewSession,
  };
};