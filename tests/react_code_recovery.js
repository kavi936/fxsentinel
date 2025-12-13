// Advanced React Code Recovery Script
// Run this in your browser console on your live React site

(function() {
    console.log('⚛️ Starting React code recovery...');
    
    // Function to extract React component tree
    function extractReactTree() {
        const root = document.querySelector('#root') || document.querySelector('[data-reactroot]');
        if (!root) {
            console.log('❌ No React root found');
            return;
        }
        
        console.log('🌳 React component tree:');
        console.log(root.innerHTML);
        
        // Try to find React DevTools data
        if (window.__REACT_DEVTOOLS_GLOBAL_HOOK__) {
            console.log('🔧 React DevTools hook found');
        }
    }
    
    // Function to extract all inline styles
    function extractInlineStyles() {
        const elements = document.querySelectorAll('[style]');
        const styles = {};
        
        elements.forEach((el, index) => {
            if (el.style.cssText) {
                styles[`element_${index}`] = {
                    tag: el.tagName,
                    className: el.className,
                    styles: el.style.cssText
                };
            }
        });
        
        console.log('🎨 Inline styles found:', styles);
        return styles;
    }
    
    // Function to extract computed styles for specific components
    function extractComputedStyles(selector) {
        const elements = document.querySelectorAll(selector);
        const computedStyles = {};
        
        elements.forEach((el, index) => {
            const styles = window.getComputedStyle(el);
            const cssText = Array.from(styles).map(prop => `${prop}: ${styles.getPropertyValue(prop)}`).join('; ');
            computedStyles[`${selector}_${index}`] = cssText;
        });
        
        console.log(`📊 Computed styles for ${selector}:`, computedStyles);
        return computedStyles;
    }
    
    // Function to extract all external resources
    function extractExternalResources() {
        const resources = {
            scripts: [],
            stylesheets: [],
            images: [],
            fonts: []
        };
        
        // Scripts
        document.querySelectorAll('script[src]').forEach(script => {
            resources.scripts.push(script.src);
        });
        
        // Stylesheets
        document.querySelectorAll('link[rel="stylesheet"]').forEach(link => {
            resources.stylesheets.push(link.href);
        });
        
        // Images
        document.querySelectorAll('img[src]').forEach(img => {
            resources.images.push(img.src);
        });
        
        // Fonts
        document.querySelectorAll('link[rel="preload"][as="font"], link[rel="stylesheet"][href*="font"]').forEach(font => {
            resources.fonts.push(font.href);
        });
        
        console.log('📦 External resources:', resources);
        return resources;
    }
    
    // Function to extract form data and state
    function extractFormData() {
        const forms = document.querySelectorAll('form');
        const formData = {};
        
        forms.forEach((form, index) => {
            const inputs = form.querySelectorAll('input, select, textarea');
            const data = {};
            
            inputs.forEach(input => {
                if (input.name) {
                    data[input.name] = input.value;
                }
            });
            
            formData[`form_${index}`] = {
                action: form.action,
                method: form.method,
                data: data
            };
        });
        
        console.log('📝 Form data:', formData);
        return formData;
    }
    
    // Function to create a comprehensive report
    function generateRecoveryReport() {
        const report = {
            timestamp: new Date().toISOString(),
            url: window.location.href,
            title: document.title,
            reactTree: document.querySelector('#root')?.innerHTML || 'Not found',
            externalResources: extractExternalResources(),
            inlineStyles: extractInlineStyles(),
            formData: extractFormData(),
            meta: {
                viewport: document.querySelector('meta[name="viewport"]')?.content,
                description: document.querySelector('meta[name="description"]')?.content,
                keywords: document.querySelector('meta[name="keywords"]')?.content
            }
        };
        
        console.log('📋 Complete recovery report:', report);
        
        // Try to save as file
        try {
            const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `fxsentinel-recovery-${Date.now()}.json`;
            a.click();
            URL.revokeObjectURL(url);
            console.log('💾 Recovery report saved as JSON file');
        } catch (error) {
            console.log('❌ Could not save file:', error);
        }
        
        return report;
    }
    
    // Run all extractions
    extractReactTree();
    extractExternalResources();
    extractInlineStyles();
    extractFormData();
    
    // Generate comprehensive report
    const report = generateRecoveryReport();
    
    // Make functions available globally
    window.reactRecovery = {
        extractReactTree,
        extractExternalResources,
        extractInlineStyles,
        extractComputedStyles,
        extractFormData,
        generateRecoveryReport
    };
    
    console.log('✅ React code recovery complete!');
    console.log('🛠️ Use window.reactRecovery.functionName() for specific extractions');
    console.log('📋 Full report generated and saved');
})();
