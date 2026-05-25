import os
import sys
import json

requests = None
try:
    import requests
except ImportError:
    pass

# API Endpoint URL (Adjust port/host according to your Django local dev server)
API_URL = "http://127.0.0.1:8000/api/process-sap/"

# Path to the sample CSV file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "sample_sap_data.csv")

def test_sap_processor():
    print("=" * 60)
    print("  BREATH ESG - SAP CSV PROCESSOR TEST UTILITY")
    print("=" * 60)
    
    if requests is None:
        print("Error: The 'requests' library is required to run this test script.")
        print("Please install it by running: pip install requests")
        sys.exit(1)
        
    if not os.path.exists(CSV_PATH):
        print(f"Error: Sample data file not found at {CSV_PATH}")
        sys.exit(1)
        
    print(f"[*] Reading sample dataset: {CSV_PATH}")
    print("[*] Target API URL:", API_URL)
    print("[*] Sending multipart POST request...")
    
    try:
        with open(CSV_PATH, 'rb') as f:
            files = {'file': ('sample_sap_data.csv', f, 'text/csv')}
            response = requests.post(API_URL, files=files)
            
        print(f"\n[+] Request Complete! HTTP Status: {response.status_code}")
        
        if response.status_code == 200:
            res_data = response.json()
            
            # Print Metadata Summary
            print("\n" + "-" * 20 + " METADATA SUMMARY " + "-" * 20)
            print(f"Status:             {res_data['metadata']['status']}")
            print(f"Processed Facts:    {res_data['metadata']['processed_rows']} rows")
            print(f"Total Evaluated:    {res_data['metadata']['total_rows_evaluated']} rows")
            
            # Print Plain-English Analyst Logs
            print("\n" + "-" * 20 + " ANALYST VALIDATION LOGS " + "-" * 20)
            logs = res_data.get("validation_log", [])
            if logs:
                for idx, log in enumerate(logs, 1):
                    print(f"  {idx}. {log}")
            else:
                print("  (0) No validation warnings detected. File is clean!")
                
            # Print Normalized Database Models (Dimension vs Fact count)
            print("\n" + "-" * 20 + " POSTGRESQL SCHEMATIC PREVIEW " + "-" * 20)
            facilities = res_data["data"]["facilities"]
            events = res_data["data"]["procurement_events"]
            
            print(f"[*] Facility Dimensions (Unique lookup table): {len(facilities)} records")
            for fac in facilities:
                print(f"    - ID {fac['id']} [{fac['sap_werks_code']}]: {fac['name']} ({fac['city']}, {fac['country']})")
                
            print(f"\n[*] Procurement Events (Fact Table): {len(events)} transactions")
            if events:
                print("    First Fact Preview:")
                print(json.dumps(events[0], indent=6))
                
            print("\n" + "=" * 60)
            print("  SUCCESS: Backend view validated perfectly!")
            print("=" * 60)
            
        else:
            print("\n[-] Server returned an error:")
            print(response.text)
            
    except requests.exceptions.ConnectionError:
        print("\n[-] Connection Error: Could not connect to Django dev server.")
        print("    Please make sure:")
        print("    1. Your Django app is running (python manage.py runserver)")
        print(f"    2. The port matches {API_URL}")
        
if __name__ == "__main__":
    test_sap_processor()
