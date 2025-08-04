"""
Enhanced content rendering system for Python Learning Studio.
Handles structured content blocks with syntax highlighting and interactive elements.
"""

import re
import json
from typing import List, Dict, Any, Optional
from django.utils.safestring import mark_safe
from django.template.loader import render_to_string

try:
    import markdown
    from markdown.extensions.codehilite import CodeHiliteExtension
    from markdown.extensions.fenced_code import FencedCodeExtension
    MARKDOWN_AVAILABLE = True
except ImportError:
    MARKDOWN_AVAILABLE = False

try:
    from pygments import highlight
    from pygments.lexers import get_lexer_by_name, guess_lexer
    from pygments.formatters import HtmlFormatter
    from pygments.util import ClassNotFound
    PYGMENTS_AVAILABLE = True
except ImportError:
    PYGMENTS_AVAILABLE = False


class ContentBlockRenderer:
    """
    Service for rendering structured content blocks with enhanced formatting.
    """
    
    # Supported content block types
    BLOCK_TYPES = {
        'text': 'render_text_block',
        'heading': 'render_heading_block', 
        'code_example': 'render_code_example_block',
        'interactive_code': 'render_interactive_code_block',
        'note': 'render_note_block',
        'warning': 'render_warning_block',
        'alert': 'render_alert_block',
        'tip': 'render_tip_block',
        'quiz_question': 'render_quiz_block',
        'image': 'render_image_block',
        'video': 'render_video_block',
        'list': 'render_list_block',
        'table': 'render_table_block'
    }
    
    def __init__(self):
        self.markdown_available = MARKDOWN_AVAILABLE
        self.pygments_available = PYGMENTS_AVAILABLE
        
        if self.markdown_available:
            self.markdown = markdown.Markdown(
                extensions=[
                    'fenced_code',
                    'codehilite',
                    'tables',
                    'toc'
                ],
                extension_configs={
                    'codehilite': {
                        'css_class': 'highlight',
                        'use_pygments': True
                    }
                }
            )
    
    def render_content_blocks(self, content_blocks: List[Dict[str, Any]]) -> str:
        """
        Render a list of content blocks to HTML.
        """
        if not isinstance(content_blocks, list):
            return ""
        
        rendered_blocks = []
        
        for block in content_blocks:
            if not isinstance(block, dict) or 'type' not in block:
                continue
                
            block_type = block.get('type')
            renderer_method = self.BLOCK_TYPES.get(block_type)
            
            if renderer_method and hasattr(self, renderer_method):
                try:
                    rendered_html = getattr(self, renderer_method)(block)
                    if rendered_html:
                        rendered_blocks.append(rendered_html)
                except Exception as e:
                    # Fallback for rendering errors
                    rendered_blocks.append(
                        f'<div class="alert alert-danger">Error rendering block: {str(e)}</div>'
                    )
            else:
                # Fallback for unknown block types
                content = block.get('content', '')
                if content:
                    rendered_blocks.append(f'<div class="content-block unknown-type">{content}</div>')
        
        return mark_safe('\n'.join(rendered_blocks))
    
    def render_text_block(self, block: Dict[str, Any]) -> str:
        """Render a text content block."""
        content = block.get('content', '')
        format_type = block.get('format', 'plain')
        
        if format_type == 'markdown' and self.markdown_available:
            content = self.markdown.convert(content)
        else:
            # Convert line breaks for plain text
            content = content.replace('\n', '<br>')
        
        css_classes = ['content-block', 'text-block']
        if block.get('highlight'):
            css_classes.append('highlighted')
        
        return f'<div class="{" ".join(css_classes)}">{content}</div>'
    
    def render_heading_block(self, block: Dict[str, Any]) -> str:
        """Render a heading block."""
        content = block.get('content', '')
        level = block.get('level', 2)
        
        # Ensure valid heading level
        level = max(1, min(6, int(level)))
        
        anchor_id = re.sub(r'[^a-zA-Z0-9\-_]', '-', content.lower())
        
        return f'''
        <h{level} id="{anchor_id}" class="lesson-heading">
            {content}
            <a href="#{anchor_id}" class="heading-anchor">#</a>
        </h{level}>
        '''
    
    def render_code_example_block(self, block: Dict[str, Any]) -> str:
        """Render a bare minimum code example block with CodeMirror syntax highlighting."""
        code = block.get('content', '')
        language = block.get('language', 'python')
        show_line_numbers = block.get('show_line_numbers', False)
        readonly = True  # Code examples are read-only
        
        # Create unique ID for this code block
        import uuid
        block_id = f"code-example-{uuid.uuid4().hex[:8]}"
        
        # Bare minimum: just code with small copy button using CodeMirror
        return f'''
        <div class="content-block code-example-block">
            <div class="code-wrapper">
                <textarea 
                    id="{block_id}" 
                    class="code-editor" 
                    data-language="{language}" 
                    data-readonly="{str(readonly).lower()}"
                    data-line-numbers="{str(show_line_numbers).lower()}"
                    spellcheck="false"
                >{self._escape_html(code)}</textarea>
                <button class="copy-code-btn" data-code="{self._escape_html(code)}" title="Copy code">
                    <i class="bi bi-copy"></i>
                </button>
            </div>
        </div>
        '''
    
    def render_interactive_code_block(self, block: Dict[str, Any]) -> str:
        """Render an interactive code block with CodeMirror 6 decorators and widgets."""
        code = block.get('content', '')
        language = block.get('language', 'python')
        exercise_type = block.get('exercise_type', 'fill_blank')
        expected_output = block.get('expected_output', '')
        blanks = block.get('blanks', [])
        instructions = block.get('instructions', {})
        
        # Create unique ID for this interactive code block
        import uuid
        import json
        block_id = f"interactive-code-{uuid.uuid4().hex[:8]}"
        
        # Serialize blanks data for JavaScript
        blanks_json = json.dumps(blanks) if blanks else ''
        
        # Render instructions if they exist
        instructions_html = ''
        if instructions:
            instructions_title = instructions.get('title', 'Instructions')
            instructions_content = instructions.get('content', '')
            instructions_html = f'''
            <div class="interactive-instructions">
                <div class="instructions-header">
                    <i class="bi bi-info-circle"></i>
                    <strong>{instructions_title}</strong>
                </div>
                <div class="instructions-content">{instructions_content}</div>
            </div>
            '''
        
        # Interactive code block with CodeMirror 6 integration
        return f'''
        <div class="content-block interactive-code-block" data-exercise-type="{exercise_type}" data-blanks='{blanks_json}'>
            <div class="interactive-code-header">
                <span><i class="bi bi-lightning-charge"></i> Interactive Code Exercise</span>
                <div class="d-flex gap-2 align-items-center">
                    <span class="exercise-type">{exercise_type.replace('_', ' ').title()}</span>
                    <button class="btn btn-primary run-code-btn" data-target="{block_id}">
                        <i class="bi bi-play-fill"></i> Run
                    </button>
                </div>
            </div>
            {instructions_html}
            <div class="interactive-code-content">
                <textarea 
                    id="{block_id}" 
                    class="interactive-code-editor" 
                    data-language="{language}" 
                    data-exercise-type="{exercise_type}"
                    data-readonly="false"
                    data-line-numbers="true"
                    spellcheck="false"
                >{self._escape_html(code)}</textarea>
            </div>
            <div class="code-output" id="output-{block_id}" style="display: none;">
                <strong>Output:</strong>
                <pre class="output-content"></pre>
            </div>
        </div>
        '''
    
    def render_note_block(self, block: Dict[str, Any]) -> str:
        """Render a note/info block."""
        content = block.get('content', '')
        title = block.get('title', 'Note')
        
        return f'''
        <div class="content-block note-block">
            <div class="note-header">
                <i class="bi bi-info-circle"></i>
                <strong>{title}</strong>
            </div>
            <div class="note-content">{content}</div>
        </div>
        '''
    
    def render_warning_block(self, block: Dict[str, Any]) -> str:
        """Render a warning block."""
        content = block.get('content', '')
        title = block.get('title', 'Warning')
        
        return f'''
        <div class="content-block warning-block">
            <div class="warning-header">
                <i class="bi bi-exclamation-triangle"></i>
                <strong>{title}</strong>
            </div>
            <div class="warning-content">{content}</div>
        </div>
        '''
    
    def render_alert_block(self, block: Dict[str, Any]) -> str:
        """Render an alert block."""
        content = block.get('content', '')
        alert_type = block.get('alert_type', 'info')  # info, success, warning, danger
        title = block.get('title', '')
        
        icon_map = {
            'info': 'bi-info-circle',
            'success': 'bi-check-circle',
            'warning': 'bi-exclamation-triangle',
            'danger': 'bi-x-circle'
        }
        
        icon = icon_map.get(alert_type, 'bi-info-circle')
        
        return f'''
        <div class="content-block alert-block alert-{alert_type}">
            <div class="alert-header">
                <i class="bi {icon}"></i>
                {f'<strong>{title}</strong>' if title else ''}
            </div>
            <div class="alert-content">{content}</div>
        </div>
        '''
    
    def render_tip_block(self, block: Dict[str, Any]) -> str:
        """Render a tip block."""
        content = block.get('content', '')
        title = block.get('title', 'Tip')
        
        return f'''
        <div class="content-block tip-block">
            <div class="tip-header">
                <i class="bi bi-lightbulb"></i>
                <strong>{title}</strong>
            </div>
            <div class="tip-content">{content}</div>
        </div>
        '''
    
    def render_quiz_block(self, block: Dict[str, Any]) -> str:
        """Render a quiz question block."""
        question = block.get('content', '')
        options = block.get('options', [])
        correct_answer = block.get('correct_answer', 0)
        explanation = block.get('explanation', '')
        
        options_html = []
        for i, option in enumerate(options):
            options_html.append(f'''
            <div class="quiz-option">
                <label>
                    <input type="radio" name="quiz_{block.get('id', 0)}" value="{i}">
                    {option}
                </label>
            </div>
            ''')
        
        return f'''
        <div class="content-block quiz-block" data-correct-answer="{correct_answer}">
            <div class="quiz-header">
                <i class="bi bi-question-circle"></i>
                <strong>Quick Check</strong>
            </div>
            <div class="quiz-question">{question}</div>
            <div class="quiz-options">
                {"".join(options_html)}
            </div>
            <button class="btn btn-primary btn-sm check-answer-btn">Check Answer</button>
            <div class="quiz-explanation" style="display: none;">
                <strong>Explanation:</strong> {explanation}
            </div>
        </div>
        '''
    
    def render_image_block(self, block: Dict[str, Any]) -> str:
        """Render an image block."""
        src = block.get('src', '')
        alt = block.get('alt', '')
        caption = block.get('caption', '')
        width = block.get('width', '')
        
        style = f'width: {width};' if width else ''
        
        image_html = f'<img src="{src}" alt="{alt}" style="{style}" class="lesson-image">'
        
        if caption:
            return f'''
            <div class="content-block image-block">
                {image_html}
                <div class="image-caption">{caption}</div>
            </div>
            '''
        else:
            return f'<div class="content-block image-block">{image_html}</div>'
    
    def render_video_block(self, block: Dict[str, Any]) -> str:
        """Render a video block."""
        url = block.get('url', '')
        title = block.get('title', '')
        
        return f'''
        <div class="content-block video-block">
            {f'<h4 class="video-title">{title}</h4>' if title else ''}
            <div class="video-container">
                <div class="ratio ratio-16x9">
                    <iframe src="{url}" allowfullscreen></iframe>
                </div>
            </div>
        </div>
        '''
    
    def render_list_block(self, block: Dict[str, Any]) -> str:
        """Render a list block."""
        items = block.get('items', [])
        list_type = block.get('list_type', 'unordered')  # ordered, unordered
        title = block.get('title', '')
        
        tag = 'ol' if list_type == 'ordered' else 'ul'
        items_html = ''.join([f'<li>{item}</li>' for item in items])
        
        return f'''
        <div class="content-block list-block">
            {f'<h4 class="list-title">{title}</h4>' if title else ''}
            <{tag} class="lesson-list">
                {items_html}
            </{tag}>
        </div>
        '''
    
    def render_table_block(self, block: Dict[str, Any]) -> str:
        """Render a table block."""
        headers = block.get('headers', [])
        rows = block.get('rows', [])
        title = block.get('title', '')
        
        header_html = ''
        if headers:
            header_html = '<thead><tr>' + ''.join([f'<th>{header}</th>' for header in headers]) + '</tr></thead>'
        
        rows_html = '<tbody>'
        for row in rows:
            rows_html += '<tr>' + ''.join([f'<td>{cell}</td>' for cell in row]) + '</tr>'
        rows_html += '</tbody>'
        
        return f'''
        <div class="content-block table-block">
            {f'<h4 class="table-title">{title}</h4>' if title else ''}
            <div class="table-responsive">
                <table class="table lesson-table">
                    {header_html}
                    {rows_html}
                </table>
            </div>
        </div>
        '''
    
    def _highlight_code(self, code: str, language: str, show_line_numbers: bool = True) -> str:
        """Apply syntax highlighting to code."""
        if not self.pygments_available:
            # Fallback without syntax highlighting
            return f'<pre class="code-block"><code>{code}</code></pre>'
        
        try:
            lexer = get_lexer_by_name(language, stripall=True)
        except ClassNotFound:
            try:
                lexer = guess_lexer(code)
            except:
                # Fallback to plain text
                return f'<pre class="code-block"><code>{code}</code></pre>'
        
        formatter = HtmlFormatter(
            cssclass='highlight',
            linenos=show_line_numbers,
            style='monokai'  # Dark theme compatible
        )
        
        highlighted = highlight(code, lexer, formatter)
        return highlighted

    def _escape_html(self, text: str) -> str:
        """Escape HTML characters in text for safe attribute usage."""
        return (text.replace('&', '&amp;')
                   .replace('<', '&lt;')
                   .replace('>', '&gt;')
                   .replace('"', '&quot;')
                   .replace("'", '&#39;'))


# Global instance for easy import
content_renderer = ContentBlockRenderer()