# Theme System Guide

## Overview

The Python Learning Studio theme system provides a flexible, responsive, and accessible theming solution for the platform. It supports both light and dark modes with user preferences persistence and includes customizable theme elements to enhance the user experience.

## Key Features

- **Theme Switching**: Toggle between light and dark modes
- **User Preference Persistence**: Remembers user theme choices across sessions
- **Bootswatch Integration**: Uses Bootswatch Darkly theme as the default dark theme
- **Bootstrap 5.3 Base**: Built on Bootstrap 5.3 with modern features
- **Theme-Aware Components**: All UI elements respond to theme changes
- **CSS Variables**: Custom properties for easy theme customization
- **Accessibility Support**: WCAG compliance considerations built in

## Implementation Details

### Theme Architecture

The theme system follows a layered approach:

1. **Base Layer**: Bootstrap 5.3 core CSS
2. **Theme Layer**: Bootswatch theme customizations
3. **Custom Layer**: Application-specific styles and overrides
4. **User Preferences**: Client-side storage for user selections

### Directory Structure

```
static/
├── css/
│   ├── themes/
│   │   ├── dark.css          # Dark theme styles
│   │   └── light.css         # Light theme styles
│   ├── base.css              # Shared base styles
│   └── theme-switcher.css    # Theme switcher component styles
├── js/
│   └── theme-switcher.js     # Theme switching functionality
└── scss/
    ├── _variables.scss       # Theme variables
    └── custom.scss           # Custom theme modifications
```

### Theme Switcher Implementation

The theme switcher uses a combination of CSS classes and localStorage to manage theme preferences:

```javascript
// static/js/theme-switcher.js
document.addEventListener('DOMContentLoaded', function() {
    const themeSwitcher = document.getElementById('theme-switcher');
    const themeStylesheet = document.getElementById('theme-stylesheet');
    const THEME_KEY = 'user-theme-preference';
    
    // Initialize theme based on user preference or system preference
    function initTheme() {
        const savedTheme = localStorage.getItem(THEME_KEY);
        
        if (savedTheme) {
            // Use saved preference
            setTheme(savedTheme);
        } else {
            // Use system preference
            const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
            setTheme(prefersDark ? 'dark' : 'light');
        }
    }
    
    // Set theme and update UI
    function setTheme(theme) {
        // Set data attribute on HTML for CSS selectors
        document.documentElement.setAttribute('data-bs-theme', theme);
        
        // Update stylesheet href
        if (themeStylesheet) {
            themeStylesheet.href = `/static/css/themes/${theme}.css`;
        }
        
        // Update switcher UI
        if (themeSwitcher) {
            themeSwitcher.checked = theme === 'dark';
        }
        
        // Save preference
        localStorage.setItem(THEME_KEY, theme);
    }
    
    // Toggle theme
    function toggleTheme() {
        const currentTheme = localStorage.getItem(THEME_KEY) || 'light';
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        setTheme(newTheme);
    }
    
    // Attach event listener
    if (themeSwitcher) {
        themeSwitcher.addEventListener('change', toggleTheme);
    }
    
    // Initialize theme
    initTheme();
});
```

### CSS Implementation

```css
/* static/css/base.css */
:root {
  /* Light theme variables (default) */
  --body-bg: #ffffff;
  --body-color: #212529;
  --primary-color: #0d6efd;
  --secondary-color: #6c757d;
  --highlight-bg: #f8f9fa;
  --border-color: #dee2e6;
  --code-bg: #f8f9fa;
}

[data-bs-theme="dark"] {
  /* Dark theme variables */
  --body-bg: #121212;
  --body-color: #f8f9fa;
  --primary-color: #0d6efd;
  --secondary-color: #6c757d;
  --highlight-bg: #2c2c2c;
  --border-color: #495057;
  --code-bg: #212529;
}

body {
  background-color: var(--body-bg);
  color: var(--body-color);
  transition: background-color 0.3s ease, color 0.3s ease;
}

/* Theme-aware CodeMirror styling */
.CodeMirror {
  background-color: var(--code-bg) !important;
  color: var(--body-color) !important;
  border: 1px solid var(--border-color);
}

/* Custom theme-aware components */
.card {
  background-color: var(--body-bg);
  border-color: var(--border-color);
}

.navbar {
  background-color: var(--highlight-bg);
  border-bottom: 1px solid var(--border-color);
}

/* Theme switcher styling */
.theme-switcher {
  position: relative;
  display: inline-block;
  width: 60px;
  height: 34px;
}

.theme-switcher input {
  opacity: 0;
  width: 0;
  height: 0;
}

.slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: var(--secondary-color);
  transition: 0.4s;
  border-radius: 34px;
}

.slider:before {
  position: absolute;
  content: "";
  height: 26px;
  width: 26px;
  left: 4px;
  bottom: 4px;
  background-color: white;
  transition: 0.4s;
  border-radius: 50%;
}

input:checked + .slider {
  background-color: var(--primary-color);
}

input:checked + .slider:before {
  transform: translateX(26px);
}
```

### HTML Integration

```html
<!-- Theme Switcher Component in base.html -->
<div class="theme-switch-wrapper ms-3">
  <label class="theme-switcher" for="theme-switcher">
    <input type="checkbox" id="theme-switcher">
    <span class="slider"></span>
  </label>
  <span class="theme-label ms-2"></span>
</div>

<!-- Theme stylesheet -->
<link id="theme-stylesheet" rel="stylesheet" href="/static/css/themes/light.css">
```

## Extending the Theme System

### Adding Custom Theme Variables

To add new custom variables to the theme system:

1. Define the variables in both light and dark modes:

```css
:root {
  /* Light theme */
  --custom-color: #value;
}

[data-bs-theme="dark"] {
  /* Dark theme */
  --custom-color: #darkvalue;
}
```

2. Use the variables in your components:

```css
.custom-component {
  color: var(--custom-color);
}
```

### Creating a New Theme

To create a custom theme:

1. Create a new CSS file in the `static/css/themes/` directory
2. Define your theme variables and override Bootstrap classes as needed
3. Update the theme switcher to include your new theme option


## Accessibility Considerations

The theme system is designed with accessibility in mind:

- **Contrast Ratios**: Both themes maintain WCAG AA compliance for text contrast
- **Focus Indicators**: Visible focus states preserved across themes
- **Color Independence**: Information is not conveyed by color alone
- **System Preferences**: Respects user's system-level theme preferences
- **Transition Effects**: Smooth transitions prevent jarring visual changes

## Future Enhancements

Planned improvements to the theme system:

1. **Theme Editor**: Admin interface for customizing theme variables
2. **Additional Theme Options**: More preset themes beyond light/dark
3. **User Theme Profiles**: Allow users to create personal theme preferences
4. **Component-Level Theming**: More granular control over component appearances
5. **Print Stylesheets**: Optimized styles for printed content
