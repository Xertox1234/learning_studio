"""
Management command to create the Interactive Python Fundamentals course
with all new interactive CodeMirror components.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from wagtail.models import Page
from apps.blog.models import (
    LearningIndexPage, CoursePage, LessonPage, SkillLevel, 
    LearningObjective, BlogCategory
)
import json

User = get_user_model()


class Command(BaseCommand):
    help = 'Creates the Interactive Python Fundamentals course with all interactive components'

    def handle(self, *args, **options):
        self.stdout.write('Creating Interactive Python Fundamentals course...')
        
        # Get or create instructor
        instructor = User.objects.filter(is_superuser=True).first()
        if not instructor:
            instructor = User.objects.create_superuser(
                username='instructor',
                email='instructor@pythonlearning.studio',
                password='instructor123'
            )
            self.stdout.write(self.style.SUCCESS(f'Created instructor user'))
        
        # Ensure skill levels and objectives exist
        self.create_prerequisites()
        
        # Get or create learning index page
        learning_index = LearningIndexPage.objects.first()
        if not learning_index:
            # Get home page (assuming it exists)
            home_page = Page.objects.filter(depth=2).first()
            if home_page:
                learning_index = LearningIndexPage(
                    title="Learning Center",
                    slug="learning",
                    intro="<p>Welcome to our interactive learning platform!</p>"
                )
                home_page.add_child(instance=learning_index)
                learning_index.save_revision().publish()
                self.stdout.write(self.style.SUCCESS('Created Learning Index page'))
        
        # Create the course
        course = self.create_course(learning_index, instructor)
        
        # Create all lessons
        self.create_lesson_1(course)
        self.create_lesson_2(course)
        self.create_lesson_3(course)
        self.create_lesson_4(course)
        self.create_final_quiz(course)
        
        self.stdout.write(self.style.SUCCESS(f'Interactive Python Fundamentals course created successfully!'))
        self.stdout.write(self.style.SUCCESS(f'Course URL: /learning/courses/{course.slug}/'))

    def create_prerequisites(self):
        """Create necessary skill levels and learning objectives."""
        # Create skill level
        SkillLevel.objects.get_or_create(
            slug='beginner',
            defaults={
                'name': 'Beginner',
                'order': 1,
                'color': '#28a745',
                'description': 'Perfect for beginners with no prior experience'
            }
        )
        
        # Create learning objectives
        objectives = [
            "Understand Python variables and data types",
            "Write conditional statements (if/elif/else)",
            "Create and call functions effectively",
            "Combine concepts to build simple programs"
        ]
        
        for obj_title in objectives:
            LearningObjective.objects.get_or_create(
                title=obj_title,
                defaults={
                    'category': 'fundamental',
                    'description': f'Learn about {obj_title.lower()}'
                }
            )

    def create_course(self, learning_index, instructor):
        """Create the main course page."""
        beginner_level = SkillLevel.objects.get(slug='beginner')
        objectives = LearningObjective.objects.filter(
            title__icontains='Python'
        ) | LearningObjective.objects.filter(
            title__icontains='conditional'
        ) | LearningObjective.objects.filter(
            title__icontains='function'
        )
        
        # Check if course already exists
        existing_course = CoursePage.objects.filter(course_code='PY-INTERACTIVE-101').first()
        if existing_course:
            self.stdout.write(self.style.WARNING('Course already exists, updating...'))
            return existing_course
        
        course = CoursePage(
            title="Interactive Python Fundamentals",
            slug="interactive-python-fundamentals",
            course_code="PY-INTERACTIVE-101",
            instructor=instructor,
            skill_level=beginner_level,
            short_description="Master Python basics through hands-on interactive exercises and real-time coding practice.",
            detailed_description="""
            <h2>Welcome to Interactive Python Fundamentals!</h2>
            <p>This comprehensive course introduces you to Python programming through engaging, interactive exercises. You'll learn by doing, with immediate feedback and guidance every step of the way.</p>
            
            <h3>What Makes This Course Special?</h3>
            <ul>
                <li><strong>Interactive Code Examples:</strong> Run Python code directly in your browser</li>
                <li><strong>Fill-in-the-Blank Exercises:</strong> Practice syntax with guided completion exercises</li>
                <li><strong>Multiple Choice Challenges:</strong> Test your understanding with interactive quizzes</li>
                <li><strong>Progressive Learning:</strong> Each lesson builds on the previous one</li>
                <li><strong>Immediate Feedback:</strong> Get instant results and AI-powered hints</li>
            </ul>
            
            <h3>Perfect For:</h3>
            <ul>
                <li>Complete beginners with no programming experience</li>
                <li>Students wanting hands-on, interactive learning</li>
                <li>Anyone who learns better by doing rather than just reading</li>
            </ul>
            """,
            estimated_duration="45 minutes",
            difficulty_level="beginner",
            is_free=True,
            featured=True,
            prerequisites="<p>No prior programming experience required! Just bring your curiosity and willingness to learn.</p>",
        )
        
        learning_index.add_child(instance=course)
        course.save_revision().publish()
        
        # Add learning objectives
        for obj in objectives:
            course.learning_objectives.add(obj)
        
        self.stdout.write(self.style.SUCCESS(f'Created course: {course.title}'))
        return course

    def create_lesson_1(self, course):
        """Create Lesson 1: Python Basics - Variables and Strings."""
        lesson = LessonPage(
            title="Python Basics - Variables and Strings",
            slug="python-basics-variables-strings",
            lesson_number=1,
            estimated_duration="10 minutes",
            intro="Welcome to Python! In this lesson, you'll learn about variables and strings - the building blocks of every Python program.",
            content=[
                {
                    "type": "text",
                    "value": "<h2>What are Variables?</h2><p>Variables in Python are like containers that store data. Think of them as labeled boxes where you can put different types of information.</p>"
                },
                {
                    "type": "runnable_code_example",
                    "value": {
                        "title": "Creating Your First Variable",
                        "language": "python",
                        "code": "# Create a variable to store your name\nname = \"Python Learner\"\nprint(f\"Hello, {name}!\")\nprint(\"Welcome to Python programming!\")",
                        "mock_output": "Hello, Python Learner!\nWelcome to Python programming!",
                        "ai_explanation": "This code creates a variable called 'name' and stores the text 'Python Learner' in it. The f-string (f\"...\") lets us insert the variable's value into our message. Try changing the name to your own!"
                    }
                },
                {
                    "type": "text",
                    "value": "<h3>Working with Numbers</h3><p>Variables can store different types of data. Let's see how to work with numbers:</p>"
                },
                {
                    "type": "runnable_code_example",
                    "value": {
                        "title": "Numbers and Calculations",
                        "language": "python",
                        "code": "# Store some numbers\nage = 25\nfavorite_number = 42\n\n# Do some math\ntotal = age + favorite_number\nprint(f\"Age: {age}\")\nprint(f\"Favorite number: {favorite_number}\")\nprint(f\"Total: {total}\")",
                        "mock_output": "Age: 25\nFavorite number: 42\nTotal: 67",
                        "ai_explanation": "Python can store and work with numbers just like text! Here we're storing two numbers and adding them together. The = sign doesn't mean 'equals' - it means 'store this value in this variable'."
                    }
                },
                {
                    "type": "text",
                    "value": "<h3>String Operations</h3><p>Strings (text) have special powers in Python. You can combine them, repeat them, and more:</p>"
                },
                {
                    "type": "runnable_code_example",
                    "value": {
                        "title": "String Magic",
                        "language": "python",
                        "code": "# Combining strings\nfirst_name = \"Python\"\nlast_name = \"Programmer\"\nfull_name = first_name + \" \" + last_name\n\n# Repeating strings\nexcitement = \"!\" * 3\n\nprint(f\"Full name: {full_name}\")\nprint(f\"Getting excited{excitement}\")\nprint(f\"Length of full name: {len(full_name)}\")",
                        "mock_output": "Full name: Python Programmer\nGetting excited!!!\nLength of full name: 16",
                        "ai_explanation": "Strings can be combined with + and repeated with *. The len() function tells us how many characters are in a string. These operations make working with text data really powerful!"
                    }
                }
            ],
            lesson_objectives=[
                {"type": "objective", "value": "Create and use variables to store data"},
                {"type": "objective", "value": "Understand the difference between strings and numbers"},
                {"type": "objective", "value": "Perform basic operations with strings and numbers"}
            ]
        )
        
        course.add_child(instance=lesson)
        lesson.save_revision().publish()
        self.stdout.write(self.style.SUCCESS('Created Lesson 1: Variables and Strings'))

    def create_lesson_2(self, course):
        """Create Lesson 2: Control Flow - Conditionals."""
        lesson = LessonPage(
            title="Control Flow - Conditionals",
            slug="control-flow-conditionals",
            lesson_number=2,
            estimated_duration="12 minutes",
            intro="Now let's make our programs smarter! Learn how to make decisions in your code using if statements.",
            content=[
                {
                    "type": "text",
                    "value": "<h2>Making Decisions with If Statements</h2><p>Sometimes your program needs to do different things based on certain conditions. That's where if statements come in!</p>"
                },
                {
                    "type": "runnable_code_example",
                    "value": {
                        "title": "Your First If Statement",
                        "language": "python",
                        "code": "# Check if someone is an adult\nage = 20\n\nif age >= 18:\n    print(\"You are an adult!\")\n    print(\"You can vote and drive.\")\nelse:\n    print(\"You are a minor.\")\n    print(\"Keep growing!\")\n\nprint(\"Thanks for checking your age!\")",
                        "mock_output": "You are an adult!\nYou can vote and drive.\nThanks for checking your age!",
                        "ai_explanation": "The 'if' statement checks if a condition is true. If the age is 18 or greater, it executes the first block. Otherwise, it runs the 'else' block. The >= symbol means 'greater than or equal to'."
                    }
                },
                {
                    "type": "text",
                    "value": "<h3>Practice Time! Fill in the Missing Parts</h3><p>Let's practice by completing some if statements. Fill in the blanks to make the code work:</p>"
                },
                {
                    "type": "fill_blank_code",
                    "value": {
                        "title": "Complete the Age Checker",
                        "language": "python",
                        "template": "# Complete this age checking program\nage = 16\n\n{{BLANK_1}} age >= 18:\n    print(\"You can vote!\")\n{{BLANK_2}} age >= 16:\n    print(\"You can drive!\")\nelse:\n    print(\"Keep growing!\")",
                        "solutions": json.dumps({"1": "if", "2": "elif"}),
                        "alternative_solutions": json.dumps({"2": ["elif", "elseif"]}),
                        "ai_hints": json.dumps({
                            "1": "This keyword starts a conditional statement and checks if something is true.",
                            "2": "This keyword is used for additional conditions after 'if'. It's short for 'else if'."
                        })
                    }
                },
                {
                    "type": "fill_blank_code",
                    "value": {
                        "title": "Grade Calculator",
                        "language": "python",
                        "template": "# Calculate letter grade from score\nscore = 85\n\nif score {{BLANK_1}} 90:\n    grade = \"A\"\nelif score >= 80:\n    grade = {{BLANK_2}}\nelif score >= 70:\n    grade = \"C\"\nelse:\n    grade = \"F\"\n\nprint(f\"Your grade is: {grade}\")",
                        "solutions": json.dumps({"1": ">=", "2": "\"B\""}),
                        "alternative_solutions": json.dumps({"2": ["'B'", "\"B\""]}),
                        "ai_hints": json.dumps({
                            "1": "We need a comparison operator that checks if the score is greater than or equal to 90.",
                            "2": "We need a string containing the letter B. Remember to use quotes!"
                        })
                    }
                },
                {
                    "type": "text",
                    "value": "<h3>Comparison Operators</h3><p>Python has several ways to compare values. Here are the most common ones:</p><ul><li><strong>></strong> greater than</li><li><strong><</strong> less than</li><li><strong>>=</strong> greater than or equal</li><li><strong><=</strong> less than or equal</li><li><strong>==</strong> equal to</li><li><strong>!=</strong> not equal to</li></ul>"
                },
                {
                    "type": "fill_blank_code",
                    "value": {
                        "title": "Weather Advisor",
                        "language": "python",
                        "template": "# Give advice based on temperature\ntemperature = 75\n\nif temperature > 80:\n    advice = \"It's hot! Stay hydrated.\"\n{{BLANK_1}} temperature < 60:\n    advice = \"It's cold! Wear a jacket.\"\nelse:\n    advice = \"Perfect weather for a walk!\"\n\nprint({{BLANK_2}})",
                        "solutions": json.dumps({"1": "elif", "2": "advice"}),
                        "alternative_solutions": json.dumps({"2": ["advice", "f\"Advice: {advice}\""]}),
                        "ai_hints": json.dumps({
                            "1": "We need another condition to check. What keyword do we use for additional conditions?",
                            "2": "We want to display the advice. What variable contains our advice message?"
                        })
                    }
                }
            ],
            lesson_objectives=[
                {"type": "objective", "value": "Write if statements to make decisions in code"},
                {"type": "objective", "value": "Use elif for multiple conditions"},
                {"type": "objective", "value": "Apply comparison operators correctly"}
            ]
        )
        
        course.add_child(instance=lesson)
        lesson.save_revision().publish()
        self.stdout.write(self.style.SUCCESS('Created Lesson 2: Control Flow - Conditionals'))

    def create_lesson_3(self, course):
        """Create Lesson 3: Functions and Logic."""
        lesson = LessonPage(
            title="Functions and Logic",
            slug="functions-and-logic",
            lesson_number=3,
            estimated_duration="12 minutes",
            intro="Functions are like mini-programs within your program. They help organize your code and avoid repetition!",
            content=[
                {
                    "type": "text",
                    "value": "<h2>What are Functions?</h2><p>Functions are reusable blocks of code that perform specific tasks. Think of them as recipes you can use over and over again!</p>"
                },
                {
                    "type": "runnable_code_example",
                    "value": {
                        "title": "Your First Function",
                        "language": "python",
                        "code": "# Define a simple greeting function\ndef greet(name):\n    \"\"\"This function greets someone by name\"\"\"\n    message = f\"Hello, {name}! Welcome to Python!\"\n    return message\n\n# Use the function\ngreeting1 = greet(\"Alice\")\ngreeting2 = greet(\"Bob\")\n\nprint(greeting1)\nprint(greeting2)\nprint(greet(\"Python Learner\"))",
                        "mock_output": "Hello, Alice! Welcome to Python!\nHello, Bob! Welcome to Python!\nHello, Python Learner! Welcome to Python!",
                        "ai_explanation": "The 'def' keyword creates a function. The function takes a 'name' parameter, creates a greeting message, and returns it. We can call this function as many times as we want with different names!"
                    }
                },
                {
                    "type": "text",
                    "value": "<h3>Choose the Right Code!</h3><p>Let's practice identifying the correct function syntax. Choose the right option for each blank:</p>"
                },
                {
                    "type": "multiple_choice_code",
                    "value": {
                        "title": "Function Definition Practice",
                        "language": "python",
                        "template": "# Create a function that doubles a number\n{{CHOICE_1}} double_number(num):\n    result = num * 2\n    {{CHOICE_2}} result\n\n# Call the function\nprint({{CHOICE_3}})",
                        "choices": json.dumps({
                            "1": ["def", "function", "create"],
                            "2": ["return", "print", "show"],
                            "3": ["double_number(5)", "double_number", "call double_number(5)"]
                        }),
                        "solutions": json.dumps({
                            "1": "def",
                            "2": "return", 
                            "3": "double_number(5)"
                        }),
                        "ai_explanations": json.dumps({
                            "1": "'def' is the Python keyword used to define a function. It's short for 'define'.",
                            "2": "'return' sends a value back from the function to wherever it was called from.",
                            "3": "To call a function, we use its name followed by parentheses with any required arguments."
                        })
                    }
                },
                {
                    "type": "multiple_choice_code",
                    "value": {
                        "title": "Calculator Function",
                        "language": "python",
                        "template": "# Create a simple calculator function\ndef calculate(a, b, operation):\n    {{CHOICE_1}} operation == \"add\":\n        return a + b\n    elif operation == \"subtract\":\n        {{CHOICE_2}} a - b\n    else:\n        return \"Unknown operation\"\n\n# Test the function\nresult = {{CHOICE_3}}\nprint(f\"Result: {result}\")",
                        "choices": json.dumps({
                            "1": ["if", "when", "check"],
                            "2": ["return", "give", "send"],
                            "3": ["calculate(10, 5, \"add\")", "calculate(10, 5, add)", "run calculate(10, 5, \"add\")"]
                        }),
                        "solutions": json.dumps({
                            "1": "if",
                            "2": "return",
                            "3": "calculate(10, 5, \"add\")"
                        }),
                        "ai_explanations": json.dumps({
                            "1": "We use 'if' to check conditions inside functions, just like anywhere else in Python.",
                            "2": "'return' is used to send the calculated result back to the caller.",
                            "3": "When calling a function, we need to provide all required arguments. Strings need quotes!"
                        })
                    }
                },
                {
                    "type": "text",
                    "value": "<h3>Functions with Multiple Parameters</h3><p>Functions can take multiple inputs (parameters) to work with. This makes them very flexible!</p>"
                },
                {
                    "type": "multiple_choice_code",
                    "value": {
                        "title": "Personal Info Function",
                        "language": "python",
                        "template": "# Function that creates a personal introduction\n{{CHOICE_1}} introduce_person(name, age, hobby):\n    intro = f\"Hi, I'm {name}. I'm {age} years old and I love {hobby}!\"\n    return intro\n\n# Create introductions\nperson1 = introduce_person({{CHOICE_2}}, 25, \"programming\")\nperson2 = introduce_person(\"Bob\", {{CHOICE_3}}, \"reading\")\n\nprint(person1)\nprint(person2)",
                        "choices": json.dumps({
                            "1": ["def", "function", "create"],
                            "2": ["\"Alice\"", "Alice", "'Alice'"],
                            "3": ["30", "\"30\"", "'30'"]
                        }),
                        "solutions": json.dumps({
                            "1": "def",
                            "2": "\"Alice\"",
                            "3": "30"
                        }),
                        "ai_explanations": json.dumps({
                            "1": "'def' is always used to define functions in Python.",
                            "2": "Names are text (strings), so they need quotes. Either single or double quotes work!",
                            "3": "Age is a number, so we don't need quotes around it."
                        })
                    }
                },
                {
                    "type": "runnable_code_example",
                    "value": {
                        "title": "Putting It All Together",
                        "language": "python",
                        "code": "# A function that combines everything we've learned\ndef smart_greeter(name, age):\n    \"\"\"Greet someone differently based on their age\"\"\"\n    if age < 13:\n        greeting = f\"Hey there, {name}! Want to play?\"\n    elif age < 20:\n        greeting = f\"Hi {name}! How's school going?\"\n    elif age < 65:\n        greeting = f\"Hello {name}! How's work treating you?\"\n    else:\n        greeting = f\"Good day, {name}! Hope you're enjoying retirement!\"\n    \n    return greeting\n\n# Test with different ages\nprint(smart_greeter(\"Emma\", 10))\nprint(smart_greeter(\"Jake\", 17))\nprint(smart_greeter(\"Sarah\", 30))\nprint(smart_greeter(\"Frank\", 70))",
                        "mock_output": "Hey there, Emma! Want to play?\nHi Jake! How's school going?\nHello Sarah! How's work treating you?\nGood day, Frank! Hope you're enjoying retirement!",
                        "ai_explanation": "This function combines variables, conditionals, and functions! It takes a name and age, then uses if/elif statements to choose the right greeting. This shows how all Python concepts work together."
                    }
                }
            ],
            lesson_objectives=[
                {"type": "objective", "value": "Define functions using def keyword"},
                {"type": "objective", "value": "Use parameters to pass data to functions"},
                {"type": "objective", "value": "Return values from functions"},
                {"type": "objective", "value": "Combine functions with conditional logic"}
            ]
        )
        
        course.add_child(instance=lesson)
        lesson.save_revision().publish()
        self.stdout.write(self.style.SUCCESS('Created Lesson 3: Functions and Logic'))

    def create_lesson_4(self, course):
        """Create Lesson 4: Integration - Putting It All Together."""
        lesson = LessonPage(
            title="Putting It All Together",
            slug="putting-it-all-together",
            lesson_number=4,
            estimated_duration="15 minutes",
            intro="Time to combine everything you've learned! Let's build a complete mini-program that uses variables, conditionals, and functions.",
            content=[
                {
                    "type": "text",
                    "value": "<h2>Building a Personal Assistant Program</h2><p>Let's create a program that acts like a simple personal assistant. It will use everything you've learned so far!</p>"
                },
                {
                    "type": "runnable_code_example",
                    "value": {
                        "title": "Personal Assistant - Demo",
                        "language": "python",
                        "code": "# Personal Assistant Demo\ndef personal_assistant(name, task, urgency):\n    \"\"\"A helpful personal assistant function\"\"\"\n    greeting = f\"Hello {name}! I'm your Python assistant.\"\n    \n    if urgency == \"high\":\n        response = f\"Right away! I'll help you with: {task}\"\n        priority = \"🔴 HIGH PRIORITY\"\n    elif urgency == \"medium\":\n        response = f\"Sure thing! I'll work on: {task}\"\n        priority = \"🟡 MEDIUM PRIORITY\"\n    else:\n        response = f\"No problem! I'll get to: {task} when I can.\"\n        priority = \"🟢 LOW PRIORITY\"\n    \n    return f\"{greeting}\\n{priority}\\n{response}\"\n\n# Test our assistant\nprint(personal_assistant(\"Alex\", \"organize my files\", \"high\"))\nprint(\"\\n\" + \"=\"*40 + \"\\n\")\nprint(personal_assistant(\"Sam\", \"plan weekend activities\", \"low\"))",
                        "mock_output": "Hello Alex! I'm your Python assistant.\\n🔴 HIGH PRIORITY\\nRight away! I'll help you with: organize my files\\n\\n========================================\\n\\nHello Sam! I'm your Python assistant.\\n🟢 LOW PRIORITY\\nNo problem! I'll get to: plan weekend activities when I can.",
                        "ai_explanation": "This assistant function combines variables (to store data), conditionals (to make decisions), and returns a formatted response. See how all our Python concepts work together to create something useful!"
                    }
                },
                {
                    "type": "text",
                    "value": "<h3>Your Turn! Complete the Shopping Helper</h3><p>Let's build a shopping helper that calculates totals and gives advice. Fill in the missing parts:</p>"
                },
                {
                    "type": "fill_blank_code",
                    "value": {
                        "title": "Shopping Calculator",
                        "language": "python",
                        "template": "# Complete the shopping helper function\n{{BLANK_1}} calculate_shopping(item_price, quantity, has_coupon):\n    \"\"\"Calculate shopping total with optional discount\"\"\"\n    total = item_price {{BLANK_2}} quantity\n    \n    if has_coupon:\n        discount = total * 0.1  # 10% discount\n        total = total - discount\n        message = \"Coupon applied! You saved $\" + {{BLANK_3}}\n    else:\n        message = \"No coupon applied.\"\n    \n    return f\"Total: ${total:.2f}\\n{message}\"\n\n# Test the function\nprint(calculate_shopping(15.99, 3, True))",
                        "solutions": json.dumps({"1": "def", "2": "*", "3": "str(discount)"}),
                        "alternative_solutions": json.dumps({
                            "2": ["*", "×"],
                            "3": ["str(discount)", "f\"{discount:.2f}\"", "str(round(discount, 2))"]
                        }),
                        "ai_hints": json.dumps({
                            "1": "We need to define a function. What keyword do we use?",
                            "2": "To get the total cost, we multiply price by quantity. What operator do we use?",
                            "3": "We're combining text with a number. We need to convert the discount to a string first."
                        })
                    }
                },
                {
                    "type": "text",
                    "value": "<h3>Choose the Best Code!</h3><p>Now let's create a weather-based outfit suggester. Pick the best options:</p>"
                },
                {
                    "type": "multiple_choice_code",
                    "value": {
                        "title": "Weather Outfit Suggester",
                        "language": "python",
                        "template": "# Weather-based outfit suggester\n{{CHOICE_1}} suggest_outfit(temperature, is_raining):\n    \"\"\"Suggest an outfit based on weather\"\"\"\n    \n    # Base outfit suggestion\n    if temperature > 75:\n        outfit = \"shorts and t-shirt\"\n    {{CHOICE_2}} temperature > 60:\n        outfit = \"jeans and long sleeves\"\n    else:\n        outfit = \"warm jacket and pants\"\n    \n    # Check for rain\n    {{CHOICE_3}} is_raining:\n        outfit += \" + umbrella and rain boots\"\n    \n    return f\"Today I suggest: {outfit}\"\n\n# Test different weather conditions\nprint(suggest_outfit(80, False))\nprint(suggest_outfit(65, True))",
                        "choices": json.dumps({
                            "1": ["def", "function", "create"],
                            "2": ["elif", "if", "else if"],
                            "3": ["if", "when", "check"]
                        }),
                        "solutions": json.dumps({
                            "1": "def",
                            "2": "elif",
                            "3": "if"
                        }),
                        "ai_explanations": json.dumps({
                            "1": "'def' is the Python keyword to define functions.",
                            "2": "'elif' is used for additional conditions after the first 'if' statement.",
                            "3": "'if' is used to check the rain condition separately from the temperature checks."
                        })
                    }
                },
                {
                    "type": "text",
                    "value": "<h3>Final Challenge: Password Strength Checker</h3><p>Let's build a password strength checker that combines everything!</p>"
                },
                {
                    "type": "multiple_choice_code",
                    "value": {
                        "title": "Password Strength Checker",
                        "language": "python", 
                        "template": "# Password strength checker\n{{CHOICE_1}} check_password_strength(password):\n    \"\"\"Check if a password is strong enough\"\"\"\n    length = {{CHOICE_2}}\n    has_numbers = any(char.isdigit() for char in password)\n    \n    if length >= 8 and has_numbers:\n        strength = \"Strong\"\n        advice = \"Great password! 🔒\"\n    elif length >= 6:\n        strength = \"Medium\"\n        advice = \"Good, but add some numbers for security!\"\n    {{CHOICE_3}}:\n        strength = \"Weak\"\n        advice = \"Make it longer and add numbers!\"\n    \n    return f\"Password strength: {strength}\\nAdvice: {advice}\"\n\n# Test different passwords\nprint(check_password_strength(\"mypassword123\"))\nprint(\"\\n---\\n\")\nprint(check_password_strength(\"short\"))",
                        "choices": json.dumps({
                            "1": ["def", "function", "define"],
                            "2": ["len(password)", "length(password)", "size(password)"],
                            "3": ["else", "otherwise", "default"]
                        }),
                        "solutions": json.dumps({
                            "1": "def",
                            "2": "len(password)",
                            "3": "else"
                        }),
                        "ai_explanations": json.dumps({
                            "1": "'def' is used to define functions in Python.",
                            "2": "'len()' is Python's built-in function to get the length of strings, lists, etc.",
                            "3": "'else' handles all other cases that don't match the previous conditions."
                        })
                    }
                },
                {
                    "type": "runnable_code_example",
                    "value": {
                        "title": "Your Complete Mini-Program!",
                        "language": "python",
                        "code": "# A complete mini-program combining everything!\ndef daily_helper(name, temperature, task_count):\n    \"\"\"A daily helper that gives personalized advice\"\"\"\n    \n    # Greeting based on name\n    greeting = f\"Good morning, {name}!\"\n    \n    # Weather advice\n    if temperature > 80:\n        weather_advice = \"It's hot! Stay hydrated and wear light clothes.\"\n    elif temperature > 60:\n        weather_advice = \"Perfect weather for outdoor activities!\"\n    else:\n        weather_advice = \"Bundle up! It's chilly today.\"\n    \n    # Productivity advice based on task count\n    if task_count > 10:\n        productivity_tip = \"Wow, that's a lot! Break tasks into smaller chunks.\"\n    elif task_count > 5:\n        productivity_tip = \"Good amount of tasks. You've got this!\"\n    elif task_count > 0:\n        productivity_tip = \"Light day ahead. Maybe add some learning time?\"\n    else:\n        productivity_tip = \"No tasks today? Perfect time to relax or learn something new!\"\n    \n    # Combine everything\n    daily_summary = f\"\"\"{greeting}\n\nWeather Update: {weather_advice}\n\nToday's Tasks: {task_count}\nTip: {productivity_tip}\n\nHave a wonderful day! 🌟\"\"\"\n    \n    return daily_summary\n\n# Test your daily helper\nprint(daily_helper(\"Python Learner\", 72, 7))\nprint(\"\\n\" + \"=\"*50 + \"\\n\")\nprint(daily_helper(\"Coding Student\", 85, 0))",
                        "mock_output": "Good morning, Python Learner!\\n\\nWeather Update: Perfect weather for outdoor activities!\\n\\nToday's Tasks: 7\\nTip: Good amount of tasks. You've got this!\\n\\nHave a wonderful day! 🌟\\n\\n==================================================\\n\\nGood morning, Coding Student!\\n\\nWeather Update: It's hot! Stay hydrated and wear light clothes.\\n\\nToday's Tasks: 0\\nTip: No tasks today? Perfect time to relax or learn something new!\\n\\nHave a wonderful day! 🌟",
                        "ai_explanation": "Congratulations! This program combines variables, conditionals, functions, and string formatting. You now understand the fundamental building blocks of Python programming. You can create variables, make decisions with if statements, organize code with functions, and combine them all to build useful programs!"
                    }
                }
            ],
            lesson_objectives=[
                {"type": "objective", "value": "Combine variables, conditionals, and functions in one program"},
                {"type": "objective", "value": "Build practical mini-programs that solve real problems"},
                {"type": "objective", "value": "Debug and complete partially written code"},
                {"type": "objective", "value": "Apply best practices for readable, well-structured code"}
            ]
        )
        
        course.add_child(instance=lesson)
        lesson.save_revision().publish()
        self.stdout.write(self.style.SUCCESS('Created Lesson 4: Putting It All Together'))

    def create_final_quiz(self, course):
        """Create the final quiz lesson."""
        lesson = LessonPage(
            title="Final Assessment - Python Fundamentals Quiz",
            slug="final-assessment-quiz",
            lesson_number=5,
            estimated_duration="8 minutes",
            intro="Time to test your Python knowledge! Complete this 3-question quiz to finish the course.",
            content=[
                {
                    "type": "text",
                    "value": "<h2>🎯 Final Quiz: Python Fundamentals</h2><p>Answer these 3 questions to demonstrate your understanding of Python basics. You've got this!</p>"
                },
                {
                    "type": "quiz",
                    "value": {
                        "question": "Which of the following is the correct way to create a string variable in Python?",
                        "options": [
                            "name = 'Alice'",
                            "name = Alice",
                            "string name = 'Alice'",
                            "var name = 'Alice'"
                        ],
                        "correct_answer": 0,
                        "explanation": "In Python, strings must be enclosed in quotes (single or double). You don't need to declare the type - Python figures it out automatically!"
                    }
                },
                {
                    "type": "quiz",
                    "value": {
                        "question": "What operator is used to check if two values are equal in Python?",
                        "options": [
                            "=",
                            "==",
                            "equals",
                            "is"
                        ],
                        "correct_answer": 1,
                        "explanation": "The == operator checks for equality. The single = is used for assignment (storing values in variables), while == compares values."
                    }
                },
                {
                    "type": "quiz",
                    "value": {
                        "question": "What keyword is used to define a function in Python?",
                        "options": [
                            "function",
                            "define",
                            "def",
                            "create"
                        ],
                        "correct_answer": 2,
                        "explanation": "The 'def' keyword is used to define functions in Python. It's short for 'define' and is followed by the function name and parentheses."
                    }
                },
                {
                    "type": "text",
                    "value": "<h2>🎉 Course Complete!</h2><p>Congratulations on completing the Interactive Python Fundamentals course! You've learned:</p><ul><li>✅ How to create and use variables</li><li>✅ How to make decisions with if statements</li><li>✅ How to create and call functions</li><li>✅ How to combine concepts to build useful programs</li></ul><p>You're now ready to continue your Python journey. Keep practicing and building awesome things!</p>"
                }
            ],
            lesson_objectives=[
                {"type": "objective", "value": "Demonstrate understanding of Python variables and strings"},
                {"type": "objective", "value": "Show knowledge of conditional statements and operators"},
                {"type": "objective", "value": "Prove mastery of function definition and usage"}
            ]
        )
        
        course.add_child(instance=lesson)
        lesson.save_revision().publish()
        self.stdout.write(self.style.SUCCESS('Created Final Quiz'))