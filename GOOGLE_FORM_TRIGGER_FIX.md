# Google Form Trigger Not Working - Fix Guide

## Problem
- Manual `testWebhook()` works ✅
- Actual form submission doesn't trigger the webhook ❌
- Records created but never updated (IDs 15, 16, 17)

## Root Cause
The `onFormSubmit` trigger is either:
1. Not installed properly
2. Not linked to the correct form
3. Using the wrong function name

---

## ✅ Solution: Reinstall the Trigger

### Step 1: Delete Old Triggers

1. In Google Apps Script editor, click **⏰ Triggers** (clock icon on left sidebar)
2. You'll see a list of triggers
3. **Delete ALL triggers** (click the 3 dots → Delete for each one)

### Step 2: Verify Function Name

In your script, make sure you have:

```javascript
function onFormSubmit(e) {
  // Your code here
}
```

**NOT** `onFormSubmitTest` or any other name!

### Step 3: Reinstall Trigger Manually

**Option A: Use setupTrigger() function**

1. Make sure your script has this function:
```javascript
function setupTrigger() {
  // Delete existing triggers
  var triggers = ScriptApp.getProjectTriggers();
  for (var i = 0; i < triggers.length; i++) {
    ScriptApp.deleteTrigger(triggers[i]);
  }
  
  // Create new trigger
  var form = FormApp.getActiveForm();
  ScriptApp.newTrigger('onFormSubmit')
    .forForm(form)
    .onFormSubmit()
    .create();
  
  Logger.log('Trigger installed successfully!');
}
```

2. Run `setupTrigger()` from the script editor
3. Authorize when prompted

**Option B: Manual trigger setup**

1. Click **⏰ Triggers** (clock icon)
2. Click **+ Add Trigger** (bottom right)
3. Configure:
   - **Function**: `onFormSubmit`
   - **Event source**: From form
   - **Event type**: On form submit
4. Click **Save**
5. Authorize if prompted

### Step 4: Verify Trigger is Installed

1. Click **⏰ Triggers**
2. You should see:
   - **Function**: `onFormSubmit`
   - **Event source**: From form
   - **Event type**: On form submit
   - **Status**: Enabled

---

## 🧪 Test After Installing Trigger

1. **Submit the Google Form** (don't run testWebhook manually)
2. **Check Flask logs** - you should see:
   ```
   127.0.0.1 - - [timestamp] "POST /api/forms/webhook HTTP/1.1" 200 -
   ```
3. **Check database** - the record should be updated with responses

---

## 🔍 Debug: Check Execution Log

If it still doesn't work:

1. In Google Apps Script, click **⚙️ Executions** (left sidebar)
2. Submit the form
3. Check if `onFormSubmit` appears in the execution log
4. If it appears with errors, click it to see the error message
5. If it doesn't appear at all, the trigger is not installed

---

## Common Issues

### Issue 1: Wrong Function Name
- ❌ `function onFormSubmitTest(e)`
- ✅ `function onFormSubmit(e)`

### Issue 2: Multiple Triggers
- Delete all old triggers before creating new one

### Issue 3: Wrong Form
- Make sure the trigger is on the CORRECT form
- If you have multiple forms, the trigger might be on the wrong one

### Issue 4: Authorization Not Granted
- When you run `setupTrigger()`, you MUST authorize
- Click "Review Permissions" → Choose your account → Allow

---

## ✅ Expected Behavior After Fix

1. User submits Google Form
2. `onFormSubmit(e)` automatically runs
3. Script sends POST to webhook
4. Flask receives webhook
5. Database record updated
6. AI summary generated
7. Notifications sent

---

## Current Webhook URL

```
https://warm-windows-fetch.loca.lt/api/forms/webhook
```

Make sure this is in your script!
