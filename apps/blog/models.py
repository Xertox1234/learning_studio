"""
Wagtail page models for Python Learning Studio blog and learning content.
"""

from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django import forms
import json
import logging

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

# Import machina models for forum integration
try:
    from machina.apps.forum.models import Forum
except ImportError:
    Forum = None

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
        ('runnable_code_example', blocks.StructBlock([
            ('title', blocks.CharBlock(required=False, help_text="Optional title for the code example")),
            ('language', blocks.ChoiceBlock(choices=[
                ('python', 'Python'),
                ('javascript', 'JavaScript'),
                ('html', 'HTML'),
                ('css', 'CSS'),
                ('java', 'Java'),
                ('cpp', 'C++'),
            ], default='python')),
            ('code', blocks.TextBlock(help_text="Code to display and run")),
            ('mock_output', blocks.TextBlock(required=False, help_text="Expected output when code is run")),
            ('ai_explanation', blocks.TextBlock(required=False, help_text="AI explanation of the code")),
        ], icon='code', help_text="Interactive code example with Run button")),
        ('fill_blank_code', blocks.StructBlock([
            ('title', blocks.CharBlock(required=False, help_text="Optional title for the exercise")),
            ('language', blocks.ChoiceBlock(choices=[
                ('python', 'Python'),
                ('javascript', 'JavaScript'),
                ('html', 'HTML'),
                ('css', 'CSS'),
                ('java', 'Java'),
                ('cpp', 'C++'),
            ], default='python')),
            ('template', blocks.TextBlock(help_text="Code template with {{BLANK_1}}, {{BLANK_2}} etc. placeholders")),
            ('solutions', blocks.TextBlock(help_text="JSON object with solutions: {\"1\": \"answer1\", \"2\": \"answer2\"}")),
            ('alternative_solutions', blocks.TextBlock(required=False, help_text="JSON object with alternative answers: {\"1\": [\"alt1\", \"alt2\"]}")),
            ('ai_hints', blocks.TextBlock(required=False, help_text="JSON object with hints: {\"1\": \"hint for blank 1\"}")),
        ], icon='form', help_text="Fill-in-the-blank coding exercise")),
        ('multiple_choice_code', blocks.StructBlock([
            ('title', blocks.CharBlock(required=False, help_text="Optional title for the exercise")),
            ('language', blocks.ChoiceBlock(choices=[
                ('python', 'Python'),
                ('javascript', 'JavaScript'),
                ('html', 'HTML'),
                ('css', 'CSS'),
                ('java', 'Java'),
                ('cpp', 'C++'),
            ], default='python')),
            ('template', blocks.TextBlock(help_text="Code template with {{CHOICE_1}}, {{CHOICE_2}} etc. placeholders")),
            ('choices', blocks.TextBlock(help_text="JSON object with choices: {\"1\": [\"option1\", \"option2\"], \"2\": [\"optionA\", \"optionB\"]}")),
            ('solutions', blocks.TextBlock(help_text="JSON object with correct answers: {\"1\": \"option1\", \"2\": \"optionA\"}")),
            ('ai_explanations', blocks.TextBlock(required=False, help_text="JSON object with explanations: {\"1\": \"explanation for choice 1\"}")),
        ], icon='list-ol', help_text="Multiple choice coding exercise with dropdowns")),
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
    Enhanced for headless CMS with fill-in-blank templates and progressive hints.
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
    
    # Layout configuration
    layout_type = models.CharField(
        max_length=20,
        choices=[
            ('standard', 'Standard Layout'),
            ('fullscreen', 'Fullscreen Editor'),
            ('split', 'Split View'),
            ('step_by_step', 'Step by Step'),
        ],
        default='standard',
        help_text="Choose how the exercise should be displayed"
    )
    
    show_sidebar = models.BooleanField(
        default=True,
        help_text="Show instructions sidebar"
    )
    
    code_editor_height = models.CharField(
        max_length=20,
        default='400px',
        help_text="Height of the code editor (e.g., 400px, 60vh)"
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
    
    # Fill-in-blank template system
    template_code = models.TextField(
        blank=True,
        help_text="Code template with {{BLANK_N}} placeholders for fill-in-blank exercises"
    )
    
    solutions = models.JSONField(
        default=dict,
        blank=True,
        help_text='{"1": "answer1", "2": "answer2"} - Solutions for each blank'
    )
    
    alternative_solutions = models.JSONField(
        default=dict,
        blank=True,
        help_text='{"1": ["answer1", "alt1"], "2": ["answer2", "alt2"]} - Alternative correct answers'
    )
    
    # Progressive hints system
    progressive_hints = models.JSONField(
        default=list,
        blank=True,
        help_text="""[
            {"level": 1, "type": "conceptual", "title": "Think About It", 
             "content": "Hint text", "triggerTime": 30, "triggerAttempts": 0}
        ] - Time and attempt-based hints"""
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
    
    # Exercise content blocks
    exercise_content = StreamField([
        ('instruction', blocks.RichTextBlock(
            help_text="Detailed instructions for the exercise"
        )),
        ('code_example', blocks.StructBlock([
            ('title', blocks.CharBlock(required=False)),
            ('language', blocks.ChoiceBlock(choices=[
                ('python', 'Python'),
                ('javascript', 'JavaScript'),
                ('html', 'HTML'),
                ('css', 'CSS'),
            ])),
            ('code', blocks.TextBlock()),
            ('explanation', blocks.RichTextBlock(required=False)),
        ])),
        ('hint_block', blocks.StructBlock([
            ('hint_type', blocks.ChoiceBlock(choices=[
                ('general', 'General Hint'),
                ('syntax', 'Syntax Hint'),
                ('logic', 'Logic Hint'),
            ])),
            ('content', blocks.RichTextBlock()),
        ])),
    ], blank=True, use_json_field=True)
    
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
        MultiFieldPanel([
            FieldPanel('layout_type'),
            FieldPanel('show_sidebar'),
            FieldPanel('code_editor_height'),
        ], heading="Layout Configuration"),
        FieldPanel('description'),
        MultiFieldPanel([
            FieldPanel('starter_code'),
            FieldPanel('solution_code'),
            FieldPanel('template_code'),
            FieldPanel('solutions'),
            FieldPanel('alternative_solutions'),
        ], heading="Code Content"),
        FieldPanel('exercise_content'),
        FieldPanel('test_cases'),
        FieldPanel('hints'),
        FieldPanel('progressive_hints'),
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


class StepBasedExercisePage(Page):
    """
    Multi-step exercise page for progressive learning experiences.
    Each step can be a different exercise type with its own validation.
    """
    template = 'blog/step_based_exercise_page.html'
    
    # Overall exercise configuration
    require_sequential = models.BooleanField(
        default=True,
        help_text="Must complete steps in order"
    )
    
    total_points = models.PositiveIntegerField(
        default=100,
        help_text="Total points for completing all steps"
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
    
    estimated_time = models.PositiveIntegerField(
        default=30,
        help_text="Estimated time to complete in minutes"
    )
    
    # Exercise steps
    exercise_steps = StreamField([
        ('exercise_step', blocks.StructBlock([
            ('step_number', blocks.IntegerBlock(
                help_text="Step order number"
            )),
            ('title', blocks.CharBlock(
                help_text="Step title"
            )),
            ('description', blocks.RichTextBlock(
                help_text="Step instructions and context"
            )),
            ('exercise_type', blocks.ChoiceBlock(choices=[
                ('code', 'Code Editor'),
                ('fill_blank', 'Fill in the Blanks'),
                ('multiple_choice', 'Multiple Choice'),
                ('quiz', 'Quiz'),
            ])),
            ('template', blocks.TextBlock(
                required=False,
                help_text="Code template with {{BLANK_N}} for fill-in-blank"
            )),
            ('solutions', blocks.TextBlock(
                required=False,
                help_text='JSON solutions: {"1": "answer1", "2": "answer2"}'
            )),
            ('points', blocks.IntegerBlock(
                default=10,
                help_text="Points for this step"
            )),
            ('success_message', blocks.TextBlock(
                default="Great job! You've completed this step.",
                help_text="Message shown on step completion"
            )),
            ('hint', blocks.TextBlock(
                required=False,
                help_text="Optional hint for this step"
            )),
        ])),
    ], use_json_field=True)
    
    # Overall hints and guidance
    general_hints = StreamField([
        ('hint', blocks.StructBlock([
            ('hint_text', blocks.RichTextBlock()),
            ('show_after_step', blocks.IntegerBlock(
                default=1,
                help_text="Show this hint after completing step N"
            )),
        ])),
    ], blank=True, use_json_field=True)
    
    # Completion configuration
    completion_message = RichTextField(
        default="Congratulations! You've completed all steps.",
        help_text="Message shown when all steps are completed"
    )
    
    show_completion_certificate = models.BooleanField(
        default=False,
        help_text="Show a completion certificate"
    )
    
    search_fields = Page.search_fields + [
        index.SearchField('exercise_steps'),
    ]
    
    content_panels = Page.content_panels + [
        MultiFieldPanel([
            FieldPanel('difficulty'),
            FieldPanel('total_points'),
            FieldPanel('estimated_time'),
            FieldPanel('require_sequential'),
        ], heading="Exercise Configuration"),
        FieldPanel('exercise_steps'),
        FieldPanel('general_hints'),
        MultiFieldPanel([
            FieldPanel('completion_message'),
            FieldPanel('show_completion_certificate'),
        ], heading="Completion Settings"),
    ]
    
    # Parent page rules
    parent_page_types = ['blog.LessonPage', 'blog.CoursePage']
    
    def get_context(self, request):
        context = super().get_context(request)
        
        # Add parent context
        parent = self.get_parent().specific
        if hasattr(parent, 'get_parent'):
            course = parent.get_parent().specific if parent.__class__.__name__ == 'LessonPage' else parent
            context['course'] = course
            if parent.__class__.__name__ == 'LessonPage':
                context['lesson'] = parent
        
        return context


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


# ============================================================================
# WAGTAIL COURSE ENROLLMENT MODEL
# ============================================================================

class WagtailCourseEnrollment(models.Model):
    """
    User enrollment in Wagtail courses.
    """
    user = models.ForeignKey(
        'users.User', 
        on_delete=models.CASCADE, 
        related_name='wagtail_enrollments'
    )
    course = models.ForeignKey(
        CoursePage, 
        on_delete=models.CASCADE, 
        related_name='enrollments'
    )
    
    # Enrollment status
    enrolled_at = models.DateTimeField(auto_now_add=True)
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Progress tracking
    progress_percentage = models.PositiveIntegerField(
        default=0, 
        validators=[MaxValueValidator(100)]
    )
    last_accessed_lesson = models.ForeignKey(
        LessonPage,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='last_accessed_by'
    )
    last_activity = models.DateTimeField(auto_now=True)
    
    # Completion tracking
    total_time_spent = models.PositiveIntegerField(
        default=0, 
        help_text="Total time in minutes"
    )
    
    class Meta:
        unique_together = ['user', 'course']
        ordering = ['-enrolled_at']
        verbose_name = 'Wagtail Course Enrollment'
        verbose_name_plural = 'Wagtail Course Enrollments'
    
    def __str__(self):
        return f"{self.user.username} enrolled in {self.course.title}"
    
    def calculate_progress(self):
        """Calculate progress based on completed lessons."""
        total_lessons = self.course.get_children().live().count()
        if total_lessons == 0:
            return 0
        
        # This would need to be implemented with lesson completion tracking
        # For now, return the stored progress
        return self.progress_percentage
    
    def mark_completed(self):
        """Mark the enrollment as completed."""
        if not self.completed:
            self.completed = True
            self.completed_at = timezone.now()
            self.progress_percentage = 100
            self.save()


logger = logging.getLogger(__name__)


class ForumIntegratedBlogPage(BlogPage):
    """
    Blog page that integrates with forum discussions.
    Extends BlogPage to automatically create forum topics for community discussion.
    """
    
    # Forum integration fields
    create_forum_topic = models.BooleanField(
        default=True,
        help_text="Automatically create a forum topic for this post"
    )
    
    forum_topic_id = models.IntegerField(
        null=True,
        blank=True,
        help_text="ID of the associated forum topic"
    )
    
    discussion_forum = models.ForeignKey(
        Forum,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Forum where the discussion topic will be created"
    )
    
    forum_topic_title = models.CharField(
        max_length=255,
        blank=True,
        help_text="Custom title for forum topic (defaults to blog post title)"
    )
    
    forum_discussion_intro = models.TextField(
        blank=True,
        help_text="Introduction text for the forum discussion (optional)"
    )
    
    enable_rich_forum_content = models.BooleanField(
        default=True,
        help_text="Use rich content blocks in forum posts"
    )
    
    # Trust level requirements
    min_trust_level_to_post = models.IntegerField(
        default=0,
        choices=[
            (0, 'TL0 - New Users'),
            (1, 'TL1 - Basic Users'),
            (2, 'TL2 - Members'),
            (3, 'TL3 - Regular Users'),
            (4, 'TL4 - Leaders'),
        ],
        help_text="Minimum trust level required to participate in discussion"
    )
    
    content_panels = BlogPage.content_panels + [
        MultiFieldPanel([
            FieldPanel('create_forum_topic'),
            FieldPanel('discussion_forum'),
            FieldPanel('forum_topic_title'),
            FieldPanel('forum_discussion_intro'),
            FieldPanel('enable_rich_forum_content'),
            FieldPanel('min_trust_level_to_post'),
        ], heading="Forum Integration", classname="collapsible"),
    ]
    
    class Meta:
        verbose_name = "Forum-Integrated Blog Post"
        verbose_name_plural = "Forum-Integrated Blog Posts"
    
    def save(self, *args, **kwargs):
        """Override save to handle forum topic creation."""
        is_new = self.pk is None
        was_live = False
        
        if not is_new:
            # Check if page was previously live
            try:
                old_instance = ForumIntegratedBlogPage.objects.get(pk=self.pk)
                was_live = old_instance.live
            except ForumIntegratedBlogPage.DoesNotExist:
                pass
        
        # Call parent save first
        super().save(*args, **kwargs)
        
        # Create forum topic if conditions are met
        if (self.create_forum_topic and 
            self.live and 
            not self.forum_topic_id and 
            (is_new or not was_live)):
            self._create_forum_topic()
    
    def _create_forum_topic(self):
        """Create associated forum topic."""
        try:
            from machina.apps.forum.models import Forum
            from machina.apps.forum_conversation.models import Topic, Post
            
            # Use specified forum or get default discussion forum
            forum = self.discussion_forum
            if not forum:
                # Try to get a default "Blog Discussions" forum
                try:
                    forum = Forum.objects.get(name="Blog Discussions")
                except Forum.DoesNotExist:
                    # Create default forum if it doesn't exist
                    logger.warning("No discussion forum found for blog integration")
                    return
            
            # Check if forum allows posting
            if forum.type != Forum.FORUM_POST:
                logger.warning(f"Forum {forum.name} doesn't allow posting")
                return
            
            # Prepare topic title and content
            topic_title = self.forum_topic_title or f"Discussion: {self.title}"
            
            # Create forum content
            forum_content = self._generate_forum_content()
            
            # Create topic
            topic = Topic.objects.create(
                forum=forum,
                subject=topic_title,
                poster=self.author or self.owner,
                type=Topic.TOPIC_POST,
                status=Topic.TOPIC_UNLOCKED,
                approved=True,
                created=timezone.now(),
                updated=timezone.now()
            )
            
            # Create first post
            post = Post.objects.create(
                topic=topic,
                poster=self.author or self.owner,
                subject=topic_title,
                content=forum_content,
                approved=True,
                enable_signature=False,
                created=timezone.now(),
                updated=timezone.now()
            )
            
            # Update topic references
            topic.first_post = post
            topic.last_post = post
            topic.last_post_on = post.created
            topic.posts_count = 1
            topic.save()
            
            # Save the topic ID to this blog post
            self.forum_topic_id = topic.id
            ForumIntegratedBlogPage.objects.filter(pk=self.pk).update(
                forum_topic_id=topic.id
            )
            
            logger.info(f"Created forum topic {topic.id} for blog post {self.title}")
            
        except Exception as e:
            logger.error(f"Failed to create forum topic for blog post {self.title}: {e}")
    
    def _generate_forum_content(self):
        """Generate forum post content from blog content."""
        if not self.enable_rich_forum_content:
            # Simple format
            content = f"**New Blog Post: {self.title}**\n\n"
            content += f"{self.intro}\n\n"
            if self.forum_discussion_intro:
                content += f"{self.forum_discussion_intro}\n\n"
            content += f"[Read the full post]({self.full_url})\n\n"
            content += "What are your thoughts on this topic? Share your experience and ask questions below!"
            return content
        
        # Rich format with StreamField content
        content = f"**📝 New Blog Post: {self.title}**\n\n"
        content += f"*{self.intro}*\n\n"
        
        if self.forum_discussion_intro:
            content += f"{self.forum_discussion_intro}\n\n"
        
        # Add preview of blog content
        if self.body:
            content += "**Preview:**\n\n"
            preview_blocks = 0
            for block in self.body:
                if preview_blocks >= 2:  # Limit preview
                    break
                
                if block.block_type == 'paragraph':
                    # Extract plain text from rich text
                    block_text = str(block.value.source) if hasattr(block.value, 'source') else str(block.value)
                    content += f"{block_text}\n\n"
                    preview_blocks += 1
                elif block.block_type == 'heading':
                    content += f"## {block.value}\n\n"
                    preview_blocks += 1
                elif block.block_type == 'code':
                    lang = block.value.get('language', 'python')
                    code = block.value.get('code', '')
                    content += f"```{lang}\n{code}\n```\n\n"
                    preview_blocks += 1
            
            if len(self.body) > 2:
                content += "*[... continued in full post]*\n\n"
        
        content += f"[**📖 Read the Full Post**]({self.full_url})\n\n"
        content += "---\n\n"
        content += "**💬 Discussion Questions:**\n"
        content += "- What are your thoughts on this topic?\n"
        content += "- Have you encountered similar challenges?\n"
        content += "- Any questions or suggestions to share?\n\n"
        content += f"*Minimum trust level to participate: TL{self.min_trust_level_to_post}*"
        
        return content
    
    def get_forum_topic(self):
        """Get the associated forum topic."""
        if not self.forum_topic_id:
            return None
        
        try:
            from machina.apps.forum_conversation.models import Topic
            return Topic.objects.get(id=self.forum_topic_id)
        except Topic.DoesNotExist:
            return None
    
    def get_forum_url(self):
        """Get URL to the forum discussion."""
        topic = self.get_forum_topic()
        if not topic:
            return None
        
        # Generate forum topic URL
        return reverse('machina:forum_conversation:topic_detail', kwargs={
            'forum_slug': topic.forum.slug,
            'forum_pk': topic.forum.pk,
            'slug': topic.slug,
            'pk': topic.pk,
        })
    
    def get_context(self, request):
        """Add forum context to template."""
        context = super().get_context(request)
        
        # Add forum topic information
        context['forum_topic'] = self.get_forum_topic()
        context['forum_url'] = self.get_forum_url()
        
        # Add recent forum posts for this topic
        if self.forum_topic_id:
            try:
                from machina.apps.forum_conversation.models import Post
                recent_posts = Post.objects.filter(
                    topic_id=self.forum_topic_id,
                    approved=True
                ).select_related('poster').order_by('-created')[:5]
                context['recent_forum_posts'] = recent_posts
            except Exception:
                context['recent_forum_posts'] = []
        
        return context


