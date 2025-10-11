import React from 'react';
import IntegratedContentCreator from '../components/IntegratedContentCreator';

const IntegratedContentDemo = () => {
  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-6xl mx-auto px-4">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            🚀 Wagtail-Forum Integration Demo
          </h1>
          <p className="text-lg text-gray-600 max-w-3xl mx-auto">
            This demo showcases the new integrated content creation system that allows publishing 
            to both Wagtail CMS and forum discussions simultaneously. Create rich blog posts that 
            automatically generate forum topics for community discussion, or create rich forum 
            topics with enhanced content blocks.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          <div className="bg-white p-6 rounded-lg shadow-lg">
            <div className="text-3xl mb-3">📝</div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              Blog Posts with Discussions
            </h3>
            <p className="text-gray-600 text-sm">
              Create blog posts that automatically generate forum topics for community discussion. 
              Uses StreamField blocks for rich content.
            </p>
          </div>

          <div className="bg-white p-6 rounded-lg shadow-lg">
            <div className="text-3xl mb-3">🗣️</div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              Rich Forum Topics
            </h3>
            <p className="text-gray-600 text-sm">
              Create forum topics with rich content blocks including code snippets, 
              images, and formatted text beyond basic markdown.
            </p>
          </div>

          <div className="bg-white p-6 rounded-lg shadow-lg">
            <div className="text-3xl mb-3">🔒</div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              Trust Level Permissions
            </h3>
            <p className="text-gray-600 text-sm">
              Content creation is gated by trust levels. Higher trust levels unlock 
              more features like integrated content and rich formatting.
            </p>
          </div>
        </div>

        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 mb-8">
          <h3 className="text-lg font-semibold text-blue-900 mb-3">
            ℹ️ Implementation Features
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-blue-800">
            <div>
              <h4 className="font-medium mb-2">✅ Completed Features:</h4>
              <ul className="list-disc list-inside space-y-1">
                <li>ForumIntegratedBlogPage model</li>
                <li>Bidirectional sync (Wagtail ↔ Forum)</li>
                <li>Rich content API service</li>
                <li>Trust level permission system</li>
                <li>Unified content creation endpoints</li>
                <li>StreamField to Markdown conversion</li>
                <li>React component for content creation</li>
              </ul>
            </div>
            <div>
              <h4 className="font-medium mb-2">🎯 Key Capabilities:</h4>
              <ul className="list-disc list-inside space-y-1">
                <li>Automatic forum topic creation</li>
                <li>Rich content with code blocks</li>
                <li>Custom discussion introductions</li>
                <li>Trust level-based permissions</li>
                <li>Forum selection for discussions</li>
                <li>Real-time validation</li>
                <li>Error handling & feedback</li>
              </ul>
            </div>
          </div>
        </div>

        <IntegratedContentCreator />

        <div className="mt-12 p-6 bg-gray-100 rounded-lg">
          <h3 className="text-lg font-semibold text-gray-900 mb-3">
            🔧 Technical Implementation
          </h3>
          <div className="text-sm text-gray-700 space-y-2">
            <p>
              <strong>Backend:</strong> Django models extend BlogPage with forum integration fields. 
              ForumContentService handles unified content creation with automatic topic generation.
            </p>
            <p>
              <strong>API:</strong> REST endpoints at <code className="bg-gray-200 px-1 rounded">/api/v1/integrated-content/</code> 
              provide CRUD operations, permission checking, and forum management.
            </p>
            <p>
              <strong>Frontend:</strong> React components with real-time validation, rich content editing, 
              and responsive design using Tailwind CSS.
            </p>
            <p>
              <strong>Security:</strong> Trust level-based permissions with rate limiting and CSRF protection.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default IntegratedContentDemo;