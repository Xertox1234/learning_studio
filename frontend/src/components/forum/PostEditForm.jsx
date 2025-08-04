import React, { useState } from 'react';
import { Edit, AlertCircle, Save, X } from 'lucide-react';
import { apiRequest } from '../../utils/api';

export default function PostEditForm({ 
  post, 
  onEditComplete, 
  onCancel 
}) {
  const [content, setContent] = useState(post.content_raw || post.content);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    if (!content.trim()) {
      setError('Please enter post content');
      return;
    }

    try {
      setLoading(true);
      
      const response = await apiRequest(`/api/v1/posts/${post.id}/edit/`, {
        method: 'PATCH',
        body: JSON.stringify({
          content: content.trim(),
          enable_signature: true
        })
      });

      if (!response.ok) {
        const errorText = await response.text();
        try {
          const errorData = JSON.parse(errorText);
          throw new Error(errorData.error || errorData.message || 'Failed to update post');
        } catch (parseError) {
          throw new Error(`Server error (${response.status}): ${errorText}`);
        }
      }

      const data = await response.json();
      
      if (data.success && data.post) {
        if (onEditComplete) {
          onEditComplete(data.post);
        }
      } else {
        throw new Error('Post update failed');
      }
    } catch (err) {
      console.error('Post edit error:', err);
      setError(err.message || 'Failed to update post. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-gray-50 dark:bg-gray-900/50 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
      <div className="flex items-center space-x-2 mb-4">
        <Edit className="w-4 h-4 text-gray-600 dark:text-gray-400" />
        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
          Editing Post
        </span>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        {error && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3">
            <div className="flex items-start space-x-2">
              <AlertCircle className="w-4 h-4 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-red-800 dark:text-red-200">{error}</p>
            </div>
          </div>
        )}

        <div>
          <label htmlFor="edit-content" className="sr-only">
            Post content
          </label>
          <textarea
            id="edit-content"
            value={content}
            onChange={(e) => setContent(e.target.value)}
            className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
            rows="6"
            placeholder="Edit your post content..."
            disabled={loading}
          />
          <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
            You can use Markdown for formatting.
          </p>
        </div>

        <div className="flex items-center justify-end space-x-3">
          <button
            type="button"
            onClick={onCancel}
            className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white transition-colors flex items-center space-x-2"
            disabled={loading}
          >
            <X className="w-4 h-4" />
            <span>Cancel</span>
          </button>
          <button
            type="submit"
            disabled={loading || !content.trim()}
            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
          >
            <Save className="w-4 h-4" />
            <span>{loading ? 'Saving...' : 'Save Changes'}</span>
          </button>
        </div>
      </form>
    </div>
  );
}