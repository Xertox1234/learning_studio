import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import { ChevronRight, AlertCircle } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { useTheme } from '../contexts/ThemeContext';
import { apiRequest } from '../utils/api';

export default function TopicCreatePage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const forumId = searchParams.get('forum');
  const { user } = useAuth();
  const { theme } = useTheme();
  
  const [forum, setForum] = useState(null);
  const [subject, setSubject] = useState('');
  const [content, setContent] = useState('');
  const [topicType, setTopicType] = useState('0'); // 0 = Normal topic
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [loadingForum, setLoadingForum] = useState(true);

  useEffect(() => {
    if (forumId) {
      fetchForumInfo();
    } else {
      setLoadingForum(false);
      setError('No forum selected. Please select a forum from the forum list.');
    }
  }, [forumId]);

  const fetchForumInfo = async () => {
    try {
      // For now, we'll just use the forum ID. 
      // In a real implementation, we'd fetch forum details
      setForum({ id: forumId, name: 'Forum' });
      setLoadingForum(false);
    } catch (err) {
      setError('Failed to load forum information');
      setLoadingForum(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    if (!subject.trim()) {
      setError('Please enter a subject');
      return;
    }

    if (!content.trim()) {
      setError('Please enter some content');
      return;
    }

    try {
      setLoading(true);
      
      console.log('Creating topic with data:', {
        forum_id: forumId,
        subject: subject.trim(),
        content: content.trim(),
        topic_type: topicType,
        enable_signature: true
      });
      
      const response = await apiRequest('/api/v1/topics/create/', {
        method: 'POST',
        body: JSON.stringify({
          forum_id: forumId,
          subject: subject.trim(),
          content: content.trim(),
          topic_type: topicType,
          enable_signature: true
        })
      });

      console.log('Topic creation response status:', response.status);
      console.log('Response ok:', response.ok);

      if (!response.ok) {
        const errorText = await response.text();
        console.error('Topic creation error response:', errorText);
        
        try {
          const errorData = JSON.parse(errorText);
          throw new Error(errorData.error || errorData.message || 'Failed to create topic');
        } catch (parseError) {
          throw new Error(`Server error (${response.status}): ${errorText}`);
        }
      }

      const data = await response.json();
      console.log('Topic creation success data:', data);
      
      if (data.success && data.topic) {
        console.log('Navigating to new topic:', `/forum/topics/${data.topic.forum.slug}/${data.topic.forum.id}/${data.topic.slug}/${data.topic.id}`);
        // Navigate to the new topic
        navigate(`/forum/topics/${data.topic.forum.slug}/${data.topic.forum.id}/${data.topic.slug}/${data.topic.id}`);
      } else {
        throw new Error('Topic creation failed - no topic data returned');
      }
    } catch (err) {
      console.error('Topic creation error:', err);
      setError(err.message || 'Failed to create topic. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  if (loadingForum) {
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

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* Breadcrumb */}
        <nav className="flex items-center space-x-2 text-sm text-gray-600 dark:text-gray-400 mb-6">
          <Link to="/forum" className="hover:text-gray-900 dark:hover:text-white">
            Forums
          </Link>
          <ChevronRight className="w-4 h-4" />
          <span className="text-gray-900 dark:text-white font-medium">Create New Topic</span>
        </nav>

        {/* Create Topic Form */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
          <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
              Create New Topic
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

            {/* Subject */}
            <div>
              <label htmlFor="subject" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Subject <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                id="subject"
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Enter a descriptive title for your topic"
                disabled={loading}
              />
            </div>

            {/* Topic Type */}
            <div>
              <label htmlFor="topicType" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Topic Type
              </label>
              <select
                id="topicType"
                value={topicType}
                onChange={(e) => setTopicType(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                disabled={loading}
              >
                <option value="0">Normal Topic</option>
                <option value="1">Sticky</option>
                <option value="2">Announcement</option>
              </select>
            </div>

            {/* Content */}
            <div>
              <label htmlFor="content" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Message <span className="text-red-500">*</span>
              </label>
              <textarea
                id="content"
                value={content}
                onChange={(e) => setContent(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                rows="10"
                placeholder="Write your post content here..."
                disabled={loading}
              />
              <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">
                You can use Markdown for formatting.
              </p>
            </div>

            {/* Form Actions */}
            <div className="flex items-center justify-between">
              <Link
                to="/forum"
                className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white transition-colors"
              >
                Cancel
              </Link>
              <div className="flex items-center space-x-3">
                <button
                  type="submit"
                  disabled={loading}
                  className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loading ? 'Creating...' : 'Create Topic'}
                </button>
              </div>
            </div>
          </form>
        </div>

        {/* Help Text */}
        <div className="mt-6 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-blue-900 dark:text-blue-200 mb-2">
            Posting Guidelines
          </h3>
          <ul className="text-sm text-blue-800 dark:text-blue-300 space-y-1">
            <li>• Be respectful and constructive in your discussions</li>
            <li>• Search before posting to avoid duplicates</li>
            <li>• Use descriptive titles that summarize your topic</li>
            <li>• Include relevant code examples when asking for help</li>
          </ul>
        </div>
      </div>
    </div>
  );
}