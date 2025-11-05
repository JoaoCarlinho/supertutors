import React, { useState, useEffect } from 'react';

interface OCRConfirmationProps {
  extractedText: string;
  confidence: number;
  imageUrl: string;
  onConfirm: (editedText: string) => void;
  onRetry: () => void;
}

export const OCRConfirmation: React.FC<OCRConfirmationProps> = ({
  extractedText,
  confidence,
  imageUrl,
  onConfirm,
  onRetry,
}) => {
  const [editedText, setEditedText] = useState(extractedText);
  const showWarning = confidence < 0.7;

  useEffect(() => {
    setEditedText(extractedText);
  }, [extractedText]);

  const handleConfirm = () => {
    if (editedText.trim()) {
      onConfirm(editedText);
    }
  };

  const handleRetry = () => {
    if (confirm('Discard extracted text and upload a different image?')) {
      onRetry();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && e.ctrlKey) {
      handleConfirm();
    } else if (e.key === 'Escape') {
      handleRetry();
    }
  };

  return (
    <div
      className="ocr-confirmation p-4 border rounded bg-white"
      role="region"
      aria-label="OCR result confirmation"
    >
      {/* Image Thumbnail */}
      <div className="mb-3">
        <img
          src={imageUrl}
          alt="Uploaded"
          className="w-32 h-32 object-cover rounded border"
        />
      </div>

      {/* Confidence Warning */}
      {showWarning && (
        <div
          className="mb-3 p-2 bg-yellow-50 border border-yellow-200 rounded flex items-start gap-2"
          role="alert"
          aria-live="polite"
        >
          <span className="text-yellow-600 text-lg">⚠️</span>
          <div>
            <p className="text-sm font-medium text-yellow-800">
              Low confidence detection
            </p>
            <p className="text-xs text-yellow-700">
              Please carefully review and edit the extracted text below.
            </p>
          </div>
        </div>
      )}

      {/* Extracted Text Editor */}
      <div className="mb-3">
        <label
          htmlFor="ocr-text"
          className="block text-sm font-medium text-gray-700 mb-1"
        >
          Extracted Text (Review and edit if needed)
        </label>
        <textarea
          id="ocr-text"
          value={editedText}
          onChange={(e) => setEditedText(e.target.value)}
          onKeyDown={handleKeyDown}
          aria-label="Extracted text for review"
          className="w-full min-h-[120px] max-h-[300px] p-3 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500 resize-y"
          placeholder="Edit the extracted text here..."
        />
        <div className="flex justify-between items-center mt-1">
          <span className="text-xs text-gray-500">
            {editedText.length} characters
          </span>
          <span className="text-xs text-gray-500">
            Ctrl+Enter to send, Esc to cancel
          </span>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex gap-2">
        <button
          onClick={handleConfirm}
          disabled={!editedText.trim()}
          className="flex-1 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed font-medium"
          aria-label="Send message with extracted text"
        >
          Send Message
        </button>
        <button
          onClick={handleRetry}
          className="px-4 py-2 border border-gray-300 text-gray-700 rounded hover:bg-gray-50 font-medium"
          aria-label="Upload different image"
        >
          Upload Different Image
        </button>
      </div>
    </div>
  );
};
