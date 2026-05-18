/**
 * Google Apps Script - Form Submit Webhook
 * 
 * HOW TO SET UP:
 * 1. Open your Google Form → click 3 dots → "Script editor"
 * 2. Paste this entire script
 * 3. Replace WEBHOOK_URL with your actual public URL
 * 4. Click "Save" → Run → "setupTrigger" to install the trigger
 * 5. Authorize when prompted
 *
 * FORM FIELD MAPPING:
 * Your Google Form must have these exact question titles (case-insensitive):
 *   - "Phone Number"
 *   - "Patient Name"
 *   - "How are you feeling today?"
 *   - "Are you experiencing shortness of breath?"
 *   - "Did you attend your dialysis session?"
 *   - "Are you taking your medications regularly?"
 *   - "Have you scheduled your nephrology follow-up?"
 *   - "Additional Notes" (optional)
 */

// ✏️ Replace with your public URL (ngrok / localtunnel / production)
var WEBHOOK_URL = "https://stale-places-speak.loca.lt/api/forms/webhook";

/**
 * Triggered automatically every time the form is submitted.
 * DO NOT RUN THIS MANUALLY - it will fail because 'e' is undefined.
 * Instead, submit the actual form to test.
 */
function onFormSubmit(e) {
  try {
    if (!e || !e.response) {
      Logger.log("ERROR: This function must be triggered by a form submission, not run manually!");
      return;
    }
    
    var responses = e.response.getItemResponses();
    var responseData = {};

    // Map each question title to a clean key
    var fieldMap = {
      "phone number": "patient_phone",
      "patient name": "patient_name",
      "how are you feeling today?": "feeling_today",
      "are you experiencing shortness of breath?": "shortness_of_breath",
      "did you attend your dialysis session?": "dialysis_attended",
      "are you taking your medications regularly?": "medications_taken",
      "have you scheduled your nephrology follow-up?": "followup_scheduled",
      "additional notes": "additional_notes"
    };

    responses.forEach(function(itemResponse) {
      var title = itemResponse.getItem().getTitle().toLowerCase().trim();
      var answer = itemResponse.getResponse();
      var key = fieldMap[title] || title.replace(/\s+/g, '_');
      responseData[key] = answer;
    });

    // Build the payload for your API
    var patientPhone = responseData["patient_phone"] || "";
    var patientName = responseData["patient_name"] || "";

    // Remove patient_phone and patient_name from responses (they go to top level)
    delete responseData["patient_phone"];
    delete responseData["patient_name"];

    var payload = {
      patient_phone: patientPhone,
      patient_name: patientName,
      submitted_at: new Date().toISOString(),
      responses: responseData
    };

    // POST to your webhook
    var options = {
      method: "post",
      contentType: "application/json",
      payload: JSON.stringify(payload),
      muteHttpExceptions: true
    };

    var response = UrlFetchApp.fetch(WEBHOOK_URL, options);
    Logger.log("Webhook response: " + response.getContentText());

  } catch (error) {
    Logger.log("Error sending to webhook: " + error.toString());
  }
}

/**
 * Run this function ONCE to set up the automatic trigger.
 * Go to Run → setupTrigger
 */
function setupTrigger() {
  // Remove existing triggers to avoid duplicates
  var triggers = ScriptApp.getProjectTriggers();
  triggers.forEach(function(trigger) {
    if (trigger.getHandlerFunction() === "onFormSubmit") {
      ScriptApp.deleteTrigger(trigger);
    }
  });

  // Create new form submit trigger
  var form = FormApp.getActiveForm();
  ScriptApp.newTrigger("onFormSubmit")
    .forForm(form)
    .onFormSubmit()
    .create();

  Logger.log("✅ Trigger set up successfully! Every form submission will now POST to: " + WEBHOOK_URL);
}

/**
 * Manual test function - Run this to verify webhook is reachable.
 * This sends a test payload to your webhook.
 */
function testWebhook() {
  var testPayload = {
    patient_phone: "+919715441374",
    patient_name: "Test Patient",
    submitted_at: new Date().toISOString(),
    responses: {
      feeling_today: "Good",
      shortness_of_breath: "No",
      dialysis_attended: "Yes",
      medications_taken: "Yes",
      followup_scheduled: "Yes",
      additional_notes: "This is a manual test from Apps Script"
    }
  };

  var options = {
    method: "post",
    contentType: "application/json",
    payload: JSON.stringify(testPayload),
    muteHttpExceptions: true
  };

  try {
    var response = UrlFetchApp.fetch(WEBHOOK_URL, options);
    var statusCode = response.getResponseCode();
    var responseText = response.getContentText();
    
    Logger.log("✅ Test webhook response:");
    Logger.log("Status Code: " + statusCode);
    Logger.log("Response: " + responseText);
    
    if (statusCode === 200) {
      Logger.log("✅ SUCCESS! Webhook is working correctly.");
    } else {
      Logger.log("❌ FAILED! Status code: " + statusCode);
    }
  } catch (error) {
    Logger.log("❌ ERROR connecting to webhook: " + error.toString());
    Logger.log("Check if the URL is correct: " + WEBHOOK_URL);
  }
}
