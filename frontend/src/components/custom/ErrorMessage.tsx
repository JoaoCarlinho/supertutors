import { AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';

interface ApiError {
  message: string;
  code?: string;
  details?: Record<string, unknown>;
}

interface ErrorMessageProps {
  error: ApiError | Error | string;
  onRetry?: () => void;
  className?: string;
}

/**
 * ErrorMessage component displays user-friendly error messages for API errors.
 * Supports different error types and provides retry functionality.
 */
export function ErrorMessage({ error, onRetry, className = '' }: ErrorMessageProps) {
  // Parse error message and code
  let message: string;
  let code: string | undefined;

  if (typeof error === 'string') {
    message = error;
  } else if (error instanceof Error) {
    message = error.message;
  } else {
    message = error.message;
    code = error.code;
  }

  // Map error codes to user-friendly messages
  const getFriendlyMessage = (errorCode?: string, originalMessage?: string): string => {
    const errorMessages: Record<string, string> = {
      LLM_TIMEOUT: 'The AI is taking longer than expected. Please try again.',
      LLM_ERROR: 'The AI service is temporarily unavailable. Please try again in a moment.',
      DATABASE_ERROR: 'We encountered a database issue. Please try again.',
      CACHE_ERROR: 'We encountered a temporary issue. Please try again.',
      VALIDATION_ERROR: originalMessage || 'Please check your input and try again.',
      NOT_FOUND: 'The requested resource was not found.',
      UNAUTHORIZED: 'You need to be logged in to access this resource.',
      FORBIDDEN: 'You do not have permission to access this resource.',
      INTERNAL_ERROR: 'An unexpected error occurred. Please try again later.',
    };

    if (errorCode && errorMessages[errorCode]) {
      return errorMessages[errorCode];
    }

    return originalMessage || 'An unexpected error occurred. Please try again.';
  };

  const friendlyMessage = getFriendlyMessage(code, message);

  // Determine if error is retryable
  const isRetryable = onRetry && (
    code === 'LLM_TIMEOUT' ||
    code === 'LLM_ERROR' ||
    code === 'DATABASE_ERROR' ||
    code === 'CACHE_ERROR' ||
    !code // Network errors and unknown errors are retryable
  );

  return (
    <Card className={`border-red-200 bg-red-50 ${className}`}>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-red-700">
          <AlertCircle className="h-5 w-5" />
          <span>Error</span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-red-600">{friendlyMessage}</p>
        {process.env.NODE_ENV === 'development' && code && (
          <p className="mt-2 text-xs text-red-500 font-mono">
            Error Code: {code}
          </p>
        )}
      </CardContent>
      {isRetryable && (
        <CardFooter>
          <Button onClick={onRetry} variant="outline" size="sm" className="text-red-700 border-red-300 hover:bg-red-100">
            Try Again
          </Button>
        </CardFooter>
      )}
    </Card>
  );
}

/**
 * Inline error message component for smaller error displays
 */
export function InlineErrorMessage({ error, className = '' }: { error: string; className?: string }) {
  return (
    <div className={`flex items-center gap-2 text-sm text-red-600 ${className}`}>
      <AlertCircle className="h-4 w-4" />
      <span>{error}</span>
    </div>
  );
}
