# Height Constraint Analysis - 400px Minimum

## Current State
- CSS `min-height: 400px` set for Prediction Markets and Central Bank cards
- JavaScript enforcing 400px minimum via `getCardHeight()`

## Potential Constraints Preventing Growth

### 1. JavaScript Constraints

**`getCardHeight()` function** (Line 1047-1057):
```javascript
const getCardHeight = (col, row) => {
  const calculatedHeight = getRowHeight(col, row) * BASE_CONTAINER_HEIGHT;
  const absoluteMinimums = {
    0: 150, // Row 1
    1: 150, // Row 2
    2: 400  // Row 3 - MINIMUM enforced
  };
  return Math.max(absoluteMinimums[row] || 150, calculatedHeight);
};
```

**Issue**: This only enforces MINIMUM, not maximum. Cards should be able to grow larger.

**`getRowHeight()` clamping** (Line 1036-1043):
```javascript
const getRowHeight = (col, row) => {
  const height = rowHeights[col]?.[row] ?? 1/3;
  const minHeight = row === 2 ? 0.4 : 0.15; // Row 3: 40% minimum
  return Math.max(minHeight, Math.min(0.9, height)); // MAX 90%!
};
```

**Potential Issue**: Maximum is clamped to 90% of BASE_CONTAINER_HEIGHT (600px) = 540px max
- If rowHeights[col][2] > 0.9, it gets clamped to 0.9
- 0.9 * 600px = 540px maximum
- But with 400px minimum, cards can grow between 400px-540px

### 2. Container Height Constraints

**Container calculation** (Line 1272-1287):
```javascript
const row3MaxHeight = Math.max(
  400, // Minimum
  Math.max(rowHeights[0]?.[2], rowHeights[1]?.[2]) * BASE_CONTAINER_HEIGHT
);
```

**Issue**: Container uses `Math.max()` of both columns, but individual cards use their own column's height.

**Example Scenario**:
- rowHeights[0][2] = 0.5 (50% = 300px) → clamped to 0.9 → 540px → enforced to 400px ✅
- rowHeights[1][2] = 0.3 (30% = 180px) → clamped to 0.4 → 240px → enforced to 400px ✅
- Container: Math.max(400, Math.max(0.5, 0.3) * 600) = Math.max(400, 300) = 400px

**Problem**: If both cards need to be 400px, but rowHeights are small, the container might not be tall enough!

### 3. BASE_CONTAINER_HEIGHT Limitation

**BASE_CONTAINER_HEIGHT = 600px** (Line 994)

**Issue**: All calculations are based on 600px base. If cards need to be larger:
- 90% max = 540px (with 400px minimum, range is 400-540px)
- If user wants cards larger than 540px, they're constrained!

### 4. CSS Constraints

**Container CSS** (Line 3205-3206):
```css
.overview-grid-container {
  min-height: 600px;
  max-height: 2000px; /* Should be fine */
}
```

**Card CSS**: No max-height set, so CSS isn't limiting growth.

## Root Cause Analysis

The issue is likely:

1. **Row heights are too small**: If `rowHeights[0][2]` or `rowHeights[1][2]` is small (e.g., 0.2 = 20%), even with 400px minimum enforcement, the container might not allocate enough space.

2. **90% maximum clamp**: Cards can't exceed 540px (90% of 600px base) even if user wants larger cards.

3. **Container height calculation**: Uses max of both columns, but if both are small, container might be too small.

## Solution

### Option 1: Increase BASE_CONTAINER_HEIGHT
- Change from 600px to 800px or 1000px
- Allows cards to grow larger (90% of 800px = 720px max)

### Option 2: Remove/Increase 90% Maximum Clamp
- Change `Math.min(0.9, height)` to `Math.min(1.0, height)` or remove max
- Allows cards to use 100% of container height if needed

### Option 3: Ensure Container Height Accounts for Minimums
- Container should always be at least: 150 + 15 + 150 + 15 + 400 = 730px
- Current calculation should handle this, but verify

### Option 4: Check localStorage Data
- If rowHeights are corrupted/small, reset to defaults
- Default: [1/3, 1/3, 1/3] = 33.33% each = 200px at 600px base
- With 400px minimum, this should work, but if data is corrupted, cards might be stuck

## Recommended Fix

1. **Increase BASE_CONTAINER_HEIGHT** to 800px or 1000px
2. **Remove 90% maximum clamp** or increase to 95%
3. **Ensure container height calculation** always accounts for 400px minimum for row 3
4. **Add validation** to detect and fix small rowHeights values
