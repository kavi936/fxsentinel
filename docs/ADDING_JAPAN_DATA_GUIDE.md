# Guide: Adding Japan (JPY) Economic Indicator Data

## Overview

This guide will help you add real economic data for Japan. You'll create CSV files similar to the US data, then use the parser script to convert them to JSON format.

---

## Japan Indicators to Add

Based on the placeholder data, Japan has **6 indicators**:

1. **Interest Rate** (`interest-rate`) - BoJ Policy Rate
2. **Inflation (CPI)** (`inflation-YoY`) - Consumer Price Index
3. **GDP Growth** (`gdp-growth`) - Quarterly GDP growth
4. **Unemployment** (`unemployment`) - Unemployment rate
5. **Consumer Confidence** (`consumer-confidence`) - Consumer confidence index
6. **Trade Balance** (`trade-balance`) - Trade surplus/deficit

---

## CSV File Format

Create CSV files in `/data/raw/` with this naming convention:
- `Economies_Indicators - Japan Interest Rates.csv`
- `Economies_Indicators - Japan Inflation.csv`
- `Economies_Indicators - Japan GDP Growth Rate.csv`
- `Economies_Indicators - Japan Unemployment Rate.csv`
- `Economies_Indicators - Japan Consumer Confidence.csv`
- `Economies_Indicators - Japan Trade Balance.csv`

### CSV Structure

**Header Row (required):**
```csv
indicator_country,indicator_name,unit,current value,date_of_release,release_value
```

**Data Rows:**
```csv
JP,Interest Rate,%,0.50,"December 10, 2025",0.50
,,,,"November 30, 2025",0.25
,,,,"October 29, 2025",0.25
,,,,"September 17, 2025",0.10
```

**Important Notes:**
- First row: Full data with country, indicator name, unit, current value, and date
- Subsequent rows: Only `date_of_release` and `release_value` (other columns can be empty)
- Country code: Use `JP` for Japan
- Dates: Can be "December 10, 2025", "September, 2025", or "Q2, 2025" format
- Values: Numeric only (no % or K symbols in the value column)

### Example: Interest Rate CSV

```csv
indicator_country,indicator_name,unit,current value,date_of_release,release_value
JP,Interest Rate,%,0.50,"December 10, 2025",0.50
,,,,"November 30, 2025",0.25
,,,,"October 29, 2025",0.25
,,,,"September 17, 2025",0.10
,,,,"August 31, 2025",0.10
,,,,"July 30, 2025",0.10
```

### Example: Inflation CSV

```csv
indicator_country,indicator_name,unit,current value,date_of_release,release_value
JP,Inflation Rate YOY,%,2.8,"September 1, 2025",2.8
,,,,"August 1, 2025",2.7
,,,,"July 1, 2025",2.6
,,,,"June 1, 2025",2.5
```

---

## Step-by-Step Process

### Step 1: Create CSV Files

1. Open Google Sheets (or Excel)
2. Create a new sheet for each indicator
3. Add the header row
4. Fill in historical data (oldest to newest, or newest to oldest - parser handles sorting)
5. Export as CSV
6. Save to `/data/raw/` with the naming convention above

### Step 2: Run the Parser Script

For each CSV file, run:

```bash
cd /Users/kavi/Desktop/fxsentinel
python3 scripts/parse_economy_csv.py "data/raw/Economies_Indicators - Japan Interest Rates.csv"
```

The script will:
- Parse the CSV
- Convert dates to ISO format
- Extract all historical data points
- Generate JSON output
- Print the result to console

### Step 3: Merge into economyIndicators.json

The parser outputs JSON in this format:

```json
{
  "JP": {
    "indicators": {
      "interest-rate": {
        "currentValue": "0.50%",
        "asOf": "2025-12-10",
        "chartData": [0.1, 0.1, 0.1, 0.25, 0.25, 0.50],
        "chartDates": ["2024-09-17", "2024-10-29", "2024-11-30", "2025-12-10"],
        ...
      }
    }
  }
}
```

**To merge:**
1. Copy the JSON output from the parser
2. Open `/src/data/economyIndicators.json`
3. Add or update the `JP` section
4. Merge indicators into the existing structure

**Or use this command to merge automatically:**

```bash
# After parsing, the script can merge automatically
# Check the parser script for merge functionality
```

---

## Data Sources for Japan

### Recommended Sources:

1. **Bank of Japan (BoJ)**
   - Interest Rates: https://www.stat-search.boj.or.jp/
   - Policy decisions and rates

2. **Statistics Bureau of Japan**
   - CPI/Inflation: https://www.stat.go.jp/english/data/cpi/
   - GDP: https://www.esri.cao.go.jp/en/sna/
   - Unemployment: https://www.stat.go.jp/english/data/roudou/

3. **Ministry of Finance**
   - Trade Balance: https://www.customs.go.jp/toukei/info/index_e.htm

4. **Cabinet Office**
   - Consumer Confidence: https://www.esri.cao.go.jp/en/stat/shouhi/shouhi.html

---

## Indicator-Specific Notes

### Interest Rate (BoJ Policy Rate)
- **Unit:** %
- **Frequency:** Irregular (BoJ meetings)
- **Format:** Decimal (e.g., 0.50, 0.25, 0.10)
- **Note:** Japan has historically very low/negative rates

### Inflation (CPI YoY)
- **Unit:** %
- **Frequency:** Monthly
- **Format:** Percentage (e.g., 2.8, 2.7)
- **Note:** Japan has struggled with deflation historically

### GDP Growth
- **Unit:** %
- **Frequency:** Quarterly
- **Format:** Percentage (can be negative)
- **Date Format:** Use "Q2, 2025" or "May 15, 2025" format

### Unemployment Rate
- **Unit:** %
- **Frequency:** Monthly
- **Format:** Percentage (e.g., 2.6, 2.7)
- **Note:** Japan typically has very low unemployment

### Consumer Confidence
- **Unit:** Index
- **Frequency:** Monthly
- **Format:** Numeric (e.g., 36.2, 38.5)
- **Note:** Not a percentage - just a number

### Trade Balance
- **Unit:** Yen (¥) or Trillions (T)
- **Frequency:** Monthly
- **Format:** Can be positive (surplus) or negative (deficit)
- **Note:** Format as "+¥1.2T" or "-¥500B" in currentValue

---

## Quick Start Template

Here's a template you can copy for each indicator:

```csv
indicator_country,indicator_name,unit,current value,date_of_release,release_value
JP,[INDICATOR NAME],%,[CURRENT VALUE],"December 10, 2025",[CURRENT VALUE]
,,,,"November 30, 2025",[PREVIOUS VALUE]
,,,,"October 29, 2025",[PREVIOUS VALUE]
```

Replace:
- `[INDICATOR NAME]` with the actual name (e.g., "Interest Rate", "Inflation Rate YOY")
- `[CURRENT VALUE]` with the latest value
- `[PREVIOUS VALUE]` with historical values

---

## Testing

After adding data:

1. **Check JSON structure:**
   ```bash
   python3 -m json.tool src/data/economyIndicators.json | grep -A 10 '"JP"'
   ```

2. **Test in app:**
   - Select "Japan" from economy dropdown
   - Verify all 6 indicators show data
   - Check charts render correctly
   - Expand cards to see full data

---

## Troubleshooting

### Parser Errors

**Error: "Could not parse date"**
- Check date format matches examples
- Use full dates: "December 10, 2025"
- Or month-year: "September, 2025"
- Or quarter: "Q2, 2025"

**Error: "ValueError: could not convert string to float"**
- Remove % symbols from value column
- Remove K, T, B suffixes (add those in description/formatting)
- Ensure values are numeric only

**Error: "Country code mismatch"**
- Use `JP` (not `JPY` or `Japan`)
- Check first row has correct country code

### Data Not Showing

- Verify JSON structure matches US data format
- Check indicator IDs match placeholder IDs:
  - `interest-rate` (not `interest-rate-jp`)
  - `inflation-YoY` (not `inflation`)
  - etc.
- Ensure `chartData` and `chartDates` arrays have same length
- Check browser console for errors

---

## Next Steps After Adding Japan

1. ✅ Test all indicators display correctly
2. ✅ Verify charts render with proper data
3. ✅ Check expanded modal shows full history
4. ✅ Add professional descriptions (similar to US indicators)
5. ✅ Consider adding more historical data points

---

## Need Help?

If you encounter issues:
1. Check the US CSV files as reference
2. Compare your JSON structure with US data
3. Review parser script output for errors
4. Test with one indicator first before adding all

Good luck! 🚀

