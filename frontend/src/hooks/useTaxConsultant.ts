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

  const initializeSession = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      const response = await TaxConsultantAPI.createSession();
      setSessionId(response.session_id);
      setCaseFile(response.case_file);
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

  return {
    sessionId,
    caseFile,
    isLoading,
    isStreaming,
    error,
    currentStreamingMessage,
    quickReplyOptions,
    sendMessage,
    forceFinalSuggestions,
    canForceFinal: canForceFinal(),
    initializeSession,
  };
};