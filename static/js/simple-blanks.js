// Minimal working fill-in-the-blank implementation
document.addEventListener('DOMContentLoaded', function() {
    // Find all interactive code editors
    const editors = document.querySelectorAll('.interactive-code-editor');
    
    editors.forEach(textarea => {
        // Simple approach: replace {{BLANK_X}} with actual input elements in the DOM
        const content = textarea.value;
        
        // Create a container div
        const container = document.createElement('div');
        container.className = 'simple-code-editor';
        container.style.cssText = `
            background: #1e1e1e;
            color: #d4d4d4;
            font-family: 'Cascadia Code', 'Fira Code', 'JetBrains Mono', monospace;
            font-size: 14px;
            line-height: 1.4;
            padding: 16px;
            white-space: pre;
            border-radius: 6px;
        `;
        
        // Replace {{BLANK_X}} with input elements
        let html = content
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/\{\{BLANK_(\d+)\}\}/g, (match, num) => {
                return `<input type="text" placeholder="BLANK_${num}" style="
                    background: #374151;
                    border: 1px solid #4b5563;
                    border-radius: 4px;
                    color: #e5e7eb;
                    font-family: inherit;
                    font-size: inherit;
                    padding: 4px 8px;
                    min-width: 120px;
                    outline: none;
                    margin: 0 2px;
                " />`;
            });
        
        container.innerHTML = html;
        
        // Replace the textarea
        textarea.parentNode.insertBefore(container, textarea);
        textarea.style.display = 'none';
        
        console.log('✅ Replaced textarea with simple editor');
    });
});