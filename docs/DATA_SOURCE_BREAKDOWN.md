# Data Source Breakdown - What Comes From Where

## Summary

**Google Sheets provides:** Raw data and values only  
**Codebase provides:** All descriptions, trading analysis, and professional content

---

## What Google Sheets Provides

The Google Sheets integration extracts **ONLY** the following data:

### 1. **Current Value**
- The latest indicator value (e.g., "3.75%", "119K")
- Formatted based on unit (%, K, T, B)

### 2. **Historical Chart Data**
- Array of numeric values: `[5.5, 5.5, 5.0, 4.75, 4.5, 3.75]`
- Array of dates: `["2024-01-31", "2024-02-29", ...]`
- Used to render the charts

### 3. **Metadata**
- `asOf`: Date of latest release
- `unit`: Unit of measurement (%, K, T, B)
- `frequency`: Release frequency (e.g., "Monthly", "8 meetings per year")
- `nextRelease`: Next release date (if available)

### 4. **Source Information**
- `source`: Organization name (e.g., "Federal Reserve")
- `sourceUrl`: Link to official data source
- `notes`: Basic notes (e.g., "Federal Funds Rate - %")

### 5. **Fallback Description** (Ignored)
- Google Sheets service has a `_get_description()` method that generates short fallback descriptions
- **These are IGNORED** - the frontend always uses placeholder descriptions instead

---

## What the Codebase Provides

### 1. **Card Descriptions** (Always Used)
- Professional, detailed descriptions for each indicator
- Stored in `Economies.jsx` placeholder data
- Examples:
  - "Federal Funds Rate - The primary monetary policy tool set by the Federal Open Market Committee (FOMC). Represents the target range for overnight interbank lending rates."
  - "Consumer Price Index Year-over-Year - Measures the annual percentage change in prices for a basket of consumer goods and services..."

### 2. **Trading Analysis** (Expanded Modal Content)
Stored in `indicatorDetails` dictionary in `Economies.jsx`:

- **Overview**: What the indicator is, why traders care
- **Measurement**: How it's calculated and measured
- **Impact**: Currency and market impact (rate hikes vs cuts, etc.)
- **Current Policy Context**: Current world scenario (December 2025 context)
- **What This Means for Traders**: FX volatility, carry trades, cross-asset reactions

### 3. **Professional Content Sections**
- **Key Insights**: Bullet points about the indicator
- **Indicator Overview**: Detailed explanation
- **How It's Measured**: Methodology
- **Currency & Market Impact**: Trading implications
- **Current Policy Context**: Real-world context
- **Trader Implications**: Actionable insights

### 4. **Content Highlighting**
- `[[text]]` markers for red underline highlighting
- Parsed by `renderHighlightedText()` function
- Used to emphasize important information

---

## Data Flow

```
Google Sheets
  ↓
Backend Service (_transform_sheet_data)
  ↓ Extracts: currentValue, chartData, chartDates, metadata
  ↓
API Response
  ↓
Frontend (mergeIndicatorData)
  ↓ Merges: Google Sheets data + Placeholder descriptions
  ↓
Final Indicator Object
  ↓
Rendered Card
  - Description: FROM CODEBASE (placeholder)
  - Current Value: FROM GOOGLE SHEETS
  - Chart Data: FROM GOOGLE SHEETS
  - Trading Analysis: FROM CODEBASE (indicatorDetails)
```

---

## Merge Logic Confirmation

**Current Implementation:**
```javascript
description: placeholderIndicator.description  // ALWAYS from codebase
currentValue: realData.currentValue || placeholderIndicator.currentValue  // From Google Sheets
chartData: normalizedCollapsed  // From Google Sheets
```

**Result:**
- ✅ Descriptions: Always from codebase
- ✅ Values: From Google Sheets (with fallback)
- ✅ Charts: From Google Sheets data
- ✅ Trading Analysis: Always from codebase (`indicatorDetails`)

---

## Why This Design?

### Benefits:
1. **Separation of Concerns**: Data (Google Sheets) vs Content (Codebase)
2. **Consistency**: All descriptions are professional and consistent
3. **Maintainability**: Update descriptions in one place (codebase)
4. **Flexibility**: Can update data without touching content
5. **Quality Control**: Professional content written once, used everywhere

### Google Sheets Role:
- **Data Entry**: Easy for non-technical users to update values
- **Historical Data**: Maintain time series data
- **No Content Management**: No need to write descriptions in sheets

---

## Confirmation

**Yes, you are correct:**

- ✅ Google Sheets = Data and values only
- ✅ Codebase = All descriptions, trading analysis, professional content
- ✅ Google Sheets descriptions are ignored (we always use codebase descriptions)
- ✅ Trading analysis comes from `indicatorDetails` dictionary in the component

This ensures that all professional content, descriptions, and trading insights are maintained in the codebase, while Google Sheets serves purely as a data source for updating values and historical data points.

