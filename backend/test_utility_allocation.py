import sys
import json

requests = None
try:
    import requests
except ImportError:
    pass

# API Endpoint URL
API_URL = "http://127.0.0.1:8000/api/utility-allocation/"

def run_test(label, payload):
    """Send a single test payload and print formatted results."""
    print("\n" + "=" * 60)
    print(f"  TEST: {label}")
    print("=" * 60)
    print("[*] Sending JSON payload:")
    print(json.dumps(payload, indent=4))
    print(f"[*] Target API URL: {API_URL}")
    print("[*] Sending request...\n")

    try:
        response = requests.post(API_URL, json=payload)

        print(f"[+] Request Complete! HTTP Status: {response.status_code}")

        if response.status_code == 200:
            res_data = response.json()

            # Print Metadata Summary
            print("\n" + "-" * 20 + " METADATA SUMMARY " + "-" * 20)
            meta = res_data.get("metadata", {})
            print(f"Algorithm:              {meta.get('algorithm')}")
            print(f"Total Evaluated Days:   {meta.get('total_days_evaluated')} days")
            print(f"Total kWh Allocated:    {meta.get('total_kwh_distributed')} kWh")
            print(f"Read Quality:           {meta.get('read_quality')}")
            print(f"ESPI Quality Code:      {meta.get('espi_quality_of_reading_code')} "
                  f"({'Estimated' if meta.get('espi_quality_of_reading_code') == '8' else 'Validated'})")

            # Print ESPI Output
            print("\n" + "-" * 20 + " GREEN BUTTON ESPI ALLOCATION " + "-" * 20)
            allocations = res_data.get("allocated_data", [])
            for alloc in allocations:
                summary = alloc.get("UsageSummary", {})
                desc = summary.get("description", "")
                consumption = summary.get("overallConsumption", {})
                quality_code = summary.get('qualityOfReading')
                quality_label = "Estimated" if quality_code == "8" else "Validated"
                print(f"[*] {desc}")
                print(f"    - UOM: {consumption.get('uom')} (72 = Watt-hours)")
                print(f"    - Value: {consumption.get('value')} Wh")
                print(f"    - Multiplier: {consumption.get('powerOfTenMultiplier')}")
                print(f"    - Billing Duration: {summary.get('billingPeriod', {}).get('duration')} seconds")
                print(f"    - Quality Code: {quality_code} ({quality_label})")
                print()

            print("=" * 60)
            print("  SUCCESS: Allocation validated!")
            print("=" * 60)

        else:
            print("\n[-] Server returned an error:")
            print(response.text)

    except requests.exceptions.ConnectionError:
        print("\n[-] Connection Error: Could not connect to dev server.")
        print("    Please make sure:")
        print("    1. Your mock server is running (python backend/mock_server.py)")
        print(f"    2. The port matches {API_URL}")


def test_utility_allocation():
    print("=" * 60)
    print("  BREATH ESG - UTILITY PRO-RATA ALLOCATION TEST UTILITY")
    print("=" * 60)
    
    if requests is None:
        print("Error: The 'requests' library is required to run this test script.")
        print("Please install it by running: pip install requests")
        sys.exit(1)

    # --- Test 1: Standard validated (actual) meter read ---
    run_test(
        label="Validated Read (is_estimated=False / omitted)",
        payload={
            "start_date": "2023-11-09",
            "end_date": "2023-12-10",
            "total_kwh": 3500
        }
    )

    # --- Test 2: Estimated meter read — flagged for manual validation ---
    run_test(
        label="Estimated Read (is_estimated=True)",
        payload={
            "start_date": "2023-11-09",
            "end_date": "2023-12-10",
            "total_kwh": 3500,
            "is_estimated": True
        }
    )


if __name__ == "__main__":
    test_utility_allocation()
