"""
Forms for advanced search functionality
"""
from django import forms
from django.contrib.auth import get_user_model
from machina.apps.forum.models import Forum
from apps.learning.models import Course

User = get_user_model()


class AdvancedSearchForm(forms.Form):
    """
    Advanced search form with multiple filters and options
    """
    CONTENT_TYPE_CHOICES = [
        ('all', 'All Content'),
        ('posts', 'Forum Posts'),
        ('topics', 'Forum Topics'),
        ('courses', 'Courses'),
        ('lessons', 'Lessons'),
        ('exercises', 'Exercises'),
    ]
    
    SORT_CHOICES = [
        ('relevance', 'Relevance'),
        ('date_desc', 'Newest First'),
        ('date_asc', 'Oldest First'),
        ('title', 'Title A-Z'),
    ]
    
    DATE_RANGE_CHOICES = [
        ('', 'Any Time'),
        ('today', 'Today'),
        ('week', 'Past Week'),
        ('month', 'Past Month'),
        ('year', 'Past Year'),
        ('custom', 'Custom Range'),
    ]
    
    DIFFICULTY_CHOICES = [
        ('', 'Any Difficulty'),
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]
    
    TRUST_LEVEL_CHOICES = [
        ('', 'Any Trust Level'),
        ('0', 'TL0+ (New User)'),
        ('1', 'TL1+ (Basic User)'),
        ('2', 'TL2+ (Member)'),
        ('3', 'TL3+ (Regular)'),
        ('4', 'TL4 (Leader)'),
    ]
    
    # Main search field
    query = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Enter search terms, "exact phrases", +required -excluded author:username',
            'autocomplete': 'off',
        })
    )
    
    # Content type filter
    content_types = forms.MultipleChoiceField(
        choices=CONTENT_TYPE_CHOICES[1:],  # Exclude 'all' from multiple choice
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input',
        })
    )
    
    # Author filter
    author = forms.CharField(
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Username',
        })
    )
    
    # Forum filter (for forum content)
    forum = forms.ModelChoiceField(
        queryset=Forum.objects.all(),
        required=False,
        empty_label="Any Forum",
        widget=forms.Select(attrs={
            'class': 'form-select',
        })
    )
    
    # Date range filter
    date_range = forms.ChoiceField(
        choices=DATE_RANGE_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select',
        })
    )
    
    # Custom date range
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
        })
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
        })
    )
    
    # Difficulty filter (for learning content)
    difficulty = forms.ChoiceField(
        choices=DIFFICULTY_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select',
        })
    )
    
    # Trust level filter
    min_trust_level = forms.ChoiceField(
        choices=TRUST_LEVEL_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select',
        })
    )
    
    # Additional options
    has_attachments = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
        })
    )
    
    # Sorting
    sort_by = forms.ChoiceField(
        choices=SORT_CHOICES,
        initial='relevance',
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select',
        })
    )
    
    # Results per page
    per_page = forms.IntegerField(
        min_value=10,
        max_value=100,
        initial=20,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '10',
            'max': '100',
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set default content types if none selected
        if not self.data.get('content_types'):
            self.fields['content_types'].initial = ['posts', 'topics', 'courses']
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Validate custom date range
        date_range = cleaned_data.get('date_range')
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')
        
        if date_range == 'custom':
            if not date_from or not date_to:
                raise forms.ValidationError(
                    "Both start and end dates are required for custom date range."
                )
            if date_from > date_to:
                raise forms.ValidationError(
                    "Start date must be before end date."
                )
        
        return cleaned_data
    
    def get_search_filters(self):
        """
        Convert form data to search engine filters
        """
        if not self.is_valid():
            return {}
        
        filters = {}
        
        # Author filter
        if self.cleaned_data.get('author'):
            filters['author'] = self.cleaned_data['author']
        
        # Forum filter
        if self.cleaned_data.get('forum'):
            filters['forum'] = self.cleaned_data['forum'].slug
        
        # Date range filter
        date_range = self.cleaned_data.get('date_range')
        if date_range:
            from datetime import date, timedelta
            today = date.today()
            
            if date_range == 'today':
                filters['date_after'] = today
            elif date_range == 'week':
                filters['date_after'] = today - timedelta(days=7)
            elif date_range == 'month':
                filters['date_after'] = today - timedelta(days=30)
            elif date_range == 'year':
                filters['date_after'] = today - timedelta(days=365)
            elif date_range == 'custom':
                if self.cleaned_data.get('date_from'):
                    filters['date_after'] = self.cleaned_data['date_from']
                if self.cleaned_data.get('date_to'):
                    filters['date_before'] = self.cleaned_data['date_to']
        
        # Difficulty filter
        if self.cleaned_data.get('difficulty'):
            filters['difficulty'] = self.cleaned_data['difficulty']
        
        # Trust level filter
        if self.cleaned_data.get('min_trust_level'):
            filters['min_trust_level'] = int(self.cleaned_data['min_trust_level'])
        
        # Attachments filter
        if self.cleaned_data.get('has_attachments'):
            filters['has_attachments'] = True
        
        return filters


class QuickSearchForm(forms.Form):
    """
    Simple search form for the navbar
    """
    q = forms.CharField(
        max_length=200,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search courses, forums, lessons...',
            'autocomplete': 'off',
        })
    )
    
    content_type = forms.ChoiceField(
        choices=[('all', 'All')] + AdvancedSearchForm.CONTENT_TYPE_CHOICES[1:],
        initial='all',
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select form-select-sm',
        })
    )


class SavedSearchForm(forms.Form):
    """
    Form for saving search queries
    """
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter a name for this search',
        })
    )
    
    query = forms.CharField(
        widget=forms.HiddenInput()
    )
    
    filters = forms.CharField(
        widget=forms.HiddenInput()
    )
    
    is_public = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
        }),
        help_text="Allow other users to see and use this search"
    )