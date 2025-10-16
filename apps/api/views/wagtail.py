"""
Wagtail CMS views for blog posts, courses, lessons, and homepage content.
"""

from django.shortcuts import get_object_or_404
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from apps.api.content_serializers.streamfield import serialize_streamfield
from apps.api.utils import serialize_tags, get_featured_image_url


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def blog_index(request):
    """Get blog posts for React frontend."""
    try:
        from apps.blog.models import BlogPage, BlogCategory
        
        # Get query parameters
        category_slug = request.GET.get('category')
        tag = request.GET.get('tag')
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 9))
        
        # Get all published blog pages
        blog_pages = BlogPage.objects.live().public().order_by('-first_published_at')
        
        # Filter by category if provided
        if category_slug:
            blog_pages = blog_pages.filter(categories__slug=category_slug)
        
        # Filter by tag if provided
        if tag:
            blog_pages = blog_pages.filter(tags__name=tag)
        
        # Calculate pagination
        total_count = blog_pages.count()
        start = (page - 1) * page_size
        end = start + page_size
        paginated_posts = blog_pages[start:end]
        
        # Serialize blog posts
        posts_data = []
        for post in paginated_posts:
            # Get categories
            categories = [
                {
                    'id': cat.id,
                    'name': cat.name,
                    'slug': cat.slug,
                    'color': cat.color
                }
                for cat in post.categories.all()
            ]
            
            # Get tags
            tags = [tag.name for tag in post.tags.all()]
            
            # Render body content (simplified for JSON)
            body_content = []
            for block in post.body:
                if block.block_type == 'paragraph':
                    body_content.append({
                        'type': 'paragraph',
                        'value': str(block.value)[:200] + '...' if len(str(block.value)) > 200 else str(block.value)
                    })
                elif block.block_type == 'heading':
                    body_content.append({
                        'type': 'heading',
                        'value': str(block.value)
                    })
                # Add more block types as needed
            
            posts_data.append({
                'id': post.id,
                'title': post.title,
                'slug': post.slug,
                'intro': post.intro,
                'url': post.url,
                'author': {
                    'username': post.author.username if post.author else 'Anonymous',
                    'display_name': post.author.get_full_name() if post.author and post.author.get_full_name() else (post.author.username if post.author else 'Anonymous')
                } if post.author else None,
                'date': post.date.isoformat() if post.date else None,
                'reading_time': post.reading_time,
                'ai_generated': post.ai_generated,
                'ai_summary': post.ai_summary,
                'categories': categories,
                'tags': tags,
                'featured_image': post.featured_image.url if post.featured_image else None,
                'body_preview': body_content[:2]  # First 2 blocks for preview
            })
        
        # Calculate pagination info
        total_pages = (total_count + page_size - 1) // page_size
        has_next = page < total_pages
        has_previous = page > 1
        
        return Response({
            'posts': posts_data,
            'pagination': {
                'current_page': page,
                'total_pages': total_pages,
                'total_count': total_count,
                'page_size': page_size,
                'has_next': has_next,
                'has_previous': has_previous
            }
        })
        
    except Exception as e:
        return Response({
            'error': f'Failed to fetch blog posts: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def blog_post_detail(request, post_slug):
    """Get individual blog post for React frontend."""
    try:
        from apps.blog.models import BlogPage
        
        # Get the blog post
        post = get_object_or_404(BlogPage.objects.live().public(), slug=post_slug)
        
        # Get categories
        categories = [
            {
                'id': cat.id,
                'name': cat.name,
                'slug': cat.slug,
                'color': cat.color
            }
            for cat in post.categories.all()
        ]
        
        # Get tags
        tags = [tag.name for tag in post.tags.all()]
        
        # Serialize full body content via shared serializer
        body_content = serialize_streamfield(post.body, request)
        
        # Get related posts
        related_posts = BlogPage.objects.live().public().exclude(
            id=post.id
        ).filter(
            categories__in=post.categories.all()
        ).distinct().order_by('-first_published_at')[:3]
        
        related_posts_data = [
            {
                'id': related.id,
                'title': related.title,
                'slug': related.slug,
                'intro': related.intro[:100] + '...' if len(related.intro) > 100 else related.intro,
                'url': related.url,
                'date': related.date.isoformat() if related.date else None,
                'reading_time': related.reading_time
            }
            for related in related_posts
        ]
        
        return Response({
            'id': post.id,
            'title': post.title,
            'slug': post.slug,
            'intro': post.intro,
            'url': post.url,
            'author': {
                'username': post.author.username if post.author else 'Anonymous',
                'display_name': post.author.get_full_name() if post.author and post.author.get_full_name() else (post.author.username if post.author else 'Anonymous')
            } if post.author else None,
            'date': post.date.isoformat() if post.date else None,
            'reading_time': post.reading_time,
            'ai_generated': post.ai_generated,
            'ai_summary': post.ai_summary,
            'categories': categories,
            'tags': tags,
            'featured_image': post.featured_image.url if post.featured_image else None,
            'body': body_content,
            'related_posts': related_posts_data
        })
        
    except Exception as e:
        return Response({
            'error': f'Failed to fetch blog post: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def blog_categories(request):
    """Get blog categories for React frontend."""
    try:
        from apps.blog.models import BlogCategory
        
        categories = BlogCategory.objects.all().order_by('name')
        
        categories_data = [
            {
                'id': cat.id,
                'name': cat.name,
                'slug': cat.slug,
                'description': cat.description,
                'color': cat.color,
                'post_count': cat.blogpage_set.live().public().count()
            }
            for cat in categories
        ]
        
        return Response({'categories': categories_data})
        
    except Exception as e:
        return Response({
            'error': f'Failed to fetch blog categories: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def wagtail_homepage(request):
    """Get Wagtail homepage data for React frontend."""
    try:
        from apps.blog.models import HomePage, BlogPage

        # Get the homepage
        homepage = HomePage.objects.live().first()
        if not homepage:
            # Return default homepage data when HomePage doesn't exist yet
            recent_posts = BlogPage.objects.live().public().order_by('-first_published_at')[:3]
            recent_posts_data = [
                {
                    'id': post.id,
                    'title': post.title,
                    'slug': post.slug,
                    'intro': post.intro,
                    'url': post.url,
                    'date': post.date.isoformat() if post.date else None,
                    'reading_time': post.reading_time,
                    'ai_generated': post.ai_generated
                }
                for post in recent_posts
            ]

            return Response({
                'title': 'Python Learning Studio',
                'hero_title': 'Learn Python Programming',
                'hero_subtitle': 'Interactive Coding Exercises',
                'hero_description': 'Master Python through hands-on exercises and real-world projects',
                'features_title': 'Why Learn With Us',
                'features': [
                    {'title': 'Interactive Exercises', 'description': 'Learn by doing with hands-on coding', 'icon': 'code'},
                    {'title': 'Step-by-Step Guidance', 'description': 'Progress at your own pace', 'icon': 'route'},
                    {'title': 'Real-time Feedback', 'description': 'Get instant feedback on your code', 'icon': 'check-circle'}
                ],
                'stats': [
                    {'number': '50+', 'label': 'Exercises', 'description': 'Interactive coding challenges'},
                    {'number': '10+', 'label': 'Courses', 'description': 'Structured learning paths'},
                    {'number': '1000+', 'label': 'Students', 'description': 'Active learners'}
                ],
                'recent_posts': recent_posts_data
            })
        
        # Get features
        features = []
        for block in homepage.features:
            if block.block_type == 'feature':
                features.append({
                    'title': block.value.get('title', ''),
                    'description': block.value.get('description', ''),
                    'icon': block.value.get('icon', '')
                })
        
        # Get stats
        stats = []
        for block in homepage.stats:
            if block.block_type == 'stat':
                stats.append({
                    'number': block.value.get('number', ''),
                    'label': block.value.get('label', ''),
                    'description': block.value.get('description', '')
                })
        
        # Get recent blog posts
        recent_posts = BlogPage.objects.live().public().order_by('-first_published_at')[:3]
        recent_posts_data = [
            {
                'id': post.id,
                'title': post.title,
                'slug': post.slug,
                'intro': post.intro,
                'url': post.url,
                'date': post.date.isoformat() if post.date else None,
                'reading_time': post.reading_time,
                'ai_generated': post.ai_generated
            }
            for post in recent_posts
        ]
        
        return Response({
            'title': homepage.title,
            'hero_title': homepage.hero_title,
            'hero_subtitle': homepage.hero_subtitle,
            'hero_description': str(homepage.hero_description) if homepage.hero_description else '',
            'features_title': homepage.features_title,
            'features': features,
            'stats': stats,
            'recent_posts': recent_posts_data
        })
        
    except Exception as e:
        return Response({
            'error': f'Failed to fetch homepage: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def learning_index(request):
    """Get learning index page with featured courses."""
    try:
        from apps.blog.models import LearningIndexPage, CoursePage, SkillLevel
        
        # Get the learning index page
        learning_page = LearningIndexPage.objects.live().first()
        if not learning_page:
            return Response({
                'error': 'Learning index page not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get featured courses
        featured_courses = CoursePage.objects.live().public().filter(
            featured=True
        ).order_by('-first_published_at')[:6]
        
        featured_courses_data = []
        for course in featured_courses:
            featured_courses_data.append({
                'id': course.id,
                'title': course.title,
                'slug': course.slug,
                'url': course.url,
                'course_code': course.course_code,
                'short_description': course.short_description,
                'difficulty_level': course.difficulty_level,
                'estimated_duration': course.estimated_duration,
                'is_free': course.is_free,
                'price': str(course.price) if course.price else None,
                'skill_level': {
                    'name': course.skill_level.name,
                    'slug': course.skill_level.slug,
                    'color': course.skill_level.color
                } if course.skill_level else None,
                'instructor': {
                    'name': course.instructor.get_full_name(),
                    'email': course.instructor.email
                } if course.instructor else None,
                'course_image': course.course_image.url if course.course_image else None,
                'categories': [
                    {
                        'name': cat.name,
                        'slug': cat.slug,
                        'color': cat.color
                    }
                    for cat in course.categories.all()
                ]
            })
        
        # Get skill levels
        skill_levels = SkillLevel.objects.all()
        skill_levels_data = [
            {
                'id': level.id,
                'name': level.name,
                'slug': level.slug,
                'description': level.description,
                'color': level.color,
                'order': level.order
            }
            for level in skill_levels
        ]
        
        return Response({
            'title': learning_page.title,
            'intro': str(learning_page.intro) if learning_page.intro else '',
            'featured_courses_title': learning_page.featured_courses_title,
            'featured_courses': featured_courses_data,
            'skill_levels': skill_levels_data
        })
        
    except Exception as e:
        return Response({
            'error': f'Failed to fetch learning index: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def courses_list(request):
    """Get list of Wagtail courses with filtering and pagination."""
    try:
        from apps.blog.models import CoursePage, SkillLevel, BlogCategory
        
        # Get query parameters
        skill_level_slug = request.GET.get('skill_level')
        category_slug = request.GET.get('category')
        difficulty = request.GET.get('difficulty')
        is_free = request.GET.get('is_free')
        search = request.GET.get('search')
        page_num = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 12))
        
        # Start with base queryset
        courses = CoursePage.objects.live().public().order_by('-first_published_at')
        
        # Apply filters
        if skill_level_slug:
            courses = courses.filter(skill_level__slug=skill_level_slug)
        
        if category_slug:
            courses = courses.filter(categories__slug=category_slug)
        
        if difficulty:
            courses = courses.filter(difficulty_level=difficulty)
        
        if is_free is not None:
            is_free_bool = is_free.lower() in ('true', '1')
            courses = courses.filter(is_free=is_free_bool)
        
        if search:
            courses = courses.search(search)
        
        # Pagination
        total_count = courses.count()
        start = (page_num - 1) * page_size
        end = start + page_size
        paginated_courses = courses[start:end]
        
        # Serialize courses
        courses_data = []
        for course in paginated_courses:
            # Get lesson count
            lesson_count = course.get_children().live().public().count()
            
            courses_data.append({
                'id': course.id,
                'title': course.title,
                'slug': course.slug,
                'url': course.url,
                'course_code': course.course_code,
                'short_description': course.short_description,
                'difficulty_level': course.difficulty_level,
                'estimated_duration': course.estimated_duration,
                'is_free': course.is_free,
                'price': str(course.price) if course.price else None,
                'lesson_count': lesson_count,
                'featured': course.featured,
                'skill_level': {
                    'name': course.skill_level.name,
                    'slug': course.skill_level.slug,
                    'color': course.skill_level.color
                } if course.skill_level else None,
                'instructor': {
                    'name': course.instructor.get_full_name(),
                    'email': course.instructor.email
                } if course.instructor else None,
                'course_image': course.course_image.url if course.course_image else None,
                'categories': [
                    {
                        'name': cat.name,
                        'slug': cat.slug,
                        'color': cat.color
                    }
                    for cat in course.categories.all()
                ],
                'tags': serialize_tags(course)
            })
        
        # Pagination info
        pagination = {
            'current_page': page_num,
            'total_pages': (total_count + page_size - 1) // page_size,
            'total_count': total_count,
            'page_size': page_size,
            'has_next': end < total_count,
            'has_previous': page_num > 1
        }
        
        return Response({
            'courses': courses_data,
            'pagination': pagination
        })
        
    except Exception as e:
        return Response({
            'error': f'Failed to fetch courses: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Course detail and exercises endpoints
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def course_detail(request, course_slug):
    """Get detailed information about a specific Wagtail course."""
    try:
        from apps.blog.models import CoursePage

        course = get_object_or_404(CoursePage.objects.live().public(), slug=course_slug)

        # Serialize course data
        course_data = {
            'id': course.id,
            'title': course.title,
            'slug': course.slug,
            'url': course.url,
            'course_code': course.course_code,
            'short_description': course.short_description,
            'detailed_description': str(course.detailed_description),
            'difficulty_level': course.difficulty_level,
            'estimated_duration': course.estimated_duration,
            'is_free': course.is_free,
            'price': str(course.price) if course.price else None,
            'enrollment_limit': course.enrollment_limit,
            'featured': course.featured,
            'prerequisites': str(course.prerequisites) if course.prerequisites else '',
            'instructor': {
                'id': course.instructor.id,
                'name': course.instructor.get_full_name() or course.instructor.username,
                'email': course.instructor.email,
            } if course.instructor else None,
            'skill_level': {
                'name': course.skill_level.name,
                'slug': course.skill_level.slug,
                'color': course.skill_level.color,
            } if course.skill_level else None,
            'learning_objectives': [
                {
                    'id': obj.id,
                    'title': obj.title,
                    'description': obj.description,
                    'category': obj.category,
                }
                for obj in course.learning_objectives.all()
            ],
            'syllabus': serialize_streamfield(course.syllabus, request) if course.syllabus else [],
            'features': serialize_streamfield(course.features, request) if course.features else [],
            'course_image': course.course_image.url if course.course_image else None,
        }

        return Response(course_data)

    except Exception as e:
        return Response({
            'error': f'Failed to fetch course: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def course_exercises(request, course_slug):
    """Get exercises for a specific course, including direct children and exercises within lessons."""
    try:
        from apps.blog.models import CoursePage, ExercisePage, StepBasedExercisePage, LessonPage

        course = get_object_or_404(CoursePage.objects.live().public(), slug=course_slug)

        exercises = []

        # Get direct exercise children
        direct_exercises = course.get_children().live().public().specific()

        for child in direct_exercises:
            if isinstance(child, (ExercisePage, StepBasedExercisePage)):
                # Determine if it's a StepBasedExercisePage or regular ExercisePage
                is_step_based = isinstance(child, StepBasedExercisePage)

                exercise_data = {
                    'id': child.id,
                    'title': child.title,
                    'slug': child.slug,
                    'url': child.url,
                    'type': 'step_based' if is_step_based else 'exercise',
                    'sequence_number': child.sequence_number,
                    'difficulty': child.difficulty,
                    'points': child.total_points if is_step_based else child.points,
                    'estimated_time': child.estimated_time if is_step_based else None,
                    'parent_type': 'course',
                    'parent_title': course.title,
                }

                if is_step_based:
                    exercise_data['step_count'] = len(child.exercise_steps)
                    exercise_data['require_sequential'] = child.require_sequential

                exercises.append(exercise_data)

            elif isinstance(child, LessonPage):
                # Get exercises within this lesson
                lesson_exercises = child.get_children().live().public().specific()

                for lesson_child in lesson_exercises:
                    if isinstance(lesson_child, (ExercisePage, StepBasedExercisePage)):
                        # Determine if it's a StepBasedExercisePage or regular ExercisePage
                        is_step_based = isinstance(lesson_child, StepBasedExercisePage)

                        exercise_data = {
                            'id': lesson_child.id,
                            'title': lesson_child.title,
                            'slug': lesson_child.slug,
                            'url': lesson_child.url,
                            'type': 'step_based' if is_step_based else 'exercise',
                            'sequence_number': lesson_child.sequence_number,
                            'difficulty': lesson_child.difficulty,
                            'points': lesson_child.total_points if is_step_based else lesson_child.points,
                            'estimated_time': lesson_child.estimated_time if is_step_based else None,
                            'parent_type': 'lesson',
                            'parent_title': child.title,
                            'lesson_number': child.lesson_number,
                        }

                        if is_step_based:
                            exercise_data['step_count'] = len(lesson_child.exercise_steps)
                            exercise_data['require_sequential'] = lesson_child.require_sequential

                        exercises.append(exercise_data)

        # Sort by sequence_number
        exercises.sort(key=lambda x: (x.get('lesson_number', 0), x['sequence_number']))

        return Response({
            'course': {
                'id': course.id,
                'title': course.title,
                'slug': course.slug,
            },
            'exercises': exercises,
            'total_count': len(exercises),
        })

    except Exception as e:
        return Response({
            'error': f'Failed to fetch course exercises: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def lesson_detail(request, course_slug, lesson_slug):
    """Get detailed information about a specific lesson."""
    return Response({'error': 'Not implemented yet'}, status=501)


def exercise_detail(request, course_slug, lesson_slug, exercise_slug):
    """Get detailed information about a specific exercise."""
    return Response({'error': 'Not implemented yet'}, status=501)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def exercises_list(request):
    """Get list of Wagtail exercises with filtering and pagination."""
    try:
        from apps.blog.models import ExercisePage, StepBasedExercisePage
        
        # Get query parameters
        exercise_type = request.GET.get('type')
        difficulty = request.GET.get('difficulty')
        programming_language = request.GET.get('language')
        search = request.GET.get('search')
        page_num = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 12))
        include_step_based = request.GET.get('step_based', 'true').lower() == 'true'
        
        exercises = []
        
        # Get regular exercises
        regular_exercises = ExercisePage.objects.live().public().order_by('-first_published_at')
        
        # Apply filters
        if exercise_type:
            regular_exercises = regular_exercises.filter(exercise_type=exercise_type)
        if difficulty:
            regular_exercises = regular_exercises.filter(difficulty=difficulty)
        if programming_language:
            regular_exercises = regular_exercises.filter(programming_language=programming_language)
        if search:
            regular_exercises = regular_exercises.search(search)
        
        # Serialize regular exercises
        for exercise in regular_exercises:
            exercises.append({
                'id': exercise.id,
                'title': exercise.title,
                'slug': exercise.slug,
                'url': exercise.url,
                'type': 'exercise',
                'exercise_type': exercise.exercise_type,
                'difficulty': exercise.difficulty,
                'points': exercise.points,
                'programming_language': exercise.programming_language,
                'layout_type': exercise.layout_type,
                'description': str(exercise.description) if exercise.description else '',
                'time_limit': exercise.time_limit,
                'max_attempts': exercise.max_attempts,
                'has_template': bool(exercise.template_code),
                'has_hints': bool(exercise.progressive_hints),
                'lesson_title': exercise.get_parent().title if exercise.get_parent() else None,
                'course_title': exercise.get_parent().get_parent().title if exercise.get_parent() and exercise.get_parent().get_parent() else None,
            })
        
        # Get step-based exercises if requested
        if include_step_based:
            step_exercises = StepBasedExercisePage.objects.live().public().order_by('-first_published_at')
            
            # Apply general filters (difficulty only applies to step-based)
            if difficulty:
                step_exercises = step_exercises.filter(difficulty=difficulty)
            if search:
                step_exercises = step_exercises.search(search)
            
            # Serialize step-based exercises
            for exercise in step_exercises:
                step_count = len(exercise.exercise_steps) if exercise.exercise_steps else 0
                exercises.append({
                    'id': exercise.id,
                    'title': exercise.title,
                    'slug': exercise.slug,
                    'url': exercise.url,
                    'type': 'step_based',
                    'exercise_type': 'step_based',
                    'difficulty': exercise.difficulty,
                    'points': exercise.total_points,
                    'estimated_time': exercise.estimated_time,
                    'require_sequential': exercise.require_sequential,
                    'step_count': step_count,
                    'lesson_title': exercise.get_parent().title if exercise.get_parent() else None,
                    'course_title': exercise.get_parent().get_parent().title if exercise.get_parent() and exercise.get_parent().get_parent() else None,
                })
        
        # Sort by creation date (newest first)
        exercises.sort(key=lambda x: x['id'], reverse=True)
        
        # Pagination
        total_count = len(exercises)
        start = (page_num - 1) * page_size
        end = start + page_size
        paginated_exercises = exercises[start:end]
        
        pagination = {
            'current_page': page_num,
            'total_pages': (total_count + page_size - 1) // page_size,
            'total_count': total_count,
            'page_size': page_size,
            'has_next': end < total_count,
            'has_previous': page_num > 1
        }
        
        return Response({
            'exercises': paginated_exercises,
            'pagination': pagination
        })
        
    except Exception as e:
        return Response({
            'error': f'Failed to fetch exercises: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def exercise_detail(request, exercise_slug):
    """Get detailed information about a specific exercise."""
    try:
        from apps.blog.models import ExercisePage
        
        # Get the exercise
        exercise = get_object_or_404(ExercisePage.objects.live().public(), slug=exercise_slug)
        
        # Parse progressive hints JSON
        progressive_hints = []
        if exercise.progressive_hints:
            if isinstance(exercise.progressive_hints, list):
                progressive_hints = exercise.progressive_hints
            elif isinstance(exercise.progressive_hints, str):
                try:
                    import json
                    progressive_hints = json.loads(exercise.progressive_hints)
                except (ValueError, json.JSONDecodeError):
                    progressive_hints = []
        
        # Parse solutions JSON
        solutions = {}
        if exercise.solutions:
            if isinstance(exercise.solutions, dict):
                solutions = exercise.solutions
            elif isinstance(exercise.solutions, str):
                try:
                    import json
                    solutions = json.loads(exercise.solutions)
                except (ValueError, json.JSONDecodeError):
                    solutions = {}
        
        # Parse alternative solutions JSON
        alternative_solutions = {}
        if exercise.alternative_solutions:
            if isinstance(exercise.alternative_solutions, dict):
                alternative_solutions = exercise.alternative_solutions
            elif isinstance(exercise.alternative_solutions, str):
                try:
                    import json
                    alternative_solutions = json.loads(exercise.alternative_solutions)
                except (ValueError, json.JSONDecodeError):
                    alternative_solutions = {}
        
        # Serialize exercise content
        exercise_content = []
        if exercise.exercise_content:
            for block in exercise.exercise_content:
                if block.block_type == 'instruction':
                    exercise_content.append({
                        'type': 'instruction',
                        'value': str(block.value)
                    })
                elif block.block_type == 'code_example':
                    exercise_content.append({
                        'type': 'code_example',
                        'title': block.value.get('title', ''),
                        'language': block.value.get('language', 'python'),
                        'code': block.value.get('code', ''),
                        'explanation': str(block.value.get('explanation', ''))
                    })
                elif block.block_type == 'hint_block':
                    exercise_content.append({
                        'type': 'hint_block',
                        'hint_type': block.value.get('hint_type', 'general'),
                        'content': str(block.value.get('content', ''))
                    })
        
        # Serialize test cases
        test_cases = []
        if exercise.test_cases:
            for block in exercise.test_cases:
                if block.block_type == 'test_case':
                    test_cases.append({
                        'input': block.value.get('input', ''),
                        'expected_output': block.value.get('expected_output', ''),
                        'description': block.value.get('description', ''),
                        'is_hidden': block.value.get('is_hidden', False)
                    })
        
        # Serialize hints
        hints_data = []
        if exercise.hints:
            for block in exercise.hints:
                if block.block_type == 'hint':
                    hints_data.append({
                        'hint_text': str(block.value.get('hint_text', '')),
                        'reveal_after_attempts': block.value.get('reveal_after_attempts', 3)
                    })
        
        # Get context (lesson and course info)
        lesson = exercise.get_parent().specific if exercise.get_parent() else None
        course = lesson.get_parent().specific if lesson and lesson.get_parent() else None
        
        return Response({
            'id': exercise.id,
            'title': exercise.title,
            'slug': exercise.slug,
            'url': exercise.url,
            'exercise_type': exercise.exercise_type,
            'difficulty': exercise.difficulty,
            'points': exercise.points,
            'programming_language': exercise.programming_language,
            'layout_type': exercise.layout_type,
            'show_sidebar': exercise.show_sidebar,
            'code_editor_height': exercise.code_editor_height,
            'description': str(exercise.description) if exercise.description else '',
            'starter_code': exercise.starter_code,
            'solution_code': exercise.solution_code,
            'template_code': exercise.template_code,
            'template': exercise.template_code,  # Alias for frontend compatibility
            'solutions': solutions,
            'alternative_solutions': alternative_solutions,
            'alternativeSolutions': alternative_solutions,  # Alias for frontend compatibility
            'progressive_hints': progressive_hints,
            'progressiveHints': progressive_hints,  # Alias for frontend compatibility
            'question_data': exercise.question_data,
            'exercise_content': exercise_content,
            'test_cases': test_cases,
            'hints': hints_data,
            'time_limit': exercise.time_limit,
            'max_attempts': exercise.max_attempts,
            'language': exercise.programming_language,  # Alias for frontend compatibility
            'lesson': {
                'id': lesson.id,
                'title': lesson.title,
                'slug': lesson.slug,
                'url': lesson.url
            } if lesson else None,
            'course': {
                'id': course.id,
                'title': course.title,
                'slug': course.slug,
                'url': course.url
            } if course else None,
        })
        
    except Exception as e:
        return Response({
            'error': f'Failed to fetch exercise: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def step_exercise_detail(request, exercise_slug):
    """Get detailed information about a specific step-based exercise."""
    try:
        from apps.blog.models import StepBasedExercisePage
        
        # Get the exercise
        exercise = get_object_or_404(StepBasedExercisePage.objects.live().public(), slug=exercise_slug)
        
        # Serialize exercise steps
        steps = []
        if exercise.exercise_steps:
            for block in exercise.exercise_steps:
                if block.block_type == 'exercise_step':
                    step_data = {
                        'step_number': block.value.get('step_number', 1),
                        'title': block.value.get('title', ''),
                        'description': str(block.value.get('description', '')),
                        'exercise_type': block.value.get('exercise_type', 'code'),
                        'template': block.value.get('template', ''),
                        'points': block.value.get('points', 10),
                        'success_message': block.value.get('success_message', ''),
                        'hint': block.value.get('hint', ''),
                    }
                    
                    # Parse solutions JSON for this step
                    solutions_text = block.value.get('solutions', '')
                    if solutions_text:
                        try:
                            import json
                            step_data['solutions'] = json.loads(solutions_text)
                        except (ValueError, json.JSONDecodeError):
                            step_data['solutions'] = {}
                    else:
                        step_data['solutions'] = {}
                    
                    steps.append(step_data)
        
        # Sort steps by step_number
        steps.sort(key=lambda x: x['step_number'])
        
        # Serialize general hints
        general_hints = []
        if exercise.general_hints:
            for block in exercise.general_hints:
                if block.block_type == 'hint':
                    general_hints.append({
                        'hint_text': str(block.value.get('hint_text', '')),
                        'reveal_after_attempts': block.value.get('reveal_after_attempts', 3)
                    })
        
        # Get context (lesson and course info)
        lesson = exercise.get_parent().specific if exercise.get_parent() else None
        course = lesson.get_parent().specific if lesson and lesson.get_parent() else None
        
        return Response({
            'id': exercise.id,
            'title': exercise.title,
            'slug': exercise.slug,
            'url': exercise.url,
            'type': 'step_based',
            'require_sequential': exercise.require_sequential,
            'total_points': exercise.total_points,
            'difficulty': exercise.difficulty,
            'estimated_time': exercise.estimated_time,
            'steps': steps,
            'step_count': len(steps),
            'general_hints': general_hints,
            'lesson': {
                'id': lesson.id,
                'title': lesson.title,
                'slug': lesson.slug,
                'url': lesson.url
            } if lesson else None,
            'course': {
                'id': course.id,
                'title': course.title,
                'slug': course.slug,
                'url': course.url
            } if course else None,
        })
        
    except Exception as e:
        return Response({
            'error': f'Failed to fetch step-based exercise: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def wagtail_playground(request):
    """Get Wagtail playground configuration."""
    return Response({'error': 'Not implemented yet'}, status=501)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def wagtail_course_enroll(request, course_slug):
    """Enroll in a Wagtail course."""
    try:
        from apps.blog.models import CoursePage, WagtailCourseEnrollment

        course = get_object_or_404(CoursePage.objects.live().public(), slug=course_slug)

        # Check if already enrolled
        enrollment, created = WagtailCourseEnrollment.objects.get_or_create(
            user=request.user,
            course=course
        )

        if created:
            return Response({
                'message': 'Successfully enrolled in course',
                'enrollment': {
                    'enrolled': True,
                    'enrolled_at': enrollment.enrolled_at,
                    'progress_percentage': enrollment.progress_percentage
                }
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'message': 'Already enrolled in this course',
                'enrollment': {
                    'enrolled': True,
                    'enrolled_at': enrollment.enrolled_at,
                    'progress_percentage': enrollment.progress_percentage
                }
            }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'error': f'Failed to enroll: {str(e)}'
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def wagtail_course_unenroll(request, course_slug):
    """Unenroll from a Wagtail course."""
    try:
        from apps.blog.models import CoursePage, WagtailCourseEnrollment

        course = get_object_or_404(CoursePage.objects.live().public(), slug=course_slug)

        enrollment = WagtailCourseEnrollment.objects.filter(
            user=request.user,
            course=course
        ).first()

        if enrollment:
            enrollment.delete()
            return Response({
                'message': 'Successfully unenrolled from course'
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': 'Not enrolled in this course'
            }, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        return Response({
            'error': f'Failed to unenroll: {str(e)}'
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def wagtail_course_enrollment_status(request, course_slug):
    """Get enrollment status for a Wagtail course."""
    try:
        from apps.blog.models import CoursePage, WagtailCourseEnrollment

        course = get_object_or_404(CoursePage.objects.live().public(), slug=course_slug)

        enrollment = WagtailCourseEnrollment.objects.filter(
            user=request.user,
            course=course
        ).first()

        if enrollment:
            return Response({
                'enrolled': True,
                'enrollment': {
                    'enrolled_at': enrollment.enrolled_at,
                    'progress_percentage': enrollment.progress_percentage,
                    'completed': enrollment.completed,
                    'completed_at': enrollment.completed_at,
                    'last_activity': enrollment.last_activity,
                    'total_time_spent': enrollment.total_time_spent
                }
            })
        else:
            return Response({
                'enrolled': False,
                'enrollment': None
            })

    except Exception as e:
        return Response({
            'error': f'Failed to get enrollment status: {str(e)}'
        }, status=status.HTTP_400_BAD_REQUEST)


def wagtail_user_enrollments(request):
    """Get user's Wagtail course enrollments."""
    return Response({'error': 'Not implemented yet'}, status=501)