# Breathe ESG — Trade-offs & Deliberate Exclusions

This document lists features and capabilities that were deliberately **not built** in this submission,
the reasons for their exclusion, the business impact of each gap, and the migration path to address them.

This is a required artefact for any production ESG system assessment under the GHG Protocol.

---

## 1. No Persistent Database / Data Storage

**What was excluded**: Django ORM migrations, a running database, and persistent storage of emission records.

**Why**: The submission focuses on the data model design (`models.py`) and calculation engine correctness. Setting up a production PostgreSQL instance was out of scope for a time-bounded technical assessment.

**Business impact**: Every upload is forgotten after the response is returned. The dashboard cannot show historical trends from real data. No audit report can be generated. **This is the highest-priority gap for a production deployment.**

**Migration path**: Run `python manage.py migrate` against a PostgreSQL instance. Refactor the three views (`utility_allocation.py`, `views.py`, `travel_emissions.py`) to save `EmissionRecord` instances using the ORM models defined in `models.py`. Estimated effort: 2–3 days of engineering work.

---

## 2. No Real Authentication or Authorization

**What was excluded**: OAuth2/OIDC token validation, user sessions, role-based access control (analyst vs. approver vs. admin roles).

**Why**: Authentication is an infrastructure concern separate from the carbon accounting logic. The calculation engine is identical with or without auth. Adding mocked auth would obscure the signal of what is being assessed.

**Business impact**: Any user with network access can POST to any endpoint. Multi-tenant data isolation is not enforced at runtime (though the data model supports it via the `Organization` foreign key). This is a **critical security gap** for production.

**Migration path**: Add `@permission_classes([IsAuthenticated])` to all views. Middleware injects `request.user.organization_id`. All ORM querysets filter by `organization_id`. Estimated effort: 3–5 days including Keycloak/Auth0 integration.

---

## 3. No PDF OCR Extraction Pipeline

**What was excluded**: Computer vision/OCR pipeline for extracting structured data from utility bill PDFs.

**Why**: Real utility bills arrive as PDFs. Parsing them requires either AWS Textract, Google Document AI, or Tesseract — a separate microservice workstream with significant ML/CV engineering investment. We assume the upstream OCR layer has already extracted structured fields.

**Business impact**: Analysts must manually enter `start_date`, `end_date`, and `total_kwh` from paper bills, or use the CSV upload path. This adds friction and human error risk.

**Migration path**: Build an OCR microservice (separate repo/service) that accepts PDF uploads and returns structured JSON. The `utility_allocation.py` view requires zero changes — it already expects that JSON payload.

---

## 4. ESPI Atom XML Wire Format

**What was excluded**: Full Green Button ESPI Atom XML serialization.

**Why**: The Green Button standard uses Atom XML with specific namespace declarations. Our output uses correct ESPI field names and enumeration codes (e.g., `qualityOfReading` codes 8/14, `uom` 72 for Watt-hours) but wraps them in JSON rather than Atom XML. JSON is the native format for our downstream consumers (React dashboard, ESG analyst tools).

**Business impact**: Direct integration with a Green Button-certified Data Custodian (utility company) would require our XML output. As a standalone ESG platform consuming already-extracted data, JSON is sufficient.

**Migration path**: Add an `ESPIXMLSerializer` that wraps the existing `UsageSummary` dict in the correct Atom XML namespace and encoding. The calculation logic is unchanged.

---

## 5. No Emission Factor Versioning at Runtime

**What was excluded**: Automatic recalculation of historical records when DEFRA publishes a new year's factors.

**Why**: The data model includes `emission_factor_version` and `emission_factor_value` fields on `EmissionRecord` to enable this — but the runtime recalculation workflow is not implemented.

**Business impact**: When DEFRA 2024 factors are published, historical records computed with DEFRA 2023 factors are not automatically updated. ESG auditors may flag year-over-year inconsistencies if different factor versions are used across reporting periods without disclosure.

**Migration path**: Implement a Django management command `recalculate_records --factor-version DEFRA2024` that: (1) loads new factors, (2) creates new `EmissionRecord` instances for affected records, (3) marks old records as `SUPERSEDED`. The `superseded_by` FK in `models.py` preserves the audit chain.

---

## 6. No Real-Time API Pull from Concur / Navan

**What was excluded**: Scheduled or webhook-triggered data pull from SAP Concur or Navan REST APIs.

**Why**: Both platforms require enterprise-tier OAuth2 credentials. Concur uses a partner program managed by SAP; Navan requires a paid API partnership. These are not available in a development context. CSV upload is the established manual workflow for finance teams in enterprise organizations.

**Business impact**: Emissions data is as current as the last manual CSV upload (typically monthly). This is acceptable for GHG Protocol Scope 3 annual reporting but creates a lag for real-time carbon dashboards.

**Migration path**: Build API adapter classes (`ConcurAdapter`, `NavanAdapter`) that each implement a `fetch_rows() -> List[dict]` interface matching the same column schema as the CSV import. The downstream calculation engine requires zero changes.

---

## 7. No CO2 Offset / Carbon Credit Tracking

**What was excluded**: Integration with voluntary carbon offset markets (Gold Standard, Verra VCS) for tracking purchased offsets and net emissions.

**Why**: Carbon offset markets are complex, contested, and regulated differently across jurisdictions. Offset quality assessment (additionality, permanence, leakage) is a specialist domain. Including a simplified offset model would risk misleading ESG analysts about their net position.

**Business impact**: The platform reports gross emissions only. Net emissions (gross minus purchased offsets) cannot be calculated. Many corporate ESG targets are expressed in net terms.

**Migration path**: Add an `OffsetCredit` model linked to `Organization`, with fields for standard (Gold Standard, VCS), vintage year, quantity (tonnes CO2e), and verification status. Net reporting requires subtracting verified credits from gross `EmissionRecord` totals.

---

## 8. No Year-Over-Year Baseline Comparison or Target Tracking

**What was excluded**: Science-Based Targets (SBTi) base year establishment, target trajectory modelling, and year-over-year variance analysis.

**Why**: Baseline and target tracking requires at minimum 2 years of historical data, a defined base year, and a GHG Protocol-compliant recalculation policy (for structural changes like acquisitions). These are reporting-layer features that depend on the persistence layer being operational first.

**Business impact**: The platform cannot show progress against net-zero targets, cannot flag target deviations, and cannot produce the trajectory charts required by frameworks like TCFD (Task Force on Climate-related Financial Disclosures).

**Migration path**: Once `EmissionRecord` persistence is operational, add an `EmissionTarget` model with `base_year`, `target_year`, `target_reduction_pct`, and `scope`. The dashboard trend chart can then show actuals vs. trajectory.

---

## 9. No Pagination on Large Dataset Responses

**What was excluded**: Cursor-based or offset-based pagination on the procurement and travel endpoints.

**Why**: For the sample datasets used in this assessment, all rows fit in a single response without performance impact.

**Business impact**: A real Concur export may contain 50,000+ rows per month for a large enterprise. Returning all rows in a single JSON response will cause memory errors and browser freezes.

**Migration path**: Add Django REST Framework `CursorPagination` to all list endpoints. Update the frontend table to use lazy loading or server-side pagination.

---

## 10. Scope 1 Direct Fuel — Not Fully Implemented

**What was excluded**: CO2 emission calculation from the SAP procurement data. The SAP processor normalizes units (GAL→L, KG→MT) and validates data, but does not apply combustion emission factors to produce kg CO2e.

**Why**: Fuel combustion factors depend on fuel type (diesel, petrol, natural gas, HFO) which is embedded in the `MATNR` (material number) field of SAP data. Mapping arbitrary SAP material numbers to fuel types requires a customer-specific material master configuration that cannot be generalized.

**Business impact**: The SAP procurement processor outputs normalized quantities and a clean fact table, but cannot independently produce Scope 1 emission totals.

**Migration path**: Add a `MaterialEmissionFactor` configuration model that maps customer-specific SAP `MATNR` codes to DEFRA fuel combustion factors (e.g., diesel: 2.6928 kg CO2e/litre). Once configured per organization, the SAP processor can complete the Scope 1 calculation.
