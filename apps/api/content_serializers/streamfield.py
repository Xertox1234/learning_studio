from __future__ import annotations

from typing import Any, Dict, List

from django.http import HttpRequest

from .common import sanitize_rich_text, serialize_image
import json


def _parse_json_maybe(value: Any, default: Any):
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return default
    return value if value is not None else default


def serialize_streamfield(stream_value: Any, request: HttpRequest) -> List[Dict[str, Any]]:
    """Serialize a Wagtail StreamField into a JSON-friendly list.
    - Rich text fields are sanitized (editor-safe).
    - Code/plain text fields are passed through verbatim.
    - Images include rendition metadata with absolute URLs.
    """
    result: List[Dict[str, Any]] = []
    if not stream_value:
        return result

    for block in stream_value:
        btype = getattr(block, 'block_type', None)
        val = getattr(block, 'value', None)
        entry: Dict[str, Any] = {'type': btype, 'value': None}

        if btype in {'paragraph', 'text'}:
            entry['value'] = sanitize_rich_text(str(val))
        elif btype in {'heading'}:
            entry['value'] = str(val)
        elif btype in {'image'}:
            entry['value'] = serialize_image(val, request) or None
        elif btype in {'embed'}:
            entry['value'] = sanitize_rich_text(str(val))
        elif btype in {'code', 'code_example', 'runnable_code_example'}:
            # These blocks contain code; pass through verbatim with minimal struct normalization
            if isinstance(val, dict):
                entry['value'] = {
                    'title': val.get('title', ''),
                    'language': val.get('language', 'text'),
                    'code': val.get('code', ''),
                    'explanation': sanitize_rich_text(str(val.get('explanation', ''))) if 'explanation' in val else '',
                    'mock_output': val.get('mock_output', ''),
                    'ai_explanation': val.get('ai_explanation', ''),
                }
            else:
                entry['value'] = str(val) if val is not None else ''
        elif btype in {'interactive_exercise'}:
            val = val or {}
            entry['value'] = {
                'title': val.get('title', ''),
                'instructions': sanitize_rich_text(str(val.get('instructions', ''))),
                'starter_code': val.get('starter_code', ''),
                'solution': val.get('solution', ''),
                'hints': val.get('hints', []),
            }
        elif btype in {'video'}:
            val = val or {}
            entry['value'] = {
                'title': val.get('title', ''),
                'video_url': val.get('video_url', ''),
                'description': sanitize_rich_text(str(val.get('description', ''))),
            }
        elif btype in {'callout'}:
            val = val or {}
            entry['value'] = {
                'type': val.get('type', 'info'),
                'title': val.get('title', ''),
                'text': sanitize_rich_text(str(val.get('text', ''))),
            }
        elif btype in {'quote'}:
            val = val or {}
            entry['value'] = {
                'text': sanitize_rich_text(str(val.get('text', ''))),
                'attribution': val.get('attribute_name', ''),
            }
        elif btype in {'quiz'}:
            val = val or {}
            entry['value'] = {
                'question': val.get('question', ''),
                'options': val.get('options', []),
                'correct_answer': val.get('correct_answer', 0),
                'explanation': sanitize_rich_text(str(val.get('explanation', ''))),
            }
        elif btype in {'feature', 'stat', 'objective', 'section_break'}:
            # Simple structs with text; sanitize subfields that are rich text-like
            if isinstance(val, dict):
                entry['value'] = {
                    k: sanitize_rich_text(str(v)) if isinstance(v, str) else v
                    for k, v in val.items()
                }
            else:
                entry['value'] = str(val) if val is not None else ''
        elif btype in {'module'}:
            val = val or {}
            lessons = []
            for lesson in val.get('lessons', []) if isinstance(val, dict) else []:
                lessons.append({
                    'lesson_title': lesson.get('lesson_title', ''),
                    'lesson_description': lesson.get('lesson_description', ''),
                    'estimated_time': lesson.get('estimated_time', ''),
                })
            entry['value'] = {
                'title': val.get('title', ''),
                'description': sanitize_rich_text(str(val.get('description', ''))),
                'lessons': lessons,
            }
        elif btype in {'example', 'shortcut', 'resource'}:
            entry['value'] = val
        elif btype in {'fill_blank_code', 'multiple_choice_code'}:
            val = val or {}
            entry['value'] = {
                'title': val.get('title', ''),
                'language': val.get('language', 'python'),
                'template': val.get('template', ''),
                'solutions': _parse_json_maybe(val.get('solutions', {}), {}),
                'alternative_solutions': _parse_json_maybe(val.get('alternative_solutions', {}), {}),
                'ai_hints': _parse_json_maybe(val.get('ai_hints', {}), {}),
                'choices': _parse_json_maybe(val.get('choices', {}), {}),
                'ai_explanations': _parse_json_maybe(val.get('ai_explanations', {}), {}),
            }
        else:
            # Fallback: stringify
            entry['value'] = str(val) if val is not None else ''

        result.append(entry)

    return result
