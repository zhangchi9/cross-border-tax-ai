import axios from 'axios';
import { SessionResponse, CaseFile } from '../types';

const API_BASE_URL = '/api';

export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
});

export class TaxConsultantAPI {
  static async createSession(): Promise<SessionResponse> {
    const response = await api.post<SessionResponse>('/session/create');
    return response.data;
  }

  static async getSession(sessionId: string): Promise<{ case_file: CaseFile }> {
    const response = await api.get(`/session/${sessionId}`);
    return response.data;
  }

  static async *streamChat(sessionId: string, message: string): AsyncGenerator<any, void, unknown> {
    const response = await fetch(`${API_BASE_URL}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        session_id: sessionId,
        message: message,
      }),
    });

    if (!response.ok) {
      throw new Error('Failed to send message');
    }

    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error('No response body');
    }

    const decoder = new TextDecoder();

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            if (data.trim()) {
              try {
                const parsed = JSON.parse(data);
                yield parsed;
              } catch (e) {
                console.error('Failed to parse SSE data:', e);
              }
            }
          }
        }
      }
    } finally {
      reader.releaseLock();
    }
  }

  static async *forceFinalSuggestions(sessionId: string): AsyncGenerator<any, void, unknown> {
    const response = await fetch(`${API_BASE_URL}/session/${sessionId}/force_final`, {
      method: 'POST',
    });

    if (!response.ok) {
      throw new Error('Failed to get final suggestions');
    }

    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error('No response body');
    }

    const decoder = new TextDecoder();

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            if (data.trim()) {
              try {
                const parsed = JSON.parse(data);
                yield parsed;
              } catch (e) {
                console.error('Failed to parse SSE data:', e);
              }
            }
          }
        }
      }
    } finally {
      reader.releaseLock();
    }
  }

  static async *editMessage(sessionId: string, messageId: string, newContent: string): AsyncGenerator<any, void, unknown> {
    const response = await fetch(`${API_BASE_URL}/message/edit`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        session_id: sessionId,
        message_id: messageId,
        new_content: newContent,
      }),
    });

    if (!response.ok) {
      throw new Error('Failed to edit message');
    }

    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error('No response body');
    }

    const decoder = new TextDecoder();

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            if (data.trim()) {
              try {
                const parsed = JSON.parse(data);
                yield parsed;
              } catch (e) {
                console.error('Failed to parse SSE data:', e);
              }
            }
          }
        }
      }
    } finally {
      reader.releaseLock();
    }
  }
}