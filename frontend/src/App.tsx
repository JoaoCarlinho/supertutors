import { useEffect } from 'react';
import { useActions } from 'kea';
import { conversationLogic } from './logic/conversationLogic';
import { ConnectionStatus } from './components/custom/ConnectionStatus';
import { ChatInput } from './components/custom/ChatInput';
import { MessageList } from './components/custom/MessageList';
import { ThreadList } from './components/custom/ThreadList';
import { StreakBadge } from './components/custom/StreakBadge';
import { Celebration } from './components/custom/Celebration';
import { SkipNav } from './components/custom/SkipNav';
import { LiveRegion } from './components/custom/LiveRegion';

function App() {
  const { initializeConnection } = useActions(conversationLogic);

  // Initialize WebSocket connection on mount
  useEffect(() => {
    initializeConnection();
  }, [initializeConnection]);

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      {/* Skip Navigation Links */}
      <SkipNav />

      {/* ARIA Live Regions for screen reader announcements */}
      <LiveRegion />

      {/* Header */}
      <header className="bg-white border-b px-4 md:px-6 py-4 flex items-center justify-between">
        <div>
          <h1 className="text-xl md:text-2xl font-bold text-blue-800">SuperTutors</h1>
          <p className="text-xs md:text-sm text-gray-600">Socratic AI Tutor for 9th Grade Math</p>
        </div>
        <ConnectionStatus />
      </header>

      {/* Main layout with sidebar and chat */}
      <div className="flex-1 flex overflow-hidden">
        {/* Thread List Sidebar */}
        <aside
          id="thread-list"
          aria-label="Conversation threads"
          className="hidden md:block md:w-64 lg:w-80"
        >
          <ThreadList />
        </aside>

        {/* Main Chat Area */}
        <main
          id="main-content"
          className="flex-1 flex flex-col bg-white"
          role="main"
        >
          <h2 className="sr-only">Chat with AI Tutor</h2>
          <MessageList />
          <div id="chat-input">
            <ChatInput />
          </div>
        </main>
      </div>

      {/* Celebration System */}
      <StreakBadge />
      <Celebration />
    </div>
  );
}

export default App;
