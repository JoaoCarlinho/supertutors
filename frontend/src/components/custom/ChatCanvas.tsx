import React, { useState } from 'react';
import { ImageUpload } from './ImageUpload';
import { OCRConfirmation } from './OCRConfirmation';
import { DrawingCanvas } from './DrawingCanvas';

type Mode = 'closed' | 'upload' | 'ocr' | 'draw';

interface ChatCanvasProps {
  onMessageSubmit: (message: string) => void;
  onClose?: () => void;
}

export const ChatCanvas: React.FC<ChatCanvasProps> = ({ onMessageSubmit, onClose }) => {
  const [mode, setMode] = useState<Mode>('upload');
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [ocrData, setOcrData] = useState<{
    text: string;
    confidence: number;
  } | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);

  // Get API URL from environment
  const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:5001';

  const handleImageUploadComplete = async (uploadedImageId: string, uploadedImageUrl: string) => {
    console.log('handleImageUploadComplete called with:', { uploadedImageId, uploadedImageUrl });
    setImageUrl(`${apiUrl}${uploadedImageUrl}`);

    // Start OCR processing
    setIsProcessing(true);
    console.log('Starting OCR processing...');

    try {
      const ocrUrl = `${apiUrl}/api/images/ocr/extract`;
      console.log('Sending OCR request to:', ocrUrl);

      // Create abort controller for timeout
      const controller = new AbortController();
      const timeoutId = setTimeout(() => {
        controller.abort();
        console.warn('OCR request timed out after 60 seconds');
      }, 60000); // 60 second timeout

      const response = await fetch(ocrUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ image_id: uploadedImageId }),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      console.log('OCR response status:', response.status);
      const data = await response.json();
      console.log('OCR response data:', data);

      if (data.success) {
        console.log('OCR successful, extracted text:', data.extracted_text);
        setOcrData({
          text: data.extracted_text,
          confidence: data.confidence,
        });
        setMode('ocr');
        console.log('Switched to OCR confirmation mode');
      } else {
        console.error('OCR failed:', data.error);
        alert(`OCR failed: ${data.error || 'Unknown error'}`);
        setMode('closed');
      }
    } catch (error) {
      console.error('OCR error:', error);
      if (error instanceof Error && error.name === 'AbortError') {
        alert('OCR processing is taking longer than expected. The vision model may be slow. Please try again or contact support.');
      } else {
        alert(`Failed to process image: ${error instanceof Error ? error.message : 'Unknown error'}`);
      }
      setMode('closed');
    } finally {
      setIsProcessing(false);
      console.log('OCR processing complete, isProcessing set to false');
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
    console.log('handleDrawingExport called with dataUrl length:', dataUrl.length);

    try {
      // Convert data URL to blob
      console.log('Converting data URL to blob...');
      const response = await fetch(dataUrl);
      const blob = await response.blob();
      console.log('Blob created, size:', blob.size, 'bytes');

      // Upload to backend
      const formData = new FormData();
      formData.append('image', blob, 'drawing.png');
      console.log('FormData prepared, uploading to:', `${apiUrl}/api/images/upload`);

      setIsProcessing(true);

      const uploadResponse = await fetch(`${apiUrl}/api/images/upload`, {
        method: 'POST',
        body: formData,
      });

      console.log('Upload response status:', uploadResponse.status);
      const uploadData = await uploadResponse.json();
      console.log('Upload response data:', uploadData);

      if (uploadData.success) {
        console.log('Upload successful, processing with OCR...');
        // Process with OCR
        handleImageUploadComplete(uploadData.image_id, uploadData.url);
      } else {
        console.error('Upload failed:', uploadData.error);
        alert(`Failed to upload drawing: ${uploadData.error || 'Unknown error'}`);
        setIsProcessing(false);
      }
    } catch (error) {
      console.error('Upload error:', error);
      alert(`Failed to export drawing: ${error instanceof Error ? error.message : 'Unknown error'}`);
      setIsProcessing(false);
    }
  };

  const handleClose = () => {
    if (mode === 'ocr' || mode === 'draw') {
      if (confirm('Close without submitting?')) {
        setMode('closed');
        setImageUrl(null);
        setOcrData(null);
        onClose?.();
      }
    } else {
      setMode('closed');
      setImageUrl(null);
      setOcrData(null);
      onClose?.();
    }
  };

  if (mode === 'closed') {
    return null;
  }

  return (
    <div
      className="chat-canvas-overlay absolute top-0 left-0 right-0 bg-white border-b shadow-lg z-30 max-h-[60vh] overflow-y-auto pt-20"
      role="dialog"
      aria-modal="true"
      aria-labelledby="canvas-title"
    >
      <div className="chat-canvas-content w-full">
        {/* Header */}
        <div className="bg-white border-b px-4 py-3">
          <div className="flex items-center justify-between mb-3">
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
          {mode === 'upload' && (
            <div className="flex gap-2">
              <button
                onClick={() => setMode('draw')}
                className="px-3 py-1 text-sm border border-gray-300 rounded hover:bg-gray-50"
              >
                ✏️ Switch to Draw
              </button>
            </div>
          )}
          {mode === 'draw' && (
            <div className="flex gap-2">
              <button
                onClick={() => setMode('upload')}
                className="px-3 py-1 text-sm border border-gray-300 rounded hover:bg-gray-50"
              >
                📷 Switch to Upload
              </button>
            </div>
          )}
        </div>

        {/* Content */}
        <div className="p-4">
          {isProcessing && (
            <div className="flex flex-col items-center justify-center py-8">
              <div className="animate-spin h-12 w-12 border-4 border-blue-600 border-t-transparent rounded-full mb-3"></div>
              <p className="text-gray-600 font-medium">Processing with Vision AI...</p>
              <p className="text-sm text-gray-500 mt-2">This may take 30-60 seconds</p>
              <p className="text-xs text-gray-400 mt-1">Extracting text and equations from your drawing</p>
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
