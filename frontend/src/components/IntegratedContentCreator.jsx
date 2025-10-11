import React, { useState, useEffect } from 'react';
import { api } from '../utils/api';

const IntegratedContentCreator = () => {
  const [formData, setFormData] = useState({
    title: '',
    intro: '',
    content_type: 'blog_post',
    body: [],
    forum_enabled: true,
    forum_id: '',
    forum_topic_title: '',
    forum_discussion_intro: '',
    enable_rich_content: true,
    trust_level_required: 0,
    ai_generated: false,
    ai_summary: ''
  });
  
  const [forums, setForums] = useState([]);
  const [userPermissions, setUserPermissions] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [bodyBlocks, setBodyBlocks] = useState([
    { type: 'paragraph', value: '' }
  ]);

  // Load available forums and user permissions
  useEffect(() => {
    loadForums();
    loadUserPermissions();
  }, []);

  const loadForums = async () => {
    try {
      const response = await api.get('/api/v1/integrated-content/forums/');
      setForums(response.data.forums || []);
    } catch (error) {
      console.error('Failed to load forums:', error);
    }
  };

  const loadUserPermissions = async () => {
    try {
      const response = await api.get('/api/v1/integrated-content/permissions/');
      setUserPermissions(response.data);
    } catch (error) {
      console.error('Failed to load permissions:', error);
    }
  };

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const addBodyBlock = (blockType = 'paragraph') => {
    const newBlock = {
      type: blockType,
      value: blockType === 'code' ? { language: 'python', code: '', caption: '' } : ''
    };
    setBodyBlocks([...bodyBlocks, newBlock]);
  };

  const updateBodyBlock = (index, value) => {
    const updatedBlocks = [...bodyBlocks];
    updatedBlocks[index].value = value;
    setBodyBlocks(updatedBlocks);
  };

  const removeBodyBlock = (index) => {
    if (bodyBlocks.length > 1) {
      setBodyBlocks(bodyBlocks.filter((_, i) => i !== index));
    }
  };

  const renderBodyBlockEditor = (block, index) => {
    switch (block.type) {
      case 'paragraph':
        return (
          <textarea
            key={index}
            className="w-full p-3 border border-gray-300 rounded-lg resize-vertical min-h-[80px]"
            placeholder="Enter paragraph content..."
            value={block.value}
            onChange={(e) => updateBodyBlock(index, e.target.value)}
          />
        );
      
      case 'heading':
        return (
          <input
            key={index}
            type="text"
            className="w-full p-3 border border-gray-300 rounded-lg text-lg font-semibold"
            placeholder="Enter heading text..."
            value={block.value}
            onChange={(e) => updateBodyBlock(index, e.target.value)}
          />
        );
      
      case 'code':
        return (
          <div key={index} className="space-y-2">
            <select
              className="px-3 py-2 border border-gray-300 rounded-lg"
              value={block.value.language || 'python'}
              onChange={(e) => updateBodyBlock(index, { ...block.value, language: e.target.value })}
            >
              <option value="python">Python</option>
              <option value="javascript">JavaScript</option>
              <option value="html">HTML</option>
              <option value="css">CSS</option>
              <option value="sql">SQL</option>
              <option value="bash">Bash</option>
            </select>
            <textarea
              className="w-full p-3 border border-gray-300 rounded-lg font-mono text-sm bg-gray-50 min-h-[120px]"
              placeholder="Enter code..."
              value={block.value.code || ''}
              onChange={(e) => updateBodyBlock(index, { ...block.value, code: e.target.value })}
            />
            <input
              type="text"
              className="w-full p-2 border border-gray-300 rounded-lg text-sm"
              placeholder="Optional caption..."
              value={block.value.caption || ''}
              onChange={(e) => updateBodyBlock(index, { ...block.value, caption: e.target.value })}
            />
          </div>
        );
      
      default:
        return (
          <div key={index} className="p-3 bg-gray-100 rounded-lg">
            Unsupported block type: {block.type}
          </div>
        );
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      // Prepare the submission data
      const submissionData = {
        ...formData,
        body: bodyBlocks.filter(block => block.value && (
          typeof block.value === 'string' ? block.value.trim() : 
          block.value.code && block.value.code.trim()
        ))
      };

      const response = await api.post('/api/v1/integrated-content/create/', submissionData);
      setResult(response.data);
      
      // Reset form on success
      if (response.data.success) {
        setFormData({
          title: '',
          intro: '',
          content_type: 'blog_post',
          body: [],
          forum_enabled: true,
          forum_id: '',
          forum_topic_title: '',
          forum_discussion_intro: '',
          enable_rich_content: true,
          trust_level_required: 0,
          ai_generated: false,
          ai_summary: ''
        });
        setBodyBlocks([{ type: 'paragraph', value: '' }]);
      }
    } catch (error) {
      console.error('Submission error:', error);
      setError(error.response?.data || { error: 'Failed to create content' });
    } finally {
      setLoading(false);
    }
  };

  const canCreateContent = userPermissions?.permissions?.create_blog_post || userPermissions?.permissions?.create_integrated_content;

  return (
    <div className="max-w-4xl mx-auto p-6 bg-white rounded-lg shadow-lg">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          🚀 Integrated Content Creator
        </h1>
        <p className="text-gray-600">
          Create content that publishes to both Wagtail CMS and forum discussions
        </p>
      </div>

      {/* User Permissions Info */}
      {userPermissions && (
        <div className="mb-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
          <h3 className="font-semibold text-blue-900 mb-2">
            Your Permissions (Trust Level {userPermissions.trust_level})
          </h3>
          <div className="grid grid-cols-2 gap-2 text-sm">
            <div className={`flex items-center ${userPermissions.permissions.create_blog_post ? 'text-green-700' : 'text-red-700'}`}>
              {userPermissions.permissions.create_blog_post ? '✅' : '❌'} Create Blog Posts
            </div>
            <div className={`flex items-center ${userPermissions.permissions.create_forum_topic ? 'text-green-700' : 'text-red-700'}`}>
              {userPermissions.permissions.create_forum_topic ? '✅' : '❌'} Create Forum Topics
            </div>
            <div className={`flex items-center ${userPermissions.permissions.create_integrated_content ? 'text-green-700' : 'text-red-700'}`}>
              {userPermissions.permissions.create_integrated_content ? '✅' : '❌'} Create Integrated Content
            </div>
            <div className={`flex items-center ${userPermissions.permissions.use_rich_content ? 'text-green-700' : 'text-red-700'}`}>
              {userPermissions.permissions.use_rich_content ? '✅' : '❌'} Use Rich Content
            </div>
          </div>
        </div>
      )}

      {!canCreateContent && (
        <div className="mb-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
          <p className="text-yellow-800">
            ⚠️ You need at least Trust Level 1 to create blog posts or Trust Level 2 for integrated content.
          </p>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Basic Content Fields */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Title *
            </label>
            <input
              type="text"
              name="title"
              required
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="Enter content title..."
              value={formData.title}
              onChange={handleInputChange}
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Content Type *
            </label>
            <select
              name="content_type"
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              value={formData.content_type}
              onChange={handleInputChange}
            >
              <option value="blog_post">Blog Post (with optional forum discussion)</option>
              <option value="forum_topic">Forum Topic (rich content)</option>
            </select>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Introduction/Summary
          </label>
          <textarea
            name="intro"
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-vertical"
            rows="3"
            placeholder="Brief introduction or summary..."
            value={formData.intro}
            onChange={handleInputChange}
          />
        </div>

        {/* Body Content Editor */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Content Body
          </label>
          <div className="space-y-4">
            {bodyBlocks.map((block, index) => (
              <div key={index} className="relative border border-gray-200 rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <select
                    className="px-3 py-1 text-sm border border-gray-300 rounded"
                    value={block.type}
                    onChange={(e) => {
                      const newBlocks = [...bodyBlocks];
                      newBlocks[index] = { 
                        type: e.target.value, 
                        value: e.target.value === 'code' ? { language: 'python', code: '', caption: '' } : ''
                      };
                      setBodyBlocks(newBlocks);
                    }}
                  >
                    <option value="paragraph">Paragraph</option>
                    <option value="heading">Heading</option>
                    <option value="code">Code Block</option>
                  </select>
                  
                  {bodyBlocks.length > 1 && (
                    <button
                      type="button"
                      onClick={() => removeBodyBlock(index)}
                      className="text-red-600 hover:text-red-800 text-sm"
                    >
                      ✕ Remove
                    </button>
                  )}
                </div>
                {renderBodyBlockEditor(block, index)}
              </div>
            ))}
            
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => addBodyBlock('paragraph')}
                className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg text-sm"
              >
                + Paragraph
              </button>
              <button
                type="button"
                onClick={() => addBodyBlock('heading')}
                className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg text-sm"
              >
                + Heading
              </button>
              <button
                type="button"
                onClick={() => addBodyBlock('code')}
                className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg text-sm"
              >
                + Code Block
              </button>
            </div>
          </div>
        </div>

        {/* Forum Integration Settings */}
        {formData.content_type === 'blog_post' && (
          <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
            <h3 className="text-lg font-medium text-gray-900 mb-4">
              🗣️ Forum Discussion Settings
            </h3>
            
            <div className="space-y-4">
              <div className="flex items-center">
                <input
                  type="checkbox"
                  name="forum_enabled"
                  id="forum_enabled"
                  className="mr-3"
                  checked={formData.forum_enabled}
                  onChange={handleInputChange}
                />
                <label htmlFor="forum_enabled" className="text-sm font-medium text-gray-700">
                  Create forum discussion for this blog post
                </label>
              </div>

              {formData.forum_enabled && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Discussion Forum (Optional)
                    </label>
                    <select
                      name="forum_id"
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg"
                      value={formData.forum_id}
                      onChange={handleInputChange}
                    >
                      <option value="">Auto-select (Blog Discussions)</option>
                      {forums.map(forum => (
                        <option key={forum.id} value={forum.id}>
                          {forum.category?.name && `${forum.category.name} > `}{forum.name}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Forum Topic Title (Optional)
                    </label>
                    <input
                      type="text"
                      name="forum_topic_title"
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg"
                      placeholder="Defaults to blog post title"
                      value={formData.forum_topic_title}
                      onChange={handleInputChange}
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Discussion Introduction (Optional)
                    </label>
                    <textarea
                      name="forum_discussion_intro"
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg"
                      rows="2"
                      placeholder="Custom introduction for the forum discussion..."
                      value={formData.forum_discussion_intro}
                      onChange={handleInputChange}
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Minimum Trust Level for Discussion
                    </label>
                    <select
                      name="trust_level_required"
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg"
                      value={formData.trust_level_required}
                      onChange={handleInputChange}
                    >
                      <option value={0}>TL0 - Everyone</option>
                      <option value={1}>TL1 - Basic Users</option>
                      <option value={2}>TL2 - Members</option>
                      <option value={3}>TL3 - Regular Users</option>
                      <option value={4}>TL4 - Leaders</option>
                    </select>
                  </div>

                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      name="enable_rich_content"
                      id="enable_rich_content"
                      className="mr-3"
                      checked={formData.enable_rich_content}
                      onChange={handleInputChange}
                    />
                    <label htmlFor="enable_rich_content" className="text-sm font-medium text-gray-700">
                      Use rich content in forum post (includes code blocks, etc.)
                    </label>
                  </div>
                </>
              )}
            </div>
          </div>
        )}

        {/* Forum Topic Settings */}
        {formData.content_type === 'forum_topic' && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Target Forum *
            </label>
            <select
              name="forum_id"
              required
              className="w-full px-4 py-3 border border-gray-300 rounded-lg"
              value={formData.forum_id}
              onChange={handleInputChange}
            >
              <option value="">Select a forum...</option>
              {forums.map(forum => (
                <option key={forum.id} value={forum.id}>
                  {forum.category?.name && `${forum.category.name} > `}{forum.name}
                </option>
              ))}
            </select>
          </div>
        )}

        {/* Submit Button */}
        <div className="flex justify-end pt-6 border-t border-gray-200">
          <button
            type="submit"
            disabled={loading || !canCreateContent}
            className={`px-8 py-3 text-white font-medium rounded-lg transition-colors ${
              loading || !canCreateContent
                ? 'bg-gray-400 cursor-not-allowed'
                : 'bg-blue-600 hover:bg-blue-700 focus:ring-2 focus:ring-blue-500'
            }`}
          >
            {loading ? (
              <span className="flex items-center">
                <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Creating...
              </span>
            ) : (
              `Create ${formData.content_type === 'blog_post' ? 'Blog Post' : 'Forum Topic'}`
            )}
          </button>
        </div>
      </form>

      {/* Results Display */}
      {result && (
        <div className="mt-6 p-4 bg-green-50 border border-green-200 rounded-lg">
          <h3 className="text-lg font-medium text-green-900 mb-2">
            ✅ Content Created Successfully!
          </h3>
          {result.blog_post && (
            <div className="mb-3">
              <p className="text-sm text-green-800">
                <strong>Blog Post:</strong> {result.blog_post.title}
              </p>
              <p className="text-xs text-green-600">
                URL: {result.blog_post.url}
              </p>
            </div>
          )}
          {result.forum_topic && (
            <div>
              <p className="text-sm text-green-800">
                <strong>Forum Discussion:</strong> {result.forum_topic.title}
              </p>
              <p className="text-xs text-green-600">
                Forum: {result.forum_topic.forum_name}
              </p>
              {result.forum_topic.url && (
                <p className="text-xs text-green-600">
                  Discussion URL: {result.forum_topic.url}
                </p>
              )}
            </div>
          )}
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-lg">
          <h3 className="text-lg font-medium text-red-900 mb-2">
            ❌ Error Creating Content
          </h3>
          <p className="text-sm text-red-800 mb-2">
            {error.error || 'An unexpected error occurred'}
          </p>
          {error.permissions && (
            <div className="text-xs text-red-600">
              <p>Required permissions:</p>
              <ul className="list-disc list-inside ml-2">
                {Object.entries(error.permissions.requirements || {}).map(([action, level]) => (
                  <li key={action}>
                    {action.replace('_', ' ')}: Trust Level {level}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default IntegratedContentCreator;