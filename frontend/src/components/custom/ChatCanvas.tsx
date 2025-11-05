import React, { useState } from 'react';
import { ImageUpload } from './ImageUpload';
import { OCRConfirmation } from './OCRConfirmation';
import { DrawingCanvas } from './DrawingCanvas';

type Mode = 'closed' | 'upload' | 'ocr' | 'draw';

interface ChatCanvasProps {
  onMessageSubmit: (message: string) => void;
}

export const ChatCanvas: React.FC<ChatCanvasProps> = ({ onMessageSubmit }) => {
  const [mode, setMode] = useState<Mode>('closed');
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [ocrData, setOcrData] = useState<{
    text: string;
    confidence: number;
  } | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);

  const handleImageUploadComplete = async (uploadedImageId: string, uploadedImageUrl: string) => {
    setImageUrl(`http://localhost:5001${uploadedImageUrl}`);

    // Start OCR processing
    setIsProcessing(true);

    try {
      const response = await fetch('http://localhost:5001/api/images/ocr/extract', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ image_id: uploadedImageId }),
      });

      const data = await response.json();

      if (data.success) {
        setOcrData({
          text: data.extracted_text,
          confidence: data.confidence,
        });
        setMode('ocr');
      } else {
        alert(`OCR failed: ${data.error || 'Unknown error'}`);
        setMode('closed');
      }
    } catch (error) {
      console.error('OCR error:', error);
      alert('Failed to process image. Please try again.');
      setMode('closed');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleOCRConfirm = (editedText: string) => {
    onMessageSubmit(editedText);
    setMode('closed');
    setImageUrl(null);
    setOcrData(null);
  };

  const handleOCRRetry = () => {
    setMode('upload');
    setImageUrl(null);
    setOcrData(null);
  };

  const handleDrawingExport = async (dataUrl: string) => {
    // Convert data URL to blob
    const response = await fetch(dataUrl);
    const blob = await response.blob();

    // Upload to backend
    const formData = new FormData();
    formData.append('image', blob, 'drawing.png');

    setIsProcessing(true);

    try {
      const uploadResponse = await fetch('http://localhost:5001/api/images/upload', {
        method: 'POST',
        body: formData,
      });

      const uploadData = await uploadResponse.json();

      if (uploadData.success) {
        // Process with OCR
        handleImageUploadComplete(uploadData.image_id, uploadData.url);
      } else {
        alert('Failed to upload drawing');
      }
    } catch (error) {
      console.error('Upload error:', error);
      alert('Failed to export drawing');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleClose = () => {
    if (mode === 'ocr' || mode === 'draw') {
      if (confirm('Close without submitting?')) {
        setMode('closed');
        setImageUrl(null);
        setOcrData(null);
      }
    } else {
      setMode('closed');
      setImageUrl(null);
      setOcrData(null);
    }
  };

  if (mode === 'closed') {
    return (
      <div className="chat-canvas-triggers flex gap-2">
        <button
          onClick={() => setMode('upload')}
          className="px-3 py-2 border border-gray-300 rounded hover:bg-gray-50 text-sm flex items-center gap-1"
          title="Upload image"
        >
          📷 Upload Image
        </button>
        <button
          onClick={() => setMode('draw')}
          className="px-3 py-2 border border-gray-300 rounded hover:bg-gray-50 text-sm flex items-center gap-1"
          title="Draw on canvas"
        >
          ✏️ Draw
        </button>
      </div>
    );
  }

  return (
    <div
      className="chat-canvas-overlay fixed inset-0 bg-black bg-opacity-50 z-[1000] md:z-50 flex items-center justify-center p-0 md:p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="canvas-title"
    >
      <div className="chat-canvas-content bg-white rounded-none md:rounded-lg shadow-xl w-full h-full md:max-w-4xl md:w-auto md:h-auto md:max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-white border-b px-4 py-3 flex items-center justify-between z-10">
          <h2 id="canvas-title" className="text-lg font-semibold text-gray-800">
            {mode === 'upload' && 'Upload Image'}
            {mode === 'ocr' && 'Review Extracted Text'}
            {mode === 'draw' && 'Draw on Canvas'}
          </h2>
          <button
            onClick={handleClose}
            className="min-w-[44px] min-h-[44px] flex items-center justify-center text-gray-500 hover:text-gray-700 text-2xl leading-none"
            aria-label="Close canvas"
          >
            ×
          </button>
        </div>

        {/* Content */}
        <div className="p-4">
          {isProcessing && (
            <div className="flex flex-col items-center justify-center py-8">
              <div className="animate-spin h-12 w-12 border-4 border-blue-600 border-t-transparent rounded-full mb-3"></div>
              <p className="text-gray-600">Processing image...</p>
            </div>
          )}

          {!isProcessing && mode === 'upload' && (
            <ImageUpload
              onImageSelected={(file) => console.log('Image selected:', file)}
              onUploadComplete={handleImageUploadComplete}
            />
          )}

          {!isProcessing && mode === 'ocr' && ocrData && imageUrl && (
            <OCRConfirmation
              extractedText={ocrData.text}
              confidence={ocrData.confidence}
              imageUrl={imageUrl}
              onConfirm={handleOCRConfirm}
              onRetry={handleOCRRetry}
            />
          )}

          {!isProcessing && mode === 'draw' && (
            <DrawingCanvas onExport={handleDrawingExport} />
          )}
        </div>
      </div>
    </div>
  );
};
