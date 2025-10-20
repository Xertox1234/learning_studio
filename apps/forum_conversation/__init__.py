"""
Custom forum_conversation app to override django-machina models.

This app overrides the default Post and Topic models to change CASCADE to SET_NULL
for user deletion, preserving forum content when users delete their accounts.
"""

default_app_config = 'apps.forum_conversation.apps.ForumConversationAppConfig'
