import React, { useState, useEffect, useRef } from 'react';
import { ImageUpload } from './ImageUpload';
import { OCRConfirmation } from './OCRConfirmation';
import { DrawingCanvas } from './DrawingCanvas';
import { SubjectSelection } from './SubjectSelection';
import { getSocket, initializeSocket } from '@/lib/socketService';

type Mode = 'closed' | 'upload' | 'subject' | 'ocr' | 'draw';

interface OCRProgress {
  stage: string;
  message: string;
  percent: number | null;
}

interface ChatCanvasProps {
  onMessageSubmit: (message: string) => void;
  onClose?: () => void;
}

export const ChatCanvas: React.FC<ChatCanvasProps> = ({ onMessageSubmit, onClose }) => {
  const [mode, setMode] = useState<Mode>('upload');
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [imageId, setImageId] = useState<string | null>(null);
  const [ocrData, setOcrData] = useState<{
    text: string;
    confidence: number;
  } | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [ocrProgress, setOcrProgress] = useState<OCRProgress | null>(null);
  const processingImageIdRef = useRef<string | null>(null);

  // Get API URL from environment
  const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:5001';

  // Setup WebSocket listeners for OCR progress
  useEffect(() => {
    const socket = getSocket() || initializeSocket();

    const handleOcrProgress = (data: OCRProgress & { image_id: string }) => {
      // Only update if this progress is for our current image
      if (data.image_id === processingImageIdRef.current) {
        console.log('[OCR Progress]', data);
        setOcrProgress({
          stage: data.stage,
          message: data.message,
          percent: data.percent
        });
      }
    };

    const handleOcrComplete = (data: {
      success: boolean;
      image_id: string;
      extracted_text?: string;
      confidence?: number;
      error?: string;
    }) => {
      // Only process if this is for our current image
      if (data.image_id !== processingImageIdRef.current) return;

      console.log('[OCR Complete]', data);
      setIsProcessing(false);
      setOcrProgress(null);
      processingImageIdRef.current = null;

      if (data.success && data.extracted_text) {
        setOcrData({
          text: data.extracted_text,
          confidence: data.confidence || 0.8,
        });
        setMode('ocr');
      } else {
        alert(`OCR failed: ${data.error || 'Unknown error'}`);
        setMode('closed');
      }
    };

    const handleOcrError = (data: { error: string; image_id?: string }) => {
      if (data.image_id && data.image_id !== processingImageIdRef.current) return;

      console.error('[OCR Error]', data);
      setIsProcessing(false);
      setOcrProgress(null);
      processingImageIdRef.current = null;
      alert(`OCR error: ${data.error}`);
      setMode('closed');
    };

    socket.on('ocr:progress', handleOcrProgress);
    socket.on('ocr:complete', handleOcrComplete);
    socket.on('ocr:error', handleOcrError);

    return () => {
      socket.off('ocr:progress', handleOcrProgress);
      socket.off('ocr:complete', handleOcrComplete);
      socket.off('ocr:error', handleOcrError);
    };
  }, []);

  // Helper function to get human-readable progress descriptions
  const getProgressStageDescription = (stage: string | undefined): string => {
    switch (stage) {
      case 'started':
        return 'Starting OCR processing...';
      case 'optimizing_image':
        return 'Optimizing image for better accuracy...';
      case 'loading_pix2text_models':
        return 'Loading math recognition models...';
      case 'pix2text_processing':
        return 'Extracting mathematical expressions...';
      case 'gpt4o_verifying':
        return 'Verifying results with AI vision...';
      case 'gpt4o_processing':
        return 'Processing with AI vision model...';
      case 'cache_hit':
        return 'Found cached result!';
      case 'completed':
        return 'Processing complete!';
      case 'error':
        return 'An error occurred';
      default:
        return 'Extracting text and equations from your image';
    }
  };

  const handleImageUploadComplete = async (uploadedImageId: string, uploadedImageUrl: string) => {
    console.log('handleImageUploadComplete called with:', { uploadedImageId, uploadedImageUrl });
    setImageUrl(`${apiUrl}${uploadedImageUrl}`);
    setImageId(uploadedImageId);

    // Show subject selection instead of immediately processing OCR
    setMode('subject');
    console.log('Switched to subject selection mode');
  };

  const handleSubjectSelected = async (subject: string) => {
    if (!imageId) {
      console.error('No image ID available for OCR');
      return;
    }

    // Start OCR processing with subject context via WebSocket
    setIsProcessing(true);
    setOcrProgress({ stage: 'starting', message: 'Initializing...', percent: 0 });
    processingImageIdRef.current = imageId;
    console.log('Starting OCR processing via WebSocket with subject:', subject);

    const socket = getSocket();
    if (!socket || !socket.connected) {
      console.error('Socket not connected, falling back to HTTP');
      // Fallback to HTTP if WebSocket not available
      await handleSubjectSelectedHTTP(subject);
      return;
    }

    // Send OCR request via WebSocket
    socket.emit('ocr:process', {
      image_id: imageId,
      subject: subject,
      method: 'hybrid'
    });

    console.log('OCR request sent via WebSocket');
  };

  // Fallback HTTP method for OCR (kept for reliability)
  const handleSubjectSelectedHTTP = async (subject: string) => {
    try {
      const ocrUrl = `${apiUrl}/api/images/ocr/extract`;
      console.log('Sending OCR request to:', ocrUrl);

      // Create abort controller for timeout (increased to 180s)
      const controller = new AbortController();
      const timeoutId = setTimeout(() => {
        controller.abort();
        console.warn('OCR request timed out after 180 seconds');
      }, 180000); // 180 second timeout (increased from 60)

      const response = await fetch(ocrUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          image_id: imageId,
          subject: subject
        }),
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
        alert('OCR processing timed out. Please try again.');
      } else {
        alert(`Failed to process image: ${error instanceof Error ? error.message : 'Unknown error'}`);
      }
      setMode('closed');
    } finally {
      setIsProcessing(false);
      setOcrProgress(null);
      processingImageIdRef.current = null;
      console.log('OCR processing complete, isProcessing set to false');
    }
  };

  const handleSubjectCancel = () => {
    setMode('upload');
    setImageUrl(null);
    setImageId(null);
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
        console.log('Upload successful, showing subject selection...');
        // Stop processing spinner, show subject selection
        setIsProcessing(false);
        // This will show subject selection UI
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
              <p className="text-gray-600 font-medium">
                {ocrProgress?.message || 'Processing with Vision AI...'}
              </p>
              {/* Progress bar */}
              {ocrProgress?.percent !== null && ocrProgress?.percent !== undefined && (
                <div className="w-64 bg-gray-200 rounded-full h-2.5 mt-3">
                  <div
                    className="bg-blue-600 h-2.5 rounded-full transition-all duration-300"
                    style={{ width: `${ocrProgress.percent}%` }}
                  ></div>
                </div>
              )}
              <p className="text-sm text-gray-500 mt-2">
                {ocrProgress?.percent !== null && ocrProgress?.percent !== undefined
                  ? `${ocrProgress.percent}% complete`
                  : 'This may take 30-60 seconds'}
              </p>
              <p className="text-xs text-gray-400 mt-1">
                {getProgressStageDescription(ocrProgress?.stage)}
              </p>
            </div>
          )}

          {!isProcessing && mode === 'upload' && (
            <ImageUpload
              onImageSelected={(file) => console.log('Image selected:', file)}
              onUploadComplete={handleImageUploadComplete}
            />
          )}

          {!isProcessing && mode === 'subject' && imageUrl && (
            <SubjectSelection
              imageUrl={imageUrl}
              onSubjectSelected={handleSubjectSelected}
              onCancel={handleSubjectCancel}
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
