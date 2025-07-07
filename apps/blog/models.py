"""
Wagtail page models for Python Learning Studio blog.
"""

from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.db import models
from django.urls import reverse
from django import forms

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


