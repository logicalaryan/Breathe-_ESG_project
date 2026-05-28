# Technical Debt & Backlog Log (`issues.md`)

This log documents the outstanding technical issues, architectural bottlenecks, and security gaps in the current version of the platform:

---

### 1. Synchronous Ingestion Thread (Render Timeout Risk)
*   **The Issue**: CSV file parsing and calculation (such as airport coordinate lookups and distance resolution) occur completely synchronously inside the HTTP request thread.
*   **The Risk**: If an enterprise analyst uploads a real-world CSV file with 50,000+ rows, the request will exceed Render's 30-second gateway limit and timeout.
*   **The Backlog Fix**: Transition to asynchronous queue processing using **Celery & Redis** (or a serverless background worker), streaming job status via WebSockets or Server-Sent Events (SSE).

### 2. In-Memory Volatile Storage (Data Loss)
*   **The Issue**: The deployed mock server holds calculated emissions in temporary in-memory variables (`MOCK_FACILITY_DB`, `procurement_events_fact` array) rather than writing to a database.
*   **The Risk**: Because Render free containers shut down or restart frequently, all ingested ESG calculation facts are permanently lost upon container sleep, preventing historical tracking.
*   **The Backlog Fix**: Run migrations and refactor the Django views to write permanently to **PostgreSQL** using the models defined in `models.py`.

### 3. Lack of Authentication and Multi-Tenant Isolation
*   **The Issue**: The endpoints are publicly accessible and contain no JWT, Keycloak, or session verification checks.
*   **The Risk**: Any user with network access can post data or retrieve metrics, and there is no active runtime row-level tenant boundary isolation.
*   **The Backlog Fix**: Integrate a secure OAuth2/OIDC workflow, apply `@permission_classes([IsAuthenticated])` annotations, and enforce dynamic middleware filters on all querysets.

### 4. Static Airport Coordinate Database Limitations
*   **The Issue**: Flight distance coordinates are read from a static dictionary containing only ~120 major airports.
*   **The Risk**: An enterprise remote employee flying out of a smaller regional or municipal airport will trigger a missing airport warning, skipping the row entirely.
*   **The Backlog Fix**: Integrate a third-party global airport coordinates database or a geographic API (e.g., AviationStack or OpenFlights) as a fallback search vector.

### 5. Exposure of Sensitive PII Data
*   **The Issue**: Employee IDs (`employee_id`) are fetched and rendered raw in the validation logs and frontend audit lists.
*   **The Risk**: Storing and displaying unmasked employee expense and travel logs violates corporate data privacy regulations (GDPR/CCPA).
*   **The Backlog Fix**: Mask all employee identifiers (e.g., rendering as `EMP***08`) at the API serialization layer and encrypt logs at rest.

### 6. Code-Bound Carbon Conversion Factors
*   **The Issue**: Greenhouse gas conversion factors (DEFRA 2023) are hardcoded directly inside view files and dictionary constants.
*   **The Risk**: Changes to regulatory conversion coefficients require full code modifications and redeployment rather than a simple database configuration update.
*   **The Backlog Fix**: Move factors to a database table `EmissionFactor(version, category, factor_value)` so calculations can dynamically lookup values by year and region.
