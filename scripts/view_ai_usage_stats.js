/**
 * Script to view AI Usage Statistics
 * Run this in browser console while logged in as admin
 * 
 * Usage:
 * 1. Open your app in browser
 * 2. Log in as admin/developer
 * 3. Open browser console (F12)
 * 4. Paste this script and run it
 */

async function viewAIUsageStats(days = 7, minAnalyses = 1) {
    try {
        // Get Firebase auth token
        const auth = window.firebase?.auth();
        if (!auth || !auth.currentUser) {
            console.error('❌ Please log in first');
            return;
        }
        
        const token = await auth.currentUser.getIdToken();
        const backendUrl = 'http://localhost:5001'; // Update if different
        
        // Fetch usage stats
        console.log(`📊 Fetching AI usage stats (last ${days} days, min ${minAnalyses} analyses)...`);
        const response = await fetch(`${backendUrl}/api/ai-usage/stats?days=${days}&min_analyses=${minAnalyses}`, {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            const error = await response.json();
            console.error('❌ Error:', error);
            return;
        }
        
        const data = await response.json();
        
        console.log('\n' + '='.repeat(60));
        console.log('📊 AI USAGE STATISTICS');
        console.log('='.repeat(60));
        console.log(`Period: Last ${data.period_days} days`);
        console.log(`Minimum analyses: ${data.min_analyses}`);
        console.log(`Active users: ${data.active_users_count}`);
        console.log(`Timestamp: ${data.timestamp}`);
        console.log('\n');
        
        if (data.active_users_count === 0) {
            console.log('ℹ️  No active users found in this period');
            return;
        }
        
        console.log('👥 ACTIVE USERS:');
        console.log('-'.repeat(60));
        
        data.active_users.forEach((user, index) => {
            console.log(`\n${index + 1}. ${user.user_name || user.user_email || 'Unknown'}`);
            console.log(`   Email: ${user.user_email || 'N/A'}`);
            console.log(`   User ID: ${user.user_id}`);
            console.log(`   Total Analyses: ${user.total_analyses}`);
            console.log(`   Last Usage: ${user.last_usage ? new Date(user.last_usage.seconds * 1000).toLocaleString() : 'N/A'}`);
            console.log(`   Last Usage Type: ${user.last_usage_type || 'N/A'}`);
        });
        
        console.log('\n' + '='.repeat(60));
        console.log('💡 To contact users for feedback:');
        console.log('   - Copy their email addresses from above');
        console.log('   - Send them a feedback request email');
        console.log('   - Or use Firebase Console to send notifications');
        console.log('='.repeat(60));
        
        return data;
        
    } catch (error) {
        console.error('❌ Error fetching usage stats:', error);
    }
}

// Also create a helper to get specific user stats
async function getUserUsageStats(userId) {
    try {
        const auth = window.firebase?.auth();
        if (!auth || !auth.currentUser) {
            console.error('❌ Please log in first');
            return;
        }
        
        const token = await auth.currentUser.getIdToken();
        const backendUrl = 'http://localhost:5001';
        
        const response = await fetch(`${backendUrl}/api/ai-usage/user/${userId}`, {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            const error = await response.json();
            console.error('❌ Error:', error);
            return;
        }
        
        const data = await response.json();
        console.log('📊 User Usage Stats:', data.stats);
        return data.stats;
        
    } catch (error) {
        console.error('❌ Error:', error);
    }
}

// Export functions for use
console.log('✅ AI Usage Stats functions loaded!');
console.log('📋 Available functions:');
console.log('   - viewAIUsageStats(days=7, minAnalyses=1)');
console.log('   - getUserUsageStats(userId)');
console.log('\n💡 Example: viewAIUsageStats(30, 5) // Last 30 days, min 5 analyses');
