#!/bin/bash

# Script to fix remaining XSS vulnerabilities by adding sanitization

# Function to add import if not present
add_import_if_needed() {
  local file=$1
  if ! grep -q "import { sanitizeHTML } from" "$file"; then
    # Find the last import line and add after it
    sed -i.bak '/^import.*from/a\
import { sanitizeHTML } from '\''../utils/sanitize'\''
' "$file"
  fi
}

# Function to replace dangerous innerHTML
fix_xss() {
  local file=$1
  echo "Fixing XSS in $file..."

  # Add import
  add_import_if_needed "$file"

  # Replace dangerouslySetInnerHTML patterns
  sed -i.bak 's/dangerouslySetInnerHTML={{ __html: \([^}]*\) }}/dangerouslySetInnerHTML={{ __html: sanitizeHTML(\1, { mode: '\''rich'\'' }) }}/g' "$file"

  echo "Fixed $file"
}

# Fix all files
cd /Users/williamtower/projects/learning_studio/frontend/src

fix_xss "pages/WagtailExercisePage.jsx"
fix_xss "pages/StepBasedExercisePage.jsx"
fix_xss "components/code-editor/FillInBlankExercise.jsx"
fix_xss "components/code-editor/ProgressiveHintPanel.jsx"

echo "All XSS fixes applied!"
