# Breathe ESG — Data Sources & Citations

All emission factors, standard codes, and reference data used in this project are listed below
with full citations. Each source is freely available for verification.

---

## 1. Emission Factors — UK DEFRA 2023

**Full title**: "Greenhouse Gas Reporting: Conversion Factors 2023"
**Publisher**: UK Department for Environment, Food & Rural Affairs (DEFRA) / Department for Business, Energy & Industrial Strategy (BEIS)
**Publication year**: 2023
**URL**: https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2023
**Format**: Microsoft Excel workbook (.xlsx) with multiple factor tables

### Specific tables used:

| Factor Category | DEFRA Spreadsheet Tab | Specific Rows Used |
|---|---|---|
| Flight emissions (per passenger-km) | "Business travel- air" | Short-haul domestic/international, Long-haul international; Economy, Premium Economy, Business, First class; with Radiative Forcing Index (RFI) |
| Hotel accommodation (per room-night) | "Business travel- hotels" | UK, Europe, North America, Asia Pacific, rest of world |
| Ground transport (per passenger-km) | "Business travel- land" | Taxi, Car (rental, average petrol), National Rail, Local bus, Battery EV |

### Key factor values (from DEFRA 2023):

**Flights (kg CO2e per passenger-km, including RFI):**
| Route | Economy | Premium Economy | Business | First |
|---|---|---|---|---|
| Short-haul (<1,500 km) | 0.25506 | 0.25506 | 0.38258 | 0.38258 |
| Long-haul (≥1,500 km) | 0.19499 | 0.28641 | 0.42869 | 0.75109 |

**Hotels (kg CO2e per room-night):**
| Region | Factor |
|---|---|
| United Kingdom | 20.8 |
| Europe | 16.5 |
| North America | 31.2 |
| Asia Pacific | 15.6 |
| Middle East | 24.5 |
| Africa | 22.1 |
| Latin America | 14.3 |
| Oceania | 28.9 |
| Global average | 26.4 |

**Ground transport (kg CO2e per passenger-km):**
| Type | Factor |
|---|---|
| Taxi / rideshare | 0.14887 |
| Rental car (petrol, average) | 0.19211 |
| National Rail (UK) | 0.03548 |
| Local bus | 0.02735 |
| Battery electric vehicle | 0.05302 |

---

## 2. Green Button ESPI Standard

**Full title**: "Energy Services Provider Interface (ESPI) Data Standard"
**Publisher**: Green Button Alliance / North American Energy Standards Board (NAESB)
**URL**: https://www.greenbuttonalliance.org/
**Standard reference**: NAESB REQ.18 (Retail Energy Quadrant Technical Standards)

### Specific codes used:

| Field | Code | Meaning |
|---|---|---|
| `qualityOfReading` | `8` | Estimated — meter read was estimated, requires manual validation |
| `qualityOfReading` | `14` | Validated — actual meter read, audit-safe |
| `uom` (Unit of Measure) | `72` | Watt-hours (Wh) |
| `powerOfTenMultiplier` | `0` | Base unit (no scaling) |

**Note on wire format**: The Green Button standard specifies Atom XML as the transport format. This implementation uses JSON with correct ESPI field names and codes. See `DECISIONS.md` ADR-004 for rationale.

---

## 3. GHG Protocol Corporate Accounting and Reporting Standard

**Full title**: "A Corporate Accounting and Reporting Standard, Revised Edition"
**Publisher**: World Resources Institute (WRI) / World Business Council for Sustainable Development (WBCSD)
**URL**: https://ghgprotocol.org/corporate-standard
**Scope framework**:
- Scope 1: Direct emissions from owned/controlled sources (fuel combustion, vehicles)
- Scope 2: Indirect emissions from purchased electricity, steam, heat, cooling
- Scope 3, Category 6: Indirect emissions from business travel

**Consolidation approach used**: Operational Control (all emission sources the organization has operational control over).

---

## 4. Airport Coordinate Data

**Full title**: OurAirports Database
**Publisher**: OurAirports (ourairports.com)
**URL**: https://ourairports.com/data/
**Format**: CSV with IATA code, airport name, latitude, longitude (WGS84 decimal degrees)
**License**: Public domain

**Usage**: The `airport_db.py` file contains 120 major airports' IATA codes mapped to WGS84 GPS coordinates, sourced from the OurAirports dataset. Used to resolve flight distances via the Haversine formula when only airport codes are available.

---

## 5. Haversine Distance Formula

**Mathematical source**: Haversine formula for great-circle distance
**Reference**: Sinnott, R.W. (1984). "Virtues of the Haversine". Sky and Telescope, 68(2), p.159.
**Earth radius used**: 6,371.0 km (IAU 2012 nominal mean radius)

**Adoption**: ICAO and IATA use Haversine (or the equivalent Vincenty formula) as the standard method for computing scheduled flight distances between airports. Our implementation uses the same methodology.

---

## 6. SAP Field Reference

**Source**: SAP ERP Materials Management (MM) and Financial Accounting (FI) documentation
**Publisher**: SAP SE
**URL**: https://help.sap.com/

**SAP column codes used in this project:**
| SAP Field Code | Full Name | Usage |
|---|---|---|
| BUKRS | Company Code (Buchungskreis) | Organization identifier |
| WERKS | Plant (Werk) | Facility identifier — mapped to `Facility.sap_werks_code` |
| MATNR | Material Number | Procurement item identifier |
| MEINS | Base Unit of Measure | Raw unit for quantity normalization |
| MENGE | Quantity | Raw consumption quantity |
| WRBTR | Amount in Document Currency | Financial value |
| WAERS | Currency Key | ISO 4217 currency code |
| ERDAT | Date on Which Record Was Created | Transaction date |

---

## 7. Unit Conversion Factors

**Source**: NIST (National Institute of Standards and Technology) standard conversions
**URL**: https://www.nist.gov/pml/weights-and-measures/metric-si/unit-conversion

| Conversion | Factor |
|---|---|
| US Gallon → Litres | 3.78541 |
| Barrel of oil (bbl) → Litres | 158.987 |
| Cubic metre (m³) → Litres | 1,000.0 |
| Kilogram → Metric Tonnes | 0.001 |
| Pounds (lbs) → Metric Tonnes | 0.00045359237 |

---

## 8. Radiative Forcing Index (RFI) — Aviation

**Context**: Aircraft emit CO2 and non-CO2 pollutants (water vapour, NOx, contrails) at altitude. The combined warming effect exceeds CO2 alone. The RFI is a multiplier applied to aviation CO2 to account for the total climate forcing.

**Source**: DEFRA 2023 "Business travel – air" tab uses RFI-inclusive factors by default.
**RFI value embedded**: DEFRA 2023 applies an RFI of approximately 1.9× for long-haul economy (CO2-only factor × 1.9 ≈ total forcing factor).
**Our usage**: We use DEFRA's pre-multiplied RFI-inclusive factors directly. No separate RFI calculation is required.
