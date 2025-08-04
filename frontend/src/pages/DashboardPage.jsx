import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  BookOpen, 
  MessageSquare, 
  Trophy, 
  Users, 
  TrendingUp, 
  Clock,
  Eye,
  ArrowRight,
  Activity,
  Star,
  Target
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { useTheme } from '../contexts/ThemeContext';
import { apiRequest } from '../utils/api';

export default function DashboardPage() {
  const { user } = useAuth();
  const { theme } = useTheme();
  const [forumStats, setForumStats] = useState(null);
  const [recentTopics, setRecentTopics] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      
      // Fetch forum statistics
      const statsResponse = await apiRequest('/api/v1/dashboard/forum-stats/');
      if (statsResponse.ok) {
        const statsData = await statsResponse.json();
        setForumStats(statsData);
      }

      // Fetch recent topics (using forums endpoint for now)
      const topicsResponse = await apiRequest('/api/v1/forums/');
      if (topicsResponse.ok) {
        const forumsData = await topicsResponse.json();
        // Ensure forumsData is an array
        if (Array.isArray(forumsData)) {
          // Extract recent topics from forums with last_post data
          const topics = forumsData
            .filter(forum => forum.last_post)
            .sort((a, b) => new Date(b.last_post.created) - new Date(a.last_post.created))
            .slice(0, 5)
            .map(forum => ({
              id: forum.last_post.topic.id,
              subject: forum.last_post.topic.subject,
              forum_name: forum.name,
              forum_slug: forum.slug,
              forum_id: forum.id,
              topic_slug: forum.last_post.topic.slug,
              replies: forum.last_post.topic.posts_count - 1,
              views: forum.last_post.topic.views_count,
              last_post: forum.last_post,
              created: forum.last_post.created
            }));
          setRecentTopics(topics);
        } else {
          console.warn('Forums API did not return an array:', forumsData);
          setRecentTopics([]);
        }
      }
    } catch (err) {
      console.error('Failed to fetch dashboard data:', err);
      setError('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const formatTimeAgo = (date) => {
    if (!date) return 'unknown';
    const now = new Date();
    const targetDate = new Date(date);
    const diff = now - targetDate;
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);

    if (days > 0) return `${days}d ago`;
    if (hours > 0) return `${hours}h ago`;
    if (minutes > 0) return `${minutes}m ago`;
    return 'just now';
  };

  const getDisplayName = (user) => {
    if (user.first_name || user.last_name) {
      return `${user.first_name || ''} ${user.last_name || ''}`.trim();
    }
    return user.username;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        <div className="max-w-7xl mx-auto px-4 py-8">
          <div className="animate-pulse space-y-6">
            <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-64"></div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="h-32 bg-gray-200 dark:bg-gray-700 rounded-lg"></div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
            Welcome back, {getDisplayName(user)}!
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Here's what's happening in your learning community
          </p>
        </div>

        {/* Stats Grid */}
        {forumStats && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Total Topics</p>
                  <p className="text-2xl font-bold text-gray-900 dark:text-white">
                    {forumStats.total_topics || 0}
                  </p>
                </div>
                <div className="w-12 h-12 bg-blue-100 dark:bg-blue-900/20 rounded-lg flex items-center justify-center">
                  <MessageSquare className="w-6 h-6 text-blue-600 dark:text-blue-400" />
                </div>
              </div>
            </div>

            <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Total Posts</p>
                  <p className="text-2xl font-bold text-gray-900 dark:text-white">
                    {forumStats.total_posts || 0}
                  </p>
                </div>
                <div className="w-12 h-12 bg-green-100 dark:bg-green-900/20 rounded-lg flex items-center justify-center">
                  <Activity className="w-6 h-6 text-green-600 dark:text-green-400" />
                </div>
              </div>
            </div>

            <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Active Users</p>
                  <p className="text-2xl font-bold text-gray-900 dark:text-white">
                    {forumStats.active_users || 0}
                  </p>
                </div>
                <div className="w-12 h-12 bg-purple-100 dark:bg-purple-900/20 rounded-lg flex items-center justify-center">
                  <Users className="w-6 h-6 text-purple-600 dark:text-purple-400" />
                </div>
              </div>
            </div>

            <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Your Posts</p>
                  <p className="text-2xl font-bold text-gray-900 dark:text-white">
                    {forumStats.user_posts || 0}
                  </p>
                </div>
                <div className="w-12 h-12 bg-orange-100 dark:bg-orange-900/20 rounded-lg flex items-center justify-center">
                  <Star className="w-6 h-6 text-orange-600 dark:text-orange-400" />
                </div>
              </div>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Recent Topics */}
          <div className="lg:col-span-2">
            <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
              <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
                <div className="flex items-center justify-between">
                  <h2 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center space-x-2">
                    <TrendingUp className="w-5 h-5" />
                    <span>Recent Forum Activity</span>
                  </h2>
                  <Link 
                    to="/forum" 
                    className="text-sm text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 flex items-center space-x-1"
                  >
                    <span>View All</span>
                    <ArrowRight className="w-4 h-4" />
                  </Link>
                </div>
              </div>
              <div className="p-6">
                {recentTopics.length > 0 ? (
                  <div className="space-y-4">
                    {recentTopics.map((topic) => (
                      <div key={topic.id} className="flex items-start space-x-4 p-4 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors">
                        <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center flex-shrink-0">
                          <MessageSquare className="w-5 h-5" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <Link 
                            to={`/forum/topics/${topic.forum_slug}/${topic.forum_id}/${topic.topic_slug}/${topic.id}`}
                            className="block"
                          >
                            <p className="font-medium text-gray-900 dark:text-white hover:text-blue-600 dark:hover:text-blue-400 truncate">
                              {topic.subject}
                            </p>
                            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                              in {topic.forum_name} • by {getDisplayName(topic.last_post.poster)}
                            </p>
                            <div className="flex items-center space-x-4 mt-2 text-xs text-gray-500 dark:text-gray-400">
                              <span className="flex items-center space-x-1">
                                <MessageSquare className="w-3 h-3" />
                                <span>{topic.replies} replies</span>
                              </span>
                              <span className="flex items-center space-x-1">
                                <Eye className="w-3 h-3" />
                                <span>{topic.views} views</span>
                              </span>
                              <span className="flex items-center space-x-1">
                                <Clock className="w-3 h-3" />
                                <span>{formatTimeAgo(topic.created)}</span>
                              </span>
                            </div>
                          </Link>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <MessageSquare className="w-12 h-12 text-gray-400 dark:text-gray-600 mx-auto mb-4" />
                    <p className="text-gray-500 dark:text-gray-400">No recent forum activity</p>
                    <Link to="/forum" className="text-blue-600 dark:text-blue-400 hover:underline mt-2 inline-block">
                      Start a discussion
                    </Link>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Quick Actions */}
          <div className="space-y-6">
            <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
              <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center space-x-2">
                  <Target className="w-5 h-5" />
                  <span>Quick Actions</span>
                </h2>
              </div>
              <div className="p-6 space-y-4">
                <Link 
                  to="/forum/topics/create"
                  className="block w-full bg-blue-600 text-white rounded-lg px-4 py-3 text-center font-medium hover:bg-blue-700 transition-colors"
                >
                  Start New Topic
                </Link>
                <Link 
                  to="/forum"
                  className="block w-full bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-white rounded-lg px-4 py-3 text-center font-medium hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
                >
                  Browse Forums
                </Link>
                <Link 
                  to="/courses"
                  className="block w-full bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-white rounded-lg px-4 py-3 text-center font-medium hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
                >
                  Explore Courses
                </Link>
              </div>
            </div>

            {/* Community Stats */}
            <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
              <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center space-x-2">
                  <Trophy className="w-5 h-5" />
                  <span>Community</span>
                </h2>
              </div>
              <div className="p-6">
                {forumStats ? (
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600 dark:text-gray-400">Forums</span>
                      <span className="font-medium text-gray-900 dark:text-white">
                        {forumStats.total_forums || 0}
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600 dark:text-gray-400">Latest Member</span>
                      <span className="font-medium text-gray-900 dark:text-white text-sm">
                        {forumStats.latest_member || 'N/A'}
                      </span>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-4">
                    <p className="text-gray-500 dark:text-gray-400 text-sm">Loading stats...</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}