"""
Management command to add progressive hints to existing StepBasedExercisePage exercises.
"""

import json
from django.core.management.base import BaseCommand
from apps.blog.models import StepBasedExercisePage


class Command(BaseCommand):
    help = 'Add progressive hints to existing multi-step exercises'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Dry run - show what would be updated without making changes',
        )

    def generate_progressive_hints_for_step(self, step_data):
        """
        Generate progressive hints based on the step's content.
        Returns a JSON string of hints array.
        """
        step_title = step_data.get('title', '')
        step_desc = step_data.get('description', '')
        step_type = step_data.get('exercise_type', 'fill_blank')
        template = step_data.get('template', '')

        # Parse solutions to understand what's being asked
        solutions = step_data.get('solutions', {})
        if isinstance(solutions, str):
            try:
                solutions = json.loads(solutions)
            except:
                solutions = {}

        # Don't add hints to quiz steps
        if step_type in ['quiz', 'multiple_choice']:
            return None

        # Create contextual hints based on the template and step content
        hints = []

        # Level 1: Conceptual hint (30 seconds)
        conceptual_hint = self.create_conceptual_hint(step_title, template, solutions)
        hints.append({
            "level": 1,
            "type": "conceptual",
            "title": "Think About It",
            "content": conceptual_hint,
            "triggerTime": 30,
            "triggerAttempts": 0
        })

        # Level 2: Approach hint (90 seconds, 2 attempts)
        approach_hint = self.create_approach_hint(step_title, template, solutions)
        hints.append({
            "level": 2,
            "type": "approach",
            "title": "Getting Closer",
            "content": approach_hint,
            "triggerTime": 90,
            "triggerAttempts": 2
        })

        # Level 3: Syntax hint (180 seconds, 3 attempts)
        syntax_hint = self.create_syntax_hint(step_title, template, solutions)
        hints.append({
            "level": 3,
            "type": "syntax",
            "title": "Syntax Help",
            "content": syntax_hint,
            "triggerTime": 180,
            "triggerAttempts": 3
        })

        # Level 4: Near-solution hint (300 seconds, 5 attempts)
        near_solution_hint = self.create_near_solution_hint(solutions)
        hints.append({
            "level": 4,
            "type": "near-solution",
            "title": "Almost There!",
            "content": near_solution_hint,
            "triggerTime": 300,
            "triggerAttempts": 5
        })

        return json.dumps(hints)

    def create_conceptual_hint(self, title, template, solutions):
        """Create a conceptual hint based on the step topic."""
        title_lower = title.lower()

        if 'variable' in title_lower:
            return "<p>Think about how we store information in Python. What creates a container for a value?</p>"
        elif 'string' in title_lower:
            return "<p>Text in Python is enclosed in quotes. What type of quotes can you use?</p>"
        elif 'concatenat' in title_lower:
            return "<p>Combining strings together is like joining words. What operator joins things?</p>"
        elif 'function' in title_lower or 'def' in title_lower:
            return "<p>Functions are reusable blocks of code. What keyword starts a function definition?</p>"
        elif 'return' in title_lower:
            return "<p>Functions can send values back to the caller. What keyword does this?</p>"
        elif 'call' in title_lower:
            return "<p>To use a function, you need to invoke it. What symbols do you use after the function name?</p>"
        elif 'if' in title_lower or 'condition' in title_lower:
            return "<p>Conditional statements check if something is true. What keyword starts a conditional?</p>"
        elif 'elif' in title_lower:
            return "<p>To check additional conditions after an if, we use another keyword. What is it?</p>"
        elif 'else' in title_lower:
            return "<p>When all conditions fail, we need a default case. What keyword provides this?</p>"
        else:
            return "<p>Read the instructions carefully. What concept is this step teaching?</p>"

    def create_approach_hint(self, title, template, solutions):
        """Create an approach hint with more specific guidance."""
        title_lower = title.lower()

        if 'variable' in title_lower:
            return "<p>In Python, you create a variable by writing: <code>variable_name = value</code></p>"
        elif 'string' in title_lower:
            return "<p>Strings can use single quotes ('text') or double quotes (\"text\"). Both work the same way!</p>"
        elif 'concatenat' in title_lower:
            return "<p>The <code>+</code> operator joins strings together: <code>\"Hello\" + \" \" + \"World\"</code></p>"
        elif 'function' in title_lower or 'def' in title_lower:
            return "<p>Functions start with <code>def</code> followed by the function name and parentheses.</p>"
        elif 'return' in title_lower:
            return "<p>The <code>return</code> keyword sends a value back from the function to where it was called.</p>"
        elif 'call' in title_lower:
            return "<p>Call a function by writing its name followed by parentheses: <code>function_name()</code></p>"
        elif 'if' in title_lower or 'condition' in title_lower:
            return "<p>Use <code>if condition:</code> to check if something is true. Don't forget the colon!</p>"
        elif 'elif' in title_lower:
            return "<p>The <code>elif</code> keyword checks another condition if the first one was false.</p>"
        elif 'else' in title_lower:
            return "<p>The <code>else</code> keyword runs when all previous conditions are false.</p>"
        else:
            return "<p>Look at the template code. What part needs to be filled in?</p>"

    def create_syntax_hint(self, title, template, solutions):
        """Create a syntax-specific hint."""
        # Count blanks
        num_blanks = len(solutions)

        if num_blanks == 1:
            blank_1_sol = solutions.get("1", "")
            return f"<p>Try using: <code>{blank_1_sol}</code></p>"
        else:
            hints_list = [f"<code>BLANK_{k}</code>: Try <code>{v}</code>" for k, v in solutions.items()]
            return "<p>Here are some hints for each blank:</p><ul>" + "".join([f"<li>{h}</li>" for h in hints_list]) + "</ul>"

    def create_near_solution_hint(self, solutions):
        """Create a near-solution hint showing the exact answers."""
        if len(solutions) == 1:
            return f"<p><strong>Solution:</strong> The answer is <code>{list(solutions.values())[0]}</code></p>"
        else:
            solution_list = [f"<code>BLANK_{k}</code> = <code>{v}</code>" for k, v in solutions.items()]
            return "<p><strong>Solutions:</strong></p><ul>" + "".join([f"<li>{s}</li>" for s in solution_list]) + "</ul>"

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))

        # Get all StepBasedExercisePage objects
        exercises = StepBasedExercisePage.objects.all()

        self.stdout.write(f'Found {exercises.count()} exercises')

        updated_count = 0

        for exercise in exercises:
            self.stdout.write(f'\nProcessing: {exercise.title}')

            # Get the raw StreamField data
            steps_data = exercise.exercise_steps.raw_data

            modified = False

            for i, step_block in enumerate(steps_data):
                if step_block['type'] == 'exercise_step':
                    step_value = step_block['value']

                    # Check if progressive_hints is None or empty
                    current_hints = step_value.get('progressive_hints')

                    if current_hints is None or current_hints == '':
                        # Generate progressive hints
                        progressive_hints = self.generate_progressive_hints_for_step(step_value)

                        if progressive_hints:
                            step_value['progressive_hints'] = progressive_hints
                            modified = True
                            self.stdout.write(f'  Step {i+1} ({step_value.get("title", "Untitled")}): Adding progressive hints')
                        else:
                            self.stdout.write(f'  Step {i+1} ({step_value.get("title", "Untitled")}): Skipped (quiz step)')
                    else:
                        self.stdout.write(f'  Step {i+1} ({step_value.get("title", "Untitled")}): Already has hints')

            if modified and not dry_run:
                # Save the exercise
                exercise.exercise_steps = steps_data
                exercise.save_revision().publish()
                updated_count += 1
                self.stdout.write(self.style.SUCCESS(f'  ✓ Updated {exercise.title}'))
            elif modified and dry_run:
                self.stdout.write(self.style.WARNING(f'  ⚠ Would update {exercise.title} (dry run)'))

        if dry_run:
            self.stdout.write(self.style.WARNING(f'\nDRY RUN COMPLETE: {updated_count} exercises would be updated'))
        else:
            self.stdout.write(self.style.SUCCESS(f'\n✓ Successfully updated {updated_count} exercises with progressive hints!'))
