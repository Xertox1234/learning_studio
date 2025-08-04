import React, { useState } from 'react';
import { MessageSquare, AlertCircle, Send } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { apiRequest } from '../../utils/api';

export default function PostCreateForm({ 
  topicId, 
  onReplyCreated, 
  placeholder = "Write your reply here...",
  buttonText = "Post Reply",
  showCancel = false,
  onCancel
}) {
  const { user } = useAuth();
  const [content, setContent] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    if (!content.trim()) {
      setError('Please enter your reply content');
      return;
    }

    try {
      setLoading(true);
      
      const response = await apiRequest('/api/v1/posts/create/', {
        method: 'POST',
        body: JSON.stringify({
          topic_id: topicId,
          content: content.trim(),
          enable_signature: true
        })
      });

      if (!response.ok) {
        const errorText = await response.text();
        try {
          const errorData = JSON.parse(errorText);
          throw new Error(errorData.error || errorData.message || 'Failed to create reply');
        } catch (parseError) {
          throw new Error(`Server error (${response.status}): ${errorText}`);
        }
      }

      const data = await response.json();
      
      if (data.success && data.post) {
        setContent(''); // Clear the form
        if (onReplyCreated) {
          onReplyCreated(data.post);
        }
      } else {
        throw new Error('Reply creation failed');
      }
    } catch (err) {
      console.error('Reply creation error:', err);
      setError(err.message || 'Failed to create reply. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const getDisplayName = (user) => {
    if (user.first_name || user.last_name) {
      return `${user.first_name || ''} ${user.last_name || ''}`.trim();
    }
    return user.username;
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
      <div className="flex items-start space-x-4">
        {/* User Avatar */}
        <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center flex-shrink-0">
          <span className="text-sm font-medium">
            {getDisplayName(user)[0].toUpperCase()}
          </span>
        </div>

        {/* Reply Form */}
        <form onSubmit={handleSubmit} className="flex-1 space-y-4">
          {error && (
            <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3">
              <div className="flex items-start space-x-2">
                <AlertCircle className="w-4 h-4 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
                <p className="text-sm text-red-800 dark:text-red-200">{error}</p>
              </div>
            </div>
          )}

          <div>
            <label htmlFor="reply-content" className="sr-only">
              Reply content
            </label>
            <textarea
              id="reply-content"
              value={content}
              onChange={(e) => setContent(e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
              rows="4"
              placeholder={placeholder}
              disabled={loading}
            />
            <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
              You can use Markdown for formatting.
            </p>
          </div>

          <div className="flex items-center justify-between">
            <div className="text-sm text-gray-500 dark:text-gray-400">
              Posting as <strong>{getDisplayName(user)}</strong>
            </div>
            <div className="flex items-center space-x-3">
              {showCancel && (
                <button
                  type="button"
                  onClick={onCancel}
                  className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white transition-colors"
                  disabled={loading}
                >
                  Cancel
                </button>
              )}
              <button
                type="submit"
                disabled={loading || !content.trim()}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
              >
                <Send className="w-4 h-4" />
                <span>{loading ? 'Posting...' : buttonText}</span>
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}