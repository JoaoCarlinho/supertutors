import { useEffect, useState } from 'react';
import { useActions } from 'kea';
import { conversationLogic } from './logic/conversationLogic';
import { ChatInput } from './components/custom/ChatInput';
import { MessageList } from './components/custom/MessageList';
import { ThreadList } from './components/custom/ThreadList';
import { StreakBadge } from './components/custom/StreakBadge';
import { Celebration } from './components/custom/Celebration';
import { SkipNav } from './components/custom/SkipNav';
import { LiveRegion } from './components/custom/LiveRegion';
import { ChatCanvas } from './components/custom/ChatCanvas';
import { ValidationFeedback } from './components/custom/ValidationFeedback';
import { ValidationTestPanel } from './components/custom/ValidationTestPanel';
import { AudioControls } from './components/custom/AudioControls';

function App() {
  const { initializeConnection, sendMessage } = useActions(conversationLogic);
  const [showCanvas, setShowCanvas] = useState(false);

  // Initialize WebSocket connection on mount
  useEffect(() => {
    initializeConnection();
  }, [initializeConnection]);

  const handleCanvasMessageSubmit = (text: string) => {
    sendMessage(text);
    setShowCanvas(false);
  };

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      {/* Skip Navigation Links */}
      <SkipNav />

      {/* ARIA Live Regions for screen reader announcements */}
      <LiveRegion />

      {/* Main layout with sidebar and chat */}
      <div className="flex-1 flex overflow-hidden">
        {/* Thread List Sidebar with Header */}
        <div
          id="thread-list"
          className="hidden md:flex md:flex-col h-full"
        >
          {/* Header - only above sidebar */}
          <header className="bg-white border-b border-r px-4 py-4 flex items-center justify-between">
            <div>
              <h1 className="text-xl font-bold text-blue-800">SuperTutors</h1>
              <p className="text-xs text-gray-600">Socratic AI Tutor</p>
            </div>
            <AudioControls />
          </header>
          <ThreadList />
        </div>

        {/* Main Chat Area */}
        <main
          id="main-content"
          className="flex-1 flex flex-col bg-white relative overflow-hidden"
          role="main"
        >
          <h2 className="sr-only">Chat with AI Tutor</h2>
          {/* ChatCanvas Overlay - positioned at top of main area */}
          {showCanvas && (
            <ChatCanvas
              onMessageSubmit={handleCanvasMessageSubmit}
              onClose={() => setShowCanvas(false)}
            />
          )}
          <div className="flex-1 overflow-hidden">
            <MessageList />
          </div>
          <div id="chat-input">
            <ChatInput onCanvasToggle={setShowCanvas} />
          </div>
        </main>
      </div>

      {/* Celebration System */}
      <StreakBadge />
      <Celebration />

      {/* Answer Validation Feedback */}
      <ValidationFeedback />

      {/* Developer Test Panel (remove in production) */}
      <ValidationTestPanel />
    </div>
  );
}

export default App;
