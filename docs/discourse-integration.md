# Discourse Forum Integration Guide

## Overview

Your Learning Community platform now has comprehensive forum integration capabilities with Discourse. This guide will help you set up and configure the integration.

## Features

- **Single Sign-On (SSO)**: Seamless login between your Django app and Discourse
- **Study Groups**: Collaborative learning groups with member management
- **Community Events**: Workshops, webinars, and coding competitions
- **Code Challenges**: Programming competitions with leaderboards
- **Admin Integration**: Full admin panel for managing community features

## Current Status

✅ **Models Created**: All database models for forum integration are in place
✅ **Views Implemented**: SSO authentication, study groups, events, and challenges
✅ **Templates Created**: Basic UI templates for community features
✅ **Admin Panel**: Full admin interface for managing all community features
✅ **Sample Data**: Demo data created for testing

## URLs Available

- **Community Dashboard**: `/community/`
- **Forum Redirect**: `/community/forum/`
- **SSO Endpoint**: `/community/forum/sso/`
- **Study Groups**: `/community/groups/`
- **Events**: `/community/events/`
- **Challenges**: `/community/challenges/`

## Discourse Setup Instructions

### 1. Set Up Discourse Instance

You can use:
- **Discourse Cloud**: https://www.discourse.org/pricing (easiest option)
- **Self-hosted**: https://github.com/discourse/discourse_docker
- **DigitalOcean One-Click**: Discourse app on DigitalOcean

### 2. Configure Discourse SSO

1. Go to your Discourse admin panel
2. Navigate to **Settings > Login**
3. Enable **enable sso** setting
4. Set **sso url** to: `https://your-app-url/community/forum/sso/`
5. Generate a strong **sso secret** (save this for Django settings)
6. Set **sso overrides email** to true
7. Set **sso overrides username** to true
8. Set **sso overrides name** to true

### 3. Get Discourse API Credentials

1. Go to your Discourse admin panel
2. Navigate to **API > Keys**
3. Create a new API key for your Django application
4. Note down:
   - API Key
   - API Username (usually the admin username)

### 4. Configure Django Settings

Update the `ForumIntegration` record in Django admin:

```python
# Access via: https://your-app-url/django-admin/community/forumintegration/
- forum_url: "https://your-discourse-forum.com"
- api_key: "your-discourse-api-key"
- api_username: "your-discourse-username"
- sso_secret: "your-sso-secret-key"
- general_category_id: 1  # Update with actual category IDs
- help_category_id: 2
- showcase_category_id: 3
- is_active: True
```

### 5. Test the Integration

1. Visit `https://your-app-url/community/`
2. Click "Visit Forum"
3. You should be redirected to your Discourse forum
4. Login should work seamlessly with your Django credentials

## Community Features

### Study Groups
- Create collaborative learning groups
- Member management with roles (member, moderator, admin)
- Programming language tags and difficulty levels
- Meeting schedules and timezone support

### Events
- Community workshops and webinars
- Registration management
- Event types: workshop, webinar, coding session, meetup, competition
- Capacity limits and registration deadlines

### Code Challenges
- Programming competitions
- Multiple language support
- Automatic scoring and leaderboards
- Time and memory limits
- Sample input/output

## Admin Features

Access the admin panel at:
- **Django Admin**: `https://your-app-url/django-admin/`
- **Community Models**: All community features are fully manageable

### Key Admin Sections:
1. **Forum Integration**: Configure Discourse connection
2. **Study Groups**: Manage groups and memberships
3. **Community Events**: Create and manage events
4. **Code Challenges**: Create programming challenges
5. **Challenge Submissions**: View and manage submissions

## Security Notes

- Keep your SSO secret secure and never commit it to version control
- Use environment variables for sensitive configuration
- Regularly rotate API keys
- Monitor SSO logs for any suspicious activity

## Environment Variables

Add these to your `.env` file:

```bash
# Discourse Integration
DISCOURSE_FORUM_URL=https://your-discourse-forum.com
DISCOURSE_API_KEY=your-discourse-api-key
DISCOURSE_API_USERNAME=your-discourse-username
DISCOURSE_SSO_SECRET=your-sso-secret-key
```

## Troubleshooting

### Common Issues:

1. **SSO not working**: Check that the SSO URL is correctly configured in Discourse
2. **API errors**: Verify API key and username are correct
3. **CSRF errors**: Ensure CORS settings allow your Discourse domain
4. **Template errors**: Check that all templates are properly loaded

### Debug Steps:

1. Check Django logs: `tail -f logs/django.log`
2. Verify database tables: `python manage.py dbshell`
3. Test SSO manually: Visit `/community/forum/sso/` directly
4. Check Discourse logs in admin panel

## Next Steps

1. **Configure Discourse**: Set up your actual Discourse instance
2. **Customize Templates**: Modify the community templates to match your design
3. **Add Features**: Implement additional community features as needed
4. **Testing**: Thoroughly test all features before going live

## Support

For additional help:
- Django documentation: https://docs.djangoproject.com/
- Discourse documentation: https://meta.discourse.org/
- Wagtail documentation: https://wagtail.org/
