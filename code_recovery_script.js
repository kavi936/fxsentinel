// Code Recovery Script for FXSentinel
// Run this in your browser console on your live site

(function() {
    console.log('🔍 Starting code recovery...');
    
    // Function to extract all CSS
    function extractCSS() {
        const styles = document.querySelectorAll('style');
        const links = document.querySelectorAll('link[rel="stylesheet"]');
        
        console.log('📄 Found CSS files:');
        styles.forEach((style, index) => {
            console.log(`Style ${index + 1}:`, style.textContent);
        });
        
        links.forEach((link, index) => {
            console.log(`CSS Link ${index + 1}:`, link.href);
        });
    }
    
    // Function to extract component structure
    function extractComponentStructure() {
        const root = document.querySelector('#root') || document.querySelector('[data-reactroot]') || document.body;
        console.log('🏗️ Component structure:', root.innerHTML);
    }
    
    // Function to extract all scripts
    function extractScripts() {
        const scripts = document.querySelectorAll('script');
        console.log('📜 Found scripts:');
        scripts.forEach((script, index) => {
            if (script.src) {
                console.log(`Script ${index + 1} (external):`, script.src);
            } else {
                console.log(`Script ${index + 1} (inline):`, script.textContent);
            }
        });
    }
    
    // Function to save data to file (if supported)
    function saveToFile(data, filename) {
        const blob = new Blob([data], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.click();
        URL.revokeObjectURL(url);
    }
    
    // Extract everything
    extractCSS();
    extractComponentStructure();
    extractScripts();
    
    console.log('✅ Code recovery complete! Check the console for extracted code.');
    console.log('💡 Tip: You can copy the output and save it to files locally.');
    
    // Return functions for manual use
    window.codeRecovery = {
        extractCSS,
        extractComponentStructure,
        extractScripts,
        saveToFile
    };
    
    console.log('🛠️ Use window.codeRecovery.functionName() to run specific extractions');
})();
