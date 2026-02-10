# Economic Indicators Content Structure Reference

**Purpose**: Quick reference guide showing the exact content structure for each indicator in the codebase.

---

## 📍 Content Location

**Main File**: `src/components/Economies.jsx`

**Key Data Structures**:
1. `indicatorDetails` object (lines ~6-2000+) - Contains detailed content sections
2. `getIndicatorInsights()` function (lines ~2497-2800+) - Generates Key Insights
3. `economyData` object (lines ~2174-2400) - Contains indicator metadata and descriptions

---

## 🏗️ Content Structure

### For Each Indicator, Content is Stored in Two Places:

#### 1. **Key Insights** (4 bullet points)
**Location**: `getIndicatorInsights()` function in `Economies.jsx`

**Format**: Returns an array of 4 strings (bullet points)

**Example Structure**:
```javascript
if (indicator.id === 'interest-rate' && selectedEconomy === 'US') {
  return [
    'Current policy stance and recent changes...',
    'Market expectations vs reality...',
    'Key drivers and forward outlook...',
    'Trading implications...'
  ];
}
```

**Current Indicators with Custom Insights**:
- `interest-rate` (US, EUR, GBP, JPY - all have custom content)
- `inflation-YoY` (US only)
- `inflation` (EUR, GBP, JPY)
- `core-inflation-YoY` (EUR, GBP, JPY)
- `gdp-growth` (all economies)
- `unemployment` (all economies)
- `nonfarm-payrolls` (US only)
- `wage-growth` (GBP only)
- `current-account` (EUR, JPY)

#### 2. **Detailed Content Sections** (5 sections)
**Location**: `indicatorDetails` object in `Economies.jsx`

**Sections**:
- `overview` - What the indicator is, why it matters
- `measurement` - How it's calculated, who publishes it
- `impact` - Currency and market impact
- `context` - Current policy context (UPDATE THIS MOST FREQUENTLY)
- `traderImplications` - What traders should monitor

**Format**: Each section is a string with `[[highlighted text]]` markers

**Example Structure**:
```javascript
'indicator-id': {
  overview: 'Text with [[highlighted terms]]...',
  measurement: 'Text with [[highlighted terms]]...',
  impact: 'Text with [[highlighted terms]]...',
  context: 'Text with [[highlighted terms]]...',  // UPDATE THIS MOST
  traderImplications: 'Text with [[highlighted terms]]...'
}
```

---

## 📋 Indicator IDs by Economy

### US Indicators
1. `interest-rate` → `indicatorDetails['interest-rate']`
2. `inflation-YoY` → `indicatorDetails['inflation-YoY']`
3. `core-inflation-YoY` → `indicatorDetails['core-inflation-YoY']`
4. `gdp-growth` → `indicatorDetails['gdp-growth']`
5. `unemployment` → `indicatorDetails['unemployment']`
6. `nonfarm-payrolls` → `indicatorDetails['nonfarm-payrolls']`

### EUR Indicators
1. `interest-rate` → `indicatorDetails['interest-rate-EUR']` (EUR-specific)
2. `inflation` → `indicatorDetails['inflation-EUR']` (EUR-specific)
3. `core-inflation-YoY` → `indicatorDetails['core-inflation-YoY-EUR']` (EUR-specific)
4. `gdp-growth` → `indicatorDetails['gdp-growth-EUR']` (EUR-specific)
5. `unemployment` → `indicatorDetails['unemployment-EUR']` (EUR-specific)
6. `current-account` → Uses generic content or needs custom

### GBP Indicators
1. `interest-rate` → `indicatorDetails['interest-rate-GBP']` (GBP-specific)
2. `inflation` → Uses generic or needs custom
3. `core-inflation-YoY` → Uses generic or needs custom
4. `gdp-growth` → `indicatorDetails['gdp-growth-GBP']` (GBP-specific)
5. `unemployment` → Uses generic or needs custom
6. `wage-growth` → Uses generic or needs custom

### JPY Indicators
1. `interest-rate` → `indicatorDetails['interest-rate-JPY']` (JPY-specific)
2. `inflation` → Uses generic or needs custom
3. `core-inflation-YoY` → Uses generic or needs custom
4. `gdp-growth` → `indicatorDetails['gdp-growth-JPY']` (JPY-specific)
5. `unemployment` → Uses generic or needs custom
6. `current-account` → Uses generic or needs custom

---

## 🔍 Finding Content to Update

### Step 1: Find Key Insights
Search in `Economies.jsx` for:
```javascript
getIndicatorInsights = (indicator, selectedEconomy) => {
```

Then find the specific condition for your indicator:
- US Interest Rate: `if (indicator.id === 'interest-rate' && selectedEconomy === 'US')`
- EUR Interest Rate: `if (indicator.id === 'interest-rate' && selectedEconomy === 'EUR')`
- etc.

### Step 2: Find Detailed Content Sections
Search in `Economies.jsx` for:
```javascript
const indicatorDetails = {
```

Then find your indicator:
- Generic: `'indicator-id': { ... }`
- Economy-specific: `'indicator-id-ECONOMY': { ... }`

---

## 📝 Content Update Workflow

### For Key Insights Updates:

1. **Locate the function**: `getIndicatorInsights()` around line 2497
2. **Find your indicator**: Search for the condition matching your indicator ID and economy
3. **Update the array**: Replace the 4 bullet point strings
4. **Keep format**: Each string should be a complete sentence/paragraph

### For Detailed Content Sections:

1. **Locate the object**: `indicatorDetails` around line 6
2. **Find your indicator**: Search for the indicator ID (with economy suffix if applicable)
3. **Update sections**: Focus on `context` section first (most frequently updated)
4. **Maintain highlighting**: Keep `[[double brackets]]` around key terms
5. **Preserve structure**: Don't change the section keys (overview, measurement, etc.)

---

## 🎯 Highlighting System

**Format**: `[[text]]` creates red underline in UI

**What to Highlight**:
- Policy terms (e.g., `[[Federal Funds Rate]]`, `[[FOMC]]`)
- Key numbers (e.g., `[[3.75%]]`, `[[December 2025]]`)
- Market concepts (e.g., `[[yield differentials]]`, `[[real yields]]`)
- Trading implications (e.g., `[[USD strength]]`, `[[dovish repricing]]`)

**Example**:
```
The [[Federal Funds Rate]] stands at [[3.75%]] as of [[December 2025]], 
following a shift toward [[cautious easing]].
```

---

## 📊 Data Integration

**Important**: Content in `Economies.jsx` is merged with data from:
1. Google Sheets API (primary)
2. `src/data/economyIndicators.json` (fallback)

**What Gets Merged**:
- Current values → From data source
- Chart data → From data source
- Descriptions → From `indicatorDetails` (always used)
- Content sections → From `indicatorDetails` (always used)

**What You Update**:
- Content sections in `indicatorDetails` object
- Key Insights in `getIndicatorInsights()` function
- NOT the data values (those come from Google Sheets/JSON)

---

## 🔄 Update Priority

### High Priority (Update Immediately):
1. **Key Insights** - Most visible to users
2. **Context sections** - Contains current policy and market conditions
3. **Trader Implications** - Contains current thresholds and monitoring points

### Medium Priority (Update Monthly):
1. **Overview** - Verify accuracy, update if methodology changes
2. **Impact** - Update if market dynamics change significantly

### Low Priority (Update Quarterly):
1. **Measurement** - Only update if calculation methodology changes

---

## 💡 Quick Reference: Indicator IDs

| Economy | Indicator | Indicator ID | Key Insights Location | Content Location |
|---------|-----------|--------------|----------------------|------------------|
| US | Interest Rate | `interest-rate` | `getIndicatorInsights()` - US condition | `indicatorDetails['interest-rate']` |
| US | Inflation | `inflation-YoY` | `getIndicatorInsights()` - US condition | `indicatorDetails['inflation-YoY']` |
| US | Core Inflation | `core-inflation-YoY` | `getIndicatorInsights()` - US condition | `indicatorDetails['core-inflation-YoY']` |
| US | GDP Growth | `gdp-growth` | `getIndicatorInsights()` - US condition | `indicatorDetails['gdp-growth']` |
| US | Unemployment | `unemployment` | `getIndicatorInsights()` - US condition | `indicatorDetails['unemployment']` |
| US | NFP | `nonfarm-payrolls` | `getIndicatorInsights()` - US condition | `indicatorDetails['nonfarm-payrolls']` |
| EUR | Interest Rate | `interest-rate` | `getIndicatorInsights()` - EUR condition | `indicatorDetails['interest-rate-EUR']` |
| EUR | Inflation | `inflation` | `getIndicatorInsights()` - EUR condition | `indicatorDetails['inflation-EUR']` |
| EUR | Core Inflation | `core-inflation-YoY` | `getIndicatorInsights()` - EUR condition | `indicatorDetails['core-inflation-YoY-EUR']` |
| EUR | GDP Growth | `gdp-growth` | `getIndicatorInsights()` - EUR condition | `indicatorDetails['gdp-growth-EUR']` |
| EUR | Unemployment | `unemployment` | `getIndicatorInsights()` - EUR condition | `indicatorDetails['unemployment-EUR']` |
| EUR | Current Account | `current-account` | `getIndicatorInsights()` - EUR condition | Generic or custom |
| GBP | Interest Rate | `interest-rate` | `getIndicatorInsights()` - GBP condition | `indicatorDetails['interest-rate-GBP']` |
| GBP | Inflation | `inflation` | `getIndicatorInsights()` - GBP condition | Generic or custom |
| GBP | Core Inflation | `core-inflation-YoY` | `getIndicatorInsights()` - GBP condition | Generic or custom |
| GBP | GDP Growth | `gdp-growth` | `getIndicatorInsights()` - GBP condition | `indicatorDetails['gdp-growth-GBP']` |
| GBP | Unemployment | `unemployment` | `getIndicatorInsights()` - GBP condition | Generic or custom |
| GBP | Wage Growth | `wage-growth` | `getIndicatorInsights()` - GBP condition | Generic or custom |
| JPY | Interest Rate | `interest-rate` | `getIndicatorInsights()` - JPY condition | `indicatorDetails['interest-rate-JPY']` |
| JPY | Inflation | `inflation` | `getIndicatorInsights()` - JPY condition | Generic or custom |
| JPY | Core Inflation | `core-inflation-YoY` | `getIndicatorInsights()` - JPY condition | Generic or custom |
| JPY | GDP Growth | `gdp-growth` | `getIndicatorInsights()` - JPY condition | `indicatorDetails['gdp-growth-JPY']` |
| JPY | Unemployment | `unemployment` | `getIndicatorInsights()` - JPY condition | Generic or custom |
| JPY | Current Account | `current-account` | `getIndicatorInsights()` - JPY condition | Generic or custom |

---

## 🚀 Quick Start Guide

1. **Open** `src/components/Economies.jsx`
2. **Search** for `getIndicatorInsights` to update Key Insights
3. **Search** for `indicatorDetails` to update content sections
4. **Focus on** `context` sections first (most frequently updated)
5. **Use** `[[brackets]]` for highlighting important terms
6. **Test** changes in the app to verify formatting

---

**Last Updated**: February 10, 2026
