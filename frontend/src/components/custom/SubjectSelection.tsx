import React, { useState } from 'react';

interface SubjectSelectionProps {
  imageUrl: string;
  onSubjectSelected: (subject: string) => void;
  onCancel: () => void;
}

type Subject = 'algebra' | 'geometry' | 'arithmetic';

export const SubjectSelection: React.FC<SubjectSelectionProps> = ({
  imageUrl,
  onSubjectSelected,
  onCancel,
}) => {
  const [selectedSubject, setSelectedSubject] = useState<Subject | null>(null);

  const subjects: { value: Subject; label: string; description: string; icon: string }[] = [
    {
      value: 'algebra',
      label: 'Algebra',
      description: 'Equations, expressions, solving for variables',
      icon: '📐',
    },
    {
      value: 'geometry',
      label: 'Geometry',
      description: 'Shapes, angles, area, perimeter, volume',
      icon: '△',
    },
    {
      value: 'arithmetic',
      label: 'Arithmetic',
      description: 'Addition, subtraction, multiplication, division',
      icon: '➕',
    },
  ];

  const handleConfirm = () => {
    if (selectedSubject) {
      onSubjectSelected(selectedSubject);
    }
  };

  return (
    <div
      className="subject-selection p-4"
      role="region"
      aria-label="Subject selection for math problem"
    >
      {/* Image Preview */}
      <div className="mb-4 text-center">
        <p className="text-sm font-medium text-gray-700 mb-2">
          What type of math problem is this?
        </p>
        <img
          src={imageUrl}
          alt="Uploaded"
          className="mx-auto w-48 h-48 object-cover rounded border shadow-sm"
        />
      </div>

      {/* Subject Options */}
      <div className="space-y-2 mb-4">
        {subjects.map((subject) => (
          <button
            key={subject.value}
            onClick={() => setSelectedSubject(subject.value)}
            className={`w-full p-3 border-2 rounded-lg text-left transition-all ${
              selectedSubject === subject.value
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-200 bg-white hover:border-gray-300'
            }`}
            aria-pressed={selectedSubject === subject.value}
          >
            <div className="flex items-start gap-3">
              <span className="text-2xl" role="img" aria-label={subject.label}>
                {subject.icon}
              </span>
              <div className="flex-1">
                <div className="font-medium text-gray-900">{subject.label}</div>
                <div className="text-sm text-gray-600">{subject.description}</div>
              </div>
              {selectedSubject === subject.value && (
                <span className="text-blue-500 text-xl" aria-hidden="true">
                  ✓
                </span>
              )}
            </div>
          </button>
        ))}
      </div>

      {/* Action Buttons */}
      <div className="flex gap-2">
        <button
          onClick={onCancel}
          className="flex-1 px-4 py-2 border border-gray-300 rounded hover:bg-gray-50 transition-colors"
          aria-label="Cancel and choose different image"
        >
          Cancel
        </button>
        <button
          onClick={handleConfirm}
          disabled={!selectedSubject}
          className={`flex-1 px-4 py-2 rounded font-medium transition-colors ${
            selectedSubject
              ? 'bg-blue-600 text-white hover:bg-blue-700'
              : 'bg-gray-200 text-gray-400 cursor-not-allowed'
          }`}
          aria-label="Confirm subject selection and process image"
        >
          Process Image
        </button>
      </div>

      {/* Keyboard Shortcuts */}
      <div className="mt-3 text-xs text-gray-500 text-center">
        Tip: This helps the AI understand your problem better
      </div>
    </div>
  );
};
