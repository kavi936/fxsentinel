// Extract Source Code from Compiled Assets
// Run this in your browser console to get the actual source files

(function() {
    console.log('🔍 Extracting source code from compiled assets...');
    
    // Function to fetch and extract source code
    async function extractSourceCode() {
        try {
            // Fetch the main JavaScript bundle
            console.log('📦 Fetching JavaScript bundle...');
            const jsResponse = await fetch('https://fxsentinel.io/assets/index-u2DxwkTq.js');
            const jsCode = await jsResponse.text();
            
            // Fetch the main CSS bundle
            console.log('🎨 Fetching CSS bundle...');
            const cssResponse = await fetch('https://fxsentinel.io/assets/index-CmwgjxDC.css');
            const cssCode = await cssResponse.text();
            
            // Create a comprehensive source code report
            const sourceReport = {
                timestamp: new Date().toISOString(),
                url: window.location.href,
                javascript: {
                    url: 'https://fxsentinel.io/assets/index-u2DxwkTq.js',
                    size: jsCode.length,
                    code: jsCode
                },
                css: {
                    url: 'https://fxsentinel.io/assets/index-CmwgjxDC.css',
                    size: cssCode.length,
                    code: cssCode
                },
                reactTree: document.querySelector('#root')?.innerHTML || 'Not found',
                externalResources: {
                    scripts: Array.from(document.querySelectorAll('script[src]')).map(s => s.src),
                    stylesheets: Array.from(document.querySelectorAll('link[rel="stylesheet"]')).map(l => l.href),
                    images: Array.from(document.querySelectorAll('img[src]')).map(i => i.src)
                }
            };
            
            console.log('📋 Source code extracted successfully!');
            console.log('📊 JavaScript size:', jsCode.length, 'characters');
            console.log('📊 CSS size:', cssCode.length, 'characters');
            
            // Save as JSON file
            try {
                const blob = new Blob([JSON.stringify(sourceReport, null, 2)], { type: 'application/json' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `fxsentinel-source-code-${Date.now()}.json`;
                a.click();
                URL.revokeObjectURL(url);
                console.log('💾 Source code saved as JSON file');
            } catch (error) {
                console.log('❌ Could not save file:', error);
            }
            
            // Also save individual files
            try {
                // Save JavaScript
                const jsBlob = new Blob([jsCode], { type: 'application/javascript' });
                const jsUrl = URL.createObjectURL(jsBlob);
                const jsLink = document.createElement('a');
                jsLink.href = jsUrl;
                jsLink.download = 'fxsentinel-main.js';
                jsLink.click();
                URL.revokeObjectURL(jsUrl);
                
                // Save CSS
                const cssBlob = new Blob([cssCode], { type: 'text/css' });
                const cssUrl = URL.createObjectURL(cssBlob);
                const cssLink = document.createElement('a');
                cssLink.href = cssUrl;
                cssLink.download = 'fxsentinel-main.css';
                cssLink.click();
                URL.revokeObjectURL(cssUrl);
                
                console.log('💾 Individual files saved (JS and CSS)');
            } catch (error) {
                console.log('❌ Could not save individual files:', error);
            }
            
            return sourceReport;
            
        } catch (error) {
            console.error('❌ Error extracting source code:', error);
            return null;
        }
    }
    
    // Function to extract component structure from the React tree
    function extractComponentStructure() {
        const root = document.querySelector('#root');
        if (!root) {
            console.log('❌ No React root found');
            return;
        }
        
        // Analyze the DOM structure to understand components
        const components = {
            dashboard: root.querySelector('.dashboard'),
            navbar: root.querySelector('.dashboard-navbar'),
            overview: root.querySelector('.overview-tab'),
            forexPairs: root.querySelector('.forex-pairs-card'),
            calendar: root.querySelector('.news-calendar')
        };
        
        console.log('🏗️ Component structure analysis:');
        Object.entries(components).forEach(([name, element]) => {
            if (element) {
                console.log(`${name}:`, element.outerHTML);
            }
        });
        
        return components;
    }
    
    // Function to extract CSS classes and styles
    function extractCSSClasses() {
        const allElements = document.querySelectorAll('*');
        const classes = new Set();
        
        allElements.forEach(el => {
            if (el.className) {
                el.className.split(' ').forEach(cls => {
                    if (cls.trim()) classes.add(cls.trim());
                });
            }
        });
        
        console.log('🎨 CSS classes found:', Array.from(classes));
        return Array.from(classes);
    }
    
    // Run the extraction
    extractSourceCode().then(report => {
        if (report) {
            extractComponentStructure();
            extractCSSClasses();
            
            console.log('✅ Complete source code extraction finished!');
            console.log('📁 Check your downloads folder for the extracted files');
            
            // Make functions available globally
            window.sourceExtractor = {
                extractSourceCode,
                extractComponentStructure,
                extractCSSClasses
            };
        }
    });
    
})();
