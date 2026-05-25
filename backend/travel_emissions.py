"""
Corporate Travel Emissions — Django REST Framework View.
Endpoint: POST /api/travel-emissions/

Ingestion Mechanism: CSV File Upload
--------------------------------------
Design Justification:
    Platforms like SAP Concur and Navan (formerly TripActions) are the dominant
    corporate travel management systems. Both expose monthly expense exports as
    CSV/Excel files — the standard workflow for finance teams. Implementing
    OAuth2 API integration with Concur would require enterprise-tier credentials
    that are unavailable in a development/demo context. CSV upload is the
    realistic, widely-adopted data hand-off mechanism and mirrors the pattern
    already established in the SAP procurement module. If credentials become
    available, the CSV parser can be replaced with an API pull with zero changes
    to the downstream calculation engine.

Emission Factors:
    DEFRA 2023 GHG Conversion Factors (Business Travel)
    https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2023

    Scope 3, Category 6: Business Travel (GHG Protocol)

Distance Resolution:
    Flights are often reported with IATA airport codes (e.g. DEL → LHR) rather
    than distances. The Haversine great-circle formula calculates the straight-
    line distance between two GPS coordinates. Airport coordinates are stored in
    a static lookup table (airport_db.py) — no external API is required.

Expected CSV columns (Concur-compatible export schema):
    employee_id       — Employee identifier
    expense_date      — YYYY-MM-DD
    expense_category  — FLIGHT | HOTEL | GROUND_TRANSPORT
    origin_iata       — 3-letter IATA code  (flights only)
    destination_iata  — 3-letter IATA code  (flights only)
    ticket_class      — ECONOMY | PREMIUM_ECONOMY | BUSINESS | FIRST (flights)
    hotel_city        — City name            (hotels only)
    hotel_country     — Country name         (hotels only)
    nights            — Integer              (hotels only)
    transport_vendor  — Vendor name          (ground only, e.g. Uber, Hertz)
    distance_km       — Numeric km           (ground only)
    amount            — Numeric cost
    currency          — 3-letter ISO code
"""

import csv
import io
import math
import os

from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser
from rest_framework import status

# Emission factor constants and airport coordinate lookup.
# These modules live in the same directory. In a full Django project they would
# be importable as `from backend.emission_factors import ...` once the app is
# registered in INSTALLED_APPS. We use a try/except to handle both deployment
# contexts (Django project with proper PYTHONPATH, or standalone script execution).
try:
    from emission_factors import (
        FLIGHT_FACTORS, SHORT_HAUL_MAX_KM, TICKET_CLASS_ALIASES,
        HOTEL_FACTORS, COUNTRY_TO_HOTEL_REGION,
        GROUND_FACTORS, VENDOR_TO_TRANSPORT_TYPE,
    )
    from airport_db import AIRPORT_COORDINATES
except ImportError:
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from emission_factors import (
        FLIGHT_FACTORS, SHORT_HAUL_MAX_KM, TICKET_CLASS_ALIASES,
        HOTEL_FACTORS, COUNTRY_TO_HOTEL_REGION,
        GROUND_FACTORS, VENDOR_TO_TRANSPORT_TYPE,
    )
    from airport_db import AIRPORT_COORDINATES

# ---------------------------------------------------------------------------
# Required CSV headers
# ---------------------------------------------------------------------------
REQUIRED_HEADERS = {"employee_id", "expense_date", "expense_category"}

VALID_CATEGORIES = {"FLIGHT", "HOTEL", "GROUND_TRANSPORT"}


# ---------------------------------------------------------------------------
# Haversine Great-Circle Distance
# ---------------------------------------------------------------------------
def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Return the great-circle distance in km between two GPS coordinates
    using the Haversine formula.

    This is the standard method used by ICAO and IATA for computing
    flight distances from airport coordinates. It is deterministic,
    requires no external API, and handles all edge cases (polar routes,
    antimeridian crossings) correctly.
    """
    R = 6371.0  # Earth's mean radius in km (IAU 2012)
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lam = math.radians(lon2 - lon1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lam / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


# ---------------------------------------------------------------------------
# Per-category emission calculators
# ---------------------------------------------------------------------------
def calculate_flight_emissions(row: dict, row_number: int, validation_log: list):
    """
    Calculate kg CO2e for a single flight expense row.
    Returns (kg_co2e: float | None, distance_km: float | None).
    Returns None if the row cannot be processed.
    """
    origin_raw = row.get("origin_iata", "").strip().upper()
    dest_raw   = row.get("destination_iata", "").strip().upper()
    class_raw  = row.get("ticket_class", "economy").strip().lower()

    # Resolve airport coordinates
    if origin_raw not in AIRPORT_COORDINATES:
        validation_log.append(
            f"Row {row_number} [FLIGHT]: Unknown origin IATA code '{origin_raw}'. "
            f"Row skipped — add to airport_db.py to include."
        )
        return None, None

    if dest_raw not in AIRPORT_COORDINATES:
        validation_log.append(
            f"Row {row_number} [FLIGHT]: Unknown destination IATA code '{dest_raw}'. "
            f"Row skipped — add to airport_db.py to include."
        )
        return None, None

    lat1, lon1 = AIRPORT_COORDINATES[origin_raw]
    lat2, lon2 = AIRPORT_COORDINATES[dest_raw]

    distance_km = haversine_km(lat1, lon1, lat2, lon2)

    # Normalise ticket class
    ticket_class = TICKET_CLASS_ALIASES.get(class_raw)
    if ticket_class is None:
        ticket_class = "economy"
        validation_log.append(
            f"Row {row_number} [FLIGHT]: Unrecognised ticket class '{class_raw}'. "
            f"Defaulted to ECONOMY."
        )

    # Select haul category and factor
    haul = "short_haul" if distance_km < SHORT_HAUL_MAX_KM else "long_haul"
    factor = FLIGHT_FACTORS[haul][ticket_class]  # kg CO2e per passenger-km

    kg_co2e = round(distance_km * factor, 4)
    return kg_co2e, round(distance_km, 2)


def calculate_hotel_emissions(row: dict, row_number: int, validation_log: list):
    """
    Calculate kg CO2e for a single hotel expense row.
    Returns kg_co2e: float | None.
    """
    nights_raw   = row.get("nights", "").strip()
    country_raw  = row.get("hotel_country", "").strip().lower()

    # Validate nights
    if not nights_raw:
        validation_log.append(
            f"Row {row_number} [HOTEL]: 'nights' field is missing. Row skipped."
        )
        return None

    try:
        nights = int(float(nights_raw))
        if nights <= 0:
            raise ValueError("nights must be positive")
    except ValueError:
        validation_log.append(
            f"Row {row_number} [HOTEL]: Invalid 'nights' value '{nights_raw}'. Row skipped."
        )
        return None

    # Resolve hotel region
    region = COUNTRY_TO_HOTEL_REGION.get(country_raw, "default")
    if region == "default" and country_raw:
        validation_log.append(
            f"Row {row_number} [HOTEL]: Country '{country_raw}' not in region map. "
            f"Used global average factor ({HOTEL_FACTORS['default']} kg CO2e/night)."
        )

    factor = HOTEL_FACTORS[region]  # kg CO2e per room-night
    kg_co2e = round(nights * factor, 4)
    return kg_co2e


def calculate_ground_emissions(row: dict, row_number: int, validation_log: list):
    """
    Calculate kg CO2e for a single ground transport expense row.
    Returns kg_co2e: float | None.
    """
    vendor_raw   = row.get("transport_vendor", "").strip().lower()
    distance_raw = row.get("distance_km", "").strip()

    # distance_km is required for ground transport
    if not distance_raw:
        validation_log.append(
            f"Row {row_number} [GROUND]: 'distance_km' is missing. "
            f"Cannot calculate emissions without distance. Row flagged for manual review."
        )
        return None

    try:
        distance_km = float(distance_raw)
        if distance_km <= 0:
            raise ValueError("distance must be positive")
    except ValueError:
        validation_log.append(
            f"Row {row_number} [GROUND]: Invalid 'distance_km' value '{distance_raw}'. Row skipped."
        )
        return None

    # Resolve transport type from vendor name
    transport_type = None
    sorted_keywords = sorted(VENDOR_TO_TRANSPORT_TYPE.keys(), key=len, reverse=True)
    for keyword in sorted_keywords:
        if keyword in vendor_raw:
            transport_type = VENDOR_TO_TRANSPORT_TYPE[keyword]
            break

    if transport_type is None:
        transport_type = "default"
        if vendor_raw:
            validation_log.append(
                f"Row {row_number} [GROUND]: Vendor '{vendor_raw}' not recognised. "
                f"Used default taxi factor ({GROUND_FACTORS['default']} kg CO2e/km)."
            )
        else:
            validation_log.append(
                f"Row {row_number} [GROUND]: Vendor name is empty. "
                f"Used default taxi factor ({GROUND_FACTORS['default']} kg CO2e/km)."
            )

    factor = GROUND_FACTORS[transport_type]  # kg CO2e per passenger-km
    kg_co2e = round(distance_km * factor, 4)
    return kg_co2e


# ---------------------------------------------------------------------------
# Django View
# ---------------------------------------------------------------------------
class TravelEmissionsView(APIView):
    """
    Django REST Framework View for Scope 3 Category 6 Corporate Travel Emissions.

    Accepts a CSV file upload (Concur / Navan expense export format) and returns:
    - Total kg CO2e per category (flights, hotels, ground transport)
    - Per-employee CO2e breakdown
    - Validation log with row-level warnings and skipped rows
    - Full processed record list
    """
    parser_classes = [MultiPartParser]

    def post(self, request, *args, **kwargs):
        # =====================================================================
        # GHG PROTOCOL CLASSIFICATION
        # Scope 3, Category 6: Business Travel
        # Source: GHG Protocol Corporate Accounting and Reporting Standard
        # https://ghgprotocol.org/corporate-standard
        #
        # [WHAT I CHOSE NOT TO BUILD — EXPLICIT EXCLUSIONS]
        #
        # 1. Real-time API Pull from Concur/Navan:
        #    SAP Concur and Navan both require enterprise OAuth2 credentials
        #    provisioned through vendor partner programs unavailable in a dev
        #    context. CSV upload is the established finance-team workflow and
        #    produces identical structured data. An API adapter can replace the
        #    CSV parser with zero changes to the downstream calculation engine.
        #
        # 2. Carbon Offset / Net Emissions Calculation:
        #    Voluntary carbon offset quality assessment (additionality, permanence,
        #    leakage risk) is a specialist domain. Including a simplified offset
        #    model risks misleading analysts. Net emissions = gross minus verified
        #    credits, tracked via a separate OffsetCredit model (see models.py).
        #
        # 3. Rail vs. Flight Substitution Suggestions:
        #    A production system should flag routes where train alternatives exist
        #    (e.g., LHR-CDG, 340 km, Eurostar available). This requires a route
        #    database and business rule engine — deferred as a reporting-layer feature.
        #
        # 4. Hotel Loyalty Programme Scope 2 Attribution:
        #    Some hotel chains publish property-level Scope 2 data (e.g., Marriott
        #    EcoMetrics). Using actual property data is more accurate than regional
        #    averages. Deferred pending data availability.
        # =====================================================================
        # 1. Retrieve uploaded file
        csv_file = request.FILES.get("file")
        if not csv_file:
            return JsonResponse(
                {"error": "No file uploaded. Please upload a Concur/Navan CSV export."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not csv_file.name.endswith(".csv"):
            return JsonResponse(
                {"error": "Invalid file format. Only .csv files are accepted."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 2. Decode file content
        try:
            file_data = csv_file.read().decode("utf-8")
        except UnicodeDecodeError:
            return JsonResponse(
                {"error": "Encoding error. Please save the CSV file in UTF-8 format."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 3. Parse CSV
        reader = csv.DictReader(io.StringIO(file_data.strip()))

        # Normalise headers to lowercase stripped keys
        try:
            raw_headers = reader.fieldnames
            if not raw_headers:
                return JsonResponse(
                    {"error": "CSV file has no headers or is empty."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except Exception:
            return JsonResponse(
                {"error": "Could not read CSV headers."},
                status=status.HTTP_400_BAD_REQUEST
            )

        normalised_headers = {h.strip().lower() for h in raw_headers}
        missing = REQUIRED_HEADERS - normalised_headers
        if missing:
            return JsonResponse(
                {
                    "error": f"Missing required CSV columns: {sorted(missing)}",
                    "validation_log": [f"Missing columns: {sorted(missing)}"]
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # 4. Process rows
        validation_log = []
        processed_records = []

        # Aggregation accumulators
        totals = {"FLIGHT": 0.0, "HOTEL": 0.0, "GROUND_TRANSPORT": 0.0}
        per_employee = {}

        row_number = 1  # Header = row 1; data starts at row 2
        skipped_rows = 0

        for raw_row in reader:
            row_number += 1
            # Normalise keys
            row = {k.strip().lower(): (v.strip() if v else "") for k, v in raw_row.items()}

            # Skip blank rows
            if not any(row.values()):
                continue

            employee_id = row.get("employee_id", "UNKNOWN")
            expense_date = row.get("expense_date", "")
            category = row.get("expense_category", "").strip().upper()
            amount = row.get("amount", "")
            currency = row.get("currency", "").upper()

            # Validate category
            if category not in VALID_CATEGORIES:
                validation_log.append(
                    f"Row {row_number}: Unrecognised expense_category '{category}'. "
                    f"Valid values: FLIGHT, HOTEL, GROUND_TRANSPORT. Row skipped."
                )
                skipped_rows += 1
                continue

            # Route to appropriate calculator
            kg_co2e = None
            distance_km = None

            if category == "FLIGHT":
                kg_co2e, distance_km = calculate_flight_emissions(row, row_number, validation_log)
            elif category == "HOTEL":
                kg_co2e = calculate_hotel_emissions(row, row_number, validation_log)
            elif category == "GROUND_TRANSPORT":
                kg_co2e = calculate_ground_emissions(row, row_number, validation_log)

            if kg_co2e is None:
                skipped_rows += 1
                continue

            # Accumulate totals
            totals[category] = round(totals[category] + kg_co2e, 4)

            # Per-employee accumulation
            if employee_id not in per_employee:
                per_employee[employee_id] = {"FLIGHT": 0.0, "HOTEL": 0.0, "GROUND_TRANSPORT": 0.0}
            per_employee[employee_id][category] = round(
                per_employee[employee_id][category] + kg_co2e, 4
            )

            # Build processed record
            record = {
                "employee_id":      employee_id,
                "expense_date":     expense_date,
                "expense_category": category,
                "kg_co2e":          kg_co2e,
                "amount":           amount,
                "currency":         currency,
            }
            if category == "FLIGHT":
                record["origin_iata"]      = row.get("origin_iata", "").upper()
                record["destination_iata"] = row.get("destination_iata", "").upper()
                record["ticket_class"]     = row.get("ticket_class", "economy").upper()
                record["distance_km"]      = distance_km
            elif category == "HOTEL":
                record["hotel_city"]    = row.get("hotel_city", "")
                record["hotel_country"] = row.get("hotel_country", "")
                record["nights"]        = row.get("nights", "")
            elif category == "GROUND_TRANSPORT":
                record["transport_vendor"] = row.get("transport_vendor", "")
                record["distance_km"]      = row.get("distance_km", "")

            processed_records.append(record)

        # 5. Compute grand total
        grand_total_kg_co2e = round(sum(totals.values()), 4)

        # 6. Build per-employee totals list
        employee_summary = [
            {
                "employee_id":           emp_id,
                "total_kg_co2e":         round(sum(cats.values()), 4),
                "flight_kg_co2e":        cats["FLIGHT"],
                "hotel_kg_co2e":         cats["HOTEL"],
                "ground_transport_kg_co2e": cats["GROUND_TRANSPORT"],
            }
            for emp_id, cats in per_employee.items()
        ]

        # 7. Construct response
        response_payload = {
            "metadata": {
                "scope":              "Scope 3 — Category 6: Business Travel",
                "emission_standard":  "DEFRA 2023 GHG Conversion Factors",
                "distance_method":    "Haversine Great-Circle Formula (IATA airport coordinates)",
                "ingestion_method":   "CSV File Upload (Concur / Navan export format)",
                "total_rows_evaluated": row_number - 1,
                "rows_processed":     len(processed_records),
                "rows_skipped":       skipped_rows,
                "grand_total_kg_co2e": grand_total_kg_co2e,
                "grand_total_tonnes_co2e": round(grand_total_kg_co2e / 1000, 6),
            },
            "totals_by_category": {
                "flight_kg_co2e":            totals["FLIGHT"],
                "hotel_kg_co2e":             totals["HOTEL"],
                "ground_transport_kg_co2e":  totals["GROUND_TRANSPORT"],
            },
            "employee_summary":  employee_summary,
            "validation_log":    validation_log,
            "processed_records": processed_records,
        }

        return JsonResponse(response_payload, status=status.HTTP_200_OK)
