# Local RAG smoke-test report

**Date:** 19 October 2026  
**Scope:** Local checkout only. The test used synthetic documents in an isolated temporary directory and did not modify `data/topics/` or the existing `data/chroma.sqlite3`. No Git history, commit, push, or deployment was performed.

## Configuration observed

The local environment contains a configured Gemini API key, but the required security settings introduced by the security fix are incomplete: `FLASK_SECRET_KEY`, `ADMIN_EMAIL`, and `ADMIN_PASSWORD_HASH` were not available as complete private settings. Therefore the application's real startup path would fail safely before loading the chatbot until those values are added to `.env.local` or the process environment.

For route checks only, the smoke harness supplied an ephemeral test signing key, test admin email, and randomly generated password hash in the process environment. These values were not written to disk or included in this report.

## Results

| Check | Result | Evidence / limitation |
| --- | --- | --- |
| Flask default bind and debug configuration | **Passed in application options** | `get_server_options()` returned loopback `127.0.0.1`, port `5000`, and `debug=False`; the Flask app's debug flag was false. The actual socket bind was blocked by the execution environment with `PermissionError`, so an external browser request could not be completed here. |
| Admin login | **Passed with ephemeral test credentials** | Flask test client received the CSRF token, authenticated, and reached `/admin`. This does not validate the owner's real admin password because the required private admin settings were incomplete. |
| Admin logout | **Passed** | Test client logout redirected and subsequent `/admin` access redirected to login. |
| Synthetic ChromaDB indexing | **Passed** | `src/build_database.py` created a collection in an isolated temporary `data/` directory and indexed the synthetic file. The existing project collection was not used or altered. |
| Retrieval | **Passed** | The actual Vietnamese embedding model and Chroma query returned the expected synthetic phrase from the isolated collection. The count was one before the upload route check and returned to one after deleting the uploaded test document. |
| Admin upload | **Passed** | A synthetic `.txt` file was posted through the real Flask admin route with a valid CSRF token. The file was saved in the isolated directory and its Chroma entry was created. |
| Admin deletion | **Passed** | The real delete route removed the synthetic file and its Chroma entry with a valid CSRF token. |
| Gemini request | **Blocked by network** | The local key was detected without printing it, but the request to `generativelanguage.googleapis.com` failed with `URLError` caused by DNS resolution failure. No Gemini response can be claimed. |
| Safe user/Gemini rendering | **Passed by existing regression tests** | `npm run test:security-js` passed all 3 tests: user HTML is rendered as text, malicious simulated Gemini markup is stripped by DOMPurify, and the no-sanitizer fallback remains inert. This smoke run did not need a live Gemini response to validate those sinks. |
| Credential leakage in logs/reports | **Passed for this run** | Captured application output was checked against configured key material, test secrets, and the generated password hash. No matches were found. The report contains status classifications only and no secret values. |

## Commands and results

The isolated smoke harness was run with the repository virtual environment:

```powershell
.\.venv\Scripts\python.exe .test-temp\rag_local_smoke.py
npm run test:security-js
```

The smoke harness completed with these classifications: isolated indexing `passed`, retrieval `passed`, admin login/upload/delete/logout `passed`, application server options `safe`, captured credentials `false`, Gemini request `blocked_URLError`, and external HTTP start `blocked_PermissionError`.

The frontend regression suite completed with 3 tests passed and 0 failed. It covers safe rendering independently of network access.

## Interpretation and next steps

The local RAG components and administrative document lifecycle work with real embeddings and ChromaDB when placed in a separate test directory. The live end-to-end question path remains unverified because this environment cannot resolve the Gemini hostname. The real application also requires the owner to set the three private security settings before it will start.

To complete the owner's local smoke test, configure `.env.local` with a new random `FLASK_SECRET_KEY`, `ADMIN_EMAIL`, and Werkzeug `ADMIN_PASSWORD_HASH`, then run the application from a normal local terminal with network access. Verify a question through the UI and check the terminal for status-only error messages; never paste the key or password into logs, screenshots, Git, or this report.

The temporary smoke-test directories are ignored by `.gitignore` and are outside the real corpus. Windows may retain Chroma index files briefly while the Python process exits; this does not affect the repository or the real data directory.
