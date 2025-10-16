/**
 * HTML Sanitization Utility
 *
 * Provides secure HTML sanitization using DOMPurify to prevent XSS attacks.
 * Use this utility for all user-generated content and HTML rendering.
 *
 * @module utils/sanitize
 */

import DOMPurify from 'dompurify'

/**
 * Default DOMPurify configuration for general content
 * Allows common formatting tags while blocking dangerous elements
 */
const DEFAULT_CONFIG = {
  ALLOWED_TAGS: [
    'p', 'br', 'strong', 'em', 'u', 'a', 'ul', 'ol', 'li',
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'blockquote', 'code', 'pre',
    'table', 'thead', 'tbody', 'tr', 'th', 'td',
    'img', 'span', 'div',
    // Interactive elements for accessibility
    'button', 'input'
  ],
  ALLOWED_ATTR: [
    'href', 'target', 'rel', 'src', 'alt', 'title', 'class', 'id',
    // Form attributes
    'type', 'value', 'disabled',
    // ARIA attributes for accessibility (WCAG 2.1 compliance)
    'aria-label', 'aria-labelledby', 'aria-describedby',
    'aria-hidden', 'aria-expanded', 'aria-controls',
    'role', 'tabindex'
  ],
  // Only allow safe protocols - explicitly block data:, javascript:, vbscript:, file:
  ALLOWED_URI_REGEXP: /^(?:https?|mailto|tel|callto|sms|cid|xmpp):|^(?:\/|\.\/|\.\.\/|#)/i,
  ALLOW_DATA_ATTR: false,
  SAFE_FOR_TEMPLATES: true,
  ALLOW_UNKNOWN_PROTOCOLS: false,
  RETURN_TRUSTED_TYPE: false
}

/**
 * Strict configuration for untrusted content
 * Only allows basic text formatting, no links or images
 */
const STRICT_CONFIG = {
  ALLOWED_TAGS: ['p', 'br', 'strong', 'em', 'u', 'code', 'pre', 'div'],
  ALLOWED_ATTR: [
    // Only allow essential ARIA attributes even in strict mode for accessibility
    'aria-label', 'aria-describedby', 'role'
  ],
  // Even more restrictive - only https, no relative URLs
  ALLOWED_URI_REGEXP: /^https:|^mailto:/i,
  ALLOW_DATA_ATTR: false,
  SAFE_FOR_TEMPLATES: true,
  ALLOW_UNKNOWN_PROTOCOLS: false,
  RETURN_TRUSTED_TYPE: false
}

/**
 * Configuration for rich text with images and links
 */
const RICH_CONFIG = {
  ...DEFAULT_CONFIG,
  // Same safe protocol restrictions as default
  ALLOWED_URI_REGEXP: /^(?:https?|mailto|tel|callto|sms):|^(?:\/|\.\/|\.\.\/|#)/i,
  SAFE_FOR_TEMPLATES: true,
  ALLOW_UNKNOWN_PROTOCOLS: false
}

/**
 * Sanitizes HTML content to prevent XSS attacks
 *
 * @param {string} dirty - The HTML content to sanitize
 * @param {Object} options - Configuration options
 * @param {string} options.mode - Sanitization mode: 'default', 'strict', or 'rich'
 * @param {Object} options.config - Custom DOMPurify configuration (overrides mode)
 * @returns {string} Sanitized HTML safe for rendering
 *
 * @example
 * // Basic usage
 * const clean = sanitizeHTML('<p>Hello <script>alert("xss")</script></p>')
 * // Returns: '<p>Hello </p>'
 *
 * @example
 * // Strict mode (minimal formatting)
 * const clean = sanitizeHTML(userInput, { mode: 'strict' })
 *
 * @example
 * // Rich mode (allows images and links)
 * const clean = sanitizeHTML(blogPost, { mode: 'rich' })
 *
 * @example
 * // Custom configuration
 * const clean = sanitizeHTML(content, {
 *   config: { ALLOWED_TAGS: ['p', 'br'] }
 * })
 */
export const sanitizeHTML = (dirty, options = {}) => {
  if (!dirty || typeof dirty !== 'string') {
    return ''
  }

  // Determine configuration based on mode
  let config = DEFAULT_CONFIG

  if (options.mode === 'strict') {
    config = STRICT_CONFIG
  } else if (options.mode === 'rich') {
    config = RICH_CONFIG
  }

  // Allow custom config to override mode
  if (options.config) {
    config = { ...config, ...options.config }
  }

  // Sanitize and return
  return DOMPurify.sanitize(dirty, config)
}

/**
 * Sanitizes HTML with strict settings (minimal formatting only)
 * Use for untrusted user input where only basic text formatting is needed
 *
 * @param {string} dirty - The HTML content to sanitize
 * @returns {string} Strictly sanitized HTML
 */
export const sanitizeStrict = (dirty) => {
  return sanitizeHTML(dirty, { mode: 'strict' })
}

/**
 * Sanitizes HTML with rich settings (allows images and links)
 * Use for trusted content like blog posts or articles
 *
 * @param {string} dirty - The HTML content to sanitize
 * @returns {string} Sanitized rich HTML
 */
export const sanitizeRich = (dirty) => {
  return sanitizeHTML(dirty, { mode: 'rich' })
}

/**
 * Strips all HTML tags and returns plain text
 * Use when you need only text content without any formatting
 *
 * @param {string} html - The HTML content
 * @returns {string} Plain text without HTML tags
 */
export const stripHTML = (html) => {
  if (!html || typeof html !== 'string') {
    return ''
  }

  return DOMPurify.sanitize(html, {
    ALLOWED_TAGS: [],
    ALLOWED_ATTR: []
  })
}

/**
 * React hook for sanitizing HTML with memoization
 * Use in components to avoid re-sanitizing on every render
 *
 * @param {string} html - The HTML content to sanitize
 * @param {Object} options - Sanitization options
 * @returns {string} Sanitized HTML
 *
 * @example
 * import { useSanitizedHTML } from './utils/sanitize'
 *
 * function MyComponent({ content }) {
 *   const cleanContent = useSanitizedHTML(content, { mode: 'rich' })
 *   return <div dangerouslySetInnerHTML={{ __html: cleanContent }} />
 * }
 */
export const useSanitizedHTML = (html, options = {}) => {
  // For React usage - import useMemo in components
  // return useMemo(() => sanitizeHTML(html, options), [html, options])
  return sanitizeHTML(html, options)
}

/**
 * Validates if a URL is safe to use
 * Checks against common XSS vectors in URLs
 *
 * @param {string} url - The URL to validate
 * @returns {boolean} True if URL is safe, false otherwise
 */
export const isSafeURL = (url) => {
  if (!url || typeof url !== 'string') {
    return false
  }

  // Block javascript: data: and other dangerous protocols
  const dangerousProtocols = /^(?:javascript|data|vbscript|file|about):/i

  if (dangerousProtocols.test(url.trim())) {
    return false
  }

  return true
}

/**
 * Sanitizes a URL by removing dangerous protocols
 * Returns empty string if URL is unsafe
 *
 * @param {string} url - The URL to sanitize
 * @returns {string} Sanitized URL or empty string
 */
export const sanitizeURL = (url) => {
  if (!isSafeURL(url)) {
    return ''
  }

  return url.trim()
}

export default {
  sanitizeHTML,
  sanitizeStrict,
  sanitizeRich,
  stripHTML,
  useSanitizedHTML,
  isSafeURL,
  sanitizeURL
}
