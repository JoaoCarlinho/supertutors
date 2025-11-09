/**
 * ValidationTestPanel - Developer utility for testing answer validation
 * Remove or hide this component in production
 */
import React, { useState } from 'react';
import { useActions } from 'kea';
import { conversationLogic } from '../../logic/conversationLogic';
import { Card } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';

export const ValidationTestPanel: React.FC = () => {
  const { validateAnswer } = useActions(conversationLogic);
  const [studentAnswer, setStudentAnswer] = useState('');
  const [expectedAnswer, setExpectedAnswer] = useState('');
  const [context, setContext] = useState('');
  const [isVisible, setIsVisible] = useState(false);

  const handleTest = () => {
    if (!studentAnswer) {
      alert('Please enter a student answer');
      return;
    }

    validateAnswer(studentAnswer, expectedAnswer || undefined, context || undefined);
  };

  const quickTests = [
    {
      name: 'Correct Answer',
      student: '5',
      expected: '5',
      context: 'x + 5 = 10'
    },
    {
      name: 'Equivalent Forms',
      student: '5x',
      expected: '2x + 3x',
      context: 'Simplification'
    },
    {
      name: 'Wrong Answer',
      student: '7',
      expected: '5',
      context: 'x + 5 = 10'
    },
    {
      name: 'Expression Match',
      student: 'x^2 - 1',
      expected: '(x-1)(x+1)',
      context: 'Factoring'
    },
  ];

  // Toggle visibility with keyboard shortcut (Ctrl+Shift+V)
  React.useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      if (e.ctrlKey && e.shiftKey && e.key === 'V') {
        setIsVisible(v => !v);
      }
    };
    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, []);

  if (!isVisible) {
    return (
      <div className="fixed bottom-4 left-4 z-50">
        <Button
          onClick={() => setIsVisible(true)}
          variant="outline"
          size="sm"
          className="bg-purple-100 hover:bg-purple-200 text-purple-900 border-purple-300"
        >
          🧪 Test Validation
        </Button>
      </div>
    );
  }

  return (
    <div className="fixed bottom-4 left-4 z-50 max-w-md">
      <Card className="p-4 bg-purple-50 border-purple-200 shadow-lg">
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-semibold text-purple-900 text-sm flex items-center gap-2">
            <span>🧪</span> Validation Test Panel
          </h3>
          <button
            onClick={() => setIsVisible(false)}
            className="text-purple-400 hover:text-purple-600"
            aria-label="Close"
          >
            ×
          </button>
        </div>

        <div className="space-y-3">
          <div>
            <Label htmlFor="student-answer" className="text-xs text-purple-900">
              Student Answer *
            </Label>
            <Input
              id="student-answer"
              value={studentAnswer}
              onChange={(e) => setStudentAnswer(e.target.value)}
              placeholder="e.g., 5 or x = 5"
              className="text-sm"
            />
          </div>

          <div>
            <Label htmlFor="expected-answer" className="text-xs text-purple-900">
              Expected Answer (optional)
            </Label>
            <Input
              id="expected-answer"
              value={expectedAnswer}
              onChange={(e) => setExpectedAnswer(e.target.value)}
              placeholder="e.g., 5 or 2x + 3x"
              className="text-sm"
            />
          </div>

          <div>
            <Label htmlFor="context" className="text-xs text-purple-900">
              Context (optional)
            </Label>
            <Input
              id="context"
              value={context}
              onChange={(e) => setContext(e.target.value)}
              placeholder="e.g., x + 5 = 10"
              className="text-sm"
            />
          </div>

          <Button
            onClick={handleTest}
            className="w-full bg-purple-600 hover:bg-purple-700"
            size="sm"
          >
            Test Validation
          </Button>

          <div className="border-t border-purple-200 pt-3 mt-3">
            <p className="text-xs text-purple-800 font-medium mb-2">Quick Tests:</p>
            <div className="space-y-1">
              {quickTests.map((test, idx) => (
                <button
                  key={idx}
                  onClick={() => {
                    setStudentAnswer(test.student);
                    setExpectedAnswer(test.expected);
                    setContext(test.context);
                  }}
                  className="w-full text-left text-xs p-2 rounded hover:bg-purple-100 transition-colors"
                >
                  <span className="font-medium text-purple-900">{test.name}</span>
                  <br />
                  <span className="text-purple-600">
                    "{test.student}" vs "{test.expected}"
                  </span>
                </button>
              ))}
            </div>
          </div>

          <p className="text-xs text-purple-700 italic">
            Tip: Press Ctrl+Shift+V to toggle this panel
          </p>
        </div>
      </Card>
    </div>
  );
};
