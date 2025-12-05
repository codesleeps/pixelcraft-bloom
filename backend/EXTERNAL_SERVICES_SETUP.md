# External Services Setup Guide

This guide explains how to configure external services (Google Calendar, SendGrid, HubSpot) for the PixelCraft backend.

## 1. Google Calendar Integration

Required for: Appointment booking and availability checks.

### Steps:
1.  **Create a Google Cloud Project:**
    *   Go to [Google Cloud Console](https://console.cloud.google.com/).
    *   Create a new project (e.g., "PixelCraft-Bloom").

2.  **Enable Google Calendar API:**
    *   In the dashboard, go to "APIs & Services" > "Library".
    *   Search for "Google Calendar API" and enable it.

3.  **Create Credentials:**
    *   Go to "APIs & Services" > "Credentials".
    *   Click "Create Credentials" > "API Key".
    *   Copy the API Key.

4.  **Get Calendar ID:**
    *   Open Google Calendar.
    *   Go to "Settings and sharing" for the calendar you want to use.
    *   Scroll down to "Integrate calendar" section.
    *   Copy the "Calendar ID" (usually your email address for the primary calendar).

5.  **Update `.env`:**
    ```env
    CALENDAR_PROVIDER=google
    CALENDAR_API_KEY=your_api_key_here
    CALENDAR_ID=your_calendar_id_here
    ```

*Note: For full write access (booking), you may need OAuth2 credentials instead of a simple API Key. The current backend supports API Key for simple operations, but for production use with user-specific calendars, OAuth2 is recommended.*

## 2. SendGrid Email Integration

Required for: Sending appointment confirmations and notifications.

### Steps:
1.  **Create SendGrid Account:**
    *   Sign up at [SendGrid](https://sendgrid.com/).

2.  **Create API Key:**
    *   Go to Settings > API Keys.
    *   Create a new key with "Full Access" or "Mail Send" permissions.
    *   Copy the API Key (you only see it once!).

3.  **Verify Sender Identity:**
    *   Go to Settings > Sender Authentication.
    *   Verify a single sender email or domain.

4.  **Update `.env`:**
    ```env
    EMAIL_PROVIDER=sendgrid
    EMAIL_API_KEY=your_sendgrid_api_key
    EMAIL_FROM=verified_sender@yourdomain.com
    ```

## 3. HubSpot CRM Integration

Required for: Syncing leads and contacts.

### Steps:
1.  **Create HubSpot Account:**
    *   Sign up at [HubSpot](https://www.hubspot.com/).

2.  **Create Private App:**
    *   Go to Settings > Integrations > Private Apps.
    *   Click "Create a private app".
    *   Name it "PixelCraft Backend".
    *   Under "Scopes", select `crm.objects.contacts` (read/write) and `crm.objects.deals` (read/write).

3.  **Get Access Token:**
    *   After creating the app, copy the "Access token".

4.  **Update `.env`:**
    ```env
    CRM_PROVIDER=hubspot
    CRM_API_KEY=your_access_token_here
    CRM_API_URL=https://api.hubapi.com
    ```

## Verification

After configuring `.env`, you can verify the integrations by running the test suite:

```bash
pytest test_external_services.py
```

*Note: The tests currently check for mock fallbacks. To test real integrations, you would need to modify the tests to use real credentials, but be careful not to spam real services during testing.*
