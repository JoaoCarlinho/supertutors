import { useEffect, useRef } from 'react';
import { useValues } from 'kea';
import { conversationLogic, type Message } from '../../logic/conversationLogic';
import { MathContent } from './Math';

export function MessageList() {
  const { messages, isTyping } = useValues(conversationLogic);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const getMessageStatusIcon = (message: Message) => {
    if (message.role !== 'student') return null;

    switch (message.status) {
      case 'sending':
        return <span className="text-xs text-gray-400">Sending...</span>;
      case 'sent':
        return <span className="text-xs text-gray-400">✓</span>;
      case 'error':
        return <span className="text-xs text-red-500">Error</span>;
      default:
        return null;
    }
  };

  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-4">
      {messages.length === 0 && (
        <div className="text-center text-gray-500 mt-8">
          <p className="text-lg">No messages yet</p>
          <p className="text-sm">Start a conversation by sending a message below</p>
        </div>
      )}

      {messages.map((message: Message) => (
        <div
          key={message.id}
          className={`flex ${message.role === 'student' ? 'justify-end' : 'justify-start'}`}
        >
          <div
            className={`max-w-[70%] rounded-lg px-4 py-2 ${
              message.role === 'student'
                ? 'bg-blue-600 text-white'
                : message.role === 'tutor'
                ? 'bg-gray-200 text-gray-900'
                : 'bg-yellow-100 text-gray-900'
            }`}
          >
            <div className="flex items-start gap-2">
              <div className="flex-1">
                <p className="text-sm font-semibold capitalize mb-1">
                  {message.role}
                </p>
                <div className="whitespace-pre-wrap">
                  <MathContent content={message.content} />
                </div>
              </div>
            </div>
            <div className="flex items-center justify-between mt-1">
              <span className="text-xs opacity-75">
                {new Date(message.created_at).toLocaleTimeString()}
              </span>
              {getMessageStatusIcon(message)}
            </div>
          </div>
        </div>
      ))}

      {isTyping && (
        <div className="flex justify-start">
          <div className="bg-gray-200 text-gray-900 rounded-lg px-4 py-2">
            <p className="text-sm font-semibold">Tutor</p>
            <p className="text-sm italic">is typing...</p>
          </div>
        </div>
      )}

      <div ref={messagesEndRef} />
    </div>
  );
}
