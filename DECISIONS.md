# Breathe ESG — Architectural Decision Records

This document records significant architectural and product decisions made during the design
and implementation of the Breathe ESG carbon accounting platform.

Each ADR follows the format: **Context → Options Considered → Decision → Rationale → Trade-off accepted**.

---

## ADR-001: Ingestion Mechanism for Corporate Travel Data — CSV Upload vs API Pull

**Context**: Corporate travel expense data lives in platforms like SAP Concur and Navan (formerly TripActions). We need to ingest structured expense records (flights, hotels, ground transport) and compute Scope 3 Category 6 emissions.

**Options considered**:
1. Real-time API pull via Concur OAuth2 / Navan REST API
2. Scheduled batch pull (cron job)
3. CSV file upload (analyst-initiated)

**Decision**: CSV file upload.

**Rationale**: Concur's API requires enterprise OAuth2 credentials provisioned through SAP's partner program — unavailable in a development or demo context. Navan's API requires a paid partnership tier. Finance teams in enterprise organizations already export monthly expense reports as CSV — this is their established workflow. CSV upload mirrors the realistic data hand-off mechanism without requiring credentials we don't have.

**Trade-off accepted**: No real-time ingestion. Emissions data is as fresh as the last manual upload, typically monthly. This is acceptable for GHG Protocol Scope 3 reporting, which is annual by standard.

**Migration path**: When enterprise credentials are available, swap the CSV parser for an API pull client. The downstream calculation engine (`TravelEmissionsView`) requires zero changes — it operates on the same row-level data regardless of source.

---

## ADR-002: Flight Distance Resolution — Haversine Formula vs External API

**Context**: Corporate expense reports (Concur, Navan) report flight origin/destination as 3-letter IATA airport codes (e.g., `DEL`, `LHR`). DEFRA emission factors are expressed in kg CO2e per passenger-km. We need distance in km.

**Options considered**:
1. External aviation distance API (e.g., FlightAware, AviationStack)
2. Google Maps Distance Matrix API
3. Haversine great-circle formula with static IATA coordinate lookup

**Decision**: Haversine formula with static airport coordinate database (`airport_db.py`).

**Rationale**: External APIs introduce rate limits, cost, and external dependencies that would cause test failures in CI and offline environments. The Haversine great-circle formula is the standard method used by ICAO and IATA for computing scheduled flight distances. Airport GPS coordinates are static public data (WGS84 decimal degrees). Our lookup covers 120 major airports used in corporate business travel — sufficient for the demo scope. Haversine is deterministic, zero-cost, requires no network access, and is auditable.

**Accuracy note**: Haversine computes straight-line (great-circle) distance. Actual flight paths deviate due to airways, jet streams, and controlled airspace. DEFRA's methodology accounts for this via the Radiative Forcing Index (RFI) uplift already embedded in the emission factors we apply. Using Haversine + RFI-inclusive DEFRA factors produces results consistent with industry practice.

**Trade-off accepted**: Airports not in `airport_db.py` will cause the row to be skipped and logged. The database covers ~120 major hubs; obscure regional airports require manual addition.

---

## ADR-003: Emission Factor Source — DEFRA 2023

**Context**: We need kg CO2e conversion factors for electricity, flights, hotels, and ground transport that are auditor-accepted and publicly cited.

**Options considered**:
1. UK DEFRA GHG Conversion Factors 2023
2. IPCC AR6 factors
3. EPA (US Environmental Protection Agency) factors
4. IEA (International Energy Agency) electricity factors

**Decision**: DEFRA 2023 as primary source for all categories.

**Rationale**: DEFRA's annual GHG Conversion Factors publication is the most widely cited source in UK and European corporate GHG reporting. It covers all required categories in a single, annually updated, freely downloadable dataset. It is explicitly referenced in the GHG Protocol Corporate Accounting and Reporting Standard. Using a single authoritative source eliminates inconsistencies from mixing datasets. The DEFRA 2023 aviation factors include the Radiative Forcing Index (RFI) uplift, which accounts for the additional warming effect of contrails and high-altitude water vapour — consistent with BEIS guidance for Scope 3 air travel.

**Trade-off accepted**: DEFRA factors are UK-centric. For organizations reporting under US or global frameworks, EPA or IEA factors may be more appropriate. This is documented for future expansion.

---

## ADR-004: ESPI Standard — JSON Output vs Atom XML Wire Format

**Context**: The Green Button ESPI (Energy Services Provider Interface) standard defines how utility energy data should be represented. The standard specifies Atom XML as the wire format.

**Options considered**:
1. Full Atom XML output with ESPI namespace declarations
2. JSON representation of ESPI field names and codes
3. Custom proprietary format

**Decision**: JSON representation using correct ESPI field names and enumeration codes.

**Rationale**: Our immediate consumers (the frontend dashboard, ESG analyst review tools) consume JSON natively. Implementing full Atom XML with namespace parsing adds significant complexity for zero downstream benefit at this stage. We preserve 100% semantic fidelity — `qualityOfReading`, `billingPeriod`, `overallConsumption`, `uom`, `powerOfTenMultiplier` are all correctly named and valued per the ESPI specification. The ESPI quality codes (`8`=Estimated, `14`=Validated) are correct. A future migration to Atom XML output (e.g., for direct Green Button Data Custodian integration) requires only a serializer change — the underlying field semantics are already correct.

**Trade-off accepted**: A Green Button-certified data consumer expecting Atom XML would reject our output. This is documented as a known gap for production deployment.

---

## ADR-005: Mock Server Architecture — Standalone HTTP Server vs Django Test Client

**Context**: We needed a way to test all three API endpoints locally without a full Django project setup (no `settings.py` configured for production, no database, no `manage.py`).

**Options considered**:
1. Django's built-in test client (`from django.test import Client`)
2. Standalone Python `http.server` mock that reimplements the logic
3. FastAPI or Flask as a lighter alternative

**Decision**: Standalone `mock_server.py` using Python's `http.server`.

**Rationale**: At time of implementation, the Django project lacked a `urls.py` and `manage.py` — there was no runnable Django app to attach the test client to. The mock server allowed immediate end-to-end testing of request/response shapes and API contracts.

**Known technical debt**: This creates logic duplication across two codebases. Bugs fixed in the Django view are not automatically fixed in the mock server. The correct long-term solution is to commit to a full Django project structure and use Django's test client (`backend/tests.py` now provides this). `mock_server.py` should be treated as a deprecated development scaffold.

**Migration path**: `backend/tests.py` now contains proper Django unit tests. `mock_server.py` should be removed once Django URL configuration is complete.

---

## ADR-006: Estimated Read Handling — Flag vs Reject

**Context**: Utility meters sometimes produce estimated reads (e.g., when a physical meter inspection is missed). These reads are flagged in utility bills but still represent real energy consumption.

**Options considered**:
1. Reject estimated reads — return HTTP 422 and require actual reads
2. Accept and flag — ingest the read, mark it as estimated, require manual reconciliation

**Decision**: Accept and flag using ESPI `qualityOfReading` code `8`.

**Rationale**: Rejecting estimated reads would create data gaps in the emissions timeline — precisely what ESG auditors flag as incomplete reporting. The GHG Protocol requires complete, consistent reporting. The correct approach is to ingest estimated reads with appropriate flagging, surface them in the analyst review queue for manual sign-off, and update them when the actual read arrives. This matches how utility companies and energy management systems handle estimated readings.

**Reconciliation workflow**: When an actual read replaces an estimated read, the original `EmissionRecord` is marked `SUPERSEDED` and a new record is created with `qualityOfReading=14`. The data lineage is preserved via the `superseded_by` foreign key in `models.py`.

---

## ADR-007: Multi-Tenancy Architecture — Row-Level vs Schema-Per-Tenant

**Context**: A production ESG SaaS platform serves multiple client organizations. Their data must be strictly isolated.

**Options considered**:
1. Schema-per-tenant (separate PostgreSQL schema per organization)
2. Database-per-tenant (separate database instance per organization)
3. Row-level tenancy with `organization_id` foreign key on every table

**Decision**: Row-level tenancy with `Organization` as the root tenant entity (implemented in `models.py`).

**Rationale**: Row-level tenancy with strict `organization_id` filtering on every query is the most operationally practical approach at this scale. Schema-per-tenant requires complex migration management (running migrations N times for N tenants). Database-per-tenant is operationally expensive and makes cross-tenant analytics impossible. Row-level tenancy is the approach used by Salesforce, Notion, and most modern SaaS platforms.

**Security note**: Every API view in production must filter querysets by `request.user.organization`. This is enforced at the ORM layer, not the URL layer, to prevent IDOR vulnerabilities. This enforcement is mocked in the current implementation but is explicitly called out in `models.py`.

---

## ADR-008: No OAuth2 / PDF OCR in This Submission

**Context**: Real-world utility data arrives as PDF bills. Real-world corporate authentication uses OAuth2/OIDC.

**Decision**: Both are explicitly excluded from this submission.

**OAuth2 rationale**: Implementing a production OIDC flow (Keycloak, Auth0, or Azure AD) requires infrastructure configuration that is out of scope for a backend logic assessment. In production, all endpoints would be protected with `@permission_classes([IsAuthenticated])` and Bearer token validation. The endpoint security layer is a thin wrapper — the allocation logic underneath is identical.

**PDF OCR rationale**: Building a computer vision pipeline (AWS Textract, Google Document AI, or Tesseract) to extract `start_date`, `end_date`, and `total_kwh` from utility bill PDFs is a separate engineering workstream. We assume the upstream OCR layer has already extracted the structured fields into the JSON payload we receive. This is standard microservice boundary design — OCR extraction and carbon calculation are separate bounded contexts.
