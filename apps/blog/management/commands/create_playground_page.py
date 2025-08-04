"""
Management command to create the Wagtail CodePlaygroundPage.
"""

from django.core.management.base import BaseCommand
from wagtail.models import Site
from apps.blog.models import HomePage, CodePlaygroundPage


class Command(BaseCommand):
    help = 'Create a Wagtail CodePlaygroundPage with default content'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Delete existing playground page and create a new one',
        )

    def handle(self, *args, **options):
        self.stdout.write('Creating Wagtail CodePlaygroundPage...')

        # Get the site root (HomePage)
        try:
            homepage = HomePage.objects.live().first()
            if not homepage:
                self.stdout.write(
                    self.style.ERROR('Homepage not found. Please create a homepage first.')
                )
                return
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error finding homepage: {e}')
            )
            return

        # Check if playground page already exists
        existing_playground = CodePlaygroundPage.objects.filter(live=True).first()
        if existing_playground:
            if options['force']:
                self.stdout.write('Deleting existing playground page...')
                existing_playground.delete()
            else:
                self.stdout.write(
                    self.style.WARNING('Playground page already exists. Use --force to recreate.')
                )
                return

        # Create the playground page
        try:
            playground_page = CodePlaygroundPage(
                title='Code Playground',
                slug='playground',
                description='<p>Write, test, and experiment with code in our interactive playground. Perfect for trying out new ideas, testing snippets, or learning programming concepts.</p>',
                default_code='''# Welcome to Python Learning Studio Playground!
# Write your Python code here and click Run to execute it.

def greet(name):
    """A simple greeting function"""
    return f"Hello, {name}! Welcome to Python programming!"

# Try it out
message = greet("Programmer")
print(message)

# You can also do calculations
result = 42 * 2
print(f"The answer to everything times 2 is: {result}")

# Let's try a loop
for i in range(3):
    print(f"Loop iteration: {i + 1}")

# And some list operations
numbers = [1, 2, 3, 4, 5]
squared = [x**2 for x in numbers]
print(f"Original: {numbers}")
print(f"Squared: {squared}")
''',
                programming_language='python',
                enable_file_operations=True,
                enable_auto_save=True,
                enable_multiple_languages=True,
                features=[
                    {
                        'type': 'feature',
                        'value': {
                            'title': 'Real-time Code Execution',
                            'description': 'Run your code instantly and see results',
                            'icon': 'play-circle'
                        }
                    },
                    {
                        'type': 'feature',
                        'value': {
                            'title': 'Syntax Highlighting',
                            'description': 'Beautiful code highlighting for better readability',
                            'icon': 'code'
                        }
                    },
                    {
                        'type': 'feature',
                        'value': {
                            'title': 'Auto-save Functionality',
                            'description': 'Your code is automatically saved as you type',
                            'icon': 'save'
                        }
                    },
                    {
                        'type': 'feature',
                        'value': {
                            'title': 'Multiple Languages',
                            'description': 'Support for Python, JavaScript, HTML, CSS, and more',
                            'icon': 'layers'
                        }
                    }
                ],
                shortcuts=[
                    {
                        'type': 'shortcut',
                        'value': {
                            'keys': 'Ctrl+S',
                            'description': 'Save code'
                        }
                    },
                    {
                        'type': 'shortcut',
                        'value': {
                            'keys': 'Ctrl+Enter',
                            'description': 'Run code'
                        }
                    },
                    {
                        'type': 'shortcut',
                        'value': {
                            'keys': 'Tab',
                            'description': 'Indent'
                        }
                    },
                    {
                        'type': 'shortcut',
                        'value': {
                            'keys': 'Shift+Tab',
                            'description': 'Unindent'
                        }
                    }
                ],
                code_examples=[
                    {
                        'type': 'example',
                        'value': {
                            'title': 'Hello World',
                            'description': 'Your first Python program',
                            'language': 'python',
                            'code': 'print("Hello, World!")',
                            'category': 'basic'
                        }
                    },
                    {
                        'type': 'example',
                        'value': {
                            'title': 'Variables and Types',
                            'description': 'Working with different data types',
                            'language': 'python',
                            'code': '''# Variables and types
name = "Alice"
age = 25
height = 5.6
is_student = True

print(f"Name: {name}")
print(f"Age: {age}")
print(f"Height: {height}")
print(f"Is student: {is_student}")''',
                            'category': 'basic'
                        }
                    },
                    {
                        'type': 'example',
                        'value': {
                            'title': 'Lists and Loops',
                            'description': 'Working with lists and iteration',
                            'language': 'python',
                            'code': '''# Lists and loops
fruits = ["apple", "banana", "orange"]

print("Fruits:")
for fruit in fruits:
    print(f"- {fruit}")

# List comprehension
upper_fruits = [fruit.upper() for fruit in fruits]
print(f"Uppercase: {upper_fruits}")''',
                            'category': 'intermediate'
                        }
                    },
                    {
                        'type': 'example',
                        'value': {
                            'title': 'Functions',
                            'description': 'Creating and using functions',
                            'language': 'python',
                            'code': '''def calculate_area(length, width):
    """Calculate the area of a rectangle."""
    return length * width

def greet_user(name, greeting="Hello"):
    """Greet a user with a custom message."""
    return f"{greeting}, {name}!"

# Using functions
area = calculate_area(5, 3)
message = greet_user("Python Developer")

print(f"Area: {area}")
print(message)''',
                            'category': 'intermediate'
                        }
                    },
                    {
                        'type': 'example',
                        'value': {
                            'title': 'Classes and Objects',
                            'description': 'Object-oriented programming basics',
                            'language': 'python',
                            'code': '''class Student:
    def __init__(self, name, grade):
        self.name = name
        self.grade = grade
        self.courses = []
    
    def add_course(self, course):
        self.courses.append(course)
    
    def get_info(self):
        return f"{self.name} (Grade: {self.grade})"

# Create a student
student = Student("Alice", "A")
student.add_course("Python Programming")
student.add_course("Data Structures")

print(student.get_info())
print(f"Courses: {student.courses}")''',
                            'category': 'advanced'
                        }
                    },
                    {
                        'type': 'example',
                        'value': {
                            'title': 'File Operations',
                            'description': 'Reading and writing files',
                            'language': 'python',
                            'code': '''# Note: File operations may be limited in the playground
import io

# Simulate file content
file_content = """Line 1
Line 2  
Line 3"""

# Read lines
lines = file_content.split('\\n')
print("File contents:")
for i, line in enumerate(lines, 1):
    print(f"{i}: {line}")

# Process data
line_count = len(lines)
char_count = len(file_content)
print(f"\\nStatistics:")
print(f"Lines: {line_count}")
print(f"Characters: {char_count}")''',
                            'category': 'advanced'
                        }
                    }
                ]
            )

            # Add the page as a child of the homepage
            homepage.add_child(instance=playground_page)
            
            # Publish the page
            playground_page.save_revision().publish()

            self.stdout.write(
                self.style.SUCCESS(f'Successfully created playground page: {playground_page.title}')
            )
            self.stdout.write(f'URL: {playground_page.url}')
            self.stdout.write(f'Admin URL: /admin/pages/{playground_page.id}/edit/')

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating playground page: {e}')
            )
            import traceback
            traceback.print_exc()