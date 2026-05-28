# Mistakes Post-Mortem & Resolution Log (`mistakes.md`)

This log documents the critical technical mistakes and bugs identified and resolved during the Breathe ESG cloud deployment and integration phase:

---

### 1. The "Silent 500" CORS Handshake Trap
*   **The Mistake**: Allowing uncaught exceptions (e.g., parsing errors, missing columns) to bubble up to the default Python `BaseHTTPRequestHandler` during a `POST` request.
*   **The Consequence**: The server returned a standard Python `500 Internal Server Error` page. Because this page did not contain the `Access-Control-Allow-Origin: *` header, the browser blocked the response and threw a generic network CORS error. This hid the actual Python traceback behind a generic `"Could not connect to backend"` message.
*   **The Resolution**: Wrapped the entire routing block in `do_POST` in a `try...except` block, ensuring any unhandled internal server error is caught and returned with clean JSON and explicit CORS headers.

### 2. Duplicate Method Overriding (`do_OPTIONS`)
*   **The Mistake**: Having two separate definitions of `do_OPTIONS` in `mock_server.py` (one at the top on line 59 and an older one at the bottom on line 668).
*   **The Consequence**: In Python, when a class defines a method twice, the second definition silently overrides the first. This caused our robust `204 No Content` handler with the correct allowed headers to be overwritten by the old `200 OK` handler, causing complex browser preflights to fail.
*   **The Resolution**: Purged the redundant `do_OPTIONS` method at the bottom of the file to allow the correct preflight handler to take full effect.

### 3. Fragile CSV Dictionary Comprehension (`NoneType` Crash)
*   **The Mistake**: Running `.strip()` directly on all keys and values in the CSV rows dictionary comprehension without checking if they were `None`:
    ```python
    row = {k.strip().lower(): (v.strip() if v else "") for k, v in raw_row.items()}
    ```
*   **The Consequence**: When an analyst uploaded a CSV file containing trailing commas or blank columns (which have no header), Python's `csv.DictReader` set the key to `None`. Calling `None.strip()` instantly crashed the entire ingestion thread with a `'NoneType' object has no attribute 'strip'` error.
*   **The Resolution**: Added a defensive check to filter out empty keys: `if k is not None`.

### 4. Hardcoded Port and Local Host Binding
*   **The Mistake**: Binding the server socket strictly to local loopback `127.0.0.1` and a hardcoded port.
*   **The Consequence**: When deployed to cloud infrastructure like Render, the container failed to bind, and the external router could not route traffic to the container because it wasn't listening on `0.0.0.0`.
*   **The Resolution**: Read the dynamic port provided by the host environment (`PORT = int(os.environ.get("PORT", 8000))`) and bound to `0.0.0.0` to permit external ingress routing.
