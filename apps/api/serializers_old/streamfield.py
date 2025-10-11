from __future__ import annotations

from typing import Any, Dict, List

from django.utils.html import escape

from .common import serialize_rich_text_field, serialize_plain_text
from .images import serialize_image


def serialize_streamfield(request, stream_value) -> List[Dict[str, Any]]:
    """
    Serialize a Wagtail StreamField value into a JSON-friendly list of blocks.
    - RichText is sanitized for display-only fields.
    - Code-bearing fields are returned as plain text (no sanitization) to be rendered by the frontend editor/viewer.
    - Images are serialized with rendition URLs.
    - Unknown blocks are stringified safely.
    """
    if not stream_value:
        return []

    blocks: List[Dict[str, Any]] = []

    for block in stream_value:
        btype = getattr(block, 'block_type', None)
        val = getattr(block, 'value', None)

        # Blog body common blocks
        if btype in ('paragraph', 'text'):  # RichText
            blocks.append({
                'type': 'paragraph',
                'value': serialize_rich_text_field(val)
            })
        elif btype in ('heading',):
            blocks.append({
                'type': 'heading',
                'value': str(val)
            })
        elif btype in ('image',):
            image_obj = val
            img = serialize_image(request, image_obj)
            if img:
                blocks.append({
                    'type': 'image',
                    'value': img
                })
        elif btype in ('code', 'code_example'):
            # value likely a StructBlock
            try:
                language = val.get('language', 'text')
                code = val.get('code', '')
                title = val.get('title', val.get('caption', ''))
                explanation = val.get('explanation', '')
            except Exception:
                language, code, title, explanation = 'text', str(val), '', ''
            blocks.append({
                'type': 'code',
                'value': {
                    'language': language,
                    'code': serialize_plain_text(code),
                    'title': str(title or ''),
                    'explanation': str(explanation or ''),
                }
            })
        elif btype in ('quote',):
            try:
                text = val.get('text', '')
                attribution = val.get('attribute_name', '')
            except Exception:
                text, attribution = str(val), ''
            blocks.append({
                'type': 'quote',
                'value': {
                    'text': str(text),
                    'attribution': str(attribution)
                }
            })
        elif btype in ('callout',):
            try:
                ctype = val.get('type', 'info')
                title = val.get('title', '')
                text = val.get('text', '')
            except Exception:
                ctype, title, text = 'info', '', str(val)
            blocks.append({
                'type': 'callout',
                'value': {
                    'type': ctype,
                    'title': str(title),
                    'text': serialize_rich_text_field(text)
                }
            })
        elif btype in ('embed',):
            # Raw HTML embeds should be passed through with caution.
            # For now, send as raw string and rely on CSP + frontend whitelist.
            blocks.append({
                'type': 'embed',
                'value': str(val)
            })
        elif btype in ('objective',):
            blocks.append({
                'type': 'objective',
                'value': str(val)
            })
        elif btype in ('video',):
            try:
                blocks.append({
                    'type': 'video',
                    'value': {
                        'title': str(val.get('title', '')),
                        'video_url': str(val.get('video_url', '')),
                        'description': serialize_rich_text_field(val.get('description', ''))
                    }
                })
            except Exception:
                blocks.append({'type': 'video', 'value': {}})
        elif btype in ('interactive_exercise',):
            try:
                blocks.append({
                    'type': 'interactive_exercise',
                    'value': {
                        'title': str(val.get('title', '')),
                        'instructions': serialize_rich_text_field(val.get('instructions', '')),
                        'starter_code': serialize_plain_text(val.get('starter_code', '')),
                        'solution': serialize_plain_text(val.get('solution', '')),
                        'hints': val.get('hints', [])
                    }
                })
            except Exception:
                blocks.append({'type': 'interactive_exercise', 'value': {}})
        elif btype in ('quiz',):
            try:
                blocks.append({
                    'type': 'quiz',
                    'value': {
                        'question': str(val.get('question', '')),
                        'options': list(val.get('options', [])),
                        'correct_answer': int(val.get('correct_answer', 0)),
                        'explanation': serialize_rich_text_field(val.get('explanation', '')),
                    }
                })
            except Exception:
                blocks.append({'type': 'quiz', 'value': {}})
        elif btype in ('runnable_code_example',):
            try:
                blocks.append({
                    'type': 'runnable_code_example',
                    'value': {
                        'title': str(val.get('title', '')),
                        'language': val.get('language', 'python'),
                        'code': serialize_plain_text(val.get('code', '')),
                        'mock_output': serialize_plain_text(val.get('mock_output', '')),
                        'ai_explanation': serialize_plain_text(val.get('ai_explanation', '')),
                    }
                })
            except Exception:
                blocks.append({'type': 'runnable_code_example', 'value': {}})
        elif btype in ('fill_blank_code', 'multiple_choice_code'):
            import json
            try:
                if btype == 'fill_blank_code':
                    solutions = json.loads(val.get('solutions', '{}') or '{}')
                    alt_solutions = json.loads(val.get('alternative_solutions', '{}') or '{}')
                    ai_hints = json.loads(val.get('ai_hints', '{}') or '{}')
                    blocks.append({
                        'type': 'fill_blank_code',
                        'value': {
                            'title': str(val.get('title', '')),
                            'language': val.get('language', 'python'),
                            'template': serialize_plain_text(val.get('template', '')),
                            'solutions': solutions,
                            'alternative_solutions': alt_solutions,
                            'ai_hints': ai_hints
                        }
                    })
                else:
                    choices = json.loads(val.get('choices', '{}') or '{}')
                    solutions = json.loads(val.get('solutions', '{}') or '{}')
                    ai_explanations = json.loads(val.get('ai_explanations', '{}') or '{}')
                    blocks.append({
                        'type': 'multiple_choice_code',
                        'value': {
                            'title': str(val.get('title', '')),
                            'language': val.get('language', 'python'),
                            'template': serialize_plain_text(val.get('template', '')),
                            'choices': choices,
                            'solutions': solutions,
                            'ai_explanations': ai_explanations
                        }
                    })
            except Exception:
                blocks.append({'type': btype, 'value': {}})
        else:
            # Fallback: stringify value
            try:
                blocks.append({'type': btype or 'unknown', 'value': str(val)})
            except Exception:
                blocks.append({'type': btype or 'unknown', 'value': ''})

    return blocks
