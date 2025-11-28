---
description: Implement core production features (AI integration, chat UI, lead detail, email notifications)
---

1. **Backend – Connect Real AI Models**
   - Replace mock calls in `backend/app/model_manager.py` with actual Ollama client usage.
   - Install Ollama Python client (`pip install ollama`).
   - Add environment variables `OLLAMA_HOST` and `DEFAULT_MODEL`.
   - Update `ModelManager.get_available_models` to query Ollama.
   - Update `ModelManager.generate` to call `ollama_client.generate`.
   - Write unit tests for real integration (see `backend/tests/test_real_models.py`).

2. **Frontend – Build Real‑Time Chat Component**
   - Create `src/components/Chat.tsx` using React hooks and SSE (`EventSource`).
   - Add UI with glassmorphic styling, smooth scroll, and typing animation.
   - Connect to `/api/chat` endpoint via `fetch` with `EventSource` for streaming responses.
   - Update `src/pages/index.tsx` to include `<Chat />`.
   - Ensure Tailwind is not used; use vanilla CSS with `src/App.css` for modern design.

3. **Frontend – Lead Detail Page**
   - Add route `src/pages/leads/[id].tsx` (React Router v6).
   - Fetch lead data from `/api/leads/{id}`.
   - Display editable fields (name, email, status) with inline save.
   - Add “Delete” button with confirmation modal.
   - Style with premium dark‑mode palette.

4. **Backend – Lead Detail Endpoints**
   - In `backend/app/lead_router.py` create `GET /leads/{id}` and `PUT /leads/{id}`.
   - Use Supabase client for DB operations.
   - Add validation via Pydantic models.
   - Add unit tests (`backend/tests/test_lead_routes.py`).

5. **Backend – Basic Email Notifications**
   - Create `backend/app/email.py` with a simple wrapper around `smtplib` or use **SendGrid**.
   - Add function `send_email(to, subject, body)`.
   - Load SMTP credentials from env vars.
   - Hook into key actions (lead creation, lead status change, successful chat completion) by calling `send_email`.
   - Write tests mocking SMTP (`backend/tests/test_email.py`).

6. **Run‑time Checks**
   - Add health‑check endpoint `/health` that verifies Ollama connectivity and DB pool.
   - Update CI pipeline to run lint, type‑check, and integration tests.

7. **Documentation**
   - Update `README.md` with new setup steps (install Ollama, env vars).
   - Add API docs notes for new endpoints.

---
**Next Actions**
- Approve creation of the above files.
- Let me know if you want me to scaffold any of the components now.
