# Minimal security implementation report

**Date:** 18 October 2026  
**Scope:** Approved fixes from `RAG_SECURITY_PLAN.md` on the local `improve/backend-portfolio` checkout. No Git history was rewritten and no commit, push, deployment, or real data deletion was performed.

## Changes made

| Files | Change |
| --- | --- |
| `app.py` | Requires a private Flask signing key, admin email, and Werkzeug password hash at startup; checks the supplied password against the hash; clears the old session at login. Normal execution binds to `127.0.0.1` with debug off. Explicit local development is required to enable debug. Sets `HttpOnly` and `SameSite=Lax` session cookies; `Secure` is enabled with `APP_ENV=production`. Flask-WTF checks CSRF on admin POST routes while the public `/chat` API remains usable without a token. |
| `templates/login.html`, `templates/admin.html` | Adds CSRF tokens to login and upload forms and to the dynamically submitted delete form. File names in the admin list are passed through a data attribute and an event listener, avoiding an inline JavaScript string. |
| `static/js/script.js`, `templates/index.html`, `static/js/purify.min.js`, `static/js/purify.LICENSE.txt` | User messages are inserted as text. Gemini response HTML is cleaned with vendored DOMPurify 3.4.17 and a narrow list of formatting tags (`p`, `br`, `ul`, `ol`, `li`, `strong`, `em`, `b`, `i`) with no attributes. If DOMPurify is unavailable, the answer is shown as text. The library license is included. |
| `.env.example`, `README.md`, `requirements.txt`, `.gitignore` | Documents private configuration, adds Flask-WTF, and ignores local Node dependencies and temporary tests. The example contains placeholders only. |
| `package.json`, `package-lock.json`, `tests/test_security.py`, `tests/test_security_frontend.cjs` | Pins the frontend test dependencies and adds backend and browser-DOM security regression tests. |

The RAG retrieval algorithm, ChromaDB schema, and source documents were not changed. The existing chatbot, upload, and delete routes remain in place.

## Validation

Run from the repository root after installing `requirements.txt` and `npm ci`:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py" -v
npm run test:security-js
git diff --check
```

**Results in this checkout:** 8 Python tests passed; 3 JavaScript tests passed; `git diff --check` passed. Git printed only Windows line-ending warnings. The tests verified:

- Valid admin login with a private test configuration and password hash, rejection of an invalid password, and failure at startup when required security settings are absent.
- HTTP localhost cookie flags, production `Secure` cookie configuration, local bind and debug-off defaults.
- HTTP 400 for missing/invalid CSRF tokens on login, upload, and delete; successful upload and delete requests with valid tokens; public `/chat` request without a token.
- User-supplied HTML is rendered as text. Simulated malicious Gemini HTML loses active elements and attributes while simple formatting remains. Missing sanitizer falls back to inert text.
- The admin delete button constructs a POST form with a CSRF token.

The Flask tests use a stubbed chatbot/Chroma layer and a temporary upload directory under `.test-temp/`; they exercise the actual Flask routes and filesystem save/delete path without making a Gemini request or touching real documents. A full live Gemini/Chroma smoke test was **not** performed because it needs the owner's private credentials and runtime data. Likewise, jsdom verifies DOM structure and sanitization; it is not a full browser exploit test.

## Required owner configuration

1. Install the updated Python dependencies with `python -m pip install -r requirements.txt`. Copy `.env.example` to ignored `.env.local` if needed, and replace every `replace_with_...` placeholder with private values. Existing `.env.local` files also need the three new security settings; the app now fails safely until they are set.
2. Generate a new random `FLASK_SECRET_KEY`, choose a unique admin password, use Werkzeug `generate_password_hash` to make `ADMIN_PASSWORD_HASH`, and set `ADMIN_EMAIL`. The exact PowerShell commands are in `README.md`. Changing the signing key invalidates old sessions. Keep all values out of Git and screenshots.
3. For any future HTTPS deployment, set `APP_ENV=production`, supply secrets through the host environment, and run behind a production WSGI server and HTTPS. HTTP localhost should use `APP_ENV=development`; its session cookie intentionally has no `Secure` flag.
4. In the providers' dashboards, verify and revoke the two Gemini keys identified in Git history and rotate any still-active key previously shared elsewhere, including the OpenAI key mentioned in `RAG_SECURITY_PLAN.md`. Review usage if applicable. **No historical API key was revoked by this implementation.**

## Remaining risks and limits

- Previously committed credentials remain visible in Git history until the owner revokes them. This work did not change history or provider-side key state.
- `/chat` is intentionally public. It has no rate limit or request-size policy, so a publicly reachable deployment could incur Gemini usage costs or abuse. This is outside the approved minimal fix.
- The existing upload/delete flow does not provide a transaction spanning file storage and ChromaDB. The tests cover the route behavior with stubbed vector operations, not failure recovery in a real Chroma collection.
- The logout link remains a GET request; a third-party page could trigger logout, although it cannot thereby gain admin access. Changing that route and UI was outside the specified CSRF form scope.
- DOMPurify is vendored; its version should be updated when security fixes are released. The sanitizer allows only formatting tags and no attributes, which may remove links or other formatting from Gemini answers by design.
