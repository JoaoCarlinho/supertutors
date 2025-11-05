import { useEffect, useState } from 'react';
import { useActions, useValues } from 'kea';
import { conversationLogic } from '../../logic/conversationLogic';
import { PlusIcon, TrashIcon } from 'lucide-react';

interface Thread {
  id: string;
  title: string;
  last_message_preview: string | null;
  updated_at: string;
}

export function ThreadList() {
  const [threads, setThreads] = useState<Thread[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const { currentConversationId } = useValues(conversationLogic);
  const { loadThread, setCurrentConversation, setMessages } = useActions(conversationLogic);

  const loadThreads = async () => {
    setIsLoading(true);
    try {
      const response = await fetch('http://localhost:5001/api/threads?limit=20');
      if (response.ok) {
        const data = await response.json();
        setThreads(data);
      }
    } catch (error) {
      console.error('Error loading threads:', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadThreads();
  }, []);

  const handleNewThread = () => {
    setCurrentConversation('');
    setMessages([]);
  };

  const handleSelectThread = (threadId: string) => {
    loadThread(threadId);
  };

  const handleDeleteThread = async (threadId: string, e: React.MouseEvent) => {
    e.stopPropagation();

    if (!confirm('Delete this conversation? This cannot be undone.')) {
      return;
    }

    try {
      const response = await fetch(`http://localhost:5001/api/threads/${threadId}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        // Remove from list
        setThreads(threads.filter(t => t.id !== threadId));

        // If deleted thread was active, create new thread
        if (currentConversationId === threadId) {
          handleNewThread();
        }
      }
    } catch (error) {
      console.error('Error deleting thread:', error);
    }
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);

    if (minutes < 1) return 'Just now';
    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    if (days < 7) return `${days}d ago`;
    return date.toLocaleDateString();
  };

  return (
    <aside
      className="w-64 bg-white border-r border-gray-200 flex flex-col"
      role="navigation"
      aria-label="Conversation threads"
    >
      {/* New Thread Button */}
      <div className="p-4 border-b border-gray-200">
        <button
          onClick={handleNewThread}
          className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          <PlusIcon className="w-4 h-4" />
          New Thread
        </button>
      </div>

      {/* Thread List */}
      <div className="flex-1 overflow-y-auto">
        {isLoading ? (
          <div className="p-4 text-center text-gray-500">Loading...</div>
        ) : threads.length === 0 ? (
          <div className="p-4 text-center text-gray-500">
            <p>No conversations yet</p>
            <p className="text-xs mt-1">Start a new conversation!</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-100">
            {threads.map((thread) => (
              <button
                key={thread.id}
                onClick={() => handleSelectThread(thread.id)}
                className={`w-full text-left p-4 hover:bg-gray-50 transition-colors group relative ${
                  currentConversationId === thread.id ? 'bg-blue-50 border-l-4 border-blue-600' : ''
                }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <h3 className="font-medium text-sm text-gray-900 truncate">
                      {thread.title}
                    </h3>
                    {thread.last_message_preview && (
                      <p className="text-xs text-gray-500 truncate mt-1">
                        {thread.last_message_preview}
                      </p>
                    )}
                    <p className="text-xs text-gray-400 mt-1">
                      {formatTimestamp(thread.updated_at)}
                    </p>
                  </div>
                  <button
                    onClick={(e) => handleDeleteThread(thread.id, e)}
                    className="opacity-0 group-hover:opacity-100 transition-opacity p-1 hover:bg-red-50 rounded"
                    aria-label="Delete conversation"
                  >
                    <TrashIcon className="w-4 h-4 text-red-600" />
                  </button>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>
    </aside>
  );
}
