# Breathe ESG — Carbon Accounting Platform

A production-minded ESG carbon accounting platform that ingests utility bills, SAP procurement data,
and corporate travel expenses — computes GHG Protocol Scope 1/2/3 emissions — and surfaces them
through a compliance-ready analyst review interface.

> **Assessment submission**: See [`DECISIONS.md`](./DECISIONS.md), [`TRADEOFFS.md`](./TRADEOFFS.md), and [`SOURCES.md`](./SOURCES.md) for architectural rationale, deliberate exclusions, and data source citations.

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────┐
│  React + TypeScript Frontend  (Vite, shadcn/ui)          │
│  Dashboard  │  Upload  │  Review Queue  │  Audit History  │
└─────────────────────────┬────────────────────────────────┘
                          │ HTTP (multipart/json)
┌─────────────────────────▼────────────────────────────────┐
│  Django REST Framework Backend                           │
│                                                          │
│  POST /api/utility-allocation/  ←── Scope 2 electricity  │
│  POST /api/process-sap/         ←── Scope 1 procurement  │
│  POST /api/travel-emissions/    ←── Scope 3 travel       │
└─────────────────────────┬────────────────────────────────┘
                          │ ORM
┌─────────────────────────▼────────────────────────────────┐
│  Data Model  (backend/models.py)                         │
│  Organization → Facility → EmissionRecord                │
│  IngestionJob  (upload audit log)                        │
└──────────────────────────────────────────────────────────┘
```

---

## Supported Emission Scopes

| Scope | Category | Source | Endpoint |
|---|---|---|---|
| Scope 2 | Purchased Electricity | Utility bill CSV (ESPI-aligned) | `/api/utility-allocation/` |
| Scope 1 | Direct Fuel / Procurement | SAP MM CSV export | `/api/process-sap/` |
| Scope 3 Cat. 6 | Business Travel | Concur/Navan CSV export | `/api/travel-emissions/` |

**GHG Protocol boundary**: Operational Control approach. **Emission factor standard**: DEFRA 2023.

---

## Backend — API Endpoints

### `POST /api/utility-allocation/`
Ingests a utility electricity bill and allocates consumption daily across calendar months.

**Content-Type**: `application/json`

```json
{
  "start_date": "2023-11-09",
  "end_date": "2023-12-10",
  "total_kwh": 3500,
  "is_estimated": false
}
```

- `is_estimated` (optional, default `false`): When `true`, sets ESPI `qualityOfReading` to `"8"` (Estimated) instead of `"14"` (Validated). Records are flagged for manual analyst review.
- Output: ESPI Green Button–aligned `UsageSummary` objects per calendar month.

### `POST /api/process-sap/`
Ingests a SAP procurement CSV and normalizes quantities to SI units.

**Content-Type**: `multipart/form-data`

- `file`: CSV file with SAP column headers (BUKRS, WERKS, MATNR, MEINS, MENGE, WRBTR, WAERS, ERDAT)
- Performs: header translation, facility dimension join (WERKS→Facility), unit conversion (GAL→L, KG→MT, etc.)
- Output: Normalized fact table + facility dimension + row-level validation log.

### `POST /api/travel-emissions/`
Ingests a Concur/Navan corporate travel CSV and computes Scope 3 Category 6 emissions.

**Content-Type**: `multipart/form-data`

- `file`: CSV file with columns: `employee_id`, `expense_date`, `expense_category`, `origin_iata`, `destination_iata`, `ticket_class`, `hotel_city`, `hotel_country`, `nights`, `transport_vendor`, `distance_km`, `amount`, `currency`
- Flight distances are computed via **Haversine great-circle formula** from IATA airport coordinates.
- Output: Per-category totals, per-employee breakdown, validation log, processed records.

---

## Data Model

```python
Organization          # Tenant root — multi-tenant isolation
  └── Facility        # Physical location (maps to SAP WERKS)
  └── EmissionRecord  # Core fact table (Scope 1/2/3, with audit trail)
  └── IngestionJob    # Upload audit log
```

Key design decisions:
- `EmissionRecord.raw_payload` is **immutable** — original source data preserved for audit.
- `EmissionRecord.emission_factor_version` — tracks which DEFRA year was used per record.
- `EmissionRecord.superseded_by` — maintains data lineage when actual reads replace estimated reads.
- Status machine: `PENDING → VALIDATED/ESTIMATED → APPROVED/REJECTED/SUPERSEDED`

See [`backend/models.py`](./backend/models.py) for full schema.

---

## Running Locally

### Backend (Mock Server — no Django setup required)
```bash
# Install dependencies
pip install django djangorestframework

# Start mock HTTP server (port 8000)
python backend/mock_server.py

# Run tests against mock server
python backend/test_utility_allocation.py
python backend/test_travel_emissions.py
```

### Backend (Django — with proper project setup)
```bash
# With manage.py configured:
python manage.py test backend  # runs backend/tests.py (30 unit tests)
python manage.py migrate       # creates database schema from models.py
```

### Frontend
```bash
npm install
npm run dev        # starts Vite dev server at http://localhost:5173
```

The Upload page sends files to `http://localhost:8000` (mock server must be running).

---

## Project Structure

```
Breath_esg/
├── backend/
│   ├── models.py               ← Django ORM data models (multi-tenant schema)
│   ├── utility_allocation.py   ← Scope 2: electricity pro-rata allocation (ESPI)
│   ├── views.py                ← Scope 1: SAP procurement CSV processor
│   ├── travel_emissions.py     ← Scope 3: corporate travel emissions (Haversine)
│   ├── emission_factors.py     ← DEFRA 2023 factor constants
│   ├── airport_db.py           ← IATA → GPS coordinate lookup (120 airports)
│   ├── mock_server.py          ← Standalone test server (dev scaffold)
│   ├── tests.py                ← Django TestCase unit tests (30 assertions)
│   ├── settings.py             ← Minimal Django settings for local use
│   └── sample_*.csv            ← Sample data files for testing
├── src/
│   ├── pages/
│   │   ├── Dashboard.tsx       ← Scope 1/2/3 trend overview
│   │   ├── Upload.tsx          ← File ingestion with live API response
│   │   ├── ReviewQueue.tsx     ← Analyst approve/reject workflow
│   │   └── AuditHistory.tsx    ← Ingestion job history
│   └── components/
├── DECISIONS.md                ← 8 Architectural Decision Records
├── TRADEOFFS.md                ← 10 deliberate exclusions with migration paths
├── SOURCES.md                  ← Full data source citations (DEFRA 2023, ESPI, GHG Protocol)
└── README.md                   ← This file
```

---

## Deliberate Exclusions

The following are intentionally not built in this submission. Each is documented with rationale and migration path in [`TRADEOFFS.md`](./TRADEOFFS.md):

1. **No persistent database** — calculation engine is correct; persistence is infrastructure
2. **No OAuth2 / OIDC authentication** — auth is a thin wrapper over unchanged business logic
3. **No PDF OCR extraction** — assumed upstream microservice; this system consumes already-extracted JSON
4. **ESPI Atom XML wire format** — JSON with correct ESPI codes used; XML is a serializer-layer change
5. **No real-time API pull** from Concur/Navan — CSV is the realistic finance team workflow
6. **No carbon offset tracking** — offset quality assessment is a specialist domain
7. **No SBTi target tracking** — requires ≥2 years of historical data (persistence prerequisite)

---

## Test Coverage

```
backend/tests.py — 30 Django TestCase assertions covering:
  ✓ Utility allocation: validated read, estimated read, energy conservation, date edge cases
  ✓ SAP processor: unit conversions, facility joins, validation log
  ✓ Travel emissions: Haversine accuracy, class multipliers, hotel region factors, vendor mapping
```

---

## Standards & Compliance References

| Standard | Usage |
|---|---|
| GHG Protocol Corporate Standard (WRI/WBCSD) | Scope 1/2/3 framework, operational control boundary |
| DEFRA 2023 GHG Conversion Factors | All emission factors (flights, hotels, ground transport) |
| Green Button ESPI (NAESB REQ.18) | Utility data field names and quality codes |
| IATA airport coordinate database | Flight distance resolution |
| NIST unit conversion tables | SAP unit normalization factors |
