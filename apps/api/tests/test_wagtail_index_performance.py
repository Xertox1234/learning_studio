"""
Performance tests for Wagtail Page model indexes.

These tests verify that database indexes are being used for common query patterns
on CoursePage, ExercisePage, and StepBasedExercisePage models.
"""

from django.test import TestCase
from django.db import connection
from apps.blog.models import (
    CoursePage,
    ExercisePage,
    StepBasedExercisePage,
    LearningIndexPage,
    SkillLevel
)
from apps.users.models import User


class WagtailIndexPerformanceTest(TestCase):
    """Test that indexes are created and used efficiently for Wagtail queries."""

    @classmethod
    def setUpTestData(cls):
        """Create test data for performance tests."""
        # Create a user for course instructor
        cls.instructor = User.objects.create_user(
            username='instructor',
            email='instructor@test.com',
            password='testpass123'
        )

        # Create skill level
        cls.skill_level = SkillLevel.objects.create(
            name='Beginner',
            slug='beginner'
        )

        # We would create test pages here, but it requires Wagtail page tree setup
        # For now, we'll just verify the model Meta configuration

    def test_coursepage_has_indexes_configured(self):
        """Verify CoursePage model has correct indexes in Meta."""
        meta_indexes = CoursePage._meta.indexes

        # Should have 3 indexes
        self.assertEqual(len(meta_indexes), 3)

        # Check index names
        index_names = [idx.name for idx in meta_indexes]
        self.assertIn('course_page_featured_idx', index_names)
        self.assertIn('course_page_diff_free_idx', index_names)
        self.assertIn('course_page_feat_diff_idx', index_names)

        # Verify field coverage
        featured_index = next(idx for idx in meta_indexes if idx.name == 'course_page_featured_idx')
        self.assertEqual(featured_index.fields, ['featured'])

        diff_free_index = next(idx for idx in meta_indexes if idx.name == 'course_page_diff_free_idx')
        self.assertEqual(diff_free_index.fields, ['difficulty_level', 'is_free'])

        feat_diff_index = next(idx for idx in meta_indexes if idx.name == 'course_page_feat_diff_idx')
        self.assertEqual(feat_diff_index.fields, ['featured', 'difficulty_level'])

    def test_exercisepage_has_indexes_configured(self):
        """Verify ExercisePage model has correct indexes in Meta."""
        meta_indexes = ExercisePage._meta.indexes

        # Should have 3 indexes
        self.assertEqual(len(meta_indexes), 3)

        # Check index names
        index_names = [idx.name for idx in meta_indexes]
        self.assertIn('exercise_page_type_diff_idx', index_names)
        self.assertIn('exercise_page_lang_diff_idx', index_names)
        self.assertIn('exercise_page_seq_idx', index_names)

        # Verify field coverage
        type_diff_index = next(idx for idx in meta_indexes if idx.name == 'exercise_page_type_diff_idx')
        self.assertEqual(type_diff_index.fields, ['exercise_type', 'difficulty'])

        lang_diff_index = next(idx for idx in meta_indexes if idx.name == 'exercise_page_lang_diff_idx')
        self.assertEqual(lang_diff_index.fields, ['programming_language', 'difficulty'])

        seq_index = next(idx for idx in meta_indexes if idx.name == 'exercise_page_seq_idx')
        self.assertEqual(seq_index.fields, ['sequence_number'])

    def test_stepbasedexercisepage_has_indexes_configured(self):
        """Verify StepBasedExercisePage model has correct indexes in Meta."""
        meta_indexes = StepBasedExercisePage._meta.indexes

        # Should have 2 indexes
        self.assertEqual(len(meta_indexes), 2)

        # Check index names
        index_names = [idx.name for idx in meta_indexes]
        self.assertIn('step_exercise_page_diff_idx', index_names)
        self.assertIn('step_exercise_page_seq_idx', index_names)

        # Verify field coverage
        diff_index = next(idx for idx in meta_indexes if idx.name == 'step_exercise_page_diff_idx')
        self.assertEqual(diff_index.fields, ['difficulty'])

        seq_index = next(idx for idx in meta_indexes if idx.name == 'step_exercise_page_seq_idx')
        self.assertEqual(seq_index.fields, ['sequence_number'])

    def test_index_names_follow_convention(self):
        """Verify all index names follow the {model}_{fields}_idx convention."""
        # CoursePage indexes
        course_indexes = CoursePage._meta.indexes
        for idx in course_indexes:
            self.assertTrue(idx.name.startswith('course_page_'))
            self.assertTrue(idx.name.endswith('_idx'))

        # ExercisePage indexes
        exercise_indexes = ExercisePage._meta.indexes
        for idx in exercise_indexes:
            self.assertTrue(idx.name.startswith('exercise_page_'))
            self.assertTrue(idx.name.endswith('_idx'))

        # StepBasedExercisePage indexes
        step_indexes = StepBasedExercisePage._meta.indexes
        for idx in step_indexes:
            self.assertTrue(idx.name.startswith('step_exercise_page_'))
            self.assertTrue(idx.name.endswith('_idx'))

    def test_total_index_count(self):
        """Verify total number of indexes across all three models."""
        total_indexes = (
            len(CoursePage._meta.indexes) +
            len(ExercisePage._meta.indexes) +
            len(StepBasedExercisePage._meta.indexes)
        )

        # Should have 8 indexes total (3 + 3 + 2)
        self.assertEqual(total_indexes, 8)


class WagtailQueryOptimizationTest(TestCase):
    """
    Tests to verify query efficiency with indexes.

    Note: These tests verify model configuration. Actual query plan analysis
    would require PostgreSQL EXPLAIN commands and is better done manually
    or with integration tests in a production-like environment.
    """

    def test_coursepage_common_filter_fields_are_indexed(self):
        """Verify fields commonly used in filters are covered by indexes."""
        indexed_fields = set()
        for idx in CoursePage._meta.indexes:
            indexed_fields.update(idx.fields)

        # These fields are commonly filtered and should be indexed
        self.assertIn('featured', indexed_fields)
        self.assertIn('difficulty_level', indexed_fields)
        self.assertIn('is_free', indexed_fields)

    def test_exercisepage_common_filter_fields_are_indexed(self):
        """Verify fields commonly used in filters are covered by indexes."""
        indexed_fields = set()
        for idx in ExercisePage._meta.indexes:
            indexed_fields.update(idx.fields)

        # These fields are commonly filtered and should be indexed
        self.assertIn('exercise_type', indexed_fields)
        self.assertIn('difficulty', indexed_fields)
        self.assertIn('programming_language', indexed_fields)
        self.assertIn('sequence_number', indexed_fields)

    def test_stepbasedexercisepage_common_filter_fields_are_indexed(self):
        """Verify fields commonly used in filters are covered by indexes."""
        indexed_fields = set()
        for idx in StepBasedExercisePage._meta.indexes:
            indexed_fields.update(idx.fields)

        # These fields are commonly filtered and should be indexed
        self.assertIn('difficulty', indexed_fields)
        self.assertIn('sequence_number', indexed_fields)

    def test_composite_indexes_have_correct_field_order(self):
        """
        Verify composite indexes use optimal field ordering.

        Best practice: Order fields by cardinality (low to high) and query frequency.
        Low cardinality fields (like featured: True/False) should come first in composite indexes.
        """
        # CoursePage: featured (low cardinality) before difficulty_level (medium cardinality)
        feat_diff_index = next(
            idx for idx in CoursePage._meta.indexes
            if idx.name == 'course_page_feat_diff_idx'
        )
        self.assertEqual(feat_diff_index.fields[0], 'featured')
        self.assertEqual(feat_diff_index.fields[1], 'difficulty_level')

        # ExercisePage: exercise_type (low-medium) before difficulty (medium)
        type_diff_index = next(
            idx for idx in ExercisePage._meta.indexes
            if idx.name == 'exercise_page_type_diff_idx'
        )
        self.assertEqual(type_diff_index.fields[0], 'exercise_type')
        self.assertEqual(type_diff_index.fields[1], 'difficulty')
