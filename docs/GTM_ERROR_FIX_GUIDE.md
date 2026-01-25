# GTM Preview Errors - Quick Fix Guide

## Errors You're Seeing

1. ❌ `DL - Funnel Step Number` - Unknown variable
2. ❌ `DL - Conversion Type` - Unknown variable  
3. ❌ `DL - Conversion Value` - Unknown variable

## Quick Fix (2 Options)

### Option 1: Create the Missing Variables (Recommended - 5 minutes)

This is the easiest fix. Just create the missing variables in GTM:

#### Step 1: Create `DL - Funnel Step Number`

1. Go to **Variables** → **New**
2. **Variable Name**: `DL - Funnel Step Number`
3. **Variable Type**: `Data Layer Variable`
4. **Data Layer Variable Name**: `funnel_step_number`
5. Click **Save**

#### Step 2: Create `DL - Conversion Type` (Optional)

1. Go to **Variables** → **New**
2. **Variable Name**: `DL - Conversion Type`
3. **Variable Type**: `Data Layer Variable`
4. **Data Layer Variable Name**: `conversion_type`
5. Click **Save**

**Note**: This variable is optional. If you don't want to track conversion_type, you can remove it from the tag instead (see Option 2).

#### Step 3: Create `DL - Conversion Value` (Optional)

1. Go to **Variables** → **New**
2. **Variable Name**: `DL - Conversion Value`
3. **Variable Type**: `Data Layer Variable`
4. **Data Layer Variable Name**: `conversion_value`
5. Click **Save**

**Note**: This variable is optional. If you don't want to track conversion_value, you can remove it from the tag instead (see Option 2).

#### Step 4: Test Again

1. Go back to **Preview** mode
2. The errors should be gone!

---

### Option 2: Remove Optional Parameters from Tags (Alternative)

If you don't want to create the conversion variables, you can remove them from the tags:

#### Fix `GA4 - Funnel Step` Tag

1. Go to **Tags** → **GA4 - Funnel Step**
2. Click **Event Parameters**
3. **Remove** the row with:
   - Parameter: `funnel_step_number`
   - Value: `{{DL - Funnel Step Number}}`
4. Click **Save**

**Note**: Actually, `funnel_step_number` IS being pushed to dataLayer, so you should create this variable (Option 1) rather than removing it.

#### Fix `GA4 - Conversion Events` Tag

1. Go to **Tags** → **GA4 - Conversion Events**
2. Click **Event Parameters**
3. **Remove** the rows with:
   - Parameter: `conversion_type` → Value: `{{DL - Conversion Type}}`
   - Parameter: `conversion_value` → Value: `{{DL - Conversion Value}}`
4. Click **Save**

**Note**: Conversion events are currently tracked via `funnel_step` events (like `signup_completion`, `payment_success`), so these parameters are optional.

---

## Recommended Solution

**Create all 3 variables** (Option 1) because:
- ✅ `funnel_step_number` is actually being pushed to dataLayer (so you need it)
- ✅ `conversion_type` and `conversion_value` might be useful later
- ✅ Takes only 5 minutes
- ✅ No need to modify tags

---

## After Fixing

1. Go back to **Preview** mode
2. Navigate through your site
3. Check **Tags Fired** - all tags should fire without errors
4. Check **Data Layer** - you should see the variables populated

---

## Still Having Issues?

If errors persist:
1. Make sure you **saved** the variables
2. **Refresh** the Preview mode
3. Check variable names match exactly (case-sensitive)
4. Verify dataLayer variable names match what's in the code

