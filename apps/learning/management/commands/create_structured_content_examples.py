"""
Django management command to create example structured content for lessons.
"""

from django.core.management.base import BaseCommand
from apps.learning.models import Lesson, Course, Category


class Command(BaseCommand):
    help = 'Create example lessons with structured content blocks'

    def add_arguments(self, parser):
        parser.add_argument(
            '--course-id',
            type=int,
            help='ID of the course to add lessons to',
        )
        parser.add_argument(
            '--create-course',
            action='store_true',
            help='Create a sample course for the structured content examples',
        )

    def handle(self, *args, **options):
        # Create or get course
        if options['create_course']:
            course = self.create_sample_course()
        elif options['course_id']:
            try:
                course = Course.objects.get(id=options['course_id'])
            except Course.DoesNotExist:
                self.stderr.write(f"Course with ID {options['course_id']} does not exist.")
                return
        else:
            # Use the first available course
            course = Course.objects.first()
            if not course:
                self.stderr.write("No courses found. Use --create-course to create one.")
                return

        self.stdout.write(f"Creating structured content examples for course: {course.title}")

        # Create sample lessons with different content types
        self.create_variables_lesson(course)
        self.create_functions_lesson(course)
        self.create_loops_lesson(course)

        self.stdout.write(
            self.style.SUCCESS('Successfully created structured content examples!')
        )

    def create_sample_course(self):
        """Create a sample course for structured content examples."""
        category, _ = Category.objects.get_or_create(
            name='Python Basics',
            defaults={
                'slug': 'python-basics',
                'description': 'Fundamental Python programming concepts',
                'color': '#3498db'
            }
        )

        from django.contrib.auth import get_user_model
        User = get_user_model()
        instructor = User.objects.first()
        
        if not instructor:
            self.stderr.write("No users found. Create a user first.")
            return None

        course, created = Course.objects.get_or_create(
            title='Structured Content Examples',
            defaults={
                'slug': 'structured-content-examples',
                'description': 'Example course showcasing structured content features',
                'short_description': 'Learn with interactive content blocks',
                'category': category,
                'instructor': instructor,
                'difficulty_level': 'beginner',
                'estimated_duration': 5,
                'learning_objectives': 'Understand structured content capabilities',
                'is_published': True,
                'is_free': True
            }
        )

        if created:
            self.stdout.write(f"Created sample course: {course.title}")
        else:
            self.stdout.write(f"Using existing course: {course.title}")

        return course

    def create_variables_lesson(self, course):
        """Create a lesson about Python variables with structured content."""
        lesson, created = Lesson.objects.get_or_create(
            title='Python Variables and Data Types',
            course=course,
            defaults={
                'slug': 'python-variables-structured',
                'description': 'Learn about Python variables using interactive content blocks',
                'lesson_type': 'theory',
                'difficulty_level': 'beginner',
                'order': 1,
                'estimated_duration': 30,
                'enable_structured_content': True,
                'content_format': 'structured',
                'is_published': True
            }
        )

        if not created:
            self.stdout.write(f"Lesson '{lesson.title}' already exists, updating content...")

        # Define structured content blocks
        lesson.structured_content = [
            {
                'type': 'heading',
                'content': 'Introduction to Python Variables',
                'level': 2,
                'id': 0
            },
            {
                'type': 'text',
                'content': 'Variables in Python are containers for storing data values. Unlike other programming languages, Python has no command for declaring a variable - you create one the moment you first assign a value to it.',
                'format': 'plain',
                'id': 1
            },
            {
                'type': 'note',
                'title': 'Important',
                'content': 'Python variable names are case-sensitive. This means that <code>myvar</code> and <code>MyVar</code> are two different variables.',
                'id': 2
            },
            {
                'type': 'heading',
                'content': 'Creating Variables',
                'level': 3,
                'id': 3
            },
            {
                'type': 'code_example',
                'content': '# Creating variables in Python\nname = "John"\nage = 25\nheight = 5.9\nis_student = True\n\n# Python automatically determines the data type\nprint(type(name))     # <class \'str\'>\nprint(type(age))      # <class \'int\'>\nprint(type(height))   # <class \'float\'>\nprint(type(is_student)) # <class \'bool\'>',
                'language': 'python',
                'title': 'Variable Creation Examples',
                'filename': 'variables.py',
                'show_line_numbers': True,
                'id': 4
            },
            {
                'type': 'tip',
                'title': 'Pro Tip',
                'content': 'Use descriptive variable names to make your code more readable. Instead of <code>x = 25</code>, use <code>student_age = 25</code>.',
                'id': 5
            },
            {
                'type': 'heading',
                'content': 'Data Types',
                'level': 3,
                'id': 6
            },
            {
                'type': 'text',
                'content': 'Python has several built-in data types:',
                'id': 7
            },
            {
                'type': 'list',
                'title': 'Common Python Data Types',
                'list_type': 'unordered',
                'items': [
                    '<strong>str</strong> - Text data (strings)',
                    '<strong>int</strong> - Whole numbers',
                    '<strong>float</strong> - Decimal numbers',
                    '<strong>bool</strong> - True/False values',
                    '<strong>list</strong> - Ordered collections',
                    '<strong>dict</strong> - Key-value pairs'
                ],
                'id': 8
            },
            {
                'type': 'interactive_code',
                'content': '# Try changing these variables and see what happens\nfavorite_color = "blue"\nlucky_number = 7\npi_value = 3.14159\n\n# What will these print?\nprint(f"My favorite color is {favorite_color}")\nprint(f"My lucky number is {lucky_number}")\nprint(f"Pi is approximately {pi_value}")',
                'language': 'python',
                'exercise_type': 'fill_blank',
                'expected_output': 'My favorite color is blue\nMy lucky number is 7\nPi is approximately 3.14159',
                'id': 9
            },
            {
                'type': 'quiz_question',
                'content': 'What data type would Python assign to the variable <code>score = 95.5</code>?',
                'options': ['int', 'float', 'str', 'bool'],
                'correct_answer': 1,
                'explanation': 'Since 95.5 contains a decimal point, Python automatically assigns it the float data type.',
                'id': 10
            },
            {
                'type': 'warning',
                'title': 'Common Mistake',
                'content': 'Don\'t forget that variable names cannot start with a number. <code>2name</code> is invalid, but <code>name2</code> is perfectly fine.',
                'id': 11
            }
        ]

        lesson.save()
        self.stdout.write(f"✓ Created/updated lesson: {lesson.title}")

    def create_functions_lesson(self, course):
        """Create a lesson about Python functions with structured content."""
        lesson, created = Lesson.objects.get_or_create(
            title='Python Functions',
            course=course,
            defaults={
                'slug': 'python-functions-structured',
                'description': 'Master Python functions with interactive examples',
                'lesson_type': 'practical',
                'difficulty_level': 'beginner',
                'order': 2,
                'estimated_duration': 45,
                'enable_structured_content': True,
                'content_format': 'structured',
                'is_published': True
            }
        )

        lesson.structured_content = [
            {
                'type': 'heading',
                'content': 'Understanding Python Functions',
                'level': 2,
                'id': 0
            },
            {
                'type': 'text',
                'content': 'Functions are reusable blocks of code that perform specific tasks. They help organize code, reduce repetition, and make programs more modular and easier to maintain.',
                'id': 1
            },
            {
                'type': 'alert',
                'alert_type': 'info',
                'title': 'Why Use Functions?',
                'content': 'Functions promote code reusability, improve readability, and make debugging easier. Instead of writing the same code multiple times, you can write it once in a function and call it whenever needed.',
                'id': 2
            },
            {
                'type': 'heading',
                'content': 'Function Syntax',
                'level': 3,
                'id': 3
            },
            {
                'type': 'code_example',
                'content': 'def function_name(parameters):\n    """\n    Optional docstring describing the function\n    """\n    # Function body\n    # Perform operations\n    return result  # Optional return statement',
                'language': 'python',
                'title': 'Basic Function Structure',
                'id': 4
            },
            {
                'type': 'heading',
                'content': 'Simple Function Example',
                'level': 3,
                'id': 5
            },
            {
                'type': 'code_example',
                'content': 'def greet(name):\n    """\n    Function to greet a person\n    """\n    message = f"Hello, {name}! Welcome to Python programming."\n    return message\n\n# Call the function\nresult = greet("Alice")\nprint(result)\n\n# You can also call it directly\nprint(greet("Bob"))',
                'language': 'python',
                'title': 'Greeting Function',
                'filename': 'greet.py',
                'id': 6
            },
            {
                'type': 'interactive_code',
                'content': 'def calculate_area(length, width):\n    """\n    Calculate the area of a rectangle\n    """\n    area = length * width\n    return area\n\n# Test the function\nroom_area = calculate_area(12, 10)\nprint(f"Room area: {room_area} square meters")',
                'language': 'python',
                'exercise_type': 'modify_and_run',
                'expected_output': 'Room area: 120 square meters',
                'id': 7
            },
            {
                'type': 'tip',
                'title': 'Function Naming',
                'content': 'Use descriptive names for your functions. <code>calculate_area()</code> is much better than <code>calc()</code> or <code>func1()</code>.',
                'id': 8
            },
            {
                'type': 'heading',
                'content': 'Parameters vs Arguments',
                'level': 3,
                'id': 9
            },
            {
                'type': 'table',
                'title': 'Parameters vs Arguments',
                'headers': ['Term', 'Definition', 'Example'],
                'rows': [
                    ['Parameter', 'Variables in function definition', 'def greet(name): # name is parameter'],
                    ['Argument', 'Actual values passed to function', 'greet("Alice") # "Alice" is argument']
                ],
                'id': 10
            },
            {
                'type': 'quiz_question',
                'content': 'What will this function return when called with <code>multiply(4, 5)</code>?<br><pre>def multiply(a, b):\n    return a * b</pre>',
                'options': ['9', '20', '45', 'Error'],
                'correct_answer': 1,
                'explanation': 'The function multiplies 4 × 5 = 20 and returns the result.',
                'id': 11
            }
        ]

        lesson.save()
        self.stdout.write(f"✓ Created/updated lesson: {lesson.title}")

    def create_loops_lesson(self, course):
        """Create a lesson about Python loops with structured content."""
        lesson, created = Lesson.objects.get_or_create(
            title='Python Loops and Iteration',
            course=course,
            defaults={
                'slug': 'python-loops-structured',
                'description': 'Learn Python loops with hands-on examples',
                'lesson_type': 'practical',
                'difficulty_level': 'intermediate',
                'order': 3,
                'estimated_duration': 40,
                'enable_structured_content': True,
                'content_format': 'structured',
                'is_published': True
            }
        )

        lesson.structured_content = [
            {
                'type': 'heading',
                'content': 'Python Loops: Automating Repetitive Tasks',
                'level': 2,
                'id': 0
            },
            {
                'type': 'text',
                'content': 'Loops allow you to execute code repeatedly without writing the same statements over and over. Python provides two main types of loops: <code>for</code> loops and <code>while</code> loops.',
                'id': 1
            },
            {
                'type': 'heading',
                'content': 'For Loops',
                'level': 3,
                'id': 2
            },
            {
                'type': 'text',
                'content': 'For loops are used to iterate over sequences (like lists, strings, or ranges). They\'re perfect when you know in advance how many times you want to repeat something.',
                'id': 3
            },
            {
                'type': 'code_example',
                'content': '# Loop through a list of fruits\nfruits = ["apple", "banana", "cherry", "date"]\n\nfor fruit in fruits:\n    print(f"I love {fruit}s!")\n\nprint("\\nLoop finished!")\n\n# Loop through a range of numbers\nprint("\\nCounting to 5:")\nfor i in range(1, 6):\n    print(f"Number: {i}")',
                'language': 'python',
                'title': 'For Loop Examples',
                'filename': 'for_loops.py',
                'id': 4
            },
            {
                'type': 'note',
                'title': 'Range Function',
                'content': 'The <code>range()</code> function generates a sequence of numbers. <code>range(1, 6)</code> creates numbers 1, 2, 3, 4, 5 (the end number is excluded).',
                'id': 5
            },
            {
                'type': 'heading',
                'content': 'While Loops',
                'level': 3,
                'id': 6
            },
            {
                'type': 'text',
                'content': 'While loops continue executing as long as a condition remains true. They\'re useful when you don\'t know exactly how many iterations you need.',
                'id': 7
            },
            {
                'type': 'code_example',
                'content': '# Simple counting with while loop\ncount = 1\n\nwhile count <= 5:\n    print(f"Count is: {count}")\n    count += 1  # Increment count\n\nprint("Loop finished!")\n\n# User input example (simulation)\nuser_input = ""\nwhile user_input != "quit":\n    # In real code, you\'d use input() here\n    print("Type \'quit\' to exit")\n    user_input = "quit"  # Simulated user input\n    \nprint("Goodbye!")',
                'language': 'python',
                'title': 'While Loop Examples',
                'filename': 'while_loops.py',
                'id': 8
            },
            {
                'type': 'warning',
                'title': 'Infinite Loops',
                'content': 'Be careful with while loops! If the condition never becomes false, you\'ll create an infinite loop. Always make sure your loop variable changes in a way that will eventually make the condition false.',
                'id': 9
            },
            {
                'type': 'interactive_code',
                'content': '# Calculate the sum of numbers from 1 to 10\ntotal = 0\n\nfor number in range(1, 11):\n    total += number\n\nprint(f"The sum of numbers 1 to 10 is: {total}")\n\n# Can you modify this to calculate the sum from 1 to 20?',
                'language': 'python',
                'exercise_type': 'modify_and_run',
                'expected_output': 'The sum of numbers 1 to 10 is: 55',
                'id': 10
            },
            {
                'type': 'quiz_question',
                'content': 'How many times will this loop execute?<br><pre>for i in range(3, 8):\n    print(i)</pre>',
                'options': ['3 times', '5 times', '8 times', '6 times'],
                'correct_answer': 1,
                'explanation': 'range(3, 8) generates numbers 3, 4, 5, 6, 7 - that\'s 5 numbers, so the loop executes 5 times.',
                'id': 11
            },
            {
                'type': 'tip',
                'title': 'Loop Control',
                'content': 'You can use <code>break</code> to exit a loop early and <code>continue</code> to skip the rest of the current iteration and move to the next one.',
                'id': 12
            }
        ]

        lesson.save()
        self.stdout.write(f"✓ Created/updated lesson: {lesson.title}")