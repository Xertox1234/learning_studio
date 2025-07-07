"""
Management command to populate the database with initial exercise data.
"""

from django.core.management.base import BaseCommand
from apps.learning.models import ProgrammingLanguage, ExerciseType


class Command(BaseCommand):
    help = 'Populate database with initial programming languages and exercise types'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Setting up programming languages...'))
        
        # Create programming languages
        languages = [
            {
                'name': 'Python',
                'slug': 'python',
                'file_extension': '.py',
                'docker_image': 'python:3.11-slim',
                'syntax_highlighter': 'python'
            },
            {
                'name': 'JavaScript',
                'slug': 'javascript',
                'file_extension': '.js',
                'docker_image': 'node:18-alpine',
                'syntax_highlighter': 'javascript'
            },
            {
                'name': 'Java',
                'slug': 'java',
                'file_extension': '.java',
                'docker_image': 'openjdk:11-jre-slim',
                'syntax_highlighter': 'java'
            },
            {
                'name': 'C++',
                'slug': 'cpp',
                'file_extension': '.cpp',
                'docker_image': 'gcc:latest',
                'syntax_highlighter': 'cpp'
            },
            {
                'name': 'HTML/CSS',
                'slug': 'html-css',
                'file_extension': '.html',
                'docker_image': 'nginx:alpine',
                'syntax_highlighter': 'html'
            },
        ]
        
        for lang_data in languages:
            language, created = ProgrammingLanguage.objects.get_or_create(
                slug=lang_data['slug'],
                defaults=lang_data
            )
            if created:
                self.stdout.write(f'  Created language: {language.name}')
            else:
                self.stdout.write(f'  Language already exists: {language.name}')
        
        self.stdout.write(self.style.SUCCESS('Setting up exercise types...'))
        
        # Create exercise types
        exercise_types = [
            {
                'name': 'function',
                'description': 'Write a function that solves a specific problem',
                'icon': 'fa-code',
                'supports_code_execution': True,
                'max_execution_time': 30
            },
            {
                'name': 'class',
                'description': 'Implement a class with specific methods and properties',
                'icon': 'fa-object-group',
                'supports_code_execution': True,
                'max_execution_time': 45
            },
            {
                'name': 'algorithm',
                'description': 'Solve algorithmic challenges and coding problems',
                'icon': 'fa-brain',
                'supports_code_execution': True,
                'max_execution_time': 60
            },
            {
                'name': 'debug',
                'description': 'Find and fix bugs in the provided code',
                'icon': 'fa-bug',
                'supports_code_execution': True,
                'max_execution_time': 30
            },
            {
                'name': 'fill_blank',
                'description': 'Fill in the missing code to complete the program',
                'icon': 'fa-edit',
                'supports_code_execution': True,
                'max_execution_time': 20
            },
            {
                'name': 'multiple_choice',
                'description': 'Answer multiple choice questions about code concepts',
                'icon': 'fa-list',
                'supports_code_execution': False,
                'max_execution_time': 0
            },
            {
                'name': 'project',
                'description': 'Build a complete mini-project',
                'icon': 'fa-project-diagram',
                'supports_code_execution': True,
                'max_execution_time': 120
            },
            {
                'name': 'quiz',
                'description': 'Interactive quiz about programming concepts',
                'icon': 'fa-question-circle',
                'supports_code_execution': False,
                'max_execution_time': 0
            },
        ]
        
        for type_data in exercise_types:
            exercise_type, created = ExerciseType.objects.get_or_create(
                name=type_data['name'],
                defaults=type_data
            )
            if created:
                self.stdout.write(f'  Created exercise type: {exercise_type.get_name_display()}')
            else:
                self.stdout.write(f'  Exercise type already exists: {exercise_type.get_name_display()}')
        
        self.stdout.write(self.style.SUCCESS('Exercise data setup completed successfully!'))