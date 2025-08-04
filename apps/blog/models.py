"""
Wagtail page models for Python Learning Studio blog and learning content.
"""

from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django import forms
import json

from wagtail.admin.panels import FieldPanel, MultiFieldPanel, InlinePanel
from wagtail.fields import RichTextField, StreamField
from wagtail.models import Page, Orderable
from wagtail.search import index
from wagtail.snippets.models import register_snippet
from wagtail import blocks
from wagtail.images.blocks import ImageChooserBlock
from modelcluster.fields import ParentalKey, ParentalManyToManyField
from modelcluster.contrib.taggit import ClusterTaggableManager
from taggit.models import TaggedItemBase

User = get_user_model()


class HomePage(Page):
    """
    Home page for the Python Learning Studio.
    """
    template = 'blog/home_page.html'
    
    # Hero section
    hero_title = models.CharField(max_length=255, default="Python Learning Studio")
    hero_subtitle = models.CharField(max_length=255, blank=True)
    hero_description = RichTextField(blank=True)
    hero_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )
    
    # Features section
    features_title = models.CharField(max_length=255, default="Why Learn With Us?")
    features = StreamField([
        ('feature', blocks.StructBlock([
            ('title', blocks.CharBlock(max_length=100)),
            ('description', blocks.TextBlock()),
            ('icon', blocks.CharBlock(max_length=50, help_text="Font Awesome icon class")),
        ])),
    ], blank=True, use_json_field=True)
    
    # Stats section
    stats = StreamField([
        ('stat', blocks.StructBlock([
            ('number', blocks.CharBlock(max_length=20)),
            ('label', blocks.CharBlock(max_length=50)),
            ('description', blocks.TextBlock(required=False)),
        ])),
    ], blank=True, use_json_field=True)

    content_panels = Page.content_panels + [
        MultiFieldPanel([
            FieldPanel('hero_title'),
            FieldPanel('hero_subtitle'),
            FieldPanel('hero_description'),
            FieldPanel('hero_image'),
        ], heading="Hero Section"),
        MultiFieldPanel([
            FieldPanel('features_title'),
            FieldPanel('features'),
        ], heading="Features Section"),
        FieldPanel('stats', heading="Statistics"),
    ]

    search_fields = Page.search_fields + [
        index.SearchField('hero_title'),
        index.SearchField('hero_description'),
    ]

    # Only allow one home page
    max_count = 1
    
    def get_context(self, request):
        context = super().get_context(request)
        # Add recent blog posts
        context['recent_posts'] = BlogPage.objects.live().public().order_by('-first_published_at')[:3]
        return context


@register_snippet
class BlogCategory(models.Model):
    """
    Categories for blog posts.
    """
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, default="#3498db", help_text="Hex color code")
    
    panels = [
        FieldPanel('name'),
        FieldPanel('slug'),
        FieldPanel('description'),
        FieldPanel('color'),
    ]
    
    class Meta:
        verbose_name_plural = 'Blog Categories'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class BlogPageTag(TaggedItemBase):
    """
    Tags for blog pages.
    """
    content_object = ParentalKey(
        'BlogPage',
        related_name='tagged_items',
        on_delete=models.CASCADE
    )


class BlogIndexPage(Page):
    """
    Index page for blog posts.
    """
    template = 'blog/blog_index_page.html'
    
    intro = RichTextField(blank=True)
    
    content_panels = Page.content_panels + [
        FieldPanel('intro'),
    ]
    
    def get_context(self, request):
        context = super().get_context(request)
        
        # Get all blog pages
        blogpages = self.get_children().live().order_by('-first_published_at')
        
        # Filter by category if provided
        category = request.GET.get('category')
        if category:
            blogpages = blogpages.filter(blogpage__categories__slug=category)
        
        # Filter by tag if provided
        tag = request.GET.get('tag')
        if tag:
            blogpages = blogpages.filter(blogpage__tags__name=tag)
        
        # Pagination
        paginator = Paginator(blogpages, 10)
        page = request.GET.get('page')
        blogpages = paginator.get_page(page)
        
        context['blogpages'] = blogpages
        context['categories'] = BlogCategory.objects.all()
        
        return context


class BlogPage(Page):
    """
    Individual blog post page.
    """
    template = 'blog/blog_page.html'
    
    # Author and publishing info
    author = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='blog_posts'
    )
    date = models.DateField("Post date")
    
    # Content
    intro = models.CharField(max_length=250, help_text="Brief introduction to the post")
    body = StreamField([
        ('heading', blocks.CharBlock(form_classname="title")),
        ('paragraph', blocks.RichTextBlock()),
        ('image', ImageChooserBlock()),
        ('code', blocks.StructBlock([
            ('language', blocks.ChoiceBlock(choices=[
                ('python', 'Python'),
                ('javascript', 'JavaScript'),
                ('html', 'HTML'),
                ('css', 'CSS'),
                ('sql', 'SQL'),
                ('bash', 'Bash'),
            ])),
            ('code', blocks.TextBlock()),
            ('caption', blocks.CharBlock(required=False)),
        ])),
        ('quote', blocks.StructBlock([
            ('text', blocks.TextBlock()),
            ('attribute_name', blocks.CharBlock(blank=True, required=False, label='Source')),
        ])),
        ('embed', blocks.RawHTMLBlock(help_text="Embed code (YouTube, CodePen, etc.)")),
        ('callout', blocks.StructBlock([
            ('type', blocks.ChoiceBlock(choices=[
                ('info', 'Info'),
                ('warning', 'Warning'),
                ('tip', 'Tip'),
                ('danger', 'Danger'),
            ])),
            ('title', blocks.CharBlock(required=False)),
            ('text', blocks.RichTextBlock()),
        ])),
    ], use_json_field=True)
    
    # Meta information
    categories = ParentalManyToManyField('blog.BlogCategory', blank=True)
    tags = ClusterTaggableManager(through=BlogPageTag, blank=True)
    
    # SEO
    featured_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        help_text="Image for social media and featured post display"
    )
    
    # Reading metrics
    reading_time = models.PositiveIntegerField(
        default=5,
        help_text="Estimated reading time in minutes"
    )
    
    # AI enhancement fields
    ai_summary = models.TextField(
        blank=True,
        help_text="AI-generated summary of the post (auto-populated)"
    )
    ai_generated = models.BooleanField(
        default=False,
        help_text="Indicates if content was AI-assisted"
    )

    search_fields = Page.search_fields + [
        index.SearchField('intro'),
        index.SearchField('body'),
        index.SearchField('tags'),
    ]

    content_panels = Page.content_panels + [
        MultiFieldPanel([
            FieldPanel('author'),
            FieldPanel('date'),
            FieldPanel('categories', widget=forms.CheckboxSelectMultiple),
            FieldPanel('tags'),
        ], heading="Publishing Information"),
        FieldPanel('intro'),
        FieldPanel('body'),
        MultiFieldPanel([
            FieldPanel('featured_image'),
            FieldPanel('reading_time'),
        ], heading="Meta Information"),
        MultiFieldPanel([
            FieldPanel('ai_summary'),
            FieldPanel('ai_generated'),
        ], heading="AI Enhancement"),
    ]

    promote_panels = Page.promote_panels + [
        FieldPanel('featured_image'),
    ]

    def save(self, *args, **kwargs):
        # Auto-generate reading time based on content
        if self.body:
            word_count = 0
            for block in self.body:
                if block.block_type == 'paragraph':
                    word_count += len(block.value.source.split())
                elif block.block_type == 'heading':
                    word_count += len(str(block.value).split())
            # Average reading speed: 200 words per minute
            self.reading_time = max(1, word_count // 200)
        
        super().save(*args, **kwargs)

    def get_context(self, request):
        context = super().get_context(request)
        
        # Add related posts
        context['related_posts'] = BlogPage.objects.live().public().exclude(
            id=self.id
        ).filter(
            categories__in=self.categories.all()
        ).distinct().order_by('-first_published_at')[:3]
        
        return context
    
    # Parent page/subpage rules
    parent_page_types = ['blog.BlogIndexPage']


class TutorialPage(Page):
    """
    Tutorial page for step-by-step programming guides.
    """
    template = 'blog/tutorial_page.html'
    
    # Author and meta
    author = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tutorials'
    )
    
    # Tutorial info
    difficulty_level = models.CharField(
        max_length=20,
        choices=[
            ('beginner', 'Beginner'),
            ('intermediate', 'Intermediate'),
            ('advanced', 'Advanced'),
        ],
        default='beginner'
    )
    
    programming_language = models.CharField(
        max_length=50,
        choices=[
            ('python', 'Python'),
            ('javascript', 'JavaScript'),
            ('html', 'HTML/CSS'),
            ('sql', 'SQL'),
            ('other', 'Other'),
        ],
        default='python'
    )
    
    estimated_time = models.CharField(
        max_length=50,
        help_text="e.g., '30 minutes', '2 hours'"
    )
    
    prerequisites = RichTextField(
        blank=True,
        help_text="What students should know before starting"
    )
    
    learning_objectives = StreamField([
        ('objective', blocks.CharBlock()),
    ], blank=True, use_json_field=True)
    
    # Content
    intro = RichTextField()
    content = StreamField([
        ('step', blocks.StructBlock([
            ('title', blocks.CharBlock()),
            ('description', blocks.RichTextBlock()),
            ('code', blocks.TextBlock(required=False)),
            ('code_language', blocks.ChoiceBlock(
                choices=[
                    ('python', 'Python'),
                    ('javascript', 'JavaScript'),
                    ('html', 'HTML'),
                    ('css', 'CSS'),
                    ('sql', 'SQL'),
                    ('bash', 'Bash'),
                ],
                required=False
            )),
            ('image', ImageChooserBlock(required=False)),
            ('tip', blocks.RichTextBlock(required=False, label='Pro Tip')),
        ])),
        ('section_break', blocks.StructBlock([
            ('title', blocks.CharBlock()),
            ('description', blocks.RichTextBlock(required=False)),
        ])),
    ], use_json_field=True)
    
    # Categories and tags (reuse from blog)
    categories = ParentalManyToManyField('blog.BlogCategory', blank=True)
    tags = ClusterTaggableManager(through=BlogPageTag, blank=True)
    
    # Featured image
    featured_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )

    search_fields = Page.search_fields + [
        index.SearchField('intro'),
        index.SearchField('content'),
        index.SearchField('programming_language'),
        index.SearchField('difficulty_level'),
    ]

    content_panels = Page.content_panels + [
        MultiFieldPanel([
            FieldPanel('author'),
            FieldPanel('difficulty_level'),
            FieldPanel('programming_language'),
            FieldPanel('estimated_time'),
        ], heading="Tutorial Information"),
        FieldPanel('prerequisites'),
        FieldPanel('learning_objectives'),
        FieldPanel('intro'),
        FieldPanel('content'),
        MultiFieldPanel([
            FieldPanel('categories', widget=forms.CheckboxSelectMultiple),
            FieldPanel('tags'),
            FieldPanel('featured_image'),
        ], heading="Classification"),
    ]

    # Parent page rules
    parent_page_types = ['blog.BlogIndexPage', 'HomePage']


# ============================================================================
# LEARNING CONTENT WAGTAIL PAGES (alongside existing Django models)
# ============================================================================

@register_snippet
class SkillLevel(models.Model):
    """
    Skill levels for courses and lessons.
    """
    name = models.CharField(max_length=50)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)
    color = models.CharField(max_length=7, default="#3498db", help_text="Hex color code")
    
    panels = [
        FieldPanel('name'),
        FieldPanel('slug'),
        FieldPanel('description'),
        FieldPanel('order'),
        FieldPanel('color'),
    ]
    
    class Meta:
        ordering = ['order', 'name']
        verbose_name_plural = 'Skill Levels'
    
    def __str__(self):
        return self.name


@register_snippet
class LearningObjective(models.Model):
    """
    Learning objectives that can be reused across courses and lessons.
    """
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.CharField(
        max_length=50,
        choices=[
            ('fundamental', 'Fundamental Concept'),
            ('practical', 'Practical Skill'),
            ('advanced', 'Advanced Topic'),
            ('project', 'Project-Based'),
        ],
        default='fundamental'
    )
    
    panels = [
        FieldPanel('title'),
        FieldPanel('description'),
        FieldPanel('category'),
    ]
    
    class Meta:
        ordering = ['category', 'title']
    
    def __str__(self):
        return self.title


class LearningIndexPage(Page):
    """
    Index page for learning content - courses, paths, tutorials.
    """
    template = 'blog/learning_index_page.html'
    
    intro = RichTextField(blank=True)
    featured_courses_title = models.CharField(
        max_length=100,
        default="Featured Courses"
    )
    
    content_panels = Page.content_panels + [
        FieldPanel('intro'),
        FieldPanel('featured_courses_title'),
    ]
    
    # Only allow one learning index page
    max_count = 1
    
    def get_context(self, request):
        context = super().get_context(request)
        
        # Get featured courses
        context['featured_courses'] = CoursePage.objects.live().public().filter(
            featured=True
        ).order_by('-first_published_at')[:6]
        
        # Get all courses grouped by skill level
        context['skill_levels'] = SkillLevel.objects.all()
        
        return context


class CoursePage(Page):
    """
    Individual course page with SEO optimization and structured content.
    Complements the existing Course Django model.
    """
    template = 'blog/course_page.html'
    
    # Course metadata
    course_code = models.CharField(
        max_length=20,
        unique=True,
        help_text="Unique identifier for this course (e.g., PY101)"
    )
    instructor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='wagtail_courses'
    )
    skill_level = models.ForeignKey(
        SkillLevel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    # Course content
    short_description = models.CharField(
        max_length=300,
        help_text="Brief course description for listings"
    )
    detailed_description = RichTextField(
        help_text="Comprehensive course description"
    )
    
    # Course structure
    prerequisites = RichTextField(
        blank=True,
        help_text="What students should know before taking this course"
    )
    learning_objectives = ParentalManyToManyField(
        LearningObjective,
        blank=True,
        help_text="What students will learn"
    )
    
    # Course details
    estimated_duration = models.CharField(
        max_length=50,
        blank=True,
        help_text="e.g., '6 weeks', '20 hours'"
    )
    difficulty_level = models.CharField(
        max_length=20,
        choices=[
            ('beginner', 'Beginner'),
            ('intermediate', 'Intermediate'),
            ('advanced', 'Advanced'),
        ],
        default='beginner'
    )
    
    # Visual content
    course_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        help_text="Main course image for SEO and display"
    )
    
    # Course syllabus
    syllabus = StreamField([
        ('module', blocks.StructBlock([
            ('title', blocks.CharBlock(max_length=200)),
            ('description', blocks.RichTextBlock()),
            ('lessons', blocks.ListBlock(blocks.StructBlock([
                ('lesson_title', blocks.CharBlock(max_length=200)),
                ('lesson_description', blocks.TextBlock()),
                ('estimated_time', blocks.CharBlock(max_length=50, required=False)),
            ]))),
        ])),
    ], blank=True, use_json_field=True)
    
    # Course features and highlights
    features = StreamField([
        ('feature', blocks.StructBlock([
            ('icon', blocks.CharBlock(max_length=50, help_text="Icon class")),
            ('title', blocks.CharBlock(max_length=100)),
            ('description', blocks.TextBlock()),
        ])),
    ], blank=True, use_json_field=True)
    
    # Pricing and enrollment
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Course price (leave blank for free)"
    )
    is_free = models.BooleanField(
        default=True,
        help_text="Is this course free?"
    )
    enrollment_limit = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Maximum number of students (leave blank for unlimited)"
    )
    
    # Course status and visibility
    featured = models.BooleanField(
        default=False,
        help_text="Show on homepage and featured listings"
    )
    
    # Tags and categories (reuse from blog)
    categories = ParentalManyToManyField('blog.BlogCategory', blank=True)
    tags = ClusterTaggableManager(through=BlogPageTag, blank=True)

    search_fields = Page.search_fields + [
        index.SearchField('short_description'),
        index.SearchField('detailed_description'),
        index.SearchField('course_code'),
        index.SearchField('tags'),
    ]

    content_panels = Page.content_panels + [
        MultiFieldPanel([
            FieldPanel('course_code'),
            FieldPanel('instructor'),
            FieldPanel('skill_level'),
            FieldPanel('difficulty_level'),
        ], heading="Course Information"),
        FieldPanel('short_description'),
        FieldPanel('detailed_description'),
        FieldPanel('prerequisites'),
        FieldPanel('learning_objectives', widget=forms.CheckboxSelectMultiple),
        MultiFieldPanel([
            FieldPanel('estimated_duration'),
            FieldPanel('price'),
            FieldPanel('is_free'),
            FieldPanel('enrollment_limit'),
        ], heading="Course Details"),
        FieldPanel('course_image'),
        FieldPanel('syllabus'),
        FieldPanel('features'),
        MultiFieldPanel([
            FieldPanel('categories', widget=forms.CheckboxSelectMultiple),
            FieldPanel('tags'),
            FieldPanel('featured'),
        ], heading="Classification"),
    ]

    promote_panels = Page.promote_panels + [
        FieldPanel('course_image'),
    ]

    # Parent page rules
    parent_page_types = ['blog.LearningIndexPage']
    subpage_types = ['blog.LessonPage']

    def get_context(self, request):
        context = super().get_context(request)
        
        # Add course lessons
        context['lessons'] = self.get_children().live().public().order_by('path')
        
        # Add related courses
        context['related_courses'] = CoursePage.objects.live().public().exclude(
            id=self.id
        ).filter(
            skill_level=self.skill_level
        ).order_by('-first_published_at')[:3]
        
        return context

    def save(self, *args, **kwargs):
        # Auto-generate search description from short description if not provided
        # Note: Using Wagtail's built-in search_description field
        if not self.search_description and self.short_description:
            self.search_description = self.short_description[:300]
        
        super().save(*args, **kwargs)


class LessonPage(Page):
    """
    Individual lesson page with interactive content and exercises.
    Complements the existing Lesson Django model.
    """
    template = 'blog/lesson_page.html'
    
    # Lesson metadata
    lesson_number = models.PositiveIntegerField(
        help_text="Order within the course"
    )
    estimated_duration = models.CharField(
        max_length=50,
        blank=True,
        help_text="e.g., '30 minutes', '1 hour'"
    )
    
    # Lesson content
    intro = RichTextField(
        help_text="Brief introduction to the lesson"
    )
    
    content = StreamField([
        ('text', blocks.RichTextBlock()),
        ('heading', blocks.CharBlock(form_classname="title")),
        ('code_example', blocks.StructBlock([
            ('title', blocks.CharBlock(required=False)),
            ('language', blocks.ChoiceBlock(choices=[
                ('python', 'Python'),
                ('javascript', 'JavaScript'),
                ('html', 'HTML'),
                ('css', 'CSS'),
                ('sql', 'SQL'),
                ('bash', 'Bash'),
            ])),
            ('code', blocks.TextBlock()),
            ('explanation', blocks.RichTextBlock(required=False)),
        ])),
        ('interactive_exercise', blocks.StructBlock([
            ('title', blocks.CharBlock()),
            ('instructions', blocks.RichTextBlock()),
            ('starter_code', blocks.TextBlock(required=False)),
            ('solution', blocks.TextBlock(required=False)),
            ('hints', blocks.ListBlock(blocks.TextBlock(), required=False)),
        ])),
        ('video', blocks.StructBlock([
            ('title', blocks.CharBlock(required=False)),
            ('video_url', blocks.URLBlock()),
            ('description', blocks.RichTextBlock(required=False)),
        ])),
        ('callout', blocks.StructBlock([
            ('type', blocks.ChoiceBlock(choices=[
                ('info', 'Info'),
                ('warning', 'Warning'),
                ('tip', 'Tip'),
                ('danger', 'Danger'),
            ])),
            ('title', blocks.CharBlock(required=False)),
            ('text', blocks.RichTextBlock()),
        ])),
        ('quiz', blocks.StructBlock([
            ('question', blocks.CharBlock()),
            ('options', blocks.ListBlock(blocks.CharBlock())),
            ('correct_answer', blocks.IntegerBlock(help_text="Index of correct option (0-based)")),
            ('explanation', blocks.RichTextBlock(required=False)),
        ])),
    ], use_json_field=True)
    
    # Learning objectives for this specific lesson
    lesson_objectives = StreamField([
        ('objective', blocks.CharBlock()),
    ], blank=True, use_json_field=True)
    
    # Prerequisites for this lesson
    lesson_prerequisites = RichTextField(
        blank=True,
        help_text="What students should know before this lesson"
    )
    
    # Additional resources
    resources = StreamField([
        ('resource', blocks.StructBlock([
            ('title', blocks.CharBlock()),
            ('url', blocks.URLBlock()),
            ('description', blocks.TextBlock(required=False)),
            ('type', blocks.ChoiceBlock(choices=[
                ('documentation', 'Documentation'),
                ('tutorial', 'Tutorial'),
                ('video', 'Video'),
                ('article', 'Article'),
                ('tool', 'Tool/Software'),
            ])),
        ])),
    ], blank=True, use_json_field=True)

    search_fields = Page.search_fields + [
        index.SearchField('intro'),
        index.SearchField('content'),
        index.SearchField('lesson_objectives'),
    ]

    content_panels = Page.content_panels + [
        MultiFieldPanel([
            FieldPanel('lesson_number'),
            FieldPanel('estimated_duration'),
        ], heading="Lesson Information"),
        FieldPanel('intro'),
        FieldPanel('lesson_objectives'),
        FieldPanel('lesson_prerequisites'),
        FieldPanel('content'),
        FieldPanel('resources'),
    ]

    # Parent page rules
    parent_page_types = ['blog.CoursePage']
    subpage_types = ['blog.ExercisePage']

    class Meta:
        ordering = ['lesson_number']

    def get_context(self, request):
        context = super().get_context(request)
        
        # Add navigation to previous/next lessons
        course = self.get_parent().specific
        lessons = course.get_children().live().public().order_by('lessonpage__lesson_number')
        
        lesson_list = list(lessons)
        current_index = next((i for i, lesson in enumerate(lesson_list) if lesson.id == self.id), None)
        
        if current_index is not None:
            if current_index > 0:
                context['previous_lesson'] = lesson_list[current_index - 1]
            if current_index < len(lesson_list) - 1:
                context['next_lesson'] = lesson_list[current_index + 1]
        
        context['course'] = course
        context['lesson_exercises'] = self.get_children().live().public()
        
        return context


class ExercisePage(Page):
    """
    Interactive coding exercise page with validation and hints.
    Complements the existing Exercise Django model.
    """
    template = 'blog/exercise_page.html'
    
    # Exercise metadata
    exercise_type = models.CharField(
        max_length=50,
        choices=[
            ('coding', 'Coding Exercise'),
            ('multiple_choice', 'Multiple Choice'),
            ('fill_blank', 'Fill in the Blanks'),
            ('project', 'Project Exercise'),
            ('quiz', 'Quiz'),
        ],
        default='coding'
    )
    
    difficulty = models.CharField(
        max_length=20,
        choices=[
            ('easy', 'Easy'),
            ('medium', 'Medium'),
            ('hard', 'Hard'),
        ],
        default='medium'
    )
    
    points = models.PositiveIntegerField(
        default=10,
        help_text="Points awarded for completing this exercise"
    )
    
    # Exercise content
    description = RichTextField(
        help_text="Clear explanation of what the student needs to do"
    )
    
    # For coding exercises
    starter_code = models.TextField(
        blank=True,
        help_text="Initial code provided to students"
    )
    
    solution_code = models.TextField(
        blank=True,
        help_text="Complete solution (hidden from students)"
    )
    
    programming_language = models.CharField(
        max_length=50,
        choices=[
            ('python', 'Python'),
            ('javascript', 'JavaScript'),
            ('html', 'HTML'),
            ('css', 'CSS'),
            ('sql', 'SQL'),
        ],
        default='python'
    )
    
    # Test cases and validation
    test_cases = StreamField([
        ('test_case', blocks.StructBlock([
            ('input', blocks.TextBlock(help_text="Input for the test")),
            ('expected_output', blocks.TextBlock(help_text="Expected output")),
            ('description', blocks.CharBlock(help_text="Description of what this tests")),
            ('is_hidden', blocks.BooleanBlock(
                default=False,
                help_text="Hide from students (for final validation)"
            )),
        ])),
    ], blank=True, use_json_field=True)
    
    # Hints and guidance
    hints = StreamField([
        ('hint', blocks.StructBlock([
            ('hint_text', blocks.RichTextBlock()),
            ('reveal_after_attempts', blocks.IntegerBlock(
                default=3,
                help_text="Show hint after this many attempts"
            )),
        ])),
    ], blank=True, use_json_field=True)
    
    # For non-coding exercises
    question_data = models.JSONField(
        blank=True,
        null=True,
        help_text="Structured data for quizzes, multiple choice, etc."
    )
    
    # Exercise constraints
    time_limit = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Time limit in minutes (leave blank for no limit)"
    )
    
    max_attempts = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Maximum attempts allowed (leave blank for unlimited)"
    )

    search_fields = Page.search_fields + [
        index.SearchField('description'),
        index.SearchField('exercise_type'),
        index.SearchField('programming_language'),
    ]

    content_panels = Page.content_panels + [
        MultiFieldPanel([
            FieldPanel('exercise_type'),
            FieldPanel('difficulty'),
            FieldPanel('points'),
            FieldPanel('programming_language'),
        ], heading="Exercise Information"),
        FieldPanel('description'),
        MultiFieldPanel([
            FieldPanel('starter_code'),
            FieldPanel('solution_code'),
        ], heading="Code Content"),
        FieldPanel('test_cases'),
        FieldPanel('hints'),
        MultiFieldPanel([
            FieldPanel('question_data'),
        ], heading="Non-Coding Exercise Data"),
        MultiFieldPanel([
            FieldPanel('time_limit'),
            FieldPanel('max_attempts'),
        ], heading="Exercise Constraints"),
    ]

    # Parent page rules
    parent_page_types = ['blog.LessonPage']

    def get_context(self, request):
        context = super().get_context(request)
        
        # Add lesson and course context
        lesson = self.get_parent().specific
        course = lesson.get_parent().specific
        
        context['lesson'] = lesson
        context['course'] = course
        
        return context

    def clean(self):
        super().clean()
        
        # Validate that coding exercises have required fields
        if self.exercise_type == 'coding':
            if not self.programming_language:
                raise ValidationError('Programming language is required for coding exercises')
            if not self.starter_code and not self.solution_code:
                raise ValidationError('Either starter code or solution code is required for coding exercises')


class CodePlaygroundPage(Page):
    """
    Interactive code playground page for experimenting with different programming languages.
    """
    template = 'blog/code_playground_page.html'
    
    # Playground configuration
    description = RichTextField(
        blank=True,
        help_text="Description of the playground and its features"
    )
    
    # Default content and examples
    default_code = models.TextField(
        blank=True,
        help_text="Default code to show when the playground loads"
    )
    
    programming_language = models.CharField(
        max_length=50,
        choices=[
            ('python', 'Python'),
            ('javascript', 'JavaScript'),
            ('html', 'HTML'),
            ('css', 'CSS'),
            ('sql', 'SQL'),
        ],
        default='python',
        help_text="Default programming language for the playground"
    )
    
    # Features configuration
    features = StreamField([
        ('feature', blocks.StructBlock([
            ('title', blocks.CharBlock(max_length=100)),
            ('description', blocks.TextBlock()),
            ('icon', blocks.CharBlock(max_length=50, help_text="Icon class")),
        ])),
    ], blank=True, use_json_field=True)
    
    # Code examples
    code_examples = StreamField([
        ('example', blocks.StructBlock([
            ('title', blocks.CharBlock(max_length=200)),
            ('description', blocks.TextBlock()),
            ('language', blocks.ChoiceBlock(choices=[
                ('python', 'Python'),
                ('javascript', 'JavaScript'),
                ('html', 'HTML'),
                ('css', 'CSS'),
                ('sql', 'SQL'),
            ])),
            ('code', blocks.TextBlock()),
            ('category', blocks.ChoiceBlock(choices=[
                ('basic', 'Basic'),
                ('intermediate', 'Intermediate'),
                ('advanced', 'Advanced'),
            ], default='basic')),
        ])),
    ], blank=True, use_json_field=True)
    
    # Keyboard shortcuts info
    shortcuts = StreamField([
        ('shortcut', blocks.StructBlock([
            ('keys', blocks.CharBlock(max_length=50, help_text="e.g., Ctrl+S")),
            ('description', blocks.CharBlock(max_length=100)),
        ])),
    ], blank=True, use_json_field=True)
    
    # Enable features flags
    enable_file_operations = models.BooleanField(
        default=True,
        help_text="Allow save/load functionality"
    )
    enable_auto_save = models.BooleanField(
        default=True,
        help_text="Enable automatic saving of code"
    )
    enable_multiple_languages = models.BooleanField(
        default=True,
        help_text="Allow switching between programming languages"
    )

    search_fields = Page.search_fields + [
        index.SearchField('description'),
        index.SearchField('code_examples'),
        index.SearchField('programming_language'),
    ]

    content_panels = Page.content_panels + [
        FieldPanel('description'),
        MultiFieldPanel([
            FieldPanel('programming_language'),
            FieldPanel('default_code'),
        ], heading="Default Configuration"),
        FieldPanel('features'),
        FieldPanel('code_examples'),
        FieldPanel('shortcuts'),
        MultiFieldPanel([
            FieldPanel('enable_file_operations'),
            FieldPanel('enable_auto_save'),
            FieldPanel('enable_multiple_languages'),
        ], heading="Feature Settings"),
    ]

    # Parent page rules
    parent_page_types = ['blog.HomePage', 'blog.LearningIndexPage']
    
    # Only allow one playground page
    max_count = 1

    def get_context(self, request):
        context = super().get_context(request)
        
        # Set default values if not configured
        if not self.default_code:
            context['initial_code'] = '''# Welcome to Python Learning Studio Playground!
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
'''
        else:
            context['initial_code'] = self.default_code
        
        # Add default features if not configured
        if not self.features:
            context['default_features'] = [
                {
                    'title': 'Real-time Code Execution',
                    'description': 'Run your code instantly and see results',
                    'icon': 'play-circle'
                },
                {
                    'title': 'Syntax Highlighting',
                    'description': 'Beautiful code highlighting for better readability',
                    'icon': 'code'
                },
                {
                    'title': 'Auto-save Functionality',
                    'description': 'Your code is automatically saved as you type',
                    'icon': 'save'
                },
                {
                    'title': 'Multiple Languages',
                    'description': 'Support for Python, JavaScript, HTML, CSS, and more',
                    'icon': 'layers'
                }
            ]
        
        # Add default shortcuts if not configured
        if not self.shortcuts:
            context['default_shortcuts'] = [
                {'keys': 'Ctrl+S', 'description': 'Save code'},
                {'keys': 'Ctrl+Enter', 'description': 'Run code'},
                {'keys': 'Tab', 'description': 'Indent'},
                {'keys': 'Shift+Tab', 'description': 'Unindent'}
            ]
        
        return context


