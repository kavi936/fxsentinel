# Prediction Markets: Archived vs Closed Markets

## Market States Explained

### **Closed Markets** (`closed=True`)

**What it means:**
- The market has **stopped accepting new orders**
- Trading is **no longer active**
- The market may or may not be resolved yet
- **Most common state** for historical markets

**Examples:**
- A market about "Will X happen by Dec 31, 2023?" - after Dec 31, it's closed
- A sports market after the game has ended
- An election market after voting has closed

**In CLOB API:**
- `closed: True` or `closed: "True"` (string boolean)
- Often paired with `active: True` (market exists in system but trading closed)

### **Archived Markets** (`archived=True`)

**What it means:**
- The market has been **moved to archive** (old/historical data)
- Usually markets that are **very old** (months/years old)
- May have question starting with "arch" prefix
- **Not accessible** for normal trading
- Used for historical data/reference

**Examples:**
- Markets from 2022 or earlier
- Markets that have been resolved for a long time
- Markets that Polymarket has archived for data management

**In CLOB API:**
- `archived: True` or `archived: "True"` (string boolean)
- Question may start with "arch" (e.g., "archWill US inflation...")

### **Active Markets** (`active=True, closed=False`)

**What it means:**
- Market is **currently accepting orders**
- Trading is **open**
- Market has **not been resolved yet**
- **This is what we want** for live trading data

**Examples:**
- "Will the Fed raise rates in Q2 2024?" (if we're in Q1 2024)
- "Will Bitcoin hit $100k by end of 2024?" (if date hasn't passed)
- Markets with future resolution dates

**In CLOB API:**
- `active: True` AND `closed: False`
- `archived: False`
- Has `end_date_iso` in the future

---

## Why CLOB API Returns Mostly Historical Markets

### **The Problem:**

After checking **5,000 markets** from the CLOB API:
- **0 markets** with `active=True, closed=False` (truly active)
- **936 markets** with `active=True, closed=True` (closed but in system)
- **Most markets** are from 2023 or earlier

### **Possible Reasons:**

1. **Default Sorting:**
   - CLOB API may sort by **volume** or **creation date** by default
   - Historical markets with high volume appear first
   - Active markets might be deeper in pagination

2. **No Filter Parameters:**
   - CLOB API doesn't seem to respect filter parameters (`active`, `closed`, `archived`)
   - All parameters return the same results
   - No way to filter for active markets via API parameters

3. **API Design:**
   - CLOB API is designed for **order book data** (prices, orders)
   - **Market discovery** might be handled by **Gamma API** instead
   - CLOB focuses on markets that have trading activity (often historical)

4. **Rate Limiting:**
   - Polymarket may prioritize **active traders** over data access
   - Historical data is easier to serve (cached)
   - Live data requires more resources

### **Is Polymarket Preventing Access?**

**Not necessarily.** More likely:

1. **Different API Purpose:**
   - **CLOB API:** For order book data (prices, orders)
   - **Gamma API:** For market discovery (finding active markets)
   - We might need to use **both APIs** together

2. **Pagination Depth:**
   - Active markets might be **deeper** in pagination
   - We'd need to fetch **many more pages** to find them
   - Not practical with rate limits

3. **Market Lifecycle:**
   - Most markets **resolve quickly** (days/weeks)
   - By the time we fetch, many are already closed
   - Active markets are a **small percentage** of total

---

## Current Solution

### **What We're Doing:**

1. **Fetch from CLOB API:**
   - Get up to 3,000 markets (3 pages)
   - Filter for forex-relevant keywords
   - Filter out archived/closed/resolved markets

2. **Relaxed Date Filtering:**
   - Show markets with **future dates** (preferred)
   - **OR** markets resolved within **last 30 days**
   - Ensures users see some data even if mostly historical

3. **Use Kalshi Markets:**
   - Kalshi (via DOME API) has more **active markets**
   - Better for finding current trading opportunities
   - Complements Polymarket data

### **Why This Works:**

- **Kalshi** provides active markets with future dates
- **Polymarket** provides historical context and volume data
- **Combined** gives users both current and historical insights

---

## Recommendations

### **To Get More Active Markets:**

1. **Use Gamma API:**
   - Try `https://gamma-api.polymarket.com/markets`
   - May have better filtering for active markets
   - Designed for market discovery

2. **Fetch More Pages:**
   - Increase `CLOB_MAX_PAGES` to 10+ (10,000 markets)
   - More likely to find active markets deeper in pagination
   - Trade-off: More API calls, slower response

3. **Combine APIs:**
   - Use **Gamma API** for market discovery (find active markets)
   - Use **CLOB API** for price/order data (get current prices)
   - Best of both worlds

4. **Focus on Kalshi:**
   - Kalshi has more active markets
   - Better for real-time trading signals
   - Polymarket for historical context

---

## Market State Combinations

| Active | Closed | Archived | Meaning |
|--------|--------|----------|---------|
| True | False | False | ✅ **Truly Active** - Open for trading |
| True | True | False | ⚠️ **Closed** - Trading stopped, not resolved |
| False | True | False | ❌ **Inactive** - Market ended |
| False | False | True | ❌ **Archived** - Old historical data |
| True | True | True | ❌ **Archived & Closed** - Historical, no trading |

---

## Summary

- **Closed Markets:** Trading stopped, but market still exists in system
- **Archived Markets:** Very old markets moved to archive
- **Active Markets:** Currently open for trading (rare in CLOB API)
- **CLOB API:** Returns mostly historical markets (by design or default sorting)
- **Solution:** Use Kalshi for active markets, Polymarket for historical context

