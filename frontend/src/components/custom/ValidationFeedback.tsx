/**
 * ValidationFeedback Component
 * Displays answer validation results with visual feedback
 */
import React, { useEffect } from 'react';
import { useValues, useActions } from 'kea';
import { conversationLogic } from '../../logic/conversationLogic';
import { celebrationLogic } from '../../logic/celebrationLogic';
import { Card } from '../ui/card';
import { CheckCircle2, XCircle, AlertCircle, X } from 'lucide-react';

export const ValidationFeedback: React.FC = () => {
  const { validationResult, validationError, isValidating } = useValues(conversationLogic);
  const { clearValidationResult } = useActions(conversationLogic);
  const { setStreak, incrementStreak, resetStreak } = useActions(celebrationLogic);

  // Update streak when validation result received
  useEffect(() => {
    if (validationResult) {
      if (validationResult.is_correct) {
        incrementStreak();
      } else {
        resetStreak();
      }
      setStreak(validationResult.new_streak);

      // Auto-clear after 10 seconds
      const timer = setTimeout(() => {
        clearValidationResult();
      }, 10000);

      return () => clearTimeout(timer);
    }
  }, [validationResult, clearValidationResult, setStreak, incrementStreak, resetStreak]);

  // Don't render if no validation activity
  if (!isValidating && !validationResult && !validationError) {
    return null;
  }

  return (
    <div
      className="fixed bottom-20 right-4 z-50 max-w-md animate-in slide-in-from-bottom-5"
      role="status"
      aria-live="polite"
      aria-atomic="true"
    >
      {isValidating && (
        <Card className="p-4 bg-blue-50 border-blue-200">
          <div className="flex items-center gap-3">
            <AlertCircle className="w-5 h-5 text-blue-600 animate-pulse" />
            <p className="text-sm text-blue-900 font-medium">
              Validating your answer...
            </p>
          </div>
        </Card>
      )}

      {validationError && (
        <Card className="p-4 bg-red-50 border-red-200">
          <div className="flex items-start gap-3">
            <XCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="text-sm text-red-900 font-medium">
                Validation Error
              </p>
              <p className="text-sm text-red-700 mt-1">
                {validationError}
              </p>
            </div>
            <button
              onClick={clearValidationResult}
              className="text-red-400 hover:text-red-600 transition-colors"
              aria-label="Dismiss error"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </Card>
      )}

      {validationResult && (
        <Card
          className={`p-4 ${
            validationResult.is_correct
              ? 'bg-green-50 border-green-200'
              : 'bg-orange-50 border-orange-200'
          }`}
        >
          <div className="flex items-start gap-3">
            {validationResult.is_correct ? (
              <CheckCircle2 className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
            ) : (
              <XCircle className="w-5 h-5 text-orange-600 flex-shrink-0 mt-0.5" />
            )}
            <div className="flex-1">
              <p
                className={`text-sm font-semibold mb-1 ${
                  validationResult.is_correct
                    ? 'text-green-900'
                    : 'text-orange-900'
                }`}
              >
                {validationResult.is_correct ? 'Correct!' : 'Not Quite'}
              </p>

              {validationResult.validation && (
                <div className="space-y-1 text-sm">
                  <p
                    className={
                      validationResult.is_correct
                        ? 'text-green-800'
                        : 'text-orange-800'
                    }
                  >
                    {validationResult.validation.explanation}
                  </p>

                  {!validationResult.is_correct && (
                    <div className="mt-2 space-y-1">
                      <p className="text-xs text-orange-700">
                        <span className="font-medium">Your answer:</span>{' '}
                        {validationResult.validation.student_answer}
                      </p>
                      <p className="text-xs text-orange-700">
                        <span className="font-medium">Expected:</span>{' '}
                        {validationResult.validation.expected_answer}
                      </p>
                    </div>
                  )}

                  {validationResult.validation.is_approximate && (
                    <p className="text-xs text-green-700 italic mt-1">
                      (Approximately correct)
                    </p>
                  )}
                </div>
              )}

              <div className="mt-2 flex items-center gap-2">
                <span className="text-xs font-medium text-gray-600">
                  Streak: {validationResult.new_streak}
                </span>
                {validationResult.celebration_triggered && (
                  <span className="text-xs bg-yellow-200 text-yellow-900 px-2 py-0.5 rounded-full">
                    🎉 Milestone!
                  </span>
                )}
              </div>
            </div>
            <button
              onClick={clearValidationResult}
              className={
                validationResult.is_correct
                  ? 'text-green-400 hover:text-green-600'
                  : 'text-orange-400 hover:text-orange-600'
              }
              aria-label="Dismiss feedback"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </Card>
      )}
    </div>
  );
};
