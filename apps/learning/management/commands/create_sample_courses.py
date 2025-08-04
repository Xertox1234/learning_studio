"""
Management command to create sample course data for Python Learning Studio.
This creates a complete learning environment with courses, lessons, and exercises.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from apps.learning.models import (
    Category, Course, Lesson, Exercise, CourseEnrollment, 
    ProgrammingLanguage, ExerciseType, TestCase
)
from apps.learning.exercise_models import Submission
import random

User = get_user_model()


class Command(BaseCommand):
    help = 'Create sample course data for Python Learning Studio'

    def add_arguments(self, parser):
        parser.add_argument(
            '--delete-existing',
            action='store_true',
            help='Delete existing course data before creating new',
        )

    def handle(self, *args, **options):
        if options['delete_existing']:
            self.stdout.write('Deleting existing course data...')
            Course.objects.all().delete()
            Category.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Existing data deleted.'))

        self.stdout.write('Creating sample course data...')
        
        # Create categories
        categories = self.create_categories()
        
        # Create instructor user
        instructor = self.create_instructor()
        
        # Create courses
        courses = self.create_courses(categories, instructor)
        
        # Create lessons for each course
        for course in courses:
            self.create_lessons_for_course(course)
        
        # Create sample enrollments
        self.create_sample_enrollments(courses)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {len(courses)} courses with lessons and exercises!'
            )
        )

    def create_categories(self):
        """Create course categories."""
        categories_data = [
            {
                'name': 'Python Programming',
                'slug': 'python-programming',
                'description': 'Learn Python from basics to advanced concepts',
                'icon': 'fab fa-python',
                'color': '#3776ab'
            },
            {
                'name': 'Web Development',
                'slug': 'web-development', 
                'description': 'Build modern web applications',
                'icon': 'fas fa-globe',
                'color': '#61dafb'
            },
            {
                'name': 'Data Science',
                'slug': 'data-science',
                'description': 'Analyze data and build machine learning models',
                'icon': 'fas fa-chart-line',
                'color': '#ff6b6b'
            },
            {
                'name': 'Algorithms',
                'slug': 'algorithms',
                'description': 'Master computer science algorithms',
                'icon': 'fas fa-sitemap',
                'color': '#4ecdc4'
            }
        ]
        
        categories = []
        for cat_data in categories_data:
            category, created = Category.objects.get_or_create(
                slug=cat_data['slug'],
                defaults=cat_data
            )
            categories.append(category)
            if created:
                self.stdout.write(f'Created category: {category.name}')
        
        return categories

    def create_instructor(self):
        """Create instructor user."""
        instructor, created = User.objects.get_or_create(
            username='instructor',
            defaults={
                'email': 'instructor@pythonlearning.com',
                'first_name': 'John',
                'last_name': 'Smith',
                'is_staff': True
            }
        )
        if created:
            instructor.set_password('instructor123')
            instructor.save()
            self.stdout.write('Created instructor user: instructor')
        return instructor

    def create_courses(self, categories, instructor):
        """Create sample courses."""
        courses_data = [
            {
                'title': 'Python Fundamentals',
                'slug': 'python-fundamentals',
                'category': categories[0],  # Python Programming
                'short_description': 'Master the basics of Python programming',
                'description': 'A comprehensive introduction to Python programming. Learn variables, data types, control structures, functions, and object-oriented programming.',
                'learning_objectives': '''
• Understand Python syntax and basic programming concepts
• Work with variables, data types, and operators
• Use control structures (if/else, loops)
• Define and use functions
• Apply object-oriented programming principles
• Handle files and exceptions
• Build simple projects
                ''',
                'prerequisites': 'No programming experience required',
                'difficulty_level': 'beginner',
                'estimated_duration': 40,
                'is_published': True,
                'is_featured': True,
                'is_free': True
            },
            {
                'title': 'Advanced Python Programming',
                'slug': 'advanced-python',
                'category': categories[0],  # Python Programming
                'short_description': 'Take your Python skills to the next level',
                'description': 'Dive deep into advanced Python concepts including decorators, generators, context managers, and metaclasses.',
                'learning_objectives': '''
• Master advanced Python features
• Use decorators and context managers
• Understand generators and iterators
• Apply metaclasses and descriptors
• Work with concurrency and async programming
• Optimize code performance
                ''',
                'prerequisites': 'Completion of Python Fundamentals or equivalent experience',
                'difficulty_level': 'advanced',
                'estimated_duration': 60,
                'is_published': True,
                'is_featured': False,
                'is_free': True
            },
            {
                'title': 'Web Development with Django',
                'slug': 'django-web-development',
                'category': categories[1],  # Web Development
                'short_description': 'Build powerful web applications with Django',
                'description': 'Learn to build modern web applications using Django framework. Cover models, views, templates, authentication, and deployment.',
                'learning_objectives': '''
• Set up Django development environment
• Create models and work with databases
• Build views and templates
• Implement user authentication
• Deploy applications to production
• Follow Django best practices
                ''',
                'prerequisites': 'Basic Python knowledge required',
                'difficulty_level': 'intermediate',
                'estimated_duration': 80,
                'is_published': True,
                'is_featured': True,
                'is_free': True
            },
            {
                'title': 'Data Science with Python',
                'slug': 'data-science-python',
                'category': categories[2],  # Data Science
                'short_description': 'Analyze data and build machine learning models',
                'description': 'Complete introduction to data science using Python. Learn pandas, numpy, matplotlib, and scikit-learn.',
                'learning_objectives': '''
• Use pandas for data manipulation
• Create visualizations with matplotlib
• Apply statistical analysis techniques
• Build machine learning models
• Work with real-world datasets
• Present data insights effectively
                ''',
                'prerequisites': 'Basic Python and statistics knowledge',
                'difficulty_level': 'intermediate',
                'estimated_duration': 100,
                'is_published': True,
                'is_featured': False,
                'is_free': True
            },
            {
                'title': 'Algorithms and Data Structures',
                'slug': 'algorithms-data-structures',
                'category': categories[3],  # Algorithms
                'short_description': 'Master essential algorithms and data structures',
                'description': 'Comprehensive course on algorithms and data structures. Perfect for technical interviews and problem-solving.',
                'learning_objectives': '''
• Understand algorithm complexity (Big O)
• Implement sorting and searching algorithms
• Work with trees, graphs, and hash tables
• Apply dynamic programming techniques
• Solve coding interview problems
• Optimize algorithm performance
                ''',
                'prerequisites': 'Solid programming foundation in any language',
                'difficulty_level': 'advanced',
                'estimated_duration': 90,
                'is_published': True,
                'is_featured': False,
                'is_free': True
            }
        ]
        
        courses = []
        for course_data in courses_data:
            course, created = Course.objects.get_or_create(
                slug=course_data['slug'],
                defaults={
                    **course_data,
                    'instructor': instructor
                }
            )
            courses.append(course)
            if created:
                self.stdout.write(f'Created course: {course.title}')
        
        return courses

    def create_lessons_for_course(self, course):
        """Create lessons for a specific course."""
        if course.slug == 'python-fundamentals':
            self.create_python_fundamentals_lessons(course)
        elif course.slug == 'advanced-python':
            self.create_advanced_python_lessons(course)
        elif course.slug == 'django-web-development':
            self.create_django_lessons(course)
        elif course.slug == 'data-science-python':
            self.create_data_science_lessons(course)
        elif course.slug == 'algorithms-data-structures':
            self.create_algorithms_lessons(course)

    def create_python_fundamentals_lessons(self, course):
        """Create lessons for Python Fundamentals course."""
        lessons_data = [
            {
                'title': 'Introduction to Python',
                'slug': 'introduction-to-python',
                'description': 'Get started with Python programming',
                'content': '''
# Introduction to Python

Welcome to Python programming! Python is a powerful, easy-to-learn programming language that's used for web development, data science, automation, and much more.

## What is Python?

Python is an interpreted, high-level programming language known for its simplicity and readability. It was created by Guido van Rossum and first released in 1991.

## Why Learn Python?

- **Easy to learn**: Simple and readable syntax
- **Versatile**: Used in many fields
- **Large community**: Extensive libraries and support
- **High demand**: Popular in job market

## Your First Python Program

Let's start with the traditional "Hello, World!" program:

```python
print("Hello, World!")
```

This simple line of code will output "Hello, World!" to the screen.

## Exercise

Try running the code above and modify it to print your own message!
                ''',
                'lesson_type': 'theory',
                'difficulty_level': 'beginner',
                'order': 1,
                'estimated_duration': 30,
                'is_published': True
            },
            {
                'title': 'Variables and Data Types',
                'slug': 'variables-data-types',
                'description': 'Learn about Python variables and basic data types',
                'content': '''
# Variables and Data Types

In Python, variables are used to store data values. Python has several built-in data types.

## Variables

Variables are created when you assign a value to them:

```python
name = "Alice"
age = 25
height = 5.6
is_student = True
```

## Basic Data Types

### Strings (str)
Text data enclosed in quotes:
```python
message = "Hello, Python!"
first_name = 'John'
```

### Integers (int)
Whole numbers:
```python
count = 42
year = 2023
```

### Floats (float)
Decimal numbers:
```python
price = 19.99
temperature = 98.6
```

### Booleans (bool)
True or False values:
```python
is_active = True
is_complete = False
```

## Type Function

You can check the type of a variable using the `type()` function:

```python
print(type(name))     # <class 'str'>
print(type(age))      # <class 'int'>
print(type(height))   # <class 'float'>
```
                ''',
                'lesson_type': 'theory',
                'difficulty_level': 'beginner',
                'order': 2,
                'estimated_duration': 45,
                'is_published': True
            },
            {
                'title': 'Control Structures',
                'slug': 'control-structures',
                'description': 'Learn if statements, loops, and decision making',
                'content': '''
# Control Structures

Control structures allow you to control the flow of your program.

## If Statements

Make decisions in your code:

```python
age = 18

if age >= 18:
    print("You are an adult")
elif age >= 13:
    print("You are a teenager")
else:
    print("You are a child")
```

## For Loops

Repeat code for each item in a sequence:

```python
fruits = ["apple", "banana", "orange"]

for fruit in fruits:
    print(f"I like {fruit}")

# Using range for numbers
for i in range(5):
    print(f"Number: {i}")
```

## While Loops

Repeat code while a condition is true:

```python
count = 0
while count < 5:
    print(f"Count: {count}")
    count += 1
```

## Practice Exercise

Write a program that prints numbers from 1 to 10, but prints "Fizz" for multiples of 3 and "Buzz" for multiples of 5.
                ''',
                'lesson_type': 'practical',
                'difficulty_level': 'beginner',
                'order': 3,
                'estimated_duration': 60,
                'is_published': True
            },
            {
                'title': 'Functions',
                'slug': 'functions',
                'description': 'Learn to create and use functions in Python',
                'content': '''
# Functions

Functions are reusable blocks of code that perform specific tasks.

## Defining Functions

Use the `def` keyword to create a function:

```python
def greet(name):
    return f"Hello, {name}!"

# Call the function
message = greet("Alice")
print(message)  # Output: Hello, Alice!
```

## Function Parameters

Functions can accept multiple parameters:

```python
def add_numbers(a, b):
    return a + b

result = add_numbers(5, 3)
print(result)  # Output: 8
```

## Default Parameters

You can provide default values for parameters:

```python
def greet(name, greeting="Hello"):
    return f"{greeting}, {name}!"

print(greet("Bob"))              # Output: Hello, Bob!
print(greet("Bob", "Hi"))        # Output: Hi, Bob!
```

## Scope

Variables inside functions have local scope:

```python
def my_function():
    local_var = "I'm local"
    print(local_var)

global_var = "I'm global"

my_function()
print(global_var)
```

## Lambda Functions

Short, anonymous functions:

```python
square = lambda x: x ** 2
print(square(5))  # Output: 25
```
                ''',
                'lesson_type': 'theory',
                'difficulty_level': 'beginner',
                'order': 4,
                'estimated_duration': 50,
                'is_published': True
            },
            {
                'title': 'Data Structures',
                'slug': 'data-structures',
                'description': 'Work with lists, dictionaries, tuples, and sets',
                'content': '''
# Data Structures

Python provides several built-in data structures to organize and store data.

## Lists

Ordered, mutable collections:

```python
fruits = ["apple", "banana", "orange"]
fruits.append("grape")
fruits[0] = "pear"
print(fruits)  # ['pear', 'banana', 'orange', 'grape']
```

## Dictionaries

Key-value pairs:

```python
person = {
    "name": "Alice",
    "age": 30,
    "city": "New York"
}

print(person["name"])        # Alice
person["email"] = "alice@example.com"
```

## Tuples

Ordered, immutable collections:

```python
coordinates = (10, 20)
x, y = coordinates  # Unpacking
print(f"X: {x}, Y: {y}")
```

## Sets

Unordered collections of unique items:

```python
numbers = {1, 2, 3, 3, 4}
print(numbers)  # {1, 2, 3, 4}

numbers.add(5)
numbers.remove(1)
```

## List Comprehensions

Concise way to create lists:

```python
squares = [x**2 for x in range(10)]
even_squares = [x**2 for x in range(10) if x % 2 == 0]
```
                ''',
                'lesson_type': 'practical',
                'difficulty_level': 'beginner',
                'order': 5,
                'estimated_duration': 70,
                'is_published': True
            }
        ]
        
        for lesson_data in lessons_data:
            lesson, created = Lesson.objects.get_or_create(
                course=course,
                slug=lesson_data['slug'],
                defaults=lesson_data
            )
            if created:
                self.stdout.write(f'  Created lesson: {lesson.title}')
                
                # Create exercises for certain lessons
                if lesson.slug in ['control-structures', 'functions', 'data-structures']:
                    self.create_exercises_for_lesson(lesson)
        
        # Update course statistics
        course.update_statistics()

    def create_advanced_python_lessons(self, course):
        """Create lessons for Advanced Python course."""
        lessons_data = [
            {
                'title': 'Decorators and Context Managers',
                'slug': 'decorators-context-managers',
                'description': 'Master advanced Python features',
                'content': '''
# Decorators and Context Managers

Learn about Python's powerful decorator and context manager features.

## Decorators

Decorators modify or enhance functions without changing their code:

```python
def timing_decorator(func):
    import time
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(f"{func.__name__} took {end - start} seconds")
        return result
    return wrapper

@timing_decorator
def slow_function():
    import time
    time.sleep(1)
    return "Done!"
```

## Context Managers

Manage resources safely with `with` statements:

```python
class FileManager:
    def __init__(self, filename, mode):
        self.filename = filename
        self.mode = mode
        self.file = None
    
    def __enter__(self):
        self.file = open(self.filename, self.mode)
        return self.file
    
    def __exit__(self, exc_type, exc_value, traceback):
        if self.file:
            self.file.close()

# Usage
with FileManager('data.txt', 'w') as f:
    f.write('Hello, World!')
```
                ''',
                'lesson_type': 'theory',
                'difficulty_level': 'advanced',
                'order': 1,
                'estimated_duration': 90,
                'is_published': True
            }
        ]
        
        for lesson_data in lessons_data:
            lesson, created = Lesson.objects.get_or_create(
                course=course,
                slug=lesson_data['slug'],
                defaults=lesson_data
            )
            if created:
                self.stdout.write(f'  Created lesson: {lesson.title}')

    def create_django_lessons(self, course):
        """Create lessons for Django course."""
        lessons_data = [
            {
                'title': 'Django Setup and First App',
                'slug': 'django-setup-first-app',
                'description': 'Set up Django and create your first application',
                'content': '''
# Django Setup and First App

Learn how to set up Django and create your first web application.

## Installing Django

Install Django using pip:

```bash
pip install django
```

## Creating a Project

Create a new Django project:

```bash
django-admin startproject myproject
cd myproject
```

## Creating an App

Create your first Django app:

```bash
python manage.py startapp myapp
```

## Your First View

Create a simple view in `myapp/views.py`:

```python
from django.http import HttpResponse

def hello(request):
    return HttpResponse("Hello, Django!")
```

## URL Configuration

Configure URLs in `myapp/urls.py`:

```python
from django.urls import path
from . import views

urlpatterns = [
    path('', views.hello, name='hello'),
]
```

## Running the Server

Start the development server:

```bash
python manage.py runserver
```
                ''',
                'lesson_type': 'practical',
                'difficulty_level': 'intermediate',
                'order': 1,
                'estimated_duration': 60,
                'is_published': True
            }
        ]
        
        for lesson_data in lessons_data:
            lesson, created = Lesson.objects.get_or_create(
                course=course,
                slug=lesson_data['slug'],
                defaults=lesson_data
            )
            if created:
                self.stdout.write(f'  Created lesson: {lesson.title}')

    def create_data_science_lessons(self, course):
        """Create lessons for Data Science course."""
        lessons_data = [
            {
                'title': 'Introduction to Pandas',
                'slug': 'introduction-pandas',
                'description': 'Learn data manipulation with pandas',
                'content': '''
# Introduction to Pandas

Pandas is the essential library for data manipulation and analysis in Python.

## Installing Pandas

```bash
pip install pandas
```

## Creating DataFrames

```python
import pandas as pd

# From dictionary
data = {
    'Name': ['Alice', 'Bob', 'Charlie'],
    'Age': [25, 30, 35],
    'City': ['New York', 'London', 'Tokyo']
}

df = pd.DataFrame(data)
print(df)
```

## Reading Data

```python
# Read CSV file
df = pd.read_csv('data.csv')

# Read Excel file
df = pd.read_excel('data.xlsx')
```

## Basic Operations

```python
# View data
print(df.head())        # First 5 rows
print(df.info())        # Data types and info
print(df.describe())    # Statistical summary

# Selecting columns
names = df['Name']
subset = df[['Name', 'Age']]

# Filtering rows
adults = df[df['Age'] >= 30]
```
                ''',
                'lesson_type': 'practical',
                'difficulty_level': 'intermediate',
                'order': 1,
                'estimated_duration': 75,
                'is_published': True
            }
        ]
        
        for lesson_data in lessons_data:
            lesson, created = Lesson.objects.get_or_create(
                course=course,
                slug=lesson_data['slug'],
                defaults=lesson_data
            )
            if created:
                self.stdout.write(f'  Created lesson: {lesson.title}')

    def create_algorithms_lessons(self, course):
        """Create lessons for Algorithms course."""
        lessons_data = [
            {
                'title': 'Big O Notation',
                'slug': 'big-o-notation',
                'description': 'Understand algorithm complexity analysis',
                'content': '''
# Big O Notation

Big O notation describes the performance or complexity of an algorithm.

## Time Complexity

### O(1) - Constant Time
```python
def get_first_element(arr):
    return arr[0]  # Always takes same time
```

### O(n) - Linear Time
```python
def find_element(arr, target):
    for element in arr:  # Time grows with input size
        if element == target:
            return True
    return False
```

### O(n²) - Quadratic Time
```python
def bubble_sort(arr):
    n = len(arr)
    for i in range(n):      # Nested loops
        for j in range(n-1):
            if arr[j] > arr[j+1]:
                arr[j], arr[j+1] = arr[j+1], arr[j]
```

### O(log n) - Logarithmic Time
```python
def binary_search(arr, target):
    left, right = 0, len(arr) - 1
    
    while left <= right:
        mid = (left + right) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1
```

## Space Complexity

Consider memory usage as well as time.
                ''',
                'lesson_type': 'theory',
                'difficulty_level': 'advanced',
                'order': 1,
                'estimated_duration': 80,
                'is_published': True
            }
        ]
        
        for lesson_data in lessons_data:
            lesson, created = Lesson.objects.get_or_create(
                course=course,
                slug=lesson_data['slug'],
                defaults=lesson_data
            )
            if created:
                self.stdout.write(f'  Created lesson: {lesson.title}')

    def create_exercises_for_lesson(self, lesson):
        """Create coding exercises for a lesson."""
        # Get Python programming language
        try:
            python_lang = ProgrammingLanguage.objects.get(name='Python')
            coding_type = ExerciseType.objects.get(name='function')
        except:
            self.stdout.write(self.style.WARNING('Python language or Coding Challenge type not found'))
            return

        if lesson.slug == 'control-structures':
            exercise_data = {
                'title': 'FizzBuzz Challenge',
                'slug': 'fizzbuzz-challenge',
                'description': 'Write a program that prints numbers 1-100, but prints "Fizz" for multiples of 3, "Buzz" for multiples of 5, and "FizzBuzz" for multiples of both.',
                'instructions': '''
Write a function called `fizzbuzz()` that:
1. Prints numbers from 1 to 100
2. For multiples of 3, print "Fizz" instead
3. For multiples of 5, print "Buzz" instead  
4. For multiples of both 3 and 5, print "FizzBuzz" instead

Example output:
1
2
Fizz
4
Buzz
Fizz
7
8
Fizz
Buzz
11
Fizz
13
14
FizzBuzz
...
                ''',
                'difficulty_level': 'beginner',
                'estimated_time': 30,
                'points': 10,
                'programming_language': python_lang,
                'exercise_type': coding_type,
                'function_name': 'fizzbuzz',
                'starter_code': '''def fizzbuzz():
    # Write your code here
    pass

# Test your function
fizzbuzz()''',
                'solution_code': '''def fizzbuzz():
    for i in range(1, 101):
        if i % 15 == 0:
            print("FizzBuzz")
        elif i % 3 == 0:
            print("Fizz")
        elif i % 5 == 0:
            print("Buzz")
        else:
            print(i)

# Test your function
fizzbuzz()''',
                'hint': 'Use the modulo operator (%) to check if a number is divisible by another. Check for 15 first (multiples of both 3 and 5).',
                'lesson': lesson,
                'is_published': True
            }
            
        elif lesson.slug == 'functions':
            exercise_data = {
                'title': 'Calculate BMI',
                'slug': 'calculate-bmi',
                'description': 'Create a function to calculate Body Mass Index (BMI)',
                'instructions': '''
Write a function called `calculate_bmi(weight, height)` that:
1. Takes weight in kilograms and height in meters as parameters
2. Calculates BMI using the formula: BMI = weight / (height * height)
3. Returns the BMI rounded to 2 decimal places

Also create a function called `bmi_category(bmi)` that:
1. Takes a BMI value as parameter
2. Returns the appropriate category:
   - "Underweight" if BMI < 18.5
   - "Normal weight" if 18.5 <= BMI < 25
   - "Overweight" if 25 <= BMI < 30
   - "Obese" if BMI >= 30
                ''',
                'difficulty_level': 'beginner',
                'estimated_time': 25,
                'points': 15,
                'programming_language': python_lang,
                'exercise_type': coding_type,
                'function_name': 'calculate_bmi',
                'starter_code': '''def calculate_bmi(weight, height):
    # Write your code here
    pass

def bmi_category(bmi):
    # Write your code here
    pass

# Test your functions
weight = 70  # kg
height = 1.75  # meters
bmi = calculate_bmi(weight, height)
category = bmi_category(bmi)
print(f"BMI: {bmi}, Category: {category}")''',
                'solution_code': '''def calculate_bmi(weight, height):
    bmi = weight / (height * height)
    return round(bmi, 2)

def bmi_category(bmi):
    if bmi < 18.5:
        return "Underweight"
    elif bmi < 25:
        return "Normal weight"
    elif bmi < 30:
        return "Overweight"
    else:
        return "Obese"

# Test your functions
weight = 70  # kg
height = 1.75  # meters
bmi = calculate_bmi(weight, height)
category = bmi_category(bmi)
print(f"BMI: {bmi}, Category: {category}")''',
                'hint': 'Remember the BMI formula: weight / (height²). Use round() to round to 2 decimal places.',
                'lesson': lesson,
                'is_published': True
            }
            
        elif lesson.slug == 'data-structures':
            exercise_data = {
                'title': 'Student Grade Manager',
                'slug': 'student-grade-manager', 
                'description': 'Create a system to manage student grades using dictionaries and lists',
                'instructions': '''
Write functions to manage student grades:

1. `add_student(students, name, grades)`: Add a student with their grades list
2. `calculate_average(grades)`: Calculate the average of a list of grades
3. `get_student_average(students, name)`: Get a specific student's average
4. `get_top_student(students)`: Return the name of the student with highest average

Use a dictionary where keys are student names and values are lists of grades.
                ''',
                'difficulty_level': 'intermediate',
                'estimated_time': 35,
                'points': 20,
                'programming_language': python_lang,
                'exercise_type': coding_type,
                'function_name': 'add_student',
                'starter_code': '''def add_student(students, name, grades):
    # Write your code here
    pass

def calculate_average(grades):
    # Write your code here
    pass

def get_student_average(students, name):
    # Write your code here
    pass

def get_top_student(students):
    # Write your code here
    pass

# Test your functions
students = {}
add_student(students, "Alice", [85, 92, 78, 96])
add_student(students, "Bob", [90, 87, 88, 85])
add_student(students, "Charlie", [95, 89, 92, 88])

print(f"Alice's average: {get_student_average(students, 'Alice')}")
print(f"Top student: {get_top_student(students)}")''',
                'solution_code': '''def add_student(students, name, grades):
    students[name] = grades

def calculate_average(grades):
    if not grades:
        return 0
    return sum(grades) / len(grades)

def get_student_average(students, name):
    if name in students:
        return calculate_average(students[name])
    return 0

def get_top_student(students):
    if not students:
        return None
    
    top_student = None
    highest_average = -1
    
    for name in students:
        avg = get_student_average(students, name)
        if avg > highest_average:
            highest_average = avg
            top_student = name
    
    return top_student

# Test your functions
students = {}
add_student(students, "Alice", [85, 92, 78, 96])
add_student(students, "Bob", [90, 87, 88, 85])
add_student(students, "Charlie", [95, 89, 92, 88])

print(f"Alice's average: {get_student_average(students, 'Alice')}")
print(f"Top student: {get_top_student(students)}")''',
                'hint': 'Use dictionary methods to store and retrieve student data. Use sum() and len() to calculate averages.',
                'lesson': lesson,
                'is_published': True
            }
        else:
            return
            
        # Create the exercise
        exercise, created = Exercise.objects.get_or_create(
            lesson=lesson,
            slug=exercise_data['slug'],
            defaults=exercise_data
        )
        
        if created:
            self.stdout.write(f'    Created exercise: {exercise.title}')
            
            # Create test cases for the exercise
            self.create_test_cases_for_exercise(exercise)

    def create_test_cases_for_exercise(self, exercise):
        """Create test cases for an exercise."""
        if exercise.slug == 'fizzbuzz-challenge':
            test_cases = [
                {
                    'input_data': '',
                    'expected_output': '1\n2\nFizz\n4\nBuzz\nFizz\n7\n8\nFizz\nBuzz\n11\nFizz\n13\n14\nFizzBuzz',
                    'description': 'Test FizzBuzz for numbers 1-15',
                    'is_hidden': False,
                    'points': 10
                }
            ]
        elif exercise.slug == 'calculate-bmi':
            test_cases = [
                {
                    'input_data': '70,1.75',
                    'expected_output': '22.86',
                    'description': 'Test BMI calculation for 70kg, 1.75m',
                    'is_hidden': False,
                    'points': 5
                },
                {
                    'input_data': '22.86',
                    'expected_output': 'Normal weight',
                    'description': 'Test BMI category for normal weight',
                    'is_hidden': False,
                    'points': 5
                }
            ]
        elif exercise.slug == 'student-grade-manager':
            test_cases = [
                {
                    'input_data': 'Alice,[85,92,78,96]',
                    'expected_output': '87.75',
                    'description': 'Test student average calculation',
                    'is_hidden': False,
                    'points': 10
                }
            ]
        else:
            return
            
        for test_data in test_cases:
            test_case, created = TestCase.objects.get_or_create(
                exercise=exercise,
                description=test_data['description'],
                defaults=test_data
            )
            if created:
                self.stdout.write(f'      Created test case: {test_case.description}')

    def create_sample_enrollments(self, courses):
        """Create sample enrollments with some demo users."""
        # Create some demo users
        demo_users = []
        for i in range(1, 6):
            user, created = User.objects.get_or_create(
                username=f'student{i}',
                defaults={
                    'email': f'student{i}@example.com',
                    'first_name': f'Student',
                    'last_name': f'{i}'
                }
            )
            if created:
                user.set_password('student123')
                user.save()
            demo_users.append(user)
        
        # Enroll users in random courses
        for user in demo_users:
            # Each user enrolls in 2-4 random courses
            user_courses = random.sample(courses, random.randint(2, 4))
            for course in user_courses:
                enrollment, created = CourseEnrollment.objects.get_or_create(
                    user=user,
                    course=course,
                    defaults={
                        'progress_percentage': random.randint(0, 100)
                    }
                )
                if created:
                    self.stdout.write(f'  Enrolled {user.username} in {course.title}')
        
        # Update all course statistics
        for course in courses:
            course.update_statistics()