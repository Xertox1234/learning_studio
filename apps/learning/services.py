"""
AI-powered learning content services for Python Learning Studio.
This module integrates with Wagtail AI to provide programming education assistance.
"""

from typing import Optional, Dict, Any
from django.conf import settings

# Import Wagtail AI components
try:
    from wagtail_ai import ai
    from wagtail_ai.ai.base import BackendFeature
    WAGTAIL_AI_AVAILABLE = True
except ImportError:
    WAGTAIL_AI_AVAILABLE = False


class LearningContentAI:
    """
    Service class to use Wagtail AI in custom learning apps.
    Provides AI-powered content generation for programming education.
    """
    
    def __init__(self):
        self.ai_available = WAGTAIL_AI_AVAILABLE and hasattr(settings, 'WAGTAIL_AI')
        if not self.ai_available:
            print("Warning: Wagtail AI is not properly configured. AI features will be disabled.")
    
    def _get_backend(self, feature=None):
        """Get the appropriate AI backend."""
        if not self.ai_available:
            return None
        
        try:
            if feature:
                return ai.get_backend(feature)
            return ai.get_backend()
        except Exception as e:
            print(f"Error getting AI backend: {e}")
            return None
    
    def _safe_ai_call(self, func, *args, **kwargs):
        """Safely call AI function with error handling."""
        if not self.ai_available:
            return "AI service not available"
        
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f"AI service error: {e}")
            return f"AI service temporarily unavailable: {str(e)}"
    
    def generate_exercise_explanation(self, code_snippet: str) -> str:
        """Generate explanation for code exercises."""
        def _call():
            backend = self._get_backend(BackendFeature.TEXT_COMPLETION)
            if not backend:
                return "AI backend not available"
            
            prompt = "Explain this code in simple terms for beginners learning programming:"
            response = backend.prompt_with_context(
                pre_prompt=prompt,
                context=code_snippet
            )
            return response.text()
        
        return self._safe_ai_call(_call)
    
    def generate_test_cases(self, function_code: str) -> str:
        """Generate test cases for coding exercises."""
        def _call():
            backend = self._get_backend()
            if not backend:
                return "AI backend not available"
            
            prompt = "Generate comprehensive test cases for this function. Include edge cases:"
            response = backend.prompt_with_context(
                pre_prompt=prompt,
                context=function_code
            )
            return response.text()
        
        return self._safe_ai_call(_call)
    
    def improve_lesson_content(self, lesson_text: str) -> str:
        """Use AI to improve lesson content."""
        def _call():
            backend = self._get_backend()
            if not backend:
                return lesson_text  # Return original if AI unavailable
            
            prompt = "Improve this programming lesson content for clarity and engagement:"
            response = backend.prompt_with_context(
                pre_prompt=prompt,
                context=lesson_text
            )
            return response.text()
        
        return self._safe_ai_call(_call)
    
    def generate_code_examples(self, concept: str) -> str:
        """Generate code examples for programming concepts."""
        def _call():
            backend = self._get_backend()
            if not backend:
                return f"# Code examples for {concept}\n# AI service not available"
            
            prompt = f"Generate practical, well-commented code examples for this programming concept: {concept}. Include multiple examples with different difficulty levels."
            response = backend.prompt_with_context(
                pre_prompt=prompt,
                context=concept
            )
            return response.text()
        
        return self._safe_ai_call(_call)
    
    def generate_course_description(self, course_title: str, difficulty: str = "beginner") -> str:
        """Generate AI-enhanced course description."""
        def _call():
            backend = self._get_backend()
            if not backend:
                return f"A comprehensive {difficulty} level course on {course_title}"
            
            prompt = f"Create an engaging course description for a {difficulty} level programming course on {course_title}. Include what students will learn and why it's valuable."
            response = backend.prompt_with_context(
                pre_prompt=prompt,
                context=f"Course: {course_title}, Level: {difficulty}"
            )
            return response.text()
        
        return self._safe_ai_call(_call)
    
    def generate_learning_objectives(self, course_title: str, description: str) -> str:
        """Generate specific learning objectives for a course."""
        def _call():
            backend = self._get_backend()
            if not backend:
                return f"Learning objectives for {course_title}:\n1. Understand core concepts\n2. Apply knowledge practically\n3. Build real-world projects"
            
            prompt = f"Generate specific, measurable learning objectives for this programming course. Format as a numbered list."
            context = f"Course: {course_title}\nDescription: {description}"
            response = backend.prompt_with_context(
                pre_prompt=prompt,
                context=context
            )
            return response.text()
        
        return self._safe_ai_call(_call)
    
    def generate_prerequisites(self, course_title: str, difficulty: str) -> str:
        """Generate course prerequisites."""
        def _call():
            backend = self._get_backend()
            if not backend:
                if difficulty == "beginner":
                    return "No prior programming experience required."
                return f"Basic programming knowledge recommended for this {difficulty} course."
            
            prompt = f"List the prerequisites for a {difficulty} level course on {course_title}. Be specific about required knowledge and skills."
            response = backend.prompt_with_context(
                pre_prompt=prompt,
                context=f"Course: {course_title}, Level: {difficulty}"
            )
            return response.text()
        
        return self._safe_ai_call(_call)
    
    def create_exercise_from_concept(self, concept: str, difficulty: str = "beginner") -> Dict[str, str]:
        """Create a complete coding exercise from a programming concept."""
        def _call():
            backend = self._get_backend()
            if not backend:
                return {
                    'title': f"Exercise: {concept}",
                    'description': f"Practice {concept} concepts",
                    'instructions': f"Write code to demonstrate {concept}",
                    'starter_code': f"# TODO: Implement {concept}",
                    'solution': f"# Solution for {concept}",
                    'test_cases': f"# Test cases for {concept}"
                }
            
            prompt = f"""Create a complete coding exercise for the concept: {concept}
            Difficulty level: {difficulty}
            
            Please provide:
            1. Exercise title
            2. Clear description
            3. Step-by-step instructions
            4. Starter code template
            5. Complete solution
            6. Test cases
            
            Format the response as sections with clear headers."""
            
            response = backend.prompt_with_context(
                pre_prompt=prompt,
                context=f"Concept: {concept}, Level: {difficulty}"
            )
            
            # Parse the response into components
            # This is a simplified parser - in production, you'd want more robust parsing
            response_text = response.text()
            return {
                'title': f"Exercise: {concept}",
                'description': response_text[:200] + "..." if len(response_text) > 200 else response_text,
                'instructions': response_text,
                'starter_code': f"# TODO: Implement {concept}",
                'solution': response_text,
                'test_cases': f"# Test cases will be generated separately"
            }
        
        return self._safe_ai_call(_call)
    
    def generate_hints_for_exercise(self, exercise_description: str, student_code: str = "") -> str:
        """Generate helpful hints for students struggling with an exercise."""
        def _call():
            backend = self._get_backend()
            if not backend:
                return "Hint: Break down the problem into smaller steps and tackle each one individually."
            
            context = f"Exercise: {exercise_description}"
            if student_code:
                context += f"\nStudent's current attempt: {student_code}"
            
            prompt = "Provide helpful hints for this programming exercise. Don't give away the solution, but guide the student toward the right approach."
            response = backend.prompt_with_context(
                pre_prompt=prompt,
                context=context
            )
            return response.text()
        
        return self._safe_ai_call(_call)
    
    def review_student_code(self, code: str, exercise_description: str) -> str:
        """Provide constructive code review feedback."""
        def _call():
            backend = self._get_backend()
            if not backend:
                return "Code review not available - AI service not configured."
            
            prompt = """Review this student's code and provide constructive feedback focusing on:
            1. Code quality and best practices
            2. Potential improvements
            3. Learning opportunities
            4. Positive aspects
            
            Be encouraging and educational."""
            
            context = f"Exercise: {exercise_description}\nStudent Code: {code}"
            response = backend.prompt_with_context(
                pre_prompt=prompt,
                context=context
            )
            return response.text()
        
        return self._safe_ai_call(_call)
    
    def generate_learning_path(self, topic: str, student_level: str = "beginner") -> str:
        """Generate a structured learning path for a programming topic."""
        def _call():
            backend = self._get_backend()
            if not backend:
                return f"Learning path for {topic}:\n1. Basic concepts\n2. Practical exercises\n3. Advanced topics\n4. Real-world projects"
            
            prompt = f"""Create a structured learning path for {topic} suitable for a {student_level} level student.
            
            Include:
            1. Prerequisites
            2. Learning objectives
            3. Lesson sequence (with topics)
            4. Practice exercises
            5. Projects to build
            6. Resources for further learning
            
            Format as a clear, actionable roadmap."""
            
            response = backend.prompt_with_context(
                pre_prompt=prompt,
                context=f"Topic: {topic}, Level: {student_level}"
            )
            return response.text()
        
        return self._safe_ai_call(_call)
    
    def explain_error_message(self, error_message: str, code_context: str = "") -> str:
        """Help students understand error messages."""
        def _call():
            backend = self._get_backend()
            if not backend:
                return f"Error explanation not available. Error: {error_message}"
            
            prompt = "Explain this programming error message in simple terms. Help the student understand what went wrong and how to fix it."
            context = f"Error: {error_message}"
            if code_context:
                context += f"\nCode context: {code_context}"
            
            response = backend.prompt_with_context(
                pre_prompt=prompt,
                context=context
            )
            return response.text()
        
        return self._safe_ai_call(_call)


# Global instance for easy import
learning_ai = LearningContentAI()