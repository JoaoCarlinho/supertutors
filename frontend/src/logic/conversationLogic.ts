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
        setMessages: (_, { messages }) => messages,
      },
    ],
    isTyping: [
      false as boolean,
      {
        setTyping: (_, { isTyping }) => isTyping,
      },
    ],
  },

  listeners: ({ actions, values }) => ({
    initializeConnection: () => {
      const socket = initializeSocket();

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
