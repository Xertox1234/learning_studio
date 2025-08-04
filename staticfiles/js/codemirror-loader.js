// CodeMirror 6 CDN Loader - Python Learning Studio
// Dynamically loads and initializes CodeMirror 6 modules

class CodeMirrorLoader {
    constructor() {
        this.modules = {};
        this.loaded = false;
        this.loading = false;
        this.loadPromise = null;
    }

    async loadModules() {
        if (this.loaded) return this.modules;
        if (this.loading) return this.loadPromise;

        this.loading = true;
        this.loadPromise = this._loadModules();
        
        try {
            await this.loadPromise;
            this.loaded = true;
            return this.modules;
        } catch (error) {
            this.loading = false;
            throw error;
        }
    }

    async _loadModules() {
        const cdnBase = 'https://cdn.jsdelivr.net/npm';
        
        // Define modules to load
        const moduleUrls = {
            // Core modules
            state: `${cdnBase}/@codemirror/state@6.2.1/dist/index.js`,
            view: `${cdnBase}/@codemirror/view@6.13.0/dist/index.js`,
            commands: `${cdnBase}/@codemirror/commands@6.2.4/dist/index.js`,
            
            // Language support
            python: `${cdnBase}/@codemirror/lang-python@6.1.3/dist/index.js`,
            javascript: `${cdnBase}/@codemirror/lang-javascript@6.2.1/dist/index.js`,
            html: `${cdnBase}/@codemirror/lang-html@6.4.5/dist/index.js`,
            css: `${cdnBase}/@codemirror/lang-css@6.2.1/dist/index.js`,
            
            // Themes
            oneDark: `${cdnBase}/@codemirror/theme-one-dark@6.1.2/dist/index.js`,
            
            // Extensions
            autocompletion: `${cdnBase}/@codemirror/autocomplete@6.9.0/dist/index.js`,
            search: `${cdnBase}/@codemirror/search@6.5.2/dist/index.js`,
            lint: `${cdnBase}/@codemirror/lint@6.4.1/dist/index.js`,
            closeBrackets: `${cdnBase}/@codemirror/autocomplete@6.9.0/dist/index.js`,
            matchBrackets: `${cdnBase}/@codemirror/language@6.8.0/dist/index.js`,
            foldGutter: `${cdnBase}/@codemirror/language@6.8.0/dist/index.js`,
            
            // Basic setup (includes many common extensions)
            basicSetup: `${cdnBase}/codemirror@6.0.1/dist/index.js`
        };

        // Load CSS first
        await this._loadCSS([
            `${cdnBase}/codemirror@6.0.1/theme/one-dark.css`,
            `${cdnBase}/@codemirror/view@6.13.0/style.css`
        ]);

        // Load modules in dependency order
        await this._loadModule('state', moduleUrls.state);
        await this._loadModule('view', moduleUrls.view);
        await this._loadModule('commands', moduleUrls.commands);
        
        // Load basic setup
        await this._loadModule('basicSetup', moduleUrls.basicSetup);
        
        // Load language modules
        await this._loadModule('python', moduleUrls.python);
        await this._loadModule('javascript', moduleUrls.javascript);
        await this._loadModule('html', moduleUrls.html);
        await this._loadModule('css', moduleUrls.css);
        
        // Load themes
        await this._loadModule('oneDark', moduleUrls.oneDark);
        
        // Load extensions
        await this._loadModule('autocompletion', moduleUrls.autocompletion);
        await this._loadModule('search', moduleUrls.search);
        await this._loadModule('lint', moduleUrls.lint);
        await this._loadModule('closeBrackets', moduleUrls.closeBrackets);
        await this._loadModule('matchBrackets', moduleUrls.matchBrackets);
        await this._loadModule('foldGutter', moduleUrls.foldGutter);

        // Setup global CodeMirror object for compatibility
        this._setupGlobalCodeMirror();
    }

    async _loadCSS(urls) {
        const promises = urls.map(url => new Promise((resolve, reject) => {
            const link = document.createElement('link');
            link.rel = 'stylesheet';
            link.href = url;
            link.onload = resolve;
            link.onerror = reject;
            document.head.appendChild(link);
        }));

        await Promise.all(promises);
    }

    async _loadModule(name, url) {
        try {
            const module = await import(url);
            this.modules[name] = module;
            console.log(`✓ Loaded CodeMirror module: ${name}`);
        } catch (error) {
            console.error(`✗ Failed to load CodeMirror module ${name}:`, error);
            throw new Error(`Failed to load ${name} module`);
        }
    }

    _setupGlobalCodeMirror() {
        // Create global CodeMirror object for backward compatibility
        window.CodeMirror = {
            // Core classes
            EditorView: this.modules.view.EditorView,
            EditorState: this.modules.state.EditorState,
            
            // Basic setup
            basicSetup: this.modules.basicSetup.basicSetup,
            
            // Languages
            python: () => this.modules.python.python(),
            javascript: () => this.modules.javascript.javascript(),
            html: () => this.modules.html.html(),
            css: () => this.modules.css.css(),
            
            // Themes
            oneDark: this.modules.oneDark.oneDark,
            
            // Extensions
            autocompletion: this.modules.autocompletion.autocompletion,
            search: this.modules.search.search,
            lint: this.modules.lint.lint,
            closeBrackets: this.modules.closeBrackets.closeBrackets,
            bracketMatching: this.modules.matchBrackets.bracketMatching,
            foldGutter: this.modules.foldGutter.foldGutter,
            
            // Utilities
            keymap: this.modules.view.keymap,
            Decoration: this.modules.view.Decoration,
            
            // Commands
            commands: this.modules.commands
        };

        console.log('✓ CodeMirror 6 global object initialized');
    }

    // Check if modules are ready
    isReady() {
        return this.loaded;
    }

    // Get specific module
    getModule(name) {
        return this.modules[name];
    }

    // Get all modules
    getAllModules() {
        return this.modules;
    }
}

// Create global loader instance
window.codeMirrorLoader = new CodeMirrorLoader();

// Auto-load when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.codeMirrorLoader.loadModules().catch(console.error);
    });
} else {
    window.codeMirrorLoader.loadModules().catch(console.error);
}

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CodeMirrorLoader;
}