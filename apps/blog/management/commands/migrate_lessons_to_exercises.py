"""
Django management command to migrate lesson-based courses to exercise-based courses.
Converts LessonPage instances to StepBasedExercisePage instances while preserving content.
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from apps.blog.models import CoursePage, LessonPage, StepBasedExercisePage, ExercisePage
import json


class Command(BaseCommand):
    help = 'Migrate lessons to direct course exercises'

    def add_arguments(self, parser):
        parser.add_argument(
            '--course-slug',
            type=str,
            help='Slug of the course to migrate (default: all courses)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes',
        )

    def handle(self, *args, **options):
        course_slug = options.get('course_slug')
        dry_run = options.get('dry_run', False)

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))

        # Get courses to migrate
        if course_slug:
            courses = CoursePage.objects.filter(slug=course_slug)
        else:
            courses = CoursePage.objects.all()

        if not courses.exists():
            self.stdout.write(self.style.ERROR('No courses found'))
            return

        for course in courses:
            self.stdout.write(f'\n{self.style.SUCCESS("="*60)}')
            self.stdout.write(f'{self.style.SUCCESS(f"Migrating: {course.title}")}')
            self.stdout.write(self.style.SUCCESS("="*60))

            try:
                self.migrate_course(course, dry_run)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error migrating {course.title}: {str(e)}'))
                import traceback
                self.stdout.write(traceback.format_exc())

        if not dry_run:
            self.stdout.write(self.style.SUCCESS('\n✅ Migration complete!'))
        else:
            self.stdout.write(self.style.WARNING('\n📋 Dry run complete - no changes made'))

    @transaction.atomic
    def migrate_course(self, course, dry_run=False):
        """Migrate a single course from lessons to exercises."""

        # Get all lessons
        lessons = course.get_children().type(LessonPage).specific().order_by('path')

        if not lessons:
            self.stdout.write(self.style.WARNING(f'  No lessons found in {course.title}'))
            return

        self.stdout.write(f'\n  Found {lessons.count()} lessons to convert')

        sequence_number = 1

        for lesson in lessons:
            self.stdout.write(f'\n  📖 Converting Lesson {lesson.lesson_number}: {lesson.title}')

            # Check if lesson has child exercises
            child_exercises = lesson.get_children().specific()

            # Convert lesson content to exercise steps
            steps_data = self.convert_lesson_to_steps(lesson)

            if not dry_run:
                # Create new StepBasedExercisePage
                exercise = StepBasedExercisePage(
                    title=lesson.title,
                    slug=f"{lesson.slug}-exercise",  # Modify slug to avoid conflicts
                    sequence_number=sequence_number,
                    difficulty=self.determine_difficulty(lesson.lesson_number),
                    total_points=self.calculate_points(steps_data),
                    estimated_time=self.estimate_time(steps_data),
                    require_sequential=True,
                    exercise_steps=steps_data,
                    general_hints=[],
                    completion_message=f"<p>Excellent work! You've completed {lesson.title}.</p>",
                    show_completion_certificate=False,
                )

                # Add as child of course
                course.add_child(instance=exercise)
                exercise.save_revision().publish()

                self.stdout.write(self.style.SUCCESS(f'    ✅ Created exercise #{sequence_number}: {exercise.title}'))

                # Handle child exercises (move them to course level)
                for child_ex in child_exercises:
                    if isinstance(child_ex, (ExercisePage, StepBasedExercisePage)):
                        sequence_number += 1
                        self.stdout.write(f'    📦 Moving child exercise: {child_ex.title}')

                        # Update sequence number
                        child_ex.sequence_number = sequence_number
                        child_ex.save()

                        # Move to course level
                        child_ex.move(course, pos='last-child')

                        self.stdout.write(self.style.SUCCESS(f'      ✅ Moved to course as exercise #{sequence_number}'))

                # Unpublish the old lesson (keep for reference)
                lesson.unpublish()
                self.stdout.write(self.style.WARNING(f'    ⚠️  Unpublished old lesson (kept for reference)'))
            else:
                self.stdout.write(f'    Would create exercise #{sequence_number} with {len(steps_data)} steps')
                if child_exercises:
                    self.stdout.write(f'    Would move {child_exercises.count()} child exercises')

            sequence_number += 1

    def convert_lesson_to_steps(self, lesson):
        """Convert lesson content StreamField to exercise steps."""
        steps = []
        step_number = 1

        # Add intro as first step
        if lesson.intro:
            steps.append({
                'type': 'exercise_step',
                'value': {
                    'step_number': step_number,
                    'title': 'Introduction',
                    'description': f'<p>{lesson.intro}</p>',
                    'exercise_type': 'code',
                    'template': '',
                    'solutions': '',
                    'points': 0,
                    'success_message': 'Great! Let\'s continue.',
                    'hint': '',
                }
            })
            step_number += 1

        # Convert content blocks to steps
        for block in lesson.content:
            block_type = block.block_type

            if block_type == 'text':
                # Text blocks become informational steps
                steps.append({
                    'type': 'exercise_step',
                    'value': {
                        'step_number': step_number,
                        'title': f'Step {step_number}',
                        'description': str(block.value),
                        'exercise_type': 'code',
                        'template': '',
                        'solutions': '',
                        'points': 0,
                        'success_message': 'Continue to the next step.',
                        'hint': '',
                    }
                })
                step_number += 1

            elif block_type == 'fill_blank_code':
                # Fill-in-blank becomes an exercise step
                title = block.value.get('title', f'Exercise {step_number}')
                template = block.value.get('template', '')
                solutions = block.value.get('solutions', '{}')
                alternative_solutions = block.value.get('alternative_solutions', '{}')
                ai_hints = block.value.get('ai_hints', '{}')

                # Create beginner-friendly description
                description = f'<p><strong>{title}</strong></p><p>Fill in the blanks to complete the code. Hover over each blank for hints!</p>'

                steps.append({
                    'type': 'exercise_step',
                    'value': {
                        'step_number': step_number,
                        'title': title,
                        'description': description,
                        'exercise_type': 'fill_blank',
                        'template': template,
                        'solutions': solutions,
                        'alternative_solutions': alternative_solutions,
                        'points': 20,
                        'success_message': 'Excellent! You got it right.',
                        'hint': ai_hints,
                    }
                })
                step_number += 1

            elif block_type == 'multiple_choice_code':
                # Multiple choice code becomes an interactive step
                title = block.value.get('title', f'Exercise {step_number}')
                template = block.value.get('template', '')
                choices = block.value.get('choices', '{}')
                solutions = block.value.get('solutions', '{}')
                ai_explanations = block.value.get('ai_explanations', '{}')

                # Create description with instructions
                description = f'<p><strong>{title}</strong></p><p>Choose the correct options to complete the code.</p>'

                steps.append({
                    'type': 'exercise_step',
                    'value': {
                        'step_number': step_number,
                        'title': title,
                        'description': description,
                        'exercise_type': 'multiple_choice',
                        'template': template,
                        'solutions': solutions,
                        'alternative_solutions': choices,  # Store choices for rendering
                        'points': 15,
                        'success_message': 'Perfect! You chose the right options.',
                        'hint': ai_explanations,
                    }
                })
                step_number += 1

            elif block_type == 'runnable_code_example':
                # Code examples become informational code steps
                steps.append({
                    'type': 'exercise_step',
                    'value': {
                        'step_number': step_number,
                        'title': block.value.get('title', f'Code Example {step_number}'),
                        'description': '<p>Study this code example and run it to see the output.</p>',
                        'exercise_type': 'code',
                        'template': block.value.get('code', ''),
                        'solutions': '',
                        'points': 0,
                        'success_message': 'Continue when ready.',
                        'hint': block.value.get('ai_explanation', ''),
                    }
                })
                step_number += 1

            elif block_type == 'quiz':
                # Quiz blocks become quiz steps
                options = block.value.get('options', [])
                steps.append({
                    'type': 'exercise_step',
                    'value': {
                        'step_number': step_number,
                        'title': f'Quiz Question {step_number}',
                        'description': f'<p>{block.value.get("question", "")}</p><ul>' + ''.join([f'<li>{opt}</li>' for opt in options]) + '</ul>',
                        'exercise_type': 'quiz',
                        'template': '',
                        'solutions': json.dumps({'correct': block.value.get('correct_answer', 0)}),
                        'points': 10,
                        'success_message': str(block.value.get('explanation', 'Correct!')),
                        'hint': '',
                    }
                })
                step_number += 1

        return steps

    def determine_difficulty(self, lesson_number):
        """Determine difficulty based on lesson position."""
        if lesson_number <= 2:
            return 'easy'
        elif lesson_number <= 4:
            return 'medium'
        else:
            return 'hard'

    def calculate_points(self, steps):
        """Calculate total points for exercise."""
        return sum(step['value'].get('points', 0) for step in steps)

    def estimate_time(self, steps):
        """Estimate time based on number of steps."""
        step_count = len(steps)
        if step_count <= 3:
            return 15
        elif step_count <= 6:
            return 30
        else:
            return 45
