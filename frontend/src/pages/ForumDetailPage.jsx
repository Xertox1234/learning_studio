import React, { useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { ChevronRight, MessageSquare, Eye, Clock, Plus, Search, Filter } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { useTheme } from '../contexts/ThemeContext';
import { useForumDetail, useForumTopics } from '../hooks/useForumQuery';

export default function ForumDetailPage() {
  const { forumSlug, forumId } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const { theme } = useTheme();
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState('last_post_on'); // last_post_on, created, replies, views

  // Fetch forum details and topics with React Query
  const { data: forum, isLoading: loadingForum, error: forumError } = useForumDetail(forumSlug);
  const { data: topicsData, isLoading: loadingTopics } = useForumTopics(forumSlug, { page: 1, page_size: 100 });

  const topics = topicsData?.results || [];
  const loading = loadingForum || loadingTopics;
  const error = forumError?.message || null;

  const handleCreateTopic = () => {
    navigate(`/forum/topics/create?forum=${forumId}`);
  };

  const filteredAndSortedTopics = topics
    .filter(topic => 
      topic.subject.toLowerCase().includes(searchTerm.toLowerCase())
    )
    .sort((a, b) => {
      switch (sortBy) {
        case 'created':
          return new Date(b.created) - new Date(a.created);
        case 'replies':
          return b.posts_count - a.posts_count;
        case 'views':
          return b.views_count - a.views_count;
        case 'last_post_on':
        default:
          return new Date(b.last_post_on || b.created) - new Date(a.last_post_on || a.created);
      }
    });

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInHours = (now - date) / (1000 * 60 * 60);

    if (diffInHours < 24) {
      return `${Math.floor(diffInHours)}h ago`;
    } else if (diffInHours < 24 * 7) {
      return `${Math.floor(diffInHours / 24)}d ago`;
    } else {
      return date.toLocaleDateString();
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        <div className="max-w-7xl mx-auto px-4 py-8">
          <div className="animate-pulse">
            <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-64 mb-4"></div>
            <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-96 mb-8"></div>
            <div className="space-y-4">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="h-16 bg-gray-200 dark:bg-gray-700 rounded"></div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        <div className="max-w-7xl mx-auto px-4 py-8">
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-red-800 dark:text-red-200 mb-2">Error Loading Forum</h3>
            <p className="text-red-600 dark:text-red-300">{error}</p>
            <div className="flex space-x-3 mt-4">
              <button
                onClick={() => window.location.reload()}
                className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
              >
                Try Again
              </button>
              <Link
                to="/forum"
                className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700 transition-colors"
              >
                Back to Forums
              </Link>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!forum) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        <div className="max-w-7xl mx-auto px-4 py-8">
          <div className="text-center">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">Forum Not Found</h2>
            <Link 
              to="/forum" 
              className="text-blue-600 dark:text-blue-400 hover:underline"
            >
              Return to Forums
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Breadcrumb */}
        <nav className="flex items-center space-x-2 text-sm text-gray-600 dark:text-gray-400 mb-6">
          <Link to="/forum" className="hover:text-gray-900 dark:hover:text-white">
            Forums
          </Link>
          <ChevronRight className="w-4 h-4" />
          <span className="text-gray-900 dark:text-white font-medium">{forum.name}</span>
        </nav>

        {/* Forum Header */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6 mb-6">
          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
                {forum.name}
              </h1>
              {forum.description && (
                <p className="text-gray-600 dark:text-gray-400 mb-4">
                  {forum.description}
                </p>
              )}
              <div className="flex items-center space-x-6 text-sm text-gray-500 dark:text-gray-400">
                <div className="flex items-center space-x-1">
                  <MessageSquare className="w-4 h-4" />
                  <span>{forum.topics_count} topics</span>
                </div>
                <div className="flex items-center space-x-1">
                  <span>{forum.posts_count} posts</span>
                </div>
              </div>
            </div>
            {user && (
              <button
                onClick={handleCreateTopic}
                className="flex items-center space-x-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
              >
                <Plus className="w-4 h-4" />
                <span>New Topic</span>
              </button>
            )}
          </div>
        </div>

        {/* Search and Filter Controls */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-4 mb-6">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <input
                type="text"
                placeholder="Search topics..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            <div className="flex items-center space-x-2">
              <Filter className="w-4 h-4 text-gray-400" />
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="last_post_on">Latest Activity</option>
                <option value="created">Date Created</option>
                <option value="replies">Most Replies</option>
                <option value="views">Most Views</option>
              </select>
            </div>
          </div>
        </div>

        {/* Topics List */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
          {filteredAndSortedTopics.length === 0 ? (
            <div className="p-8 text-center">
              <MessageSquare className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                {searchTerm ? 'No topics found' : 'No topics yet'}
              </h3>
              <p className="text-gray-600 dark:text-gray-400 mb-6">
                {searchTerm 
                  ? 'Try adjusting your search terms or filters.'
                  : 'Be the first to start a discussion in this forum!'
                }
              </p>
              {user && !searchTerm && (
                <button
                  onClick={handleCreateTopic}
                  className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors"
                >
                  Create First Topic
                </button>
              )}
            </div>
          ) : (
            <div className="divide-y divide-gray-200 dark:divide-gray-700">
              {filteredAndSortedTopics.map((topic) => (
                <div key={topic.id} className="p-6 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors">
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <Link
                        to={`/forum/topics/${forum.slug}/${forum.id}/${topic.slug}/${topic.id}`}
                        className="text-lg font-semibold text-gray-900 dark:text-white hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
                      >
                        {topic.subject}
                      </Link>
                      <div className="flex items-center space-x-4 mt-2 text-sm text-gray-500 dark:text-gray-400">
                        <span>by {topic.poster.display_name || topic.poster.username}</span>
                        <span>•</span>
                        <div className="flex items-center space-x-1">
                          <Clock className="w-3 h-3" />
                          <span>{formatDate(topic.created)}</span>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center space-x-6 ml-4">
                      {/* Stats */}
                      <div className="text-center">
                        <div className="flex items-center space-x-1 text-sm text-gray-500 dark:text-gray-400">
                          <MessageSquare className="w-3 h-3" />
                          <span>{topic.posts_count - 1}</span>
                        </div>
                        <span className="text-xs text-gray-400">replies</span>
                      </div>
                      <div className="text-center">
                        <div className="flex items-center space-x-1 text-sm text-gray-500 dark:text-gray-400">
                          <Eye className="w-3 h-3" />
                          <span>{topic.views_count}</span>
                        </div>
                        <span className="text-xs text-gray-400">views</span>
                      </div>

                      {/* Last Post */}
                      {topic.last_post && (
                        <div className="text-right min-w-0">
                          <div className="text-sm text-gray-900 dark:text-white">
                            {topic.last_post.poster.display_name || topic.last_post.poster.username}
                          </div>
                          <div className="text-xs text-gray-500 dark:text-gray-400">
                            {formatDate(topic.last_post_on)}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Forum Stats */}
        <div className="mt-6 bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-4">
          <div className="flex justify-between items-center text-sm text-gray-600 dark:text-gray-400">
            <span>
              Showing {filteredAndSortedTopics.length} of {topics.length} topics
            </span>
            <span>
              {forum.topics_count} topics • {forum.posts_count} posts
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}