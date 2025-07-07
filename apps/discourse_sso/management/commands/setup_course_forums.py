"""
Management command to set up course-specific forum categories and groups in Discourse.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from apps.discourse_sso.models import DiscourseGroupMapping
from apps.learning.models import Course, Enrollment
from apps.discourse_sso.services import DiscourseSSO


class Command(BaseCommand):
    help = 'Set up course-specific forum categories and groups for Discourse integration'

    def add_arguments(self, parser):
        parser.add_argument(
            '--course-slug',
            type=str,
            help='Set up forum for specific course by slug',
        )
        parser.add_argument(
            '--all-courses',
            action='store_true',
            help='Set up forums for all courses',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without actually creating it',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Recreate existing group mappings',
        )
        parser.add_argument(
            '--enroll-users',
            action='store_true',
            help='Automatically add enrolled users to course groups',
        )

    def handle(self, *args, **options):
        self.sso_service = DiscourseSSO()
        
        self.stdout.write(
            self.style.SUCCESS('Setting up course-specific forum categories...')
        )

        # Get courses to process
        courses = self.get_courses_to_process(options)
        
        if not courses:
            return

        # Process each course
        for course in courses:
            self.setup_course_forum(course, options)

        self.stdout.write(
            self.style.SUCCESS('Course forum setup complete!')
        )

    def get_courses_to_process(self, options):
        """Get the list of courses to process based on options."""
        
        if options['course_slug']:
            try:
                return [Course.objects.get(slug=options['course_slug'])]
            except Course.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f"Course with slug '{options['course_slug']}' not found.")
                )
                return []

        if options['all_courses']:
            courses = Course.objects.filter(is_published=True)
            self.stdout.write(f'Found {courses.count()} published courses to process.')
            return list(courses)

        # If no specific option, show help
        self.stdout.write(
            self.style.WARNING(
                'Please specify which courses to process using --course-slug or --all-courses'
            )
        )
        return []

    def setup_course_forum(self, course, options):
        """Set up forum category and groups for a specific course."""
        
        self.stdout.write(f'\nProcessing course: {course.title} ({course.slug})')
        
        # Create course group
        self.create_course_group(course, options)
        
        # Create instructor group for course
        self.create_instructor_group(course, options)
        
        # Add enrolled users to groups if requested
        if options['enroll_users']:
            self.enroll_users_in_groups(course, options['dry_run'])

    def create_course_group(self, course, options):
        """Create a group for course participants."""
        
        django_group_name = f"Course-{course.slug}"
        discourse_group_name = f"course-{course.slug}"
        
        # Get or create Django group
        django_group, group_created = Group.objects.get_or_create(name=django_group_name)
        
        if group_created:
            self.stdout.write(
                self.style.WARNING(f'  Created Django group: {django_group_name}')
            )

        # Check if mapping already exists
        existing_mapping = DiscourseGroupMapping.objects.filter(
            django_group=django_group
        ).first()

        if existing_mapping and not options['force']:
            self.stdout.write(
                self.style.WARNING(
                    f'  Group mapping already exists: {django_group_name} → {existing_mapping.discourse_group_name}'
                )
            )
            return

        if options['dry_run']:
            action = 'UPDATE' if existing_mapping else 'CREATE'
            self.stdout.write(
                f'  [DRY RUN] {action}: {django_group_name} → {discourse_group_name}'
            )
            return

        # Create or update the mapping
        mapping, created = DiscourseGroupMapping.objects.update_or_create(
            django_group=django_group,
            defaults={
                'discourse_group_name': discourse_group_name,
                'auto_sync': True,
            }
        )

        if created:
            self.stdout.write(
                self.style.SUCCESS(
                    f'  ✓ Created group mapping: {django_group_name} → {discourse_group_name}'
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    f'  ↻ Updated group mapping: {django_group_name} → {discourse_group_name}'
                )
            )

    def create_instructor_group(self, course, options):
        """Create a group for course instructors."""
        
        django_group_name = f"Course-{course.slug}-Instructors"
        discourse_group_name = f"course-{course.slug}-instructors"
        
        # Get or create Django group
        django_group, group_created = Group.objects.get_or_create(name=django_group_name)
        
        if group_created:
            self.stdout.write(
                self.style.WARNING(f'  Created Django instructor group: {django_group_name}')
            )

        # Check if mapping already exists
        existing_mapping = DiscourseGroupMapping.objects.filter(
            django_group=django_group
        ).first()

        if existing_mapping and not options['force']:
            self.stdout.write(
                self.style.WARNING(
                    f'  Instructor group mapping already exists: {django_group_name} → {existing_mapping.discourse_group_name}'
                )
            )
            return

        if options['dry_run']:
            action = 'UPDATE' if existing_mapping else 'CREATE'
            self.stdout.write(
                f'  [DRY RUN] {action}: {django_group_name} → {discourse_group_name}'
            )
            return

        # Create or update the mapping
        mapping, created = DiscourseGroupMapping.objects.update_or_create(
            django_group=django_group,
            defaults={
                'discourse_group_name': discourse_group_name,
                'auto_sync': True,
            }
        )

        # Add course instructor to the group if available
        if hasattr(course, 'instructor') and course.instructor:
            django_group.user_set.add(course.instructor)
            self.stdout.write(
                f'    Added instructor {course.instructor.username} to group'
            )

        if created:
            self.stdout.write(
                self.style.SUCCESS(
                    f'  ✓ Created instructor group mapping: {django_group_name} → {discourse_group_name}'
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    f'  ↻ Updated instructor group mapping: {django_group_name} → {discourse_group_name}'
                )
            )

    def enroll_users_in_groups(self, course, dry_run=False):
        """Add enrolled users to course groups."""
        
        try:
            # Get course group
            course_group_name = f"Course-{course.slug}"
            course_group = Group.objects.get(name=course_group_name)
            
            # Get enrolled users
            enrollments = Enrollment.objects.filter(course=course, is_active=True)
            enrolled_users = [enrollment.user for enrollment in enrollments]
            
            if not enrolled_users:
                self.stdout.write(
                    self.style.WARNING(f'    No enrolled users found for {course.title}')
                )
                return

            if dry_run:
                self.stdout.write(
                    f'    [DRY RUN] Would add {len(enrolled_users)} users to {course_group_name}'
                )
                return

            # Add users to group
            for user in enrolled_users:
                course_group.user_set.add(user)
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'    ✓ Added {len(enrolled_users)} enrolled users to {course_group_name}'
                )
            )

        except Group.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'    Course group not found: {course_group_name}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'    Error enrolling users: {e}')
            )

    def display_course_forum_structure(self):
        """Display the current course forum structure."""
        
        self.stdout.write('\n' + '='*60)
        self.stdout.write('COURSE FORUM STRUCTURE')
        self.stdout.write('='*60)
        
        # Get all course-related mappings
        course_mappings = DiscourseGroupMapping.objects.filter(
            discourse_group_name__startswith='course-'
        ).order_by('discourse_group_name')
        
        if not course_mappings.exists():
            self.stdout.write('No course forum groups found.')
            return

        current_course = None
        for mapping in course_mappings:
            # Extract course slug from group name
            if mapping.discourse_group_name.endswith('-instructors'):
                course_slug = mapping.discourse_group_name.replace('course-', '').replace('-instructors', '')
                group_type = 'Instructors'
            else:
                course_slug = mapping.discourse_group_name.replace('course-', '')
                group_type = 'Students'

            if course_slug != current_course:
                if current_course is not None:
                    self.stdout.write('')  # Add spacing between courses
                
                try:
                    course = Course.objects.get(slug=course_slug)
                    self.stdout.write(f'📚 {course.title} ({course_slug})')
                except Course.DoesNotExist:
                    self.stdout.write(f'📚 Unknown Course ({course_slug})')
                
                current_course = course_slug

            member_count = mapping.django_group.user_set.count()
            auto_sync_status = "✓" if mapping.auto_sync else "✗"
            
            self.stdout.write(
                f'  └─ {group_type}: {mapping.discourse_group_name} '
                f'[{member_count} members] [Auto-sync: {auto_sync_status}]'
            )

        self.stdout.write('='*60)

    def generate_discourse_category_config(self):
        """Generate suggested Discourse category configuration."""
        
        self.stdout.write('\n' + '='*60)
        self.stdout.write('SUGGESTED DISCOURSE CATEGORY CONFIGURATION')
        self.stdout.write('='*60)
        
        courses = Course.objects.filter(is_published=True)
        
        if not courses.exists():
            self.stdout.write('No published courses found.')
            return

        self.stdout.write('\nCreate these categories in your Discourse admin:')
        self.stdout.write('')
        
        for course in courses:
            course_group = f"course-{course.slug}"
            instructor_group = f"course-{course.slug}-instructors"
            
            self.stdout.write(f'📁 {course.title}')
            self.stdout.write(f'   Slug: {course.slug}')
            self.stdout.write(f'   Read Access: {course_group}, {instructor_group}')
            self.stdout.write(f'   Create/Reply: {course_group}')
            self.stdout.write(f'   Moderate: {instructor_group}')
            self.stdout.write('')

        self.stdout.write('Note: Set up these groups in Discourse with the same names')
        self.stdout.write('as the discourse_group_name values shown above.')
        self.stdout.write('='*60)