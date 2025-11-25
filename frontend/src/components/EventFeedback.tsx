import { useState } from 'react';
import { apiClient } from '../utils/api';

interface EventFeedbackProps {
  eventId: string;
  onFeedbackSubmitted?: () => void;
}

/**
 * EventFeedback - A component for users to provide feedback on event relevance and quality.
 *
 * Feedback is used to improve enrichment algorithms and scoring.
 *
 * Usage:
 * <EventFeedback eventId={event.id} />
 */
export default function EventFeedback({ eventId, onFeedbackSubmitted }: EventFeedbackProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const feedbackOptions = [
    { type: 'relevant', label: 'Relevant', icon: '✓', color: 'text-green-600' },
    { type: 'important', label: 'Important', icon: '⭐', color: 'text-yellow-600' },
    { type: 'irrelevant', label: 'Irrelevant', icon: '✗', color: 'text-gray-600' },
    { type: 'misclassified', label: 'Wrong Category', icon: '⚠', color: 'text-orange-600' },
  ];

  const handleFeedback = async (feedbackType: string) => {
    setIsSubmitting(true);

    try {
      await apiClient.post('/feedback/event', {
        event_id: eventId,
        feedback_type: feedbackType,
      });

      setSubmitted(true);
      setIsOpen(false);

      if (onFeedbackSubmitted) {
        onFeedbackSubmitted();
      }

      // Reset after 3 seconds
      setTimeout(() => setSubmitted(false), 3000);
    } catch (error) {
      console.error('Failed to submit feedback:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  if (submitted) {
    return (
      <div className="inline-flex items-center text-sm text-green-600">
        <svg
          className="w-4 h-4 mr-1"
          fill="currentColor"
          viewBox="0 0 20 20"
        >
          <path
            fillRule="evenodd"
            d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
            clipRule="evenodd"
          />
        </svg>
        Feedback submitted
      </div>
    );
  }

  return (
    <div className="relative inline-block">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="inline-flex items-center text-sm text-gray-600 hover:text-gray-900 focus:outline-none"
        aria-label="Provide feedback"
      >
        <svg
          className="w-4 h-4 mr-1"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z"
          />
        </svg>
        <span className="hidden sm:inline">Feedback</span>
      </button>

      {isOpen && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 z-40"
            onClick={() => setIsOpen(false)}
          />

          {/* Dropdown */}
          <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg z-50 border border-gray-200">
            <div className="py-1">
              <div className="px-4 py-2 text-xs text-gray-500 font-medium">
                How useful is this event?
              </div>

              {feedbackOptions.map((option) => (
                <button
                  key={option.type}
                  onClick={() => handleFeedback(option.type)}
                  disabled={isSubmitting}
                  className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
                >
                  <span className={`mr-2 ${option.color}`}>{option.icon}</span>
                  {option.label}
                </button>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
