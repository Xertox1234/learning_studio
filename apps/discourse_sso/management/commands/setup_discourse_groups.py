"""
Management command to set up Discourse group mappings based on Django groups and course structure.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from apps.discourse_sso.models import DiscourseGroupMapping
from apps.learning.models import Course


class Command(BaseCommand):
    help = 'Set up Discourse group mappings for user roles and course access'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without actually creating it',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Recreate existing mappings',
        )
        parser.add_argument(
            '--course-groups',
            action='store_true',
            help='Create course-specific groups',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Setting up Discourse group mappings...')
        )

        # Default role-based groups
        role_mappings = [
            ('Instructors', 'instructors'),
            ('Students', 'students'),
            ('Mentors', 'mentors'),
            ('Teaching Assistants', 'teaching_assistants'),
            ('Moderators', 'moderators'),
            ('Premium Users', 'premium_users'),
        ]

        # Create role-based group mappings
        for django_group_name, discourse_group_name in role_mappings:
            self.create_group_mapping(
                django_group_name, 
                discourse_group_name, 
                options['dry_run'], 
                options['force']
            )

        # Create course-specific groups if requested
        if options['course_groups']:
            self.create_course_groups(options['dry_run'], options['force'])

        self.stdout.write(
            self.style.SUCCESS('Discourse group mapping setup complete!')
        )

    def create_group_mapping(self, django_group_name, discourse_group_name, dry_run=False, force=False):
        """Create a mapping between Django group and Discourse group."""
        
        # Get or create Django group
        django_group, group_created = Group.objects.get_or_create(name=django_group_name)
        
        if group_created:
            self.stdout.write(
                self.style.WARNING(f'Created Django group: {django_group_name}')
            )

        # Check if mapping already exists
        existing_mapping = DiscourseGroupMapping.objects.filter(
            django_group=django_group
        ).first()

        if existing_mapping and not force:
            self.stdout.write(
                self.style.WARNING(
                    f'Mapping already exists: {django_group_name} → {existing_mapping.discourse_group_name}'
                )
            )
            return

        if dry_run:
            action = 'UPDATE' if existing_mapping else 'CREATE'
            self.stdout.write(
                f'[DRY RUN] {action}: {django_group_name} → {discourse_group_name}'
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
                    f'Created mapping: {django_group_name} → {discourse_group_name}'
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    f'Updated mapping: {django_group_name} → {discourse_group_name}'
                )
            )

    def create_course_groups(self, dry_run=False, force=False):
        """Create course-specific groups for forum categories."""
        
        self.stdout.write('\nCreating course-specific groups...')
        
        try:
            courses = Course.objects.all()
            
            if not courses.exists():
                self.stdout.write(
                    self.style.WARNING('No courses found. Skipping course group creation.')
                )
                return

            for course in courses:
                # Create group name based on course slug
                django_group_name = f"Course-{course.slug}"
                discourse_group_name = f"course-{course.slug}"
                
                self.create_group_mapping(
                    django_group_name, 
                    discourse_group_name, 
                    dry_run, 
                    force
                )

                # If not dry run, add enrolled users to the group
                if not dry_run:
                    self.add_enrolled_users_to_group(course, django_group_name)

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating course groups: {e}')
            )

    def add_enrolled_users_to_group(self, course, group_name):
        """Add enrolled users to course group."""
        
        try:
            group = Group.objects.get(name=group_name)
            
            # Get enrolled users (assuming enrollment model exists)
            if hasattr(course, 'enrollments'):
                enrolled_users = [enrollment.user for enrollment in course.enrollments.all()]
                
                for user in enrolled_users:
                    group.user_set.add(user)
                
                self.stdout.write(
                    f'  Added {len(enrolled_users)} users to {group_name}'
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'  No enrollment model found for course: {course.title}'
                    )
                )
                
        except Group.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Group not found: {group_name}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error adding users to group {group_name}: {e}')
            )

    def display_summary(self):
        """Display a summary of current mappings."""
        
        self.stdout.write('\n' + '='*50)
        self.stdout.write('CURRENT DISCOURSE GROUP MAPPINGS')
        self.stdout.write('='*50)
        
        mappings = DiscourseGroupMapping.objects.all().order_by('django_group__name')
        
        if not mappings.exists():
            self.stdout.write('No group mappings found.')
            return

        for mapping in mappings:
            auto_sync_status = "✓" if mapping.auto_sync else "✗"
            member_count = mapping.django_group.user_set.count()
            
            self.stdout.write(
                f'{mapping.django_group.name} → {mapping.discourse_group_name} '
                f'[{member_count} members] [Auto-sync: {auto_sync_status}]'
            )

        self.stdout.write('='*50)