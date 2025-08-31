# FXSentinel Dashboard Feedback - TODO List

## 🎯 **Priority: Critical Issues (Fix Today)**

### 1. **Alert Bot Continuity Issue** ✅ RESOLVED
**Problem**: Alert bot stops working for some users in the background
**Status**: ✅ IMPLEMENTED - Webhook-based alert system with external cron jobs
**Files Modified**:
- `backend/app.py` (new endpoints)
- `ALERT_BOT_CONTINUITY_SOLUTION.md` (comprehensive solution)

**Tasks**:
- [x] Investigate why alert bot stops for some users (hosting platform limitations)
- [x] Add better error handling and recovery mechanisms
- [x] Implement heartbeat monitoring for alert service
- [x] Add automatic restart functionality
- [x] Create alert bot health dashboard

**Resolution**: Implemented webhook-based alert system that eliminates dependency on background processes. Added `/api/trigger-alerts` endpoint for external cron jobs and `/api/health/alert-service` for monitoring. This ensures alerts work continuously regardless of hosting platform limitations.

### 2. **Navbar Responsive Design** ✅ RESOLVED
**Problem**: Navbar needs optimization for smaller screens and wider displays
**Status**: ✅ TESTED AND WORKING - No issues found across different screen sizes
**Files to Modify**:
- `src/components/Dashboard.css`
- `src/components/Dashboard.jsx`

**Tasks**:
- [x] Optimize navbar layout for mobile devices (< 768px)
- [x] Improve navbar for tablet screens (768px - 1024px)
- [x] Enhance navbar for wide screens (> 1400px)
- [x] Fix mobile menu functionality
- [x] Ensure proper spacing and readability on all screen sizes
- [x] Test navbar on various device sizes

**Resolution**: Tested with browser dev tools using zoom in/out and different screen sizes. Navbar works properly across all tested resolutions. Issue may have been user-specific or resolved in previous updates.

### 3. **Economic Calendar Grid Optimization** 🔴 HIGH PRIORITY
**Problem**: Economic calendar needs to take up more space in the grid for wider screens
**Status**: Layout improvement needed
**Files to Modify**:
- `src/components/Overview.css`
- `src/components/Overview.jsx`

**Tasks**:
- [ ] Implement responsive grid system for economic calendar
- [ ] Increase calendar width on wider screens (> 1200px)
- [ ] Optimize calendar height and content display
- [ ] Ensure proper scaling on different screen sizes
- [ ] Test calendar layout on various resolutions

### 3.6. **Economic Calendar Value Formatting** ✅ RESOLVED
**Problem**: Economic calendar shows raw numbers (73, 78) instead of formatted values (73K, 78K)
**Status**: ✅ IMPLEMENTED - Smart value formatting with proper units
**Files Modified**:
- `backend/services/finnhub_calendar.py`

**Tasks**:
- [x] Fix format_economic_value function to detect event types
- [x] Add proper unit formatting for employment data (K suffix)
- [x] Add proper unit formatting for percentage data (% suffix)
- [x] Add proper unit formatting for index data (decimal precision)
- [x] Improve enhanced expected value generation formatting

**Resolution**: Enhanced the format_economic_value function to intelligently detect event types and apply appropriate units. Non-Farm Payrolls will now show "73K" and "78K" instead of raw numbers.

## 🟡 **Priority: Functional Issues**

### 4. **Filter and Sorting Problems** 🟡 MEDIUM PRIORITY
**Problem**: Filter functionality and sorting have issues for some reason
**Status**: Bug fixes needed
**Files to Check**:
- `src/components/LiveNewsFeed.jsx`
- `src/components/Alerts.jsx`
- `src/components/Overview.jsx`

**Tasks**:
- [ ] Debug filter functionality in live news feed
- [ ] Fix sorting issues in alerts history
- [ ] Ensure economic calendar filters work correctly
- [ ] Test all filter combinations
- [ ] Add proper error handling for filter operations
- [ ] Implement filter state persistence

### 5. **Live News Analysis Refresh Issue** 🟡 MEDIUM PRIORITY
**Problem**: Live news analysis refreshes even when there's no new live news, annoying users
**Status**: UX improvement needed
**Files to Modify**:
- `src/components/LiveNewsFeed.jsx`
- `src/components/LiveNewsFeed.css`

**Tasks**:
- [ ] Implement smart refresh logic (only refresh when new news available)
- [ ] Add visual indicator when refreshing vs. when new content is available
- [ ] Reduce unnecessary API calls
- [ ] Add user preference for refresh frequency
- [ ] Implement proper loading states

## 🟢 **Priority: Content and Analysis Improvements**

### 6. **AI Analysis Detail Enhancement** 🟢 MEDIUM PRIORITY
**Problem**: AI Analysis is not very detailed, users need to know why and what is happening
**Status**: Content improvement needed
**Files to Modify**:
- `backend/services/ai_analysis_service.py`
- `src/components/LiveNewsFeed.jsx`

**Tasks**:
- [ ] Enhance AI prompts to provide more detailed analysis
- [ ] Add "why" explanations for market movements
- [ ] Include "how" mechanisms of market impact
- [ ] Provide more context and background information
- [ ] Add historical comparison data
- [ ] Include market sentiment analysis

### 7. **AI Article Reading Enhancement** 🟢 MEDIUM PRIORITY
**Problem**: Use AI to read through article website instead of just headlines and text
**Status**: Feature enhancement needed
**Files to Modify**:
- `backend/services/news_alert_trigger.py`
- `backend/services/ai_analysis_service.py`

**Tasks**:
- [ ] Implement web scraping for full article content
- [ ] Add article summarization using AI
- [ ] Extract key insights from full articles
- [ ] Handle different article formats and sources
- [ ] Implement proper error handling for failed scrapes
- [ ] Add content validation and quality checks

### 8. **Price Level and Probability Analysis** 🟢 MEDIUM PRIORITY
**Problem**: Need more about why and how, what price levels, probability of price going up or down
**Status**: Advanced analysis feature needed
**Files to Modify**:
- `backend/services/ai_analysis_service.py`
- `src/components/LiveNewsFeed.jsx`

**Tasks**:
- [ ] Add price level analysis to AI responses
- [ ] Include probability assessments for price movements
- [ ] Provide support/resistance level identification
- [ ] Add risk/reward ratio calculations
- [ ] Include timeframe-specific price targets
- [ ] Add confidence intervals for predictions

### 9. **Market Context Section Improvement** 🟢 LOW PRIORITY
**Problem**: Market context section can be removed or altered to be better, main sub captions and less major ones not helpful for decision making
**Status**: Content restructuring needed
**Files to Modify**:
- `src/components/Overview.jsx`
- `src/components/Overview.css`

**Tasks**:
- [ ] Redesign market context section
- [ ] Remove or improve less helpful sub-captions
- [ ] Focus on decision-relevant information
- [ ] Add actionable insights
- [ ] Improve information hierarchy
- [ ] Test with users for feedback

### 10. **Event Count Display Fix** 🟢 LOW PRIORITY
**Problem**: "Showing 0 of 3 events" may confuse users, remove or only show total events after filter
**Status**: UX improvement needed
**Files to Modify**:
- `src/components/Overview.jsx`

**Tasks**:
- [ ] Remove confusing "0 of X" display
- [ ] Show only total filtered events count
- [ ] Improve empty state messaging
- [ ] Add helpful guidance when no events match filters
- [ ] Test different display formats

## 📋 **Implementation Checklist**

### Phase 1: Critical Fixes (Today)
- [ ] Fix alert bot continuity issues
- [x] Optimize navbar for all screen sizes
- [ ] Improve economic calendar grid layout

### Phase 2: Functional Improvements (This Week)
- [ ] Fix filter and sorting issues
- [ ] Implement smart refresh for live news
- [ ] Enhance AI analysis detail level

### Phase 3: Advanced Features (Next Week)
- [ ] Implement full article AI reading
- [ ] Add price level and probability analysis
- [ ] Redesign market context section

## 🔧 **Technical Notes**

### Files to Monitor:
- `backend/services/background_alert_worker.py` - Alert bot continuity
- `src/components/Dashboard.jsx` - Navbar optimization
- `src/components/Overview.jsx` - Economic calendar and filters
- `src/components/LiveNewsFeed.jsx` - Live news and AI analysis
- `src/components/Alerts.jsx` - Alert filtering and sorting

### Testing Requirements:
- [ ] Test on mobile devices (320px - 768px)
- [ ] Test on tablet devices (768px - 1024px)
- [ ] Test on desktop devices (1024px+)
- [ ] Test on wide screens (1400px+)
- [ ] Test alert bot functionality
- [ ] Test all filter combinations
- [ ] Test AI analysis quality

### Performance Considerations:
- [ ] Optimize API calls to reduce unnecessary refreshes
- [ ] Implement proper caching for AI analysis
- [ ] Ensure responsive design doesn't impact performance
- [ ] Monitor alert bot resource usage

## 📊 **Success Metrics**

### User Experience:
- [ ] Alert bot uptime > 99%
- [ ] Navbar usability score > 4.5/5
- [ ] Economic calendar visibility improvement
- [ ] Filter functionality success rate > 95%

### Content Quality:
- [ ] AI analysis detail level improvement
- [ ] User satisfaction with analysis depth
- [ ] Price level accuracy assessment
- [ ] Article reading comprehension improvement

### Technical Performance:
- [ ] Page load time < 3 seconds
- [ ] API response time < 2 seconds
- [ ] Mobile responsiveness score > 90%
- [ ] Cross-browser compatibility

---

**Last Updated**: Today
**Priority**: High - All items should be addressed today
**Assigned**: Development Team
**Status**: In Progress
