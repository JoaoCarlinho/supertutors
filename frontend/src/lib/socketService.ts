import { io, Socket } from 'socket.io-client';

/**
 * Socket Service for WebSocket communication
 *
 * Manages connection to Flask-SocketIO backend with:
 * - Automatic reconnection with exponential backoff
 * - Heartbeat/ping mechanism
 * - Connection state management
 * - Error handling
 */

const SOCKET_URL = import.meta.env.VITE_SOCKET_URL || 'http://localhost:5001';

// Reconnection configuration: 1s, 2s, 4s, 8s, max 30s
const RECONNECTION_DELAYS = [1000, 2000, 4000, 8000, 30000];

let socket: Socket | null = null;
let heartbeatInterval: ReturnType<typeof setInterval> | null = null;
let lastPongTime: number = Date.now();

/**
 * Initialize socket connection
 */
export function initializeSocket(): Socket {
  if (socket) {
    return socket;
  }

  socket = io(SOCKET_URL, {
    reconnection: true,
    reconnectionAttempts: Infinity,
    reconnectionDelay: RECONNECTION_DELAYS[0],
    reconnectionDelayMax: RECONNECTION_DELAYS[4],
    timeout: 20000,
    autoConnect: true,
  });

  // Connection event handlers
  socket.on('connect', handleConnect);
  socket.on('disconnect', handleDisconnect);
  socket.on('connect_error', handleConnectionError);
  socket.on('pong', handlePong);

  // Start heartbeat
  startHeartbeat();

  return socket;
}

/**
 * Get existing socket instance
 */
export function getSocket(): Socket | null {
  return socket;
}

/**
 * Manual reconnect
 */
export function reconnectSocket(): void {
  if (socket) {
    socket.connect();
  } else {
    initializeSocket();
  }
}

/**
 * Disconnect socket
 */
export function disconnectSocket(): void {
  if (socket) {
    stopHeartbeat();
    socket.disconnect();
  }
}

/**
 * Connection event handlers
 */
function handleConnect(): void {
  console.log('[Socket] Connected to server', {
    id: socket?.id,
    url: SOCKET_URL,
    timestamp: new Date().toISOString(),
  });
  lastPongTime = Date.now();
}

function handleDisconnect(reason: string): void {
  console.log('[Socket] Disconnected from server', {
    reason,
    timestamp: new Date().toISOString(),
  });
}

function handleConnectionError(error: Error): void {
  console.error('[Socket] Connection error', {
    error: error.message,
    timestamp: new Date().toISOString(),
  });
}

function handlePong(): void {
  lastPongTime = Date.now();
  console.log('[Socket] Pong received');
}

/**
 * Heartbeat mechanism
 * Sends ping every 25 seconds, checks for pong within 35 seconds
 */
function startHeartbeat(): void {
  stopHeartbeat();

  heartbeatInterval = setInterval(() => {
    if (!socket || !socket.connected) {
      return;
    }

    // Check if last pong was received within 35 seconds
    const timeSinceLastPong = Date.now() - lastPongTime;
    if (timeSinceLastPong > 35000) {
      console.warn('[Socket] Stale connection detected, reconnecting...');
      reconnectSocket();
      return;
    }

    // Send ping
    socket.emit('ping');
    console.log('[Socket] Ping sent');
  }, 25000);
}

function stopHeartbeat(): void {
  if (heartbeatInterval) {
    clearInterval(heartbeatInterval);
    heartbeatInterval = null;
  }
}

/**
 * Get connection status
 */
export function getConnectionStatus(): 'connected' | 'disconnected' | 'connecting' {
  if (!socket) return 'disconnected';
  if (socket.connected) return 'connected';
  if (socket.disconnected) return 'disconnected';
  return 'connecting';
}
