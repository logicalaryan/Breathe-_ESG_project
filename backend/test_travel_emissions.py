import sys
import json
import os

requests = None
try:
    import requests
except ImportError:
    pass

API_URL = "http://127.0.0.1:8000/api/travel-emissions/"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "sample_travel_data.csv")


def test_travel_emissions():
    print("=" * 60)
    print("  BREATH ESG — CORPORATE TRAVEL EMISSIONS TEST")
    print("  Scope 3 | Category 6 | DEFRA 2023 | Haversine")
    print("=" * 60)

    if requests is None:
        print("Error: The 'requests' library is required to run this test script.")
        print("Please install it by running: pip install requests")
        sys.exit(1)

    if not os.path.exists(CSV_PATH):
        print(f"[-] Sample CSV not found at: {CSV_PATH}")
        sys.exit(1)

    print(f"[*] Uploading: {CSV_PATH}")
    print(f"[*] Target:    {API_URL}\n")

    try:
        with open(CSV_PATH, "rb") as f:
            response = requests.post(API_URL, files={"file": ("sample_travel_data.csv", f, "text/csv")})

        print(f"[+] HTTP Status: {response.status_code}\n")

        if response.status_code == 200:
            data = response.json()
            meta = data.get("metadata", {})

            # ── Metadata ──────────────────────────────────────────────────
            print("-" * 20 + " METADATA " + "-" * 20)
            print(f"  Scope:              {meta.get('scope')}")
            print(f"  Standard:           {meta.get('emission_standard')}")
            print(f"  Distance Method:    {meta.get('distance_method')}")
            print(f"  Ingestion Method:   {meta.get('ingestion_method')}")
            print(f"  Rows Evaluated:     {meta.get('total_rows_evaluated')}")
            print(f"  Rows Processed:     {meta.get('rows_processed')}")
            print(f"  Rows Skipped:       {meta.get('rows_skipped')}")
            print(f"  Grand Total:        {meta.get('grand_total_kg_co2e')} kg CO2e")
            print(f"  Grand Total:        {meta.get('grand_total_tonnes_co2e')} tonnes CO2e")

            # ── Category Totals ───────────────────────────────────────────
            print("\n" + "-" * 20 + " TOTALS BY CATEGORY " + "-" * 20)
            cat = data.get("totals_by_category", {})
            print(f"  ✈  Flights:          {cat.get('flight_kg_co2e')} kg CO2e")
            print(f"  🏨  Hotels:           {cat.get('hotel_kg_co2e')} kg CO2e")
            print(f"  🚗  Ground Transport: {cat.get('ground_transport_kg_co2e')} kg CO2e")

            # ── Per Employee ──────────────────────────────────────────────
            print("\n" + "-" * 20 + " PER-EMPLOYEE BREAKDOWN " + "-" * 20)
            for emp in data.get("employee_summary", []):
                print(f"  [{emp['employee_id']}]  Total: {emp['total_kg_co2e']} kg CO2e"
                      f"  |  Flights: {emp['flight_kg_co2e']}"
                      f"  |  Hotels: {emp['hotel_kg_co2e']}"
                      f"  |  Ground: {emp['ground_transport_kg_co2e']}")

            # ── Validation Log ────────────────────────────────────────────
            logs = data.get("validation_log", [])
            print("\n" + "-" * 20 + " VALIDATION LOG " + "-" * 20)
            if logs:
                for i, log in enumerate(logs, 1):
                    print(f"  {i}. {log}")
            else:
                print("  (0) No warnings — all rows processed cleanly.")

            print("\n" + "=" * 60)
            print("  SUCCESS: Travel emissions endpoint validated.")
            print("=" * 60)

        else:
            print("[-] Server returned an error:")
            print(response.text)

    except requests.exceptions.ConnectionError:
        print("[-] Connection Error: Could not reach the mock server.")
        print("    Run: python backend/mock_server.py")
        print(f"    Then retry against: {API_URL}")


if __name__ == "__main__":
    test_travel_emissions()
