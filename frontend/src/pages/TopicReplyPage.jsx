import React, { useState, useEffect } from 'react';
import { useNavigate, useParams, Link } from 'react-router-dom';
import { ChevronRight, AlertCircle, MessageSquare } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { useTheme } from '../contexts/ThemeContext';
import { apiRequest } from '../utils/api';

export default function TopicReplyPage() {
  const navigate = useNavigate();
  const { forumSlug, forumId, topicSlug, topicId } = useParams();
  const { user } = useAuth();
  const { theme } = useTheme();
  
  const [topic, setTopic] = useState(null);
  const [content, setContent] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [loadingTopic, setLoadingTopic] = useState(true);

  useEffect(() => {
    fetchTopic();
  }, [forumSlug, forumId, topicSlug, topicId]);

  const fetchTopic = async () => {
    try {
      const response = await apiRequest(
        `/api/v1/forums/${forumSlug}/${forumId}/topics/${topicSlug}/${topicId}/`
      );
      
      if (!response.ok) {
        throw new Error(`Failed to fetch topic: ${response.status}`);
      }
      
      const data = await response.json();
      setTopic(data);
    } catch (err) {
      setError(`Failed to load topic: ${err.message}`);
    } finally {
      setLoadingTopic(false);
    }
  };

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
      
      if (data.success) {
        // Navigate back to the topic page
        navigate(`/forum/topics/${forumSlug}/${forumId}/${topicSlug}/${topicId}`);
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

  if (loadingTopic) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        <div className="max-w-4xl mx-auto px-4 py-8">
          <div className="animate-pulse">
            <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-64 mb-8"></div>
            <div className="space-y-4">
              <div className="h-12 bg-gray-200 dark:bg-gray-700 rounded"></div>
              <div className="h-64 bg-gray-200 dark:bg-gray-700 rounded"></div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error && !topic) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold mb-4">Topic Not Found</h1>
          <p className="text-gray-600 dark:text-gray-400 mb-4">{error}</p>
          <Link
            to="/forum"
            className="btn-primary inline-flex items-center space-x-2"
          >
            <span>Back to Forums</span>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* Breadcrumb */}
        <nav className="flex items-center space-x-2 text-sm text-gray-600 dark:text-gray-400 mb-6">
          <Link to="/forum" className="hover:text-gray-900 dark:hover:text-white">
            Forums
          </Link>
          <ChevronRight className="w-4 h-4" />
          <Link 
            to={`/forum/${forumSlug}/${forumId}`} 
            className="hover:text-gray-900 dark:hover:text-white"
          >
            {topic?.forum?.name || 'Forum'}
          </Link>
          <ChevronRight className="w-4 h-4" />
          <Link 
            to={`/forum/topics/${forumSlug}/${forumId}/${topicSlug}/${topicId}`}
            className="hover:text-gray-900 dark:hover:text-white"
          >
            {topic?.subject || 'Topic'}
          </Link>
          <ChevronRight className="w-4 h-4" />
          <span className="text-gray-900 dark:text-white font-medium">Reply</span>
        </nav>

        {/* Reply Form */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
          <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center space-x-2">
              <MessageSquare className="w-6 h-6" />
              <span>Reply to: {topic?.subject}</span>
            </h1>
          </div>

          <form onSubmit={handleSubmit} className="p-6 space-y-6">
            {error && (
              <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
                <div className="flex items-start space-x-3">
                  <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
                  <p className="text-sm text-red-800 dark:text-red-200">{error}</p>
                </div>
              </div>
            )}

            {/* Content */}
            <div>
              <label htmlFor="content" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Your Reply <span className="text-red-500">*</span>
              </label>
              <textarea
                id="content"
                value={content}
                onChange={(e) => setContent(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                rows="10"
                placeholder="Write your reply here..."
                disabled={loading}
              />
              <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">
                You can use Markdown for formatting.
              </p>
            </div>

            {/* Form Actions */}
            <div className="flex items-center justify-between">
              <Link
                to={`/forum/topics/${forumSlug}/${forumId}/${topicSlug}/${topicId}`}
                className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white transition-colors"
              >
                Cancel
              </Link>
              <div className="flex items-center space-x-3">
                <button
                  type="submit"
                  disabled={loading}
                  className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
                >
                  <MessageSquare className="w-4 h-4" />
                  <span>{loading ? 'Posting...' : 'Post Reply'}</span>
                </button>
              </div>
            </div>
          </form>
        </div>

        {/* Help Text */}
        <div className="mt-6 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-blue-900 dark:text-blue-200 mb-2">
            Reply Guidelines
          </h3>
          <ul className="text-sm text-blue-800 dark:text-blue-300 space-y-1">
            <li>• Stay on topic and be constructive</li>
            <li>• Quote specific parts if replying to a particular point</li>
            <li>• Be respectful of other users' opinions</li>
            <li>• Include code examples when relevant</li>
          </ul>
        </div>
      </div>
    </div>
  );
}