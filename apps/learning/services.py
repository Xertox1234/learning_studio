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

    def contextual_chat_response(self, user_message: str, exercise_context: dict = None, student_code: str = "", conversation_history: list = None) -> str:
        """Generate contextual AI chat responses for the floating assistant."""
        def _call():
            backend = self._get_backend()
            if not backend:
                return "I'm sorry, I'm currently unavailable. Please try again later."
            
            # Build comprehensive context
            context_parts = [f"Student question: {user_message}"]
            
            if exercise_context:
                context_parts.append(f"Current exercise: {exercise_context.get('title', 'N/A')}")
                context_parts.append(f"Exercise description: {exercise_context.get('description', 'N/A')}")
                context_parts.append(f"Exercise type: {exercise_context.get('type', 'N/A')}")
                
            if student_code:
                context_parts.append(f"Student's current code:\n{student_code}")
                
            if conversation_history:
                context_parts.append("Recent conversation:")
                for msg in conversation_history[-3:]:  # Last 3 messages
                    sender = "Student" if msg.get('type') == 'user' else "Assistant"
                    context_parts.append(f"{sender}: {msg.get('content', '')}")
            
            context = "\n\n".join(context_parts)
            
            prompt = """You are an expert programming tutor and AI assistant. Provide helpful, encouraging, and educational responses to programming students.

Guidelines:
1. Be conversational and supportive
2. Explain concepts clearly for the student's level
3. Provide specific, actionable advice
4. Use examples when helpful
5. Don't just give answers - help students learn
6. If they're struggling, offer step-by-step guidance
7. Celebrate their progress and efforts
8. Connect concepts to real-world applications when relevant

Respond in a friendly, professional tone."""

            response = backend.prompt_with_context(
                pre_prompt=prompt,
                context=context
            )
            return response.text()
        
        return self._safe_ai_call(_call)

    def generate_real_world_examples(self, concept: str, industry_focus: str = "general") -> str:
        """Generate real-world examples of programming concepts."""
        def _call():
            backend = self._get_backend()
            if not backend:
                return f"Real-world examples of {concept} are commonly found in web development, data analysis, and software engineering."
            
            prompt = f"""Provide 3-4 concrete, real-world examples of how the programming concept "{concept}" is used in the software industry.

Focus on {industry_focus} applications. For each example:
1. Describe the specific use case
2. Explain why this concept is important for that use case
3. Mention what companies or types of projects might use it
4. Keep explanations accessible for students

Make it engaging and show the practical value of learning this concept."""

            response = backend.prompt_with_context(
                pre_prompt=prompt,
                context=f"Concept: {concept}, Industry focus: {industry_focus}"
            )
            return response.text()
        
        return self._safe_ai_call(_call)

    def analyze_student_struggle(self, exercise_data: dict, time_spent: int, wrong_attempts: int, code_attempts: list = None) -> str:
        """Analyze student struggle patterns and provide targeted assistance."""
        def _call():
            backend = self._get_backend()
            if not backend:
                return "Consider taking a break and reviewing the fundamentals. You're making progress!"
            
            struggle_indicators = []
            if time_spent > 300:  # 5+ minutes
                struggle_indicators.append(f"Time spent: {time_spent // 60} minutes")
            if wrong_attempts > 3:
                struggle_indicators.append(f"Multiple attempts: {wrong_attempts}")
            if code_attempts and len(code_attempts) > 5:
                struggle_indicators.append(f"Many code revisions: {len(code_attempts)}")
            
            context = f"""Exercise: {exercise_data.get('title', 'Programming exercise')}
Exercise type: {exercise_data.get('type', 'N/A')}
Difficulty indicators: {', '.join(struggle_indicators) if struggle_indicators else 'Student appears to be progressing normally'}
Exercise description: {exercise_data.get('description', 'N/A')}"""
            
            if code_attempts:
                context += f"\nRecent code attempts:\n" + "\n---\n".join(code_attempts[-3:])
            
            prompt = """Analyze this student's learning situation and provide supportive, targeted guidance.

Consider:
1. What specific challenges they might be facing
2. What concepts they might need to review
3. Motivational support to keep them engaged  
4. Specific next steps or strategies
5. Whether they should take a different approach

Be encouraging and provide actionable advice. Don't just identify problems - offer solutions."""

            response = backend.prompt_with_context(
                pre_prompt=prompt,
                context=context
            )
            return response.text()
        
        return self._safe_ai_call(_call)

    def generate_debugging_guidance(self, error_type: str, code_context: str, student_level: str = "beginner") -> str:
        """Provide step-by-step debugging guidance."""
        def _call():
            backend = self._get_backend()
            if not backend:
                return "Debugging tip: Read the error message carefully, check your syntax, and test small parts of your code."
            
            prompt = f"""Provide step-by-step debugging guidance for a {student_level} level programming student.

Error type: {error_type}
Student level: {student_level}

Create a structured debugging approach:
1. Understanding the error
2. Common causes for this type of error
3. Step-by-step investigation process
4. How to fix it
5. How to prevent it in the future

Make it educational - help them become better at debugging, not just fix this one issue."""

            context = f"Error: {error_type}\nCode context: {code_context}"

            response = backend.prompt_with_context(
                pre_prompt=prompt,
                context=context
            )
            return response.text()
        
        return self._safe_ai_call(_call)

    def suggest_next_learning_step(self, current_progress: dict, skill_assessment: dict) -> str:
        """Suggest personalized next learning steps based on student progress."""
        def _call():
            backend = self._get_backend()
            if not backend:
                return "Continue practicing the fundamentals and try building small projects to apply what you've learned."
            
            prompt = """Based on this student's progress and skill assessment, suggest the most appropriate next learning step.

Consider:
1. Their current skill strengths and weaknesses
2. What they've recently completed successfully
3. Areas where they're struggling
4. Appropriate difficulty progression
5. Variety in learning (concepts, practice, projects)

Provide specific, actionable recommendations with brief explanations of why each step will help them grow."""

            context = f"Current progress: {current_progress}\nSkill assessment: {skill_assessment}"

            response = backend.prompt_with_context(
                pre_prompt=prompt,
                context=context
            )
            return response.text()
        
        return self._safe_ai_call(_call)


# Global instance for easy import
learning_ai = LearningContentAI()