import { kea } from 'kea';
import { initializeSocket, reconnectSocket, getConnectionStatus } from '../lib/socketService';
import type { Socket } from 'socket.io-client';
import { v4 as uuidv4 } from 'uuid';

export type ConnectionStatus = 'connected' | 'disconnected' | 'connecting';
export type MessageStatus = 'sending' | 'sent' | 'error';
export type MessageRole = 'student' | 'tutor' | 'system';

export interface Message {
  id: string;
  conversation_id: string;
  role: MessageRole;
  content: string;
  created_at: string;
  status?: MessageStatus;
  metadata?: Record<string, unknown>;
}

export interface ValidationResult {
  correct: boolean;
  student_answer: string;
  expected_answer: string;
  explanation: string;
  is_approximate: boolean;
}

export interface AnswerValidationResponse {
  conversation_id: string;
  is_correct: boolean;
  new_streak: number;
  celebration_triggered: boolean;
  validation?: ValidationResult;
}

export const conversationLogic = kea({
  path: ['conversation'],
  actions: {
    initializeConnection: true,
    // @ts-expect-error - Kea action typing requires kea-typegen
    setConnectionStatus: (status: ConnectionStatus) => ({ status }),
    // @ts-expect-error - Kea action typing requires kea-typegen
    setConnectionError: (error: string | null) => ({ error }),
    reconnect: true,
    // @ts-expect-error - Kea action typing requires kea-typegen
    setCurrentConversation: (conversationId: string) => ({ conversationId }),
    // @ts-expect-error - Kea action typing requires kea-typegen
    sendMessage: (content: string) => ({ content }),
    // @ts-expect-error - Kea action typing requires kea-typegen
    receiveMessage: (message: Message) => ({ message }),
    // @ts-expect-error - Kea action typing requires kea-typegen
    updateMessageStatus: (messageId: string, status: MessageStatus) => ({ messageId, status }),
    // @ts-expect-error - Kea action typing requires kea-typegen
    setTyping: (isTyping: boolean) => ({ isTyping }),
    // @ts-expect-error - Kea action typing requires kea-typegen
    loadThread: (threadId: string) => ({ threadId }),
    // @ts-expect-error - Kea action typing requires kea-typegen
    setMessages: (messages: Message[]) => ({ messages }),
    // Answer validation actions
    // @ts-expect-error - Kea action typing requires kea-typegen
    validateAnswer: (studentAnswer: string, expectedAnswer?: string, context?: string) => ({
      studentAnswer,
      expectedAnswer,
      context
    }),
    // @ts-expect-error - Kea action typing requires kea-typegen
    receiveValidationResult: (result: AnswerValidationResponse) => ({ result }),
    // @ts-expect-error - Kea action typing requires kea-typegen
    setValidationError: (error: string) => ({ error }),
    clearValidationResult: () => ({}),
  },

  reducers: {
    connectionStatus: [
      'disconnected' as ConnectionStatus,
      {
        setConnectionStatus: (_, { status }) => status,
      },
    ],
    connectionError: [
      null as string | null,
      {
        setConnectionError: (_, { error }) => error,
      },
    ],
    socket: [
      null as Socket | null,
      {
        initializeConnection: () => {
          const socket = initializeSocket();
          return socket;
        },
      },
    ],
    currentConversationId: [
      null as string | null,
      {
        setCurrentConversation: (_, { conversationId }) => conversationId,
      },
    ],
    messages: [
      [] as Message[],
      {
        receiveMessage: (state, { message }) => {
          // Check for duplicate message IDs to prevent duplication
          const messageExists = state.some((msg: Message) => msg.id === message.id);
          if (messageExists) {
            // Message already exists, don't add duplicate
            return state;
          }

          // Insert message in chronological order
          const newMessages = [...state, message];
          return newMessages.sort((a, b) =>
            new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
          );
        },
        updateMessageStatus: (state, { messageId, status }) => {
          return state.map((msg: Message) =>
            msg.id === messageId ? { ...msg, status } : msg
          );
        },
        setMessages: (_, { messages }) => {
          // Sort messages chronologically to ensure consistent ordering
          return messages.sort((a: Message, b: Message) =>
            new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
          );
        },
      },
    ],
    isTyping: [
      false as boolean,
      {
        setTyping: (_, { isTyping }) => isTyping,
      },
    ],
    validationResult: [
      null as AnswerValidationResponse | null,
      {
        receiveValidationResult: (_, { result }) => result,
        clearValidationResult: () => null,
      },
    ],
    validationError: [
      null as string | null,
      {
        setValidationError: (_, { error }) => error,
        clearValidationResult: () => null,
      },
    ],
    isValidating: [
      false as boolean,
      {
        validateAnswer: () => true,
        receiveValidationResult: () => false,
        setValidationError: () => false,
      },
    ],
  },

  listeners: ({ actions, values }) => ({
    initializeConnection: () => {
      const socket = initializeSocket();

      // Guard: Remove existing listeners before attaching to prevent duplication
      socket.off('connect');
      socket.off('disconnect');
      socket.off('connect_error');
      socket.off('message:receive');
      socket.off('message:ack');
      socket.off('message:error');
      socket.off('answer:validated');
      socket.off('answer:validation_error');

      // Update connection status based on socket events
      socket.on('connect', () => {
        actions.setConnectionStatus('connected');
        actions.setConnectionError(null);
      });

      socket.on('disconnect', () => {
        actions.setConnectionStatus('disconnected');
      });

      socket.on('connect_error', (error: Error) => {
        actions.setConnectionStatus('disconnected');
        actions.setConnectionError(error.message || 'Connection error');
      });

      // Message event listeners
      socket.on('message:receive', (message: Message) => {
        actions.receiveMessage(message);
      });

      socket.on('message:ack', ({ message_id }: { message_id: string }) => {
        actions.updateMessageStatus(message_id, 'sent');
      });

      socket.on('message:error', ({ message_id, error }: { message_id: string; error: string }) => {
        console.error('Message error:', error);
        actions.updateMessageStatus(message_id, 'error');
      });

      // Answer validation listeners
      socket.on('answer:validated', (response: AnswerValidationResponse) => {
        console.log('Answer validation received:', response);
        actions.receiveValidationResult(response);
      });

      socket.on('answer:validation_error', ({ error }: { error: string }) => {
        console.error('Answer validation error:', error);
        actions.setValidationError(error);
      });

      // Set initial status
      const initialStatus = getConnectionStatus();
      actions.setConnectionStatus(initialStatus);
    },

    reconnect: () => {
      actions.setConnectionStatus('connecting');
      reconnectSocket();
    },

    sendMessage: ({ content }) => {
      const socket = values.socket;
      if (!socket) {
        console.error('Socket not initialized');
        return;
      }

      if (!values.currentConversationId) {
        // Create new conversation ID
        const newConversationId = uuidv4();
        actions.setCurrentConversation(newConversationId);
      }

      const messageId = uuidv4();
      const conversationId = values.currentConversationId || uuidv4();

      // Add message to local state with "sending" status
      const message: Message = {
        id: messageId,
        conversation_id: conversationId,
        role: 'student',
        content,
        created_at: new Date().toISOString(),
        status: 'sending',
      };
      actions.receiveMessage(message);

      // Emit message to server
      socket.emit('message:send', {
        message_id: messageId,
        conversation_id: conversationId,
        content,
      });
    },

    setTyping: ({ isTyping }) => {
      const socket = values.socket;
      if (!socket || !values.currentConversationId) {
        return;
      }

      if (isTyping) {
        socket.emit('typing:start', {
          conversation_id: values.currentConversationId,
        });
      } else {
        socket.emit('typing:stop', {
          conversation_id: values.currentConversationId,
        });
      }
    },

    validateAnswer: ({ studentAnswer, expectedAnswer, context }) => {
      const socket = values.socket;
      if (!socket) {
        console.error('Socket not initialized');
        actions.setValidationError('Not connected to server');
        return;
      }

      if (!values.currentConversationId) {
        console.error('No active conversation');
        actions.setValidationError('No active conversation');
        return;
      }

      console.log('Validating answer:', { studentAnswer, expectedAnswer, context });

      // Emit validation request to server
      socket.emit('answer:validate', {
        conversation_id: values.currentConversationId,
        student_answer: studentAnswer,
        expected_answer: expectedAnswer,
        context: context,
        current_streak: 0, // Will be updated by server
      });
    },

    loadThread: async ({ threadId }) => {
      try {
        const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:5001';
        const response = await fetch(`${apiUrl}/api/threads/${threadId}`);
        if (!response.ok) {
          throw new Error('Failed to load thread');
        }

        const data = await response.json();
        actions.setCurrentConversation(data.id);
        actions.setMessages(data.messages);
      } catch (error) {
        console.error('Error loading thread:', error);
        actions.setConnectionError('Failed to load conversation');
      }
    },

    setCurrentConversation: ({ conversationId }) => {
      const socket = values.socket;
      if (socket && conversationId) {
        // Join the conversation room for real-time updates
        socket.emit('conversation:join', { conversation_id: conversationId });
      }
    },
  }),
});
