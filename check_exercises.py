#!/usr/bin/env python
"""Check all exercises for validation issues."""

import os
import sys
import django
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'learning_community.settings.development')
sys.path.insert(0, '/Users/williamtower/projects/learning_studio')
django.setup()

from apps.blog.models import StepBasedExercisePage

exercises = StepBasedExercisePage.objects.all().order_by('sequence_number')

for ex in exercises:
    print('\n' + '='*80)
    print(f'EXERCISE: {ex.title}')
    print('='*80)

    for i, step_block in enumerate(ex.exercise_steps):
        if step_block.block_type != 'exercise_step':
            continue

        step = step_block.value
        print(f'\n  Step {i+1}: {step["title"]}')
        print(f'  Type: {step["exercise_type"]}')

        if step['exercise_type'] == 'fill_blank':
            template = step['template']
            print(f'  Template: {template[:100]}...' if len(template) > 100 else f'  Template: {template}')

            solutions = step['solutions']
            if isinstance(solutions, str):
                try:
                    solutions = json.loads(solutions)
                except:
                    solutions = {}

            print(f'  Solutions: {solutions}')

            # Check if template has the blanks that solutions reference
            for blank_id in solutions.keys():
                blank_pattern = f'{{{{BLANK_{blank_id}}}}}'
                if blank_pattern not in step['template']:
                    print(f'  ⚠️  WARNING: Solution references BLANK_{blank_id} but template doesn\'t have {blank_pattern}')

            # Check for potential validation issues
            for blank_id, solution in solutions.items():
                if solution.startswith('"') and solution.endswith('"'):
                    print(f'    BLANK_{blank_id}: Expects quoted string -> Any quoted string will be accepted')
                elif solution.startswith("'") and solution.endswith("'"):
                    print(f'    BLANK_{blank_id}: Expects quoted string -> Any quoted string will be accepted')
                else:
                    print(f'    BLANK_{blank_id}: Expects exact match -> Must enter "{solution}"')

        elif step['exercise_type'] in ['quiz', 'multiple_choice']:
            quiz_data = step['solutions']
            if isinstance(quiz_data, str):
                try:
                    quiz_data = json.loads(quiz_data)
                except:
                    quiz_data = {}

            questions = quiz_data.get('questions', [])
            print(f'  Quiz with {len(questions)} questions')

print('\n' + '='*80)
print('VALIDATION CHECK COMPLETE')
print('='*80)
