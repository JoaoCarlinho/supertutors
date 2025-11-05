import { useState, type FormEvent, useEffect } from 'react';
import { useActions } from 'kea';
import { conversationLogic } from '../../logic/conversationLogic';
import { Math } from './Math';
import { parseNaturalMathToLatex } from '../../utils/mathParser';
import { ChatCanvas } from './ChatCanvas';

export function ChatInput() {
  const [message, setMessage] = useState('');
  const [isTypingDebounce, setIsTypingDebounce] = useState<NodeJS.Timeout | null>(null);
  const [mathMode, setMathMode] = useState(false);
  const [preview, setPreview] = useState('');
  const [previewError, setPreviewError] = useState(false);
  const [showCanvas, setShowCanvas] = useState(false);
  const { sendMessage, setTyping } = useActions(conversationLogic);

  const handleCanvasMessageSubmit = (text: string) => {
    sendMessage(text);
    setShowCanvas(false);
  };

  // Update preview when in math mode
  useEffect(() => {
    if (!mathMode || !message.trim()) {
      setPreview('');
      setPreviewError(false);
      return;
    }

    const timer = setTimeout(() => {
      try {
        // Parse natural language to LaTeX if needed
        const latexContent = parseNaturalMathToLatex(message);
        setPreview(latexContent);
        setPreviewError(false);
      } catch {
        setPreviewError(true);
      }
    }, 300); // Debounce

    return () => clearTimeout(timer);
  }, [message, mathMode]);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (!message.trim()) return;

    // If in math mode, wrap with delimiters
    const finalMessage = mathMode ? `$${message}$` : message;
    sendMessage(finalMessage);
    setMessage('');
    setPreview('');

    // Stop typing indicator
    setTyping(false);
    if (isTypingDebounce) {
      clearTimeout(isTypingDebounce);
      setIsTypingDebounce(null);
    }
  };

  const handleInputChange = (value: string) => {
    setMessage(value);

    // Clear existing timeout
    if (isTypingDebounce) {
      clearTimeout(isTypingDebounce);
    }

    // Start typing
    if (value.trim()) {
      setTyping(true);

      // Stop typing after 2 seconds of inactivity
      const timeout = setTimeout(() => {
        setTyping(false);
        setIsTypingDebounce(null);
      }, 2000);

      setIsTypingDebounce(timeout);
    } else {
      setTyping(false);
      setIsTypingDebounce(null);
    }
  };

  const insertLatexShortcut = (latex: string) => {
    const cursorPos = message.length;
    const newValue = message.slice(0, cursorPos) + latex + message.slice(cursorPos);
    setMessage(newValue);
  };

  return (
    <div className="border-t bg-white">
      {/* ChatCanvas Overlay */}
      {showCanvas && <ChatCanvas onMessageSubmit={handleCanvasMessageSubmit} />}

      {/* Math Mode Toggle and Shortcuts */}
      <div className="flex items-center gap-2 px-4 py-2 border-b bg-gray-50">
        <button
          type="button"
          onClick={() => setMathMode(!mathMode)}
          className={`px-3 py-1 text-sm rounded ${
            mathMode
              ? 'bg-blue-600 text-white'
              : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
          }`}
          title="Toggle Math Mode (Ctrl+M)"
        >
          ƒₓ Math Mode
        </button>

        {mathMode && (
          <>
            <div className="w-px h-6 bg-gray-300" />
            <div className="flex gap-1">
              <button
                type="button"
                onClick={() => insertLatexShortcut('\\pi')}
                className="px-2 py-1 text-sm bg-white border rounded hover:bg-gray-100"
                title="Insert π"
              >
                π
              </button>
              <button
                type="button"
                onClick={() => insertLatexShortcut('\\sqrt{}')}
                className="px-2 py-1 text-sm bg-white border rounded hover:bg-gray-100"
                title="Insert square root"
              >
                √
              </button>
              <button
                type="button"
                onClick={() => insertLatexShortcut('\\frac{}{}')}
                className="px-2 py-1 text-sm bg-white border rounded hover:bg-gray-100"
                title="Insert fraction"
              >
                ½
              </button>
              <button
                type="button"
                onClick={() => insertLatexShortcut('\\int')}
                className="px-2 py-1 text-sm bg-white border rounded hover:bg-gray-100"
                title="Insert integral"
              >
                ∫
              </button>
              <button
                type="button"
                onClick={() => insertLatexShortcut('\\sum')}
                className="px-2 py-1 text-sm bg-white border rounded hover:bg-gray-100"
                title="Insert summation"
              >
                Σ
              </button>
              <button
                type="button"
                onClick={() => insertLatexShortcut('\\infty')}
                className="px-2 py-1 text-sm bg-white border rounded hover:bg-gray-100"
                title="Insert infinity"
              >
                ∞
              </button>
            </div>
          </>
        )}

        <div className="w-px h-6 bg-gray-300" />

        {/* Image/Canvas Tools */}
        <button
          type="button"
          onClick={() => setShowCanvas(true)}
          className="px-3 py-1 text-sm bg-white border border-gray-300 rounded hover:bg-gray-50"
          title="Upload image or draw"
        >
          📷 Image/Draw
        </button>
      </div>

      {/* Preview Pane */}
      {mathMode && preview && (
        <div className="px-4 py-3 bg-blue-50 border-b">
          <p className="text-xs text-gray-600 mb-1">Preview:</p>
          <div className="bg-white p-2 rounded border">
            {previewError ? (
              <span className="text-red-600 text-sm">Invalid LaTeX</span>
            ) : (
              <Math latex={preview} displayMode={false} />
            )}
          </div>
        </div>
      )}

      {/* Input Form */}
      <form onSubmit={handleSubmit} className="flex gap-2 p-4">
        <input
          type="text"
          value={message}
          onChange={(e) => handleInputChange(e.target.value)}
          placeholder={mathMode ? "Type math notation or LaTeX..." : "Type your message..."}
          className="flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          aria-label="Type your message"
        />
        <button
          type="submit"
          disabled={!message.trim()}
          className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
        >
          Send
        </button>
      </form>
    </div>
  );
}
