"""
Template tags for enhanced content rendering in Python Learning Studio.
"""

from django import template
from django.utils.safestring import mark_safe
from ..content_renderer import content_renderer

register = template.Library()


@register.filter
def render_structured_content(content_blocks):
    """
    Template filter to render structured content blocks.
    
    Usage: {{ lesson.structured_content|render_structured_content }}
    """
    if not content_blocks:
        return ""
    
    return content_renderer.render_content_blocks(content_blocks)


@register.filter  
def render_lesson_content(lesson):
    """
    Template filter to render lesson content in the appropriate format.
    
    Usage: {{ lesson|render_lesson_content }}
    """
    if not lesson:
        return ""
    
    if lesson.enable_structured_content and lesson.structured_content:
        return content_renderer.render_content_blocks(lesson.structured_content)
    elif lesson.content_format == 'markdown':
        # Handle markdown rendering if available
        try:
            import markdown
            md = markdown.Markdown(extensions=['fenced_code', 'codehilite', 'tables'])
            return mark_safe(md.convert(lesson.content))
        except ImportError:
            # Fallback to plain text with line breaks
            return mark_safe(lesson.content.replace('\n', '<br>'))
    else:
        # Plain text with line breaks
        return mark_safe(lesson.content.replace('\n', '<br>'))


@register.inclusion_tag('learning/content_blocks/code_example.html', takes_context=True)
def render_code_block(context, code, language='python', title='', filename='', show_line_numbers=True):
    """
    Inclusion tag for rendering individual code blocks.
    
    Usage: {% render_code_block code="print('hello')" language="python" title="Example" %}
    """
    block = {
        'content': code,
        'language': language,
        'title': title,
        'filename': filename,
        'show_line_numbers': show_line_numbers
    }
    
    return {
        'block': block,
        'rendered_content': content_renderer.render_code_example_block(block)
    }


@register.inclusion_tag('learning/content_blocks/note.html')
def render_note(content, title='Note', note_type='info'):
    """
    Inclusion tag for rendering note blocks.
    
    Usage: {% render_note "This is important information" title="Important" note_type="warning" %}
    """
    block = {
        'content': content,
        'title': title,
        'type': note_type
    }
    
    if note_type == 'warning':
        rendered_content = content_renderer.render_warning_block(block)
    elif note_type == 'tip':
        rendered_content = content_renderer.render_tip_block(block)
    else:
        rendered_content = content_renderer.render_note_block(block)
    
    return {
        'block': block,
        'rendered_content': rendered_content
    }


@register.simple_tag
def content_block_css():
    """
    Returns CSS classes and styles for content blocks.
    """
    return mark_safe('''
    <style>
    /* Enhanced Content Block Styling */
    .content-block {
        margin-bottom: 1.5rem;
    }
    
    .lesson-heading {
        position: relative;
        margin-top: 2rem;
        margin-bottom: 1rem;
        color: #e2e8f0;
    }
    
    .heading-anchor {
        position: absolute;
        left: -1.5rem;
        opacity: 0;
        color: #68d391;
        text-decoration: none;
        transition: opacity 0.2s;
    }
    
    .lesson-heading:hover .heading-anchor {
        opacity: 1;
    }
    
    /* Code Example Blocks - Bare Minimum Style with CodeMirror */
    .code-example-block {
        position: relative;
        margin: 1.5rem 0;
    }
    
    .code-wrapper {
        position: relative;
        background: #1e1e1e;
        border-radius: 6px;
        overflow: hidden;
    }
    
    .code-wrapper .cm-editor {
        border: none;
        background: transparent;
    }
    
    .code-wrapper textarea.code-editor {
        width: 100%;
        min-height: 100px;
        background: #1e1e1e;
        color: #d4d4d4;
        border: none;
        padding: 16px;
        font-family: 'Cascadia Code', 'Fira Code', 'JetBrains Mono', monospace;
        font-size: 14px;
        line-height: 1.4;
        resize: none;
        outline: none;
    }
    
    /* Small Copy Button */
    .copy-code-btn {
        position: absolute;
        top: 8px;
        right: 8px;
        background: rgba(45, 55, 72, 0.8);
        border: 1px solid #4a5568;
        color: #a0aec0;
        border-radius: 4px;
        width: 32px;
        height: 32px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 12px;
        cursor: pointer;
        transition: all 0.2s ease;
        z-index: 10;
    }
    
    .copy-code-btn:hover {
        background: #68d391;
        color: #1a202c;
        border-color: #68d391;
    }
    
    .copy-code-btn i {
        font-size: 12px;
    }
    
    /* Interactive Code Blocks */
    .interactive-code-block {
        background: #1e1e1e;
        border: 2px solid #68d391;
        border-radius: 8px;
        overflow: hidden;
        margin: 1.5rem 0;
        box-shadow: 0 4px 12px rgba(104, 211, 145, 0.1);
    }
    
    .interactive-code-header {
        background: #2d3748;
        padding: 12px 16px;
        border-bottom: 1px solid #68d391;
        display: flex;
        justify-content: space-between;
        align-items: center;
        color: #e2e8f0;
        font-size: 0.875rem;
    }
    
    .interactive-code-content {
        position: relative;
        background: #1e1e1e;
    }
    
    .interactive-code-content .cm-editor {
        border: none;
        background: transparent;
    }
    
    .interactive-code-content textarea.interactive-code-editor {
        width: 100%;
        min-height: 120px;
        background: #1e1e1e;
        color: #d4d4d4;
        border: none;
        padding: 16px;
        font-family: 'Cascadia Code', 'Fira Code', 'JetBrains Mono', monospace;
        font-size: 14px;
        line-height: 1.4;
        resize: none;
        outline: none;
    }
    
    .run-code-btn {
        background: #68d391;
        color: #1a202c;
        border: none;
        padding: 6px 12px;
        border-radius: 4px;
        font-size: 0.875rem;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    
    .run-code-btn:hover {
        background: #48bb78;
    }
    
    .run-code-btn i {
        margin-right: 4px;
    }
    
    .expected-output, .code-output {
        background: #2d3748;
        border-top: 1px solid #4a5568;
        padding: 12px 16px;
        color: #cbd5e0;
    }
    
    .expected-output pre, .code-output pre {
        background: #1a202c;
        padding: 8px 12px;
        border-radius: 4px;
        margin: 8px 0 0 0;
        color: #e2e8f0;
        font-family: 'Cascadia Code', 'Fira Code', 'JetBrains Mono', monospace;
        font-size: 13px;
    }
    
    .fill-blank-input {
        background: #2d3748 !important;
        border: 1px solid #68d391 !important;
        color: #e2e8f0 !important;
        padding: 2px 6px !important;
        border-radius: 3px !important;
        font-family: inherit !important;
        font-size: inherit !important;
        min-width: 60px !important;
    }
    
    .exercise-type {
        background: #68d391;
        color: #1a202c;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.75rem;
        margin-left: auto;
    }
    
    .expected-output {
        background: #2d3748;
        padding: 16px;
        border-top: 1px solid #4a5568;
        color: #cbd5e0;
    }
    
    .expected-output pre {
        background: #1a202c;
        padding: 12px;
        border-radius: 4px;
        color: #68d391;
        font-family: monospace;
        margin: 8px 0 0 0;
    }
    
    /* Note Blocks */
    .note-block {
        background: #2d3748;
        border: 1px solid #4a5568;
        border-left: 4px solid #68d391;
        border-radius: 8px;
        padding: 16px;
        margin: 1.5rem 0;
    }
    
    .note-header {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 8px;
        color: #68d391;
        font-weight: 600;
    }
    
    .note-content {
        color: #cbd5e0;
        line-height: 1.6;
    }
    
    /* Warning Blocks */
    .warning-block {
        background: #2d3748;
        border: 1px solid #4a5568;
        border-left: 4px solid #ed8936;
        border-radius: 8px;
        padding: 16px;
        margin: 1.5rem 0;
    }
    
    .warning-header {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 8px;
        color: #ed8936;
        font-weight: 600;
    }
    
    .warning-content {
        color: #cbd5e0;
        line-height: 1.6;
    }
    
    /* Alert Blocks */
    .alert-block {
        border-radius: 8px;
        padding: 16px;
        margin: 1.5rem 0;
        border: 1px solid;
    }
    
    .alert-info {
        background: #2d3748;
        border-color: #63b3ed;
        border-left: 4px solid #63b3ed;
    }
    
    .alert-success {
        background: #2d3748;
        border-color: #68d391;
        border-left: 4px solid #68d391;
    }
    
    .alert-warning {
        background: #2d3748;
        border-color: #ed8936;
        border-left: 4px solid #ed8936;
    }
    
    .alert-danger {
        background: #2d3748;
        border-color: #fc8181;
        border-left: 4px solid #fc8181;
    }
    
    .alert-header {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 8px;
        font-weight: 600;
    }
    
    .alert-info .alert-header { color: #63b3ed; }
    .alert-success .alert-header { color: #68d391; }
    .alert-warning .alert-header { color: #ed8936; }
    .alert-danger .alert-header { color: #fc8181; }
    
    .alert-content {
        color: #cbd5e0;
        line-height: 1.6;
    }
    
    /* Tip Blocks */
    .tip-block {
        background: #2d3748;
        border: 1px solid #4a5568;
        border-left: 4px solid #f6e05e;
        border-radius: 8px;
        padding: 16px;
        margin: 1.5rem 0;
    }
    
    .tip-header {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 8px;
        color: #f6e05e;
        font-weight: 600;
    }
    
    .tip-content {
        color: #cbd5e0;
        line-height: 1.6;
    }
    
    /* Quiz Blocks */
    .quiz-block {
        background: #2d3748;
        border: 1px solid #4a5568;
        border-radius: 8px;
        padding: 16px;
        margin: 1.5rem 0;
    }
    
    .quiz-header {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 16px;
        color: #9f7aea;
        font-weight: 600;
    }
    
    .quiz-question {
        color: #e2e8f0;
        font-weight: 500;
        margin-bottom: 16px;
    }
    
    .quiz-option {
        margin-bottom: 8px;
    }
    
    .quiz-option label {
        color: #cbd5e0;
        cursor: pointer;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    .quiz-option input[type="radio"] {
        accent-color: #68d391;
    }
    
    .quiz-explanation {
        background: #1a202c;
        padding: 12px;
        border-radius: 6px;
        margin-top: 12px;
        color: #cbd5e0;
        border-left: 4px solid #68d391;
    }
    
    /* Image Blocks */
    .image-block {
        text-align: center;
        margin: 1.5rem 0;
    }
    
    .lesson-image {
        max-width: 100%;
        height: auto;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    }
    
    .image-caption {
        margin-top: 8px;
        color: #a0aec0;
        font-style: italic;
        font-size: 0.875rem;
    }
    
    /* Video Blocks */
    .video-block {
        margin: 1.5rem 0;
    }
    
    .video-title {
        color: #e2e8f0;
        margin-bottom: 1rem;
    }
    
    .video-container {
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    }
    
    /* List Blocks */
    .list-block {
        margin: 1.5rem 0;
    }
    
    .list-title {
        color: #e2e8f0;
        margin-bottom: 1rem;
    }
    
    .lesson-list {
        color: #cbd5e0;
        line-height: 1.6;
    }
    
    .lesson-list li {
        margin-bottom: 0.5rem;
    }
    
    /* Table Blocks */
    .table-block {
        margin: 1.5rem 0;
    }
    
    .table-title {
        color: #e2e8f0;
        margin-bottom: 1rem;
    }
    
    .lesson-table {
        background: #2d3748;
        color: #cbd5e0;
        border: 1px solid #4a5568;
    }
    
    .lesson-table th {
        background: #4a5568;
        color: #e2e8f0;
        border-color: #718096;
    }
    
    .lesson-table td {
        border-color: #4a5568;
    }
    
    /* Copy Code Button */
    .copy-code-btn {
        background: #4a5568;
        border: 1px solid #718096;
        color: #e2e8f0;
        padding: 4px 8px;
        border-radius: 4px;
        transition: all 0.2s ease;
    }
    
    .copy-code-btn:hover {
        background: #68d391;
        border-color: #68d391;
        color: #1a202c;
    }
    
    /* Responsive Design */
    @media (max-width: 768px) {
        .code-block-header {
            flex-direction: column;
            align-items: flex-start;
            gap: 8px;
        }
        
        .interactive-code-header {
            flex-direction: column;
            align-items: flex-start;
            gap: 8px;
        }
        
        .exercise-type {
            margin-left: 0;
        }
    }
    </style>
    ''')