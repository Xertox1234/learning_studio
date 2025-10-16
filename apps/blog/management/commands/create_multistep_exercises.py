"""
Management command to create multi-step exercises with fill-in-blank steps and quizzes.
"""

import json
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from wagtail.models import Page
from apps.blog.models import CoursePage, ExercisePage, StepBasedExercisePage

User = get_user_model()


class Command(BaseCommand):
    help = 'Delete old single-step exercises and create new multi-step exercises'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without actually creating it'
        )

    def generate_progressive_hints(self, step_title, step_description, template, solutions, step_type='fill_blank'):
        """
        Generate contextual progressive hints based on step content.
        """
        # Extract the main concept from the title
        title_lower = step_title.lower()

        # Parse the template to understand what's being asked
        blank_count = template.count('{{BLANK_')

        # Generate hints based on the type of exercise
        hints = []

        # Level 1: Conceptual understanding (30 seconds)
        if 'variable' in title_lower or 'assignment' in title_lower:
            concept = "Variables store values that can be used later in your program."
        elif 'string' in title_lower or 'concatenat' in title_lower:
            concept = "Strings are text values that can be combined using operators."
        elif 'function' in title_lower or 'def' in title_lower:
            concept = "Functions are reusable blocks of code that perform specific tasks."
        elif 'return' in title_lower:
            concept = "The return statement sends a value back from a function."
        elif 'if' in title_lower or 'condition' in title_lower:
            concept = "Conditional statements let your code make decisions based on conditions."
        elif 'elif' in title_lower:
            concept = "The elif clause checks additional conditions when the previous ones are false."
        elif 'else' in title_lower:
            concept = "The else clause handles all cases that don't match the previous conditions."
        elif 'call' in title_lower:
            concept = "Calling a function executes its code with the provided arguments."
        elif 'parameter' in title_lower:
            concept = "Parameters let functions accept input values to work with."
        elif 'operator' in title_lower or 'operation' in title_lower:
            concept = "Operators perform calculations or manipulations on values."
        elif 'type' in title_lower or 'conversion' in title_lower:
            concept = "Type conversion changes a value from one type to another (like number to string)."
        else:
            concept = f"Understanding {step_title} is key to writing effective Python code."

        hints.append({
            "level": 1,
            "type": "conceptual",
            "title": "Think About It",
            "content": f"<p>{concept}</p><p>What does this step require you to understand?</p>",
            "triggerTime": 30,
            "triggerAttempts": 0
        })

        # Level 2: Approach hint (60 seconds, 2 attempts)
        if 'variable' in title_lower:
            approach = "Think about the <strong>=</strong> operator and what type of value goes on the right side."
        elif 'string' in title_lower:
            approach = "Remember that strings need to be wrapped in <strong>quotes</strong> (\" or ')."
        elif 'function' in title_lower and 'def' in template.lower():
            approach = "Functions start with the <strong>def</strong> keyword, followed by the function name."
        elif 'return' in title_lower:
            approach = "Use the <strong>return</strong> keyword to send a value back from the function."
        elif 'if' in title_lower:
            approach = "Conditional statements start with the <strong>if</strong> keyword."
        elif 'elif' in title_lower:
            approach = "Use <strong>elif</strong> (else if) for additional conditions to check."
        elif 'else' in title_lower:
            approach = "The <strong>else</strong> keyword handles all remaining cases."
        elif 'call' in title_lower or 'calling' in title_lower:
            approach = "Call a function by using its <strong>name followed by parentheses</strong>, like: <code>function_name()</code>"
        elif '*' in template or 'repet' in title_lower:
            approach = "The <strong>*</strong> operator can multiply numbers or repeat strings."
        elif '+' in template and 'string' in step_description.lower():
            approach = "The <strong>+</strong> operator concatenates (combines) strings together."
        elif 'parameter' in title_lower:
            approach = "Parameters go inside the parentheses when defining the function."
        elif 'conversion' in title_lower or 'str(' in template:
            approach = "Use <strong>str()</strong> to convert other types to strings."
        else:
            approach = f"Look at the code template and identify what keyword or operator is needed."

        hints.append({
            "level": 2,
            "type": "approach",
            "title": "Approach Hint",
            "content": f"<p>{approach}</p>",
            "triggerTime": 60,
            "triggerAttempts": 2
        })

        # Level 3: Syntax/structure hint (90 seconds, 3 attempts)
        # Try to give a more specific hint based on the template
        if blank_count == 1:
            # Extract context around the blank
            if '"' in template or "'" in template:
                syntax = "Make sure to use matching quotes for your string value."
            elif '(' in template and ')' in template:
                syntax = "Check the syntax carefully - parentheses, colons, and indentation matter."
            elif '=' in template:
                syntax = "Remember the syntax: <code>variable_name = value</code>"
            else:
                # Try to extract what's expected from solutions
                solution_keys = list(solutions.keys())
                if solution_keys:
                    first_solution = solutions[solution_keys[0]]
                    if first_solution.startswith('"') or first_solution.startswith("'"):
                        syntax = f"You need a string value here. Try wrapping your answer in quotes."
                    elif first_solution in ['if', 'elif', 'else', 'def', 'return']:
                        syntax = f"This is a Python <strong>keyword</strong>. Use: <code>{first_solution}</code>"
                    else:
                        syntax = f"Think about the exact syntax needed here."
                else:
                    syntax = "Review the Python syntax for this type of statement."
        else:
            syntax = f"You have {blank_count} blanks to fill. Make sure each one is syntactically correct."

        hints.append({
            "level": 3,
            "type": "structure",
            "title": "Syntax Hint",
            "content": f"<p>{syntax}</p>",
            "triggerTime": 90,
            "triggerAttempts": 3
        })

        # Level 4: Near-solution hint (120 seconds, 5 attempts)
        # Give a very direct hint without completely giving away the answer
        solution_keys = list(solutions.keys())
        if solution_keys and len(solution_keys) == 1:
            first_solution = solutions[solution_keys[0]]
            # Clean up the solution for display
            clean_solution = first_solution.strip('"').strip("'")

            if first_solution.startswith('"') or first_solution.startswith("'"):
                near_solution = f"The answer is a string. Try: <code>{first_solution}</code>"
            elif first_solution in ['if', 'elif', 'else', 'def', 'return', '*', '+', '-', '/', '=']:
                near_solution = f"Use the keyword or operator: <code>{first_solution}</code>"
            elif '(' in first_solution:
                # It's a function call
                near_solution = f"Call the function like this: <code>{first_solution}</code>"
            else:
                near_solution = f"The answer is: <code>{first_solution}</code>"
        else:
            near_solution = "Check the example code carefully and match the pattern you see."

        hints.append({
            "level": 4,
            "type": "near_solution",
            "title": "Almost There",
            "content": f"<p>{near_solution}</p>",
            "triggerTime": 120,
            "triggerAttempts": 5
        })

        return json.dumps(hints)

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
            self.stdout.write('')

        # Step 1: Delete old ExercisePage objects
        self.stdout.write('Step 1: Deleting old single-step exercises...')
        old_exercises = ExercisePage.objects.all()
        count = old_exercises.count()

        if not dry_run:
            for ex in old_exercises:
                self.stdout.write(f'  Deleting: {ex.title}')
                ex.delete()

        self.stdout.write(self.style.SUCCESS(f'✓ Deleted {count} old exercises'))
        self.stdout.write('')

        # Step 2: Get the parent course
        self.stdout.write('Step 2: Finding parent course...')
        try:
            course = CoursePage.objects.get(slug='interactive-python-fundamentals')
            self.stdout.write(self.style.SUCCESS(f'✓ Found course: {course.title}'))
        except CoursePage.DoesNotExist:
            self.stdout.write(self.style.ERROR('✗ Course not found. Please create it first.'))
            return
        self.stdout.write('')

        # Step 3: Create multi-step exercises
        self.stdout.write('Step 3: Creating multi-step exercises...')
        self.stdout.write('')

        exercises_data = self.get_exercises_data()

        for exercise_data in exercises_data:
            self.create_exercise(course, exercise_data, dry_run)

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(exercises_data)} multi-step exercises!'))

    def get_exercises_data(self):
        """Define all exercise data with steps and quizzes."""
        return [
            # Exercise 1: Python Basics - Variables and Strings
            {
                'title': 'Python Basics - Variables and Strings',
                'slug': 'python-basics-variables-strings',
                'sequence_number': 1,
                'difficulty': 'easy',
                'total_points': 100,
                'estimated_time': 15,
                'require_sequential': True,
                'steps': [
                    self.create_step(
                        step_number=1,
                        title='Variable Assignment',
                        description='<div class="step-intro"><p>Let\'s start by learning how to create variables and assign values to them.</p><p><strong>Your Task:</strong> Fill in the blank to assign the string "Python" to the variable.</p></div>',
                        template='first_name = {{BLANK_1}}\nprint(f"My name is {first_name}")',
                        solutions={"1": '"Python"'},
                        points=25,
                        success_message='Excellent! You understand variable assignment.',
                        hint='Variables in Python are created using the = operator. Strings must be wrapped in quotes.'
                    ),
                    {
                        'step_number': 2,
                        'title': 'String Concatenation',
                        'description': '<div class="step-intro"><p>Now let\'s combine strings using the + operator.</p><p><strong>Your Task:</strong> Fill in the blank to add a space between the strings.</p></div>',
                        'exercise_type': 'fill_blank',
                        'template': 'first_name = "Python"\nlast_name = "Programmer"\nfull_name = first_name + {{BLANK_1}} + last_name\nprint(f"Full name: {full_name}")',
                        'solutions': json.dumps({"1": '" "'}),
                        'points': 25,
                        'success_message': 'Great work! String concatenation mastered.',
                        'hint': 'Use a space string " " to separate the names.'
                    },
                    {
                        'step_number': 3,
                        'title': 'String Repetition',
                        'description': '<div class="step-intro"><p>The * operator can repeat strings multiple times.</p><p><strong>Your Task:</strong> Fill in the operator to repeat the exclamation mark 3 times.</p></div>',
                        'exercise_type': 'fill_blank',
                        'template': 'excitement = "!" {{BLANK_1}} 3\nprint(f"Wow{excitement}")',
                        'solutions': json.dumps({"1": "*"}),
                        'points': 25,
                        'success_message': 'Perfect! You know how to repeat strings.',
                        'hint': 'Use the multiplication operator to repeat strings.'
                    },
                    {
                        'step_number': 4,
                        'title': 'Knowledge Check: Variables and Strings',
                        'description': '<div class="quiz-intro"><p>Test your understanding of Python variables and strings!</p></div>',
                        'exercise_type': 'quiz',
                        'template': '',
                        'solutions': json.dumps({
                            "questions": [
                                {
                                    "id": "1",
                                    "question": "What operator is used to assign a value to a variable in Python?",
                                    "options": ["==", "=", "===", ":="],
                                    "correct": "1",
                                    "explanation": "The single equals sign (=) is the assignment operator in Python."
                                },
                                {
                                    "id": "2",
                                    "question": "What does the * operator do when used with a string and a number?",
                                    "options": ["Multiplies the numbers in the string", "Repeats the string", "Divides the string", "Returns an error"],
                                    "correct": "1",
                                    "explanation": "The * operator repeats a string the specified number of times."
                                },
                                {
                                    "id": "3",
                                    "question": "How do you combine two strings in Python?",
                                    "options": ["Using the - operator", "Using the / operator", "Using the + operator", "Using the % operator"],
                                    "correct": "2",
                                    "explanation": "The + operator concatenates (combines) strings in Python."
                                }
                            ]
                        }),
                        'points': 25,
                        'success_message': 'Excellent! You aced the variables and strings quiz!',
                        'hint': ''
                    }
                ],
                'completion_message': '<h2>Congratulations! 🎉</h2><p>You\'ve mastered the basics of Python variables and strings!</p>',
                'show_completion_certificate': False
            },

            # Exercise 2: Control Flow - Conditionals
            {
                'title': 'Control Flow - Conditionals',
                'slug': 'control-flow-conditionals',
                'sequence_number': 2,
                'difficulty': 'medium',
                'total_points': 100,
                'estimated_time': 20,
                'require_sequential': True,
                'steps': [
                    {
                        'step_number': 1,
                        'title': 'The If Statement',
                        'description': '<div class="step-intro"><p>Conditional statements let your code make decisions.</p><p><strong>Your Task:</strong> Fill in the keyword to start a conditional check.</p></div>',
                        'exercise_type': 'fill_blank',
                        'template': 'age = 20\n{{BLANK_1}} age >= 18:\n    print("You can vote!")',
                        'solutions': json.dumps({"1": "if"}),
                        'points': 25,
                        'success_message': 'Perfect! You know how to use if statements.',
                        'hint': 'Use "if" to check a condition.'
                    },
                    {
                        'step_number': 2,
                        'title': 'The Elif Clause',
                        'description': '<div class="step-intro"><p>Use elif to check additional conditions.</p><p><strong>Your Task:</strong> Add the keyword for an additional condition check.</p></div>',
                        'exercise_type': 'fill_blank',
                        'template': 'age = 16\nif age >= 18:\n    print("You can vote!")\n{{BLANK_1}} age >= 16:\n    print("You can drive!")',
                        'solutions': json.dumps({"1": "elif"}),
                        'points': 25,
                        'success_message': 'Great! You understand elif clauses.',
                        'hint': 'Use "elif" for additional conditions.'
                    },
                    {
                        'step_number': 3,
                        'title': 'The Else Clause',
                        'description': '<div class="step-intro"><p>The else clause handles all other cases.</p><p><strong>Your Task:</strong> Complete the conditional with the final keyword.</p></div>',
                        'exercise_type': 'fill_blank',
                        'template': 'age = 14\nif age >= 18:\n    print("You can vote!")\nelif age >= 16:\n    print("You can drive!")\n{{BLANK_1}}:\n    print("Keep growing!")',
                        'solutions': json.dumps({"1": "else"}),
                        'points': 25,
                        'success_message': 'Excellent! Conditional logic mastered.',
                        'hint': 'Use "else" for the default case.'
                    },
                    {
                        'step_number': 4,
                        'title': 'Knowledge Check: Conditionals',
                        'description': '<div class="quiz-intro"><p>Test your knowledge of Python conditional statements!</p></div>',
                        'exercise_type': 'quiz',
                        'template': '',
                        'solutions': json.dumps({
                            "questions": [
                                {
                                    "id": "1",
                                    "question": "Which keyword starts a conditional statement in Python?",
                                    "options": ["when", "if", "check", "condition"],
                                    "correct": "1",
                                    "explanation": "The 'if' keyword begins a conditional statement in Python."
                                },
                                {
                                    "id": "2",
                                    "question": "What does the elif keyword do?",
                                    "options": ["Ends the conditional", "Checks additional conditions", "Loops through conditions", "Defines a function"],
                                    "correct": "1",
                                    "explanation": "elif (else if) checks additional conditions when the previous conditions are False."
                                },
                                {
                                    "id": "3",
                                    "question": "When does the else block execute?",
                                    "options": ["Always", "When all conditions are True", "When all conditions are False", "Never"],
                                    "correct": "2",
                                    "explanation": "The else block executes when all previous conditions are False."
                                }
                            ]
                        }),
                        'points': 25,
                        'success_message': 'Perfect score! You understand conditionals!',
                        'hint': ''
                    }
                ],
                'completion_message': '<h2>Amazing Work! 🎉</h2><p>You\'ve mastered Python conditional logic!</p>',
                'show_completion_certificate': False
            },

            # Exercise 3: Functions and Logic
            {
                'title': 'Functions and Logic',
                'slug': 'functions-and-logic',
                'sequence_number': 3,
                'difficulty': 'medium',
                'total_points': 100,
                'estimated_time': 20,
                'require_sequential': True,
                'steps': [
                    {
                        'step_number': 1,
                        'title': 'Defining a Function',
                        'description': '<div class="step-intro"><p>Functions let you organize and reuse code.</p><p><strong>Your Task:</strong> Fill in the keyword to define a function.</p></div>',
                        'exercise_type': 'fill_blank',
                        'template': '{{BLANK_1}} double_number(x):\n    return x * 2',
                        'solutions': json.dumps({"1": "def"}),
                        'points': 25,
                        'success_message': 'Great! You know how to define functions.',
                        'hint': 'Use "def" to define a function in Python.'
                    },
                    {
                        'step_number': 2,
                        'title': 'Returning Values',
                        'description': '<div class="step-intro"><p>Functions can return values using the return keyword.</p><p><strong>Your Task:</strong> Add the keyword to return the result.</p></div>',
                        'exercise_type': 'fill_blank',
                        'template': 'def double_number(x):\n    {{BLANK_1}} x * 2',
                        'solutions': json.dumps({"1": "return"}),
                        'points': 25,
                        'success_message': 'Perfect! You understand return statements.',
                        'hint': 'Use "return" to send a value back from a function.'
                    },
                    {
                        'step_number': 3,
                        'title': 'Calling Functions',
                        'description': '<div class="step-intro"><p>Call a function by using its name with parentheses.</p><p><strong>Your Task:</strong> Call the function with the argument 5.</p></div>',
                        'exercise_type': 'fill_blank',
                        'template': 'def double_number(x):\n    return x * 2\n\nresult = {{BLANK_1}}\nprint(f"Result: {result}")',
                        'solutions': json.dumps({"1": "double_number(5)"}),
                        'points': 25,
                        'success_message': 'Excellent! You can call functions.',
                        'hint': 'Call the function with: double_number(5)'
                    },
                    {
                        'step_number': 4,
                        'title': 'Knowledge Check: Functions',
                        'description': '<div class="quiz-intro"><p>Test your understanding of Python functions!</p></div>',
                        'exercise_type': 'quiz',
                        'template': '',
                        'solutions': json.dumps({
                            "questions": [
                                {
                                    "id": "1",
                                    "question": "What keyword is used to create a function in Python?",
                                    "options": ["function", "def", "func", "define"],
                                    "correct": "1",
                                    "explanation": "The 'def' keyword is used to define functions in Python."
                                },
                                {
                                    "id": "2",
                                    "question": "What does the return statement do?",
                                    "options": ["Ends the program", "Sends a value back", "Prints output", "Creates a variable"],
                                    "correct": "1",
                                    "explanation": "The return statement sends a value back from the function to where it was called."
                                },
                                {
                                    "id": "3",
                                    "question": "How do you call a function named 'greet'?",
                                    "options": ["call greet", "greet()", "run greet", "execute greet"],
                                    "correct": "1",
                                    "explanation": "Functions are called by using their name followed by parentheses: greet()"
                                }
                            ]
                        }),
                        'points': 25,
                        'success_message': 'Fantastic! You understand functions!',
                        'hint': ''
                    }
                ],
                'completion_message': '<h2>Superb! 🎉</h2><p>You\'ve mastered Python functions!</p>',
                'show_completion_certificate': False
            },

            # Exercise 4: Putting It All Together
            {
                'title': 'Putting It All Together',
                'slug': 'putting-it-all-together',
                'sequence_number': 4,
                'difficulty': 'hard',
                'total_points': 100,
                'estimated_time': 25,
                'require_sequential': True,
                'steps': [
                    {
                        'step_number': 1,
                        'title': 'Function with Multiple Parameters',
                        'description': '<div class="step-intro"><p>Functions can accept multiple parameters.</p><p><strong>Your Task:</strong> Define a function that takes two parameters.</p></div>',
                        'exercise_type': 'fill_blank',
                        'template': '{{BLANK_1}} calculate_discount(price, percent):\n    discount = price * (percent / 100)\n    return discount',
                        'solutions': json.dumps({"1": "def"}),
                        'points': 25,
                        'success_message': 'Great! You can create multi-parameter functions.',
                        'hint': 'Use "def" to define the function.'
                    },
                    {
                        'step_number': 2,
                        'title': 'Mathematical Operations',
                        'description': '<div class="step-intro"><p>Perform calculations inside functions.</p><p><strong>Your Task:</strong> Complete the multiplication operation.</p></div>',
                        'exercise_type': 'fill_blank',
                        'template': 'def calculate_discount(price, percent):\n    discount = price {{BLANK_1}} (percent / 100)\n    return discount',
                        'solutions': json.dumps({"1": "*"}),
                        'points': 25,
                        'success_message': 'Perfect! You understand math in functions.',
                        'hint': 'Use * to multiply the price by the percentage.'
                    },
                    {
                        'step_number': 3,
                        'title': 'Type Conversion',
                        'description': '<div class="step-intro"><p>Convert numbers to strings for concatenation.</p><p><strong>Your Task:</strong> Convert the discount number to a string.</p></div>',
                        'exercise_type': 'fill_blank',
                        'template': 'def calculate_discount(price, percent):\n    discount = price * (percent / 100)\n    return "Discount: $" + {{BLANK_1}}\n\nresult = calculate_discount(100, 20)\nprint(result)',
                        'solutions': json.dumps({"1": "str(discount)"}),
                        'points': 25,
                        'success_message': 'Excellent! You know about type conversion.',
                        'hint': 'Use str() to convert the number to a string.'
                    },
                    {
                        'step_number': 4,
                        'title': 'Knowledge Check: Integration',
                        'description': '<div class="quiz-intro"><p>Test your understanding of combining Python concepts!</p></div>',
                        'exercise_type': 'quiz',
                        'template': '',
                        'solutions': json.dumps({
                            "questions": [
                                {
                                    "id": "1",
                                    "question": "Why do we need to convert a number to a string when concatenating?",
                                    "options": ["For performance", "To avoid type errors", "To make it readable", "It's not necessary"],
                                    "correct": "1",
                                    "explanation": "Python can't concatenate strings and numbers directly - they must be the same type."
                                },
                                {
                                    "id": "2",
                                    "question": "What function converts a number to a string?",
                                    "options": ["int()", "str()", "float()", "string()"],
                                    "correct": "1",
                                    "explanation": "The str() function converts any value to a string representation."
                                },
                                {
                                    "id": "3",
                                    "question": "What does this code do: price * (percent / 100)?",
                                    "options": ["Divides price by percent", "Calculates percentage of price", "Multiplies price by 100", "Returns an error"],
                                    "correct": "1",
                                    "explanation": "This calculates what percentage of the price the discount represents."
                                }
                            ]
                        }),
                        'points': 25,
                        'success_message': 'Outstanding! You can integrate multiple concepts!',
                        'hint': ''
                    }
                ],
                'completion_message': '<h2>Incredible! 🎉</h2><p>You\'ve mastered combining Python concepts!</p>',
                'show_completion_certificate': False
            },

            # Exercise 5: Final Assessment
            {
                'title': 'Final Assessment',
                'slug': 'final-assessment',
                'sequence_number': 5,
                'difficulty': 'hard',
                'total_points': 100,
                'estimated_time': 25,
                'require_sequential': True,
                'steps': [
                    {
                        'step_number': 1,
                        'title': 'Building a Greeting Function',
                        'description': '<div class="step-intro"><p>Let\'s create a complete function from scratch.</p><p><strong>Your Task:</strong> Define the function.</p></div>',
                        'exercise_type': 'fill_blank',
                        'template': '{{BLANK_1}} greet(name):\n    message = "Hello, " + name + "!"\n    return message',
                        'solutions': json.dumps({"1": "def"}),
                        'points': 25,
                        'success_message': 'Perfect start!',
                        'hint': 'Use "def" to define functions.'
                    },
                    {
                        'step_number': 2,
                        'title': 'String Building',
                        'description': '<div class="step-intro"><p>Build the greeting message.</p><p><strong>Your Task:</strong> Complete the greeting string.</p></div>',
                        'exercise_type': 'fill_blank',
                        'template': 'def greet(name):\n    message = {{BLANK_1}} + name + "!"\n    return message',
                        'solutions': json.dumps({"1": '"Hello, "'}),
                        'points': 25,
                        'success_message': 'Great string building!',
                        'hint': 'Start with "Hello, " as a string.'
                    },
                    {
                        'step_number': 3,
                        'title': 'Returning the Result',
                        'description': '<div class="step-intro"><p>Return the completed message.</p><p><strong>Your Task:</strong> Return the message variable.</p></div>',
                        'exercise_type': 'fill_blank',
                        'template': 'def greet(name):\n    message = "Hello, " + name + "!"\n    {{BLANK_1}} message\n\ngreeting = greet("Python")\nprint(greeting)',
                        'solutions': json.dumps({"1": "return"}),
                        'points': 25,
                        'success_message': 'Excellent! Complete function created!',
                        'hint': 'Use "return" to send back the message.'
                    },
                    {
                        'step_number': 4,
                        'title': 'Final Knowledge Check',
                        'description': '<div class="quiz-intro"><p>Final quiz covering everything you\'ve learned!</p></div>',
                        'exercise_type': 'quiz',
                        'template': '',
                        'solutions': json.dumps({
                            "questions": [
                                {
                                    "id": "1",
                                    "question": "What are the three main parts of a complete function?",
                                    "options": ["def, name, return", "if, elif, else", "for, while, break", "class, method, object"],
                                    "correct": "0",
                                    "explanation": "Functions need a definition (def), a name, and typically a return statement."
                                },
                                {
                                    "id": "2",
                                    "question": "Which operator combines strings in Python?",
                                    "options": ["&", "+", "*", "/"],
                                    "correct": "1",
                                    "explanation": "The + operator concatenates (combines) strings together."
                                },
                                {
                                    "id": "3",
                                    "question": "What makes code reusable and organized?",
                                    "options": ["Comments", "Functions", "Variables", "Strings"],
                                    "correct": "1",
                                    "explanation": "Functions allow you to organize code into reusable blocks that can be called multiple times."
                                }
                            ]
                        }),
                        'points': 25,
                        'success_message': 'Perfect! You\'ve completed the course!',
                        'hint': ''
                    }
                ],
                'completion_message': '<h2>🎉 CONGRATULATIONS! 🎉</h2><p>You\'ve completed the entire Python Fundamentals course!</p><p>You\'re now ready to build amazing things with Python!</p>',
                'show_completion_certificate': True
            }
        ]

    def create_exercise(self, course, exercise_data, dry_run):
        """Create a single multi-step exercise."""
        title = exercise_data['title']
        self.stdout.write(f'Creating: {title}')

        if dry_run:
            self.stdout.write(f'  Would create exercise with {len(exercise_data["steps"])} steps')
            for step in exercise_data['steps']:
                self.stdout.write(f'    Step {step["step_number"]}: {step["title"]} ({step["exercise_type"]})')
            return

        # Create the StepBasedExercisePage
        exercise = StepBasedExercisePage(
            title=exercise_data['title'],
            slug=exercise_data['slug'],
            sequence_number=exercise_data['sequence_number'],
            difficulty=exercise_data['difficulty'],
            total_points=exercise_data['total_points'],
            estimated_time=exercise_data['estimated_time'],
            require_sequential=exercise_data['require_sequential'],
            completion_message=exercise_data['completion_message'],
            show_completion_certificate=exercise_data['show_completion_certificate']
        )

        # Build the StreamField data for steps
        steps_data = []
        for step in exercise_data['steps']:
            steps_data.append(('exercise_step', {
                'step_number': step['step_number'],
                'title': step['title'],
                'description': step['description'],
                'exercise_type': step['exercise_type'],
                'template': step['template'],
                'solutions': step['solutions'],
                'points': step['points'],
                'success_message': step['success_message'],
                'hint': step['hint']
            }))

        exercise.exercise_steps = steps_data

        # Add as child of course
        course.add_child(instance=exercise)

        # Publish the exercise
        revision = exercise.save_revision()
        revision.publish()

        self.stdout.write(self.style.SUCCESS(f'  ✓ Created with {len(exercise_data["steps"])} steps'))
