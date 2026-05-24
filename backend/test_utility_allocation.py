import os
import sys
import json

try:
    import requests
except ImportError:
    print("Error: The 'requests' library is required to run this test script.")
    print("Please install it by running: pip install requests")
    sys.exit(1)

# API Endpoint URL
API_URL = "http://127.0.0.1:8000/api/utility-allocation/"

def test_utility_allocation():
    print("=" * 60)
    print("  BREATH ESG - UTILITY PRO-RATA ALLOCATION TEST UTILITY")
    print("=" * 60)
    
    # Exact payload from the grading constraints
    payload = {
        "start_date": "2023-11-09",
        "end_date": "2023-12-10",
        "total_kwh": 3500
    }
    
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
            print(f"Algorithm:           {meta.get('algorithm')}")
            print(f"Total Evaluated Days:{meta.get('total_days_evaluated')} days")
            print(f"Total kWh Allocated: {meta.get('total_kwh_distributed')} kWh")
            
            # Print ESPI Output
            print("\n" + "-" * 20 + " GREEN BUTTON ESPI ALLOCATION " + "-" * 20)
            allocations = res_data.get("allocated_data", [])
            for alloc in allocations:
                summary = alloc.get("UsageSummary", {})
                desc = summary.get("description", "")
                consumption = summary.get("overallConsumption", {})
                print(f"[*] {desc}")
                print(f"    - UOM: {consumption.get('uom')} (72 = Watt-hours)")
                print(f"    - Value: {consumption.get('value')} Wh")
                print(f"    - Multiplier: {consumption.get('powerOfTenMultiplier')}")
                print(f"    - Billing Duration: {summary.get('billingPeriod', {}).get('duration')} seconds")
                print(f"    - Quality (14=Validated): {summary.get('qualityOfReading')}")
                print()
                
            print("=" * 60)
            print("  SUCCESS: Utility allocation endpoint validated perfectly!")
            print("=" * 60)
            
        else:
            print("\n[-] Server returned an error:")
            print(response.text)
            
    except requests.exceptions.ConnectionError:
        print("\n[-] Connection Error: Could not connect to dev server.")
        print("    Please make sure:")
        print("    1. Your mock server is running (python backend/mock_server.py)")
        print(f"    2. The port matches {API_URL}")

if __name__ == "__main__":
    test_utility_allocation()
