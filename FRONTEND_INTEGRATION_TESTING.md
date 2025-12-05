# Frontend Integration Testing Guide

## Overview
This document provides step-by-step instructions for testing the frontend integration with the backend API.

## Prerequisites
1. Backend server running on `http://localhost:8000`
2. Ollama running on `http://localhost:11434` with models loaded
3. Frontend dev server running on `http://localhost:5173`
4. Supabase instance configured (or using local mock)

## Test Scenarios

### 1. Chat Widget Integration

**Test Steps:**
1. Navigate to the homepage (`/`)
2. Click the chat widget button (bottom-right floating button)
3. Type a message: "I need help with my website"
4. Press Enter or click Send

**Expected Results:**
- ✅ Chat widget opens with welcome message
- ✅ User message appears on the right side
- ✅ Loading indicator shows while AI processes
- ✅ AI response appears on the left side within 10-30 seconds
- ✅ Response includes relevant information about PixelCraft services
- ✅ Conversation ID is maintained across messages

**API Endpoint Tested:**
- `POST /api/chat/message`

**Troubleshooting:**
- If timeout occurs, check Ollama is running: `curl http://localhost:11434/api/tags`
- Check browser console for errors
- Verify VITE_API_URL is set correctly in `.env`

---

### 2. Lead Submission & AI Analysis

**Test Steps:**
1. Navigate to homepage contact form or `/strategy-session`
2. Fill out the form with:
   - Name: "Test User"
   - Email: "test@example.com"
   - Company: "Test Corp"
   - Services: Select "Web Development"
   - Budget: "$10,000-$25,000"
   - Message: "We need a modern e-commerce platform"
3. Submit the form

**Expected Results:**
- ✅ Form submits successfully
- ✅ Success toast notification appears
- ✅ Email confirmation sent (check logs if using mock)
- ✅ Lead appears in `/dashboard/leads` (requires authentication)
- ✅ AI analysis runs automatically (check lead detail page)
- ✅ Lead score is calculated (0-100)

**API Endpoints Tested:**
- `POST /api/leads/submit`
- `POST /api/leads/{id}/analyze`

---

### 3. Leads Management (Authenticated)

**Test Steps:**
1. Navigate to `/auth` and sign in
2. Go to `/dashboard/leads`
3. Search for "Test User"
4. Click on the lead to view details
5. Change status to "Contacted"
6. Add a note: "Initial contact made"
7. Click "Run AI Analysis"

**Expected Results:**
- ✅ Leads list loads with pagination
- ✅ Search filters results correctly
- ✅ Lead detail page shows all information
- ✅ Status update saves successfully
- ✅ Note is added with timestamp
- ✅ AI analysis completes and shows:
  - Lead score
  - Priority level
  - Recommended services
  - Key insights
  - Suggested actions

**API Endpoints Tested:**
- `GET /api/leads?limit=50&offset=0`
- `GET /api/leads/{id}`
- `PATCH /api/leads/{id}`
- `POST /api/leads/{id}/analyze`

---

### 4. Appointment Booking Flow

**Test Steps:**
1. Navigate to `/strategy-session`
2. Fill out the strategy session form:
   - First Name: "John"
   - Last Name: "Doe"
   - Email: "john@example.com"
   - Company: "Acme Inc"
   - Phone: "+1234567890"
   - Goals: "Increase online sales by 50%"
   - Budget: "£5,000 - £10,000"
   - Timeline: "Within 3 months"
3. Click "Continue to Select Time"
4. Select a date (tomorrow or later)
5. Choose an available time slot
6. Click "Confirm Appointment"

**Expected Results:**
- ✅ Form validation works correctly
- ✅ Calendar shows available dates (past dates disabled)
- ✅ Time slots load for selected date
- ✅ Selected slot is highlighted
- ✅ Appointment books successfully
- ✅ Success toast appears
- ✅ Confirmation email sent (check logs)
- ✅ Form resets after booking

**API Endpoints Tested:**
- `GET /api/appointments/availability?date=YYYY-MM-DD&duration=60&timezone=UTC`
- `POST /api/appointments/book`

**Common Issues:**
- No available slots: Check that the date is in the future
- Booking fails: Verify timezone is correctly detected
- Calendar doesn't load: Check browser console for errors

---

### 5. Real-Time Notifications (WebSocket)

**Test Steps:**
1. Open two browser windows/tabs
2. Sign in to both with the same account
3. In Window 1: Navigate to `/dashboard/leads`
4. In Window 2: Submit a new lead via contact form
5. Observe Window 1 for real-time updates

**Expected Results:**
- ✅ WebSocket connection established (check browser console)
- ✅ Connection status shows "Connected" in chat widget
- ✅ New lead appears in Window 1 without refresh
- ✅ Notification badge updates in real-time
- ✅ Reconnection works after network interruption

**WebSocket Endpoint:**
- `ws://localhost:8000/api/ws/notifications`

**Debugging:**
- Check browser DevTools → Network → WS tab
- Look for WebSocket connection and messages
- Verify authentication token is sent

---

## Integration Checklist

### Backend Verification
- [ ] Backend server running (`http://localhost:8000/docs`)
- [ ] Ollama running with models loaded
- [ ] Redis running (for caching and pub/sub)
- [ ] Supabase configured or mock enabled
- [ ] All environment variables set in `backend/.env`

### Frontend Verification
- [ ] Frontend dev server running (`http://localhost:5173`)
- [ ] `VITE_API_URL` set to `http://localhost:8000`
- [ ] `VITE_SUPABASE_URL` and `VITE_SUPABASE_PUBLISHABLE_KEY` configured
- [ ] Browser console shows no CORS errors
- [ ] Authentication working (can sign in/out)

### API Integration Tests
- [ ] Chat widget sends and receives messages
- [ ] Lead submission works with AI analysis
- [ ] Leads list loads and filters correctly
- [ ] Lead detail page shows all data
- [ ] Lead updates (status, notes) save successfully
- [ ] AI re-analysis works on demand
- [ ] Appointment availability loads
- [ ] Appointment booking completes
- [ ] WebSocket connection establishes
- [ ] Real-time updates work across tabs

### UI/UX Verification
- [ ] Loading states show during API calls
- [ ] Error messages display for failed requests
- [ ] Success toasts appear after successful actions
- [ ] Forms validate input correctly
- [ ] Pagination works in lists
- [ ] Search and filters update results
- [ ] Responsive design works on mobile

---

## Performance Benchmarks

### Expected Response Times
- Chat message: 5-30 seconds (depends on Ollama model)
- Lead submission: 1-3 seconds
- Lead list load: < 1 second
- Lead detail load: < 500ms
- Appointment availability: < 1 second
- Appointment booking: 1-2 seconds
- WebSocket connection: < 500ms

### Known Limitations
- First AI request may be slow (model cold start)
- Large models (mixtral:8x7b) can take 5-10 minutes on first use
- Recommend using mistral:7b for development

---

## Troubleshooting Guide

### Chat Widget Not Responding
1. Check backend logs for errors
2. Verify Ollama is running: `curl http://localhost:11434/api/tags`
3. Check browser console for network errors
4. Verify CORS is configured correctly in backend

### Authentication Issues
1. Clear browser localStorage
2. Check Supabase credentials in `.env`
3. Verify JWT token in browser DevTools → Application → Local Storage
4. Try signing out and back in

### WebSocket Connection Fails
1. Check Redis is running: `redis-cli ping`
2. Verify WebSocket endpoint in browser DevTools
3. Check authentication token is being sent
4. Look for firewall/proxy blocking WebSocket connections

### API Calls Return 401/403
1. Verify user is signed in
2. Check authentication token in request headers
3. Ensure `authenticatedFetch` is being used
4. Verify user has correct role for protected routes

---

## Next Steps

After completing frontend integration testing:

1. **End-to-End Testing**: Run full user journeys
2. **Performance Optimization**: Profile and optimize slow endpoints
3. **Error Handling**: Test edge cases and error scenarios
4. **Mobile Testing**: Verify responsive design on actual devices
5. **Production Deployment**: Deploy to staging environment

---

## Support

For issues or questions:
- Check backend logs: `backend/logs/`
- Review API documentation: `http://localhost:8000/docs`
- See backend README: `backend/README.md`
- Review progress: `AI_INTEGRATION_PROGRESS.md`
