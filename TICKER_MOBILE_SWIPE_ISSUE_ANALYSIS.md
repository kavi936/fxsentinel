# Market Ticker Mobile Swipe Issue - Root Cause Analysis

## Problem Statement
Users cannot swipe left and right on the market ticker pairs container on mobile devices. The horizontal scrolling/swiping functionality is not working.

---

## Root Cause Analysis

### Issue #1: Parent Container Blocks Scrolling
**Severity**: Critical  
**Location**: `Overview.css` line 2349

**Problem**:
The parent container `.market-ticker` has `overflow-x: hidden`, which prevents the child `.ticker-pairs-inline` from scrolling horizontally.

**Code Reference**:
```css
.market-ticker {
  /* ... other styles ... */
  overflow-x: hidden; /* ❌ This blocks child scrolling */
  overflow-y: hidden;
  /* Mobile touch support */
  touch-action: pan-x; /* ⚠️ This is on parent, not child */
}
```

**Why This Breaks Scrolling**:
- When a parent has `overflow-x: hidden`, it creates a clipping context
- The child `.ticker-pairs-inline` has `overflow-x: auto`, but the parent's `overflow-x: hidden` prevents the overflow from being visible
- The child cannot scroll because the parent clips the overflow

---

### Issue #2: Mobile-Specific Styles Override
**Severity**: Critical  
**Location**: `Overview.css` lines 2964, 2994

**Problem**:
Mobile media queries explicitly set `overflow-x: hidden` on `.market-ticker`, which completely blocks scrolling on mobile devices.

**Code Reference**:
```css
@media (max-width: 768px) {
  .market-ticker {
    /* ... */
    overflow-x: hidden; /* ❌ Explicitly blocks scrolling on mobile */
    touch-action: pan-x;
  }
}

@media (max-width: 480px) {
  .market-ticker {
    /* ... */
    overflow-x: hidden; /* ❌ Blocks scrolling on small mobile */
    touch-action: pan-x;
  }
}
```

**Impact**:
- These mobile-specific styles override the base styles
- Even if we fix the base styles, these mobile styles will still block scrolling
- This is the primary reason scrolling doesn't work on mobile

---

### Issue #3: Touch Action on Wrong Element
**Severity**: Medium  
**Location**: `Overview.css` lines 2354, 2965, 2995

**Problem**:
`touch-action: pan-x` is set on the parent `.market-ticker` instead of the scrollable child `.ticker-pairs-inline`.

**Code Reference**:
```css
.market-ticker {
  touch-action: pan-x; /* ⚠️ Should be on child, not parent */
}

.ticker-pairs-inline {
  touch-action: pan-x; /* ✅ This is correct */
}
```

**Why This Matters**:
- `touch-action` should be on the element that actually scrolls
- Having it on the parent may cause touch events to be handled incorrectly
- The child already has `touch-action: pan-x`, so the parent doesn't need it

---

### Issue #4: Flex Container Width Constraint
**Severity**: Low  
**Location**: `Overview.css` line 2390

**Problem**:
`.ticker-pairs-inline` has `flex: 1`, which makes it shrink to fit the container. Combined with `width: max-content` (line 2402), this creates a conflict.

**Code Reference**:
```css
.ticker-pairs-inline {
  flex: 1; /* Makes it shrink to fit */
  /* ... */
  width: max-content; /* Makes it expand to content */
}
```

**Impact**:
- The flex container may constrain the width
- The `width: max-content` may not work as expected in a flex context
- This could prevent the content from overflowing and triggering scroll

---

## Current CSS Structure

```
.market-ticker-container (no overflow restrictions)
  └── .market-ticker (overflow-x: hidden ❌)
      ├── .ticker-edit-btn
      └── .ticker-pairs-inline (overflow-x: auto ✅, but blocked by parent)
          └── .ticker-pair-inline (multiple pairs)
```

---

## Solution

### Fix #1: Remove overflow-x: hidden from Parent
**Location**: `Overview.css` line 2349

**Change**:
```css
.market-ticker {
  /* ... */
  overflow-x: visible; /* ✅ Allow child to scroll */
  overflow-y: hidden; /* Keep vertical hidden */
  /* Remove touch-action from parent */
}
```

### Fix #2: Remove Mobile-Specific overflow-x: hidden
**Location**: `Overview.css` lines 2964, 2994

**Change**:
```css
@media (max-width: 768px) {
  .market-ticker {
    /* ... */
    overflow-x: visible; /* ✅ Allow scrolling on mobile */
    /* Remove touch-action: pan-x from parent */
  }
}

@media (max-width: 480px) {
  .market-ticker {
    /* ... */
    overflow-x: visible; /* ✅ Allow scrolling on small mobile */
    /* Remove touch-action: pan-x from parent */
  }
}
```

### Fix #3: Ensure Child Can Scroll
**Location**: `Overview.css` lines 2386-2407

**Verify** (already correct):
```css
.ticker-pairs-inline {
  overflow-x: auto; /* ✅ Correct */
  touch-action: pan-x; /* ✅ Correct */
  -webkit-overflow-scrolling: touch; /* ✅ Correct for iOS */
  overscroll-behavior-x: contain; /* ✅ Correct */
}
```

### Fix #4: Ensure Proper Width
**Location**: `Overview.css` line 2402

**Verify**:
- `width: max-content` ensures content expands beyond container
- `flex: 1` allows it to shrink, but content width takes precedence
- This should work correctly once parent overflow is fixed

---

## Complete Fix Implementation

### Base Styles (Desktop)
```css
.market-ticker {
  background: transparent;
  border-radius: 20px;
  padding: 0 16px;
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 16px;
  box-shadow: none;
  border: 1px solid rgba(255, 255, 255, 0.1);
  position: relative;
  overflow-x: visible; /* ✅ Changed from hidden */
  overflow-y: hidden;
  height: 50px;
  border-bottom: 1px solid rgba(51, 51, 51, 0.3);
  /* ✅ Removed touch-action: pan-x from parent */
}
```

### Mobile Styles (768px)
```css
@media (max-width: 768px) {
  .market-ticker {
    height: auto;
    min-height: 50px;
    padding: 10px 16px;
    overflow-x: visible; /* ✅ Changed from hidden */
    /* ✅ Removed touch-action: pan-x from parent */
  }
  
  .ticker-pairs-inline {
    /* ✅ Already correct - keep these */
    -webkit-overflow-scrolling: touch;
    touch-action: pan-x;
    overscroll-behavior-x: contain;
  }
}
```

### Small Mobile Styles (480px)
```css
@media (max-width: 480px) {
  .market-ticker {
    padding: 8px 12px;
    overflow-x: visible; /* ✅ Changed from hidden */
    /* ✅ Removed touch-action: pan-x from parent */
  }
  
  .ticker-pairs-inline {
    /* ✅ Already correct - keep these */
    -webkit-overflow-scrolling: touch;
    touch-action: pan-x;
    overscroll-behavior-x: contain;
  }
}
```

---

## Testing Checklist

After implementing the fix:

- [ ] Test horizontal swipe on iOS Safari
- [ ] Test horizontal swipe on Android Chrome
- [ ] Test horizontal swipe on Android Firefox
- [ ] Verify scrolling works smoothly with momentum
- [ ] Verify no vertical scrolling occurs when swiping horizontally
- [ ] Verify edit button still works
- [ ] Verify ticker pairs display correctly
- [ ] Test on various screen sizes (320px, 375px, 414px, 768px)
- [ ] Verify no horizontal page scroll occurs when swiping ticker
- [ ] Test with many pairs (10+ pairs) to ensure scrolling is needed

---

## Additional Considerations

### Why overflow-x: visible Works
- `visible` allows the child's overflow to be visible and scrollable
- The child `.ticker-pairs-inline` handles the scrolling with `overflow-x: auto`
- The parent doesn't need to clip horizontally since the child handles it

### Why Remove touch-action from Parent
- `touch-action: pan-x` should be on the scrollable element (`.ticker-pairs-inline`)
- Having it on the parent may cause conflicts
- The child already has the correct `touch-action` settings

### Why This Architecture Works
```
Parent (.market-ticker): 
  - overflow-x: visible (allows child overflow)
  - overflow-y: hidden (prevents vertical overflow)
  - No touch-action (child handles it)

Child (.ticker-pairs-inline):
  - overflow-x: auto (creates scrollable area)
  - touch-action: pan-x (allows horizontal panning)
  - -webkit-overflow-scrolling: touch (iOS momentum)
  - overscroll-behavior-x: contain (prevents scroll chaining)
```

---

## Summary

**Root Cause**: The parent container `.market-ticker` has `overflow-x: hidden` which blocks the child `.ticker-pairs-inline` from scrolling horizontally. This is especially problematic on mobile where media queries explicitly set `overflow-x: hidden`.

**Solution**: 
1. Change `.market-ticker` `overflow-x` from `hidden` to `visible`
2. Remove `overflow-x: hidden` from mobile media queries
3. Remove `touch-action: pan-x` from parent (child already has it)
4. Keep all child scrolling properties as they are (already correct)

**Files to Modify**:
- `src/components/Overview.css` (lines 2349, 2964, 2994)

This fix will allow the `.ticker-pairs-inline` container to scroll horizontally on mobile devices while maintaining all other functionality.
