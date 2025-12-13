// Reconstruct React Components from Compiled Code
// This script helps you understand the component structure

(function() {
    console.log('🔧 Reconstructing React components...');
    
    // Function to analyze the dashboard structure
    function analyzeDashboard() {
        const dashboard = document.querySelector('.dashboard');
        if (!dashboard) {
            console.log('❌ Dashboard not found');
            return;
        }
        
        const structure = {
            navbar: {
                left: {
                    logo: dashboard.querySelector('.navbar-logo'),
                    welcome: dashboard.querySelector('.welcome-message'),
                    time: dashboard.querySelector('.live-time')
                },
                center: {
                    tabs: dashboard.querySelector('.navbar-tabs')
                },
                right: {
                    marketStatus: dashboard.querySelector('.market-status'),
                    refreshBtn: dashboard.querySelector('.refresh-btn'),
                    notificationBtn: dashboard.querySelector('.notification-btn'),
                    profileBtn: dashboard.querySelector('.profile-btn'),
                    settingsBtn: dashboard.querySelector('.settings-btn'),
                    homeBtn: dashboard.querySelector('.home-btn')
                }
            },
            main: {
                overview: dashboard.querySelector('.overview-tab'),
                forexPairs: dashboard.querySelector('.forex-pairs-card'),
                calendar: dashboard.querySelector('.news-calendar')
            }
        };
        
        console.log('🏗️ Dashboard structure:', structure);
        return structure;
    }
    
    // Function to extract forex pairs data
    function extractForexData() {
        const pairs = document.querySelectorAll('.forex-pair');
        const forexData = [];
        
        pairs.forEach(pair => {
            const name = pair.querySelector('.pair-name')?.textContent;
            const price = pair.querySelector('.pair-price')?.textContent;
            const change = pair.querySelector('.change-value')?.textContent;
            const percent = pair.querySelector('.change-percent')?.textContent;
            const direction = pair.querySelector('.pair-price')?.classList.contains('up') ? 'up' : 'down';
            
            forexData.push({
                name,
                price,
                change,
                percent,
                direction
            });
        });
        
        console.log('💱 Forex pairs data:', forexData);
        return forexData;
    }
    
    // Function to extract calendar events
    function extractCalendarEvents() {
        const events = document.querySelectorAll('.event-card');
        const calendarData = [];
        
        events.forEach(event => {
            const time = event.querySelector('.time')?.textContent;
            const date = event.querySelector('.date')?.textContent;
            const title = event.querySelector('.event-title')?.textContent;
            const currency = event.querySelector('.currency')?.textContent;
            const status = event.querySelector('.status-indicator')?.textContent;
            const category = event.querySelector('.event-category')?.textContent;
            
            const dataPoints = event.querySelectorAll('.data-point');
            const data = {};
            dataPoints.forEach(dp => {
                const label = dp.querySelector('.label')?.textContent?.replace(':', '');
                const value = dp.querySelector('.value')?.textContent;
                if (label) data[label] = value;
            });
            
            calendarData.push({
                time,
                date,
                title,
                currency,
                status,
                category,
                data
            });
        });
        
        console.log('📅 Calendar events:', calendarData);
        return calendarData;
    }
    
    // Function to generate component templates
    function generateComponentTemplates() {
        const templates = {
            Dashboard: {
                structure: analyzeDashboard(),
                forexData: extractForexData(),
                calendarData: extractCalendarEvents()
            }
        };
        
        console.log('📝 Component templates:', templates);
        
        // Save templates as JSON
        try {
            const blob = new Blob([JSON.stringify(templates, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `fxsentinel-component-templates-${Date.now()}.json`;
            a.click();
            URL.revokeObjectURL(url);
            console.log('💾 Component templates saved');
        } catch (error) {
            console.log('❌ Could not save templates:', error);
        }
        
        return templates;
    }
    
    // Function to extract CSS for specific components
    function extractComponentCSS() {
        const components = {
            dashboard: '.dashboard',
            navbar: '.dashboard-navbar',
            overview: '.overview-tab',
            forexPairs: '.forex-pairs-card',
            calendar: '.news-calendar'
        };
        
        const cssData = {};
        
        Object.entries(components).forEach(([name, selector]) => {
            const element = document.querySelector(selector);
            if (element) {
                const styles = window.getComputedStyle(element);
                const cssText = Array.from(styles).map(prop => `${prop}: ${styles.getPropertyValue(prop)}`).join('; ');
                cssData[name] = cssText;
            }
        });
        
        console.log('🎨 Component CSS:', cssData);
        return cssData;
    }
    
    // Run the reconstruction
    const templates = generateComponentTemplates();
    const cssData = extractComponentCSS();
    
    // Make functions available globally
    window.componentReconstructor = {
        analyzeDashboard,
        extractForexData,
        extractCalendarEvents,
        generateComponentTemplates,
        extractComponentCSS
    };
    
    console.log('✅ Component reconstruction complete!');
    console.log('🛠️ Use window.componentReconstructor.functionName() for specific extractions');
    
})();
