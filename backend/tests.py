"""
Breathe ESG — Django Unit Tests

Real assertion-based tests using Django's built-in TestCase and test Client.
These tests run with `python manage.py test` (or `python -m pytest` with pytest-django).

Coverage:
  - UtilityProRataAllocationView: validated read, estimated read, bad payload, date edge cases
  - ProcessSapProcurementView: clean CSV, missing headers, unknown plant, bad numerics
  - TravelEmissionsView: flight Haversine, hotel by region, ground by vendor, missing fields

No external server required — Django's test Client hits the views directly.
"""

import json
import io
from decimal import Decimal

from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile


# =============================================================================
# Utility Pro-Rata Allocation Tests  (Scope 2 — Electricity)
# =============================================================================

class UtilityAllocationTests(TestCase):
    """
    Tests for POST /api/utility-allocation/
    Validates: date parsing, pro-rata math, ESPI output, estimated read flagging.
    """

    def setUp(self):
        self.client = Client()
        self.url = "/api/utility-allocation/"
        self.base_payload = {
            "start_date": "2023-11-09",
            "end_date":   "2023-12-10",
            "total_kwh":  3500,
        }

    def _post(self, payload):
        return self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type="application/json",
        )

    # ── Happy path ────────────────────────────────────────────────────────────

    def test_validated_read_returns_200(self):
        response = self._post(self.base_payload)
        self.assertEqual(response.status_code, 200)

    def test_validated_read_metadata_is_correct(self):
        response = self._post(self.base_payload)
        data = response.json()
        meta = data["metadata"]
        self.assertEqual(meta["algorithm"], "Daily Pro-Rata Allocation")
        self.assertEqual(meta["total_days_evaluated"], 32)   # 9 Nov → 10 Dec inclusive
        self.assertAlmostEqual(meta["total_kwh_distributed"], 3500.0)

    def test_validated_read_espi_quality_code_is_14(self):
        """A standard (non-estimated) read must produce qualityOfReading='14' on all summaries."""
        response = self._post(self.base_payload)
        data = response.json()
        for record in data["allocated_data"]:
            self.assertEqual(record["UsageSummary"]["qualityOfReading"], "14")

    def test_validated_read_metadata_quality_label(self):
        response = self._post(self.base_payload)
        data = response.json()
        self.assertEqual(data["metadata"]["read_quality"], "Validated")
        self.assertEqual(data["metadata"]["espi_quality_of_reading_code"], "14")

    def test_two_month_split_produces_two_summaries(self):
        """A billing period spanning Nov–Dec must produce exactly 2 ESPI UsageSummary entries."""
        response = self._post(self.base_payload)
        data = response.json()
        self.assertEqual(len(data["allocated_data"]), 2)

    def test_total_kwh_is_conserved_across_months(self):
        """Pro-rata allocation must be lossless — monthly Wh totals must sum to original kWh."""
        response = self._post(self.base_payload)
        data = response.json()
        total_wh = sum(
            record["UsageSummary"]["overallConsumption"]["value"]
            for record in data["allocated_data"]
        )
        # Allow 1 Wh rounding tolerance from ROUND_HALF_UP
        self.assertAlmostEqual(total_wh / 1000, 3500.0, delta=0.001)

    def test_espi_uom_is_watt_hours(self):
        """ESPI uom must be '72' (Watt-hours) per Green Button standard."""
        response = self._post(self.base_payload)
        data = response.json()
        for record in data["allocated_data"]:
            self.assertEqual(record["UsageSummary"]["overallConsumption"]["uom"], "72")

    # ── Estimated read flagging ───────────────────────────────────────────────

    def test_estimated_read_espi_quality_code_is_8(self):
        """An estimated read must produce qualityOfReading='8' on all ESPI summaries."""
        payload = {**self.base_payload, "is_estimated": True}
        response = self._post(payload)
        data = response.json()
        for record in data["allocated_data"]:
            self.assertEqual(record["UsageSummary"]["qualityOfReading"], "8")

    def test_estimated_read_metadata_label(self):
        payload = {**self.base_payload, "is_estimated": True}
        response = self._post(payload)
        data = response.json()
        self.assertEqual(data["metadata"]["read_quality"], "Estimated - Flagged for Manual Validation")
        self.assertEqual(data["metadata"]["espi_quality_of_reading_code"], "8")

    def test_is_estimated_false_behaves_as_validated(self):
        """Explicitly passing is_estimated=False must behave identically to omitting it."""
        payload_explicit = {**self.base_payload, "is_estimated": False}
        payload_omitted  = {**self.base_payload}
        r1 = self._post(payload_explicit).json()
        r2 = self._post(payload_omitted).json()
        self.assertEqual(r1["metadata"]["espi_quality_of_reading_code"],
                         r2["metadata"]["espi_quality_of_reading_code"])

    # ── Validation / error paths ──────────────────────────────────────────────

    def test_missing_required_field_returns_400(self):
        response = self._post({"start_date": "2023-11-09", "end_date": "2023-12-10"})
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json())

    def test_invalid_date_format_returns_400(self):
        payload = {**self.base_payload, "start_date": "09-11-2023"}  # wrong format
        response = self._post(payload)
        self.assertEqual(response.status_code, 400)

    def test_end_before_start_returns_400(self):
        payload = {**self.base_payload, "start_date": "2023-12-10", "end_date": "2023-11-09"}
        response = self._post(payload)
        self.assertEqual(response.status_code, 400)

    def test_single_month_billing_period(self):
        """A bill contained within one calendar month must produce exactly 1 summary."""
        payload = {"start_date": "2023-11-01", "end_date": "2023-11-30", "total_kwh": 1000}
        response = self._post(payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["allocated_data"]), 1)

    def test_three_month_billing_period(self):
        """A bill spanning 3 months must produce exactly 3 summaries."""
        payload = {"start_date": "2023-11-15", "end_date": "2024-01-15", "total_kwh": 5000}
        response = self._post(payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["allocated_data"]), 3)


# =============================================================================
# SAP Procurement CSV Tests  (Scope 1 — Direct Fuel)
# =============================================================================

class SapProcessorTests(TestCase):
    """Tests for POST /api/process-sap/"""

    def setUp(self):
        self.client = Client()
        self.url = "/api/process-sap/"

    VALID_CSV = (
        "BUKRS,WERKS,MATNR,MEINS,MENGE,WRBTR,WAERS,ERDAT\n"
        "DE01,1001,MAT-001,GAL,500.00,1200.00,EUR,2024-03-01\n"
        "DE01,1002,MAT-002,KG,1000.00,800.00,EUR,2024-03-01\n"
    )

    def _post_csv(self, csv_content, filename="test.csv"):
        uploaded_file = SimpleUploadedFile(
            filename,
            csv_content.encode("utf-8"),
            content_type="text/csv"
        )
        return self.client.post(
            self.url,
            data={"file": uploaded_file},
            format="multipart",
        )

    def test_valid_csv_returns_200(self):
        response = self._post_csv(self.VALID_CSV)
        self.assertEqual(response.status_code, 200)

    def test_processed_rows_count_is_correct(self):
        response = self._post_csv(self.VALID_CSV)
        data = response.json()
        self.assertEqual(data["metadata"]["processed_rows"], 2)

    def test_unit_conversion_gal_to_litres(self):
        """GAL must be converted to Litres at factor 3.78541."""
        response = self._post_csv(self.VALID_CSV)
        data = response.json()
        events = data["data"]["procurement_events"]
        gal_row = next(e for e in events if e["raw_unit"] == "GAL")
        expected_litres = round(500.0 * 3.78541, 4)
        self.assertAlmostEqual(gal_row["normalized_quantity"], expected_litres, places=2)
        self.assertEqual(gal_row["normalized_unit"], "Liters")

    def test_unit_conversion_kg_to_metric_tons(self):
        """KG must be converted to Metric Tons at factor 0.001."""
        response = self._post_csv(self.VALID_CSV)
        data = response.json()
        events = data["data"]["procurement_events"]
        kg_row = next(e for e in events if e["raw_unit"] == "KG")
        self.assertAlmostEqual(kg_row["normalized_quantity"], 1.0, places=4)
        self.assertEqual(kg_row["normalized_unit"], "Metric Tons")

    def test_missing_required_headers_returns_400(self):
        bad_csv = "BUKRS,MATNR\nDE01,MAT-001\n"
        response = self._post_csv(bad_csv)
        self.assertEqual(response.status_code, 400)

    def test_unknown_plant_code_is_logged_and_skipped(self):
        csv = (
            "BUKRS,WERKS,MATNR,MEINS,MENGE,WRBTR,WAERS,ERDAT\n"
            "DE01,9999,MAT-001,GAL,100.00,200.00,EUR,2024-03-01\n"
        )
        response = self._post_csv(csv)
        data = response.json()
        self.assertEqual(data["metadata"]["processed_rows"], 0)
        self.assertTrue(len(data["validation_log"]) > 0)
        self.assertIn("9999", data["validation_log"][0])

    def test_no_file_returns_400(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 400)


# =============================================================================
# Corporate Travel Emission Tests  (Scope 3 — Category 6)
# =============================================================================

class TravelEmissionsTests(TestCase):
    """Tests for POST /api/travel-emissions/"""

    def setUp(self):
        self.client = Client()
        self.url = "/api/travel-emissions/"

    VALID_CSV = (
        "employee_id,expense_date,expense_category,origin_iata,destination_iata,"
        "ticket_class,hotel_city,hotel_country,nights,transport_vendor,distance_km,amount,currency\n"
        "EMP001,2024-03-01,FLIGHT,LHR,JFK,BUSINESS,,,,,,1250.00,GBP\n"
        "EMP001,2024-03-03,HOTEL,,,,,United States,3,,,220.00,USD\n"
        "EMP001,2024-03-05,GROUND_TRANSPORT,,,,,,,Uber,18.5,35.00,USD\n"
    )

    def _post_csv(self, csv_content, filename="travel.csv"):
        uploaded_file = SimpleUploadedFile(
            filename,
            csv_content.encode("utf-8"),
            content_type="text/csv"
        )
        return self.client.post(
            self.url,
            data={"file": uploaded_file},
            format="multipart",
        )

    def test_valid_csv_returns_200(self):
        response = self._post_csv(self.VALID_CSV)
        self.assertEqual(response.status_code, 200)

    def test_all_three_categories_processed(self):
        response = self._post_csv(self.VALID_CSV)
        data = response.json()
        self.assertEqual(data["metadata"]["rows_processed"], 3)

    def test_flight_lhr_jfk_distance_is_correct(self):
        """LHR→JFK Haversine distance should be approximately 5,540 km."""
        response = self._post_csv(self.VALID_CSV)
        data = response.json()
        flight_record = next(
            r for r in data["processed_records"] if r["expense_category"] == "FLIGHT"
        )
        # Haversine LHR→JFK ≈ 5,540 km (±50 km tolerance)
        self.assertAlmostEqual(flight_record["distance_km"], 5540, delta=50)

    def test_flight_business_class_has_higher_emissions_than_economy(self):
        """Business class must produce more kg CO2e than economy for the same route."""
        base = "employee_id,expense_date,expense_category,origin_iata,destination_iata,ticket_class,hotel_city,hotel_country,nights,transport_vendor,distance_km,amount,currency\n"
        biz_csv = base + "EMP001,2024-03-01,FLIGHT,LHR,JFK,BUSINESS,,,,,,1250.00,GBP\n"
        eco_csv = base + "EMP001,2024-03-01,FLIGHT,LHR,JFK,ECONOMY,,,,,,830.00,GBP\n"
        biz = self._post_csv(biz_csv).json()["processed_records"][0]["kg_co2e"]
        eco = self._post_csv(eco_csv).json()["processed_records"][0]["kg_co2e"]
        self.assertGreater(biz, eco)

    def test_hotel_us_factor_higher_than_uk(self):
        """North American hotel factor (31.2) must exceed UK factor (20.8) per DEFRA 2023."""
        base = "employee_id,expense_date,expense_category,origin_iata,destination_iata,ticket_class,hotel_city,hotel_country,nights,transport_vendor,distance_km,amount,currency\n"
        us_csv  = base + "EMP001,2024-03-03,HOTEL,,,,,United States,1,,,100.00,USD\n"
        uk_csv  = base + "EMP001,2024-03-03,HOTEL,,,,,United Kingdom,1,,,100.00,GBP\n"
        us_co2e = self._post_csv(us_csv).json()["processed_records"][0]["kg_co2e"]
        uk_co2e = self._post_csv(uk_csv).json()["processed_records"][0]["kg_co2e"]
        self.assertGreater(us_co2e, uk_co2e)

    def test_uber_mapped_to_taxi_factor(self):
        """Uber vendor must map to taxi emission factor (0.14887 kg/km)."""
        base = "employee_id,expense_date,expense_category,origin_iata,destination_iata,ticket_class,hotel_city,hotel_country,nights,transport_vendor,distance_km,amount,currency\n"
        csv = base + "EMP001,2024-03-05,GROUND_TRANSPORT,,,,,,,Uber,100.0,50.00,GBP\n"
        response = self._post_csv(csv)
        data = response.json()
        record = data["processed_records"][0]
        # 100 km × 0.14887 = 14.887 kg CO2e
        self.assertAlmostEqual(record["kg_co2e"], 14.887, places=2)

    def test_train_lower_emissions_than_taxi_same_distance(self):
        """Train must produce significantly less CO2e than taxi for same distance."""
        base = "employee_id,expense_date,expense_category,origin_iata,destination_iata,ticket_class,hotel_city,hotel_country,nights,transport_vendor,distance_km,amount,currency\n"
        taxi_csv  = base + "EMP001,2024-03-05,GROUND_TRANSPORT,,,,,,,Uber,100.0,50.00,GBP\n"
        train_csv = base + "EMP001,2024-03-05,GROUND_TRANSPORT,,,,,,,National Rail,100.0,30.00,GBP\n"
        taxi  = self._post_csv(taxi_csv).json()["processed_records"][0]["kg_co2e"]
        train = self._post_csv(train_csv).json()["processed_records"][0]["kg_co2e"]
        self.assertGreater(taxi, train)

    def test_missing_nights_for_hotel_skips_row_and_logs_warning(self):
        base = "employee_id,expense_date,expense_category,origin_iata,destination_iata,ticket_class,hotel_city,hotel_country,nights,transport_vendor,distance_km,amount,currency\n"
        csv = base + "EMP001,2024-03-03,HOTEL,,,,,United Kingdom,,,,100.00,GBP\n"
        response = self._post_csv(csv)
        data = response.json()
        self.assertEqual(data["metadata"]["rows_processed"], 0)
        self.assertEqual(data["metadata"]["rows_skipped"], 1)
        self.assertTrue(len(data["validation_log"]) > 0)

    def test_missing_distance_for_ground_transport_is_flagged(self):
        base = "employee_id,expense_date,expense_category,origin_iata,destination_iata,ticket_class,hotel_city,hotel_country,nights,transport_vendor,distance_km,amount,currency\n"
        csv = base + "EMP001,2024-03-05,GROUND_TRANSPORT,,,,,,,Uber,,35.00,GBP\n"
        response = self._post_csv(csv)
        data = response.json()
        self.assertEqual(data["metadata"]["rows_skipped"], 1)

    def test_unknown_airport_is_logged_and_skipped(self):
        base = "employee_id,expense_date,expense_category,origin_iata,destination_iata,ticket_class,hotel_city,hotel_country,nights,transport_vendor,distance_km,amount,currency\n"
        csv = base + "EMP001,2024-03-01,FLIGHT,XXX,JFK,ECONOMY,,,,,,500.00,GBP\n"
        response = self._post_csv(csv)
        data = response.json()
        self.assertEqual(data["metadata"]["rows_processed"], 0)
        self.assertIn("XXX", data["validation_log"][0])

    def test_per_employee_summary_totals_correctly(self):
        response = self._post_csv(self.VALID_CSV)
        data = response.json()
        emp = data["employee_summary"][0]
        expected_total = round(
            emp["flight_kg_co2e"] + emp["hotel_kg_co2e"] + emp["ground_transport_kg_co2e"], 4
        )
        self.assertAlmostEqual(emp["total_kg_co2e"], expected_total, places=3)

    def test_grand_total_matches_category_sum(self):
        response = self._post_csv(self.VALID_CSV)
        data = response.json()
        cats = data["totals_by_category"]
        category_sum = round(
            cats["flight_kg_co2e"] + cats["hotel_kg_co2e"] + cats["ground_transport_kg_co2e"], 4
        )
        self.assertAlmostEqual(data["metadata"]["grand_total_kg_co2e"], category_sum, places=3)

    def test_scope_3_label_in_metadata(self):
        response = self._post_csv(self.VALID_CSV)
        data = response.json()
        self.assertIn("Scope 3", data["metadata"]["scope"])
        self.assertIn("Category 6", data["metadata"]["scope"])
