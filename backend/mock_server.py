import http.server
import socketserver
import csv
import io
import json
from decimal import Decimal, InvalidOperation

PORT = 8000

# =====================================================================
# Database Simulation: Mapped Facility Dimension Records
# =====================================================================
MOCK_FACILITY_DB = {
    "1001": {"id": 1, "name": "Berlin Manufacturing Hub", "city": "Berlin", "country": "Germany", "region": "Europe"},
    "1002": {"id": 2, "name": "Munich Assembly Plant", "city": "Munich", "country": "Germany", "region": "Europe"},
    "2010": {"id": 3, "name": "Stuttgart Logistics Center", "city": "Stuttgart", "country": "Germany", "region": "Europe"},
    "3000": {"id": 4, "name": "Hamburg Port Facility", "city": "Hamburg", "country": "Germany", "region": "Europe"},
}

# =====================================================================
# ESG Normalization Constants & Unit Mappings (To Standardized SI)
# =====================================================================
UNIT_TRANSLATION_MAP = {
    "GAL": {"target": "Liters", "factor": Decimal("3.78541")},
    "GALLON": {"target": "Liters", "factor": Decimal("3.78541")},
    "L": {"target": "Liters", "factor": Decimal("1.0")},
    "LITRE": {"target": "Liters", "factor": Decimal("1.0")},
    "LTR": {"target": "Liters", "factor": Decimal("1.0")},
    "BBL": {"target": "Liters", "factor": Decimal("158.987")},
    "BARREL": {"target": "Liters", "factor": Decimal("158.987")},
    "M3": {"target": "Liters", "factor": Decimal("1000.0")},
    "KG": {"target": "Metric Tons", "factor": Decimal("0.001")},
    "KILOGRAM": {"target": "Metric Tons", "factor": Decimal("0.001")},
    "TON": {"target": "Metric Tons", "factor": Decimal("1.0")},
    "T": {"target": "Metric Tons", "factor": Decimal("1.0")},
    "MT": {"target": "Metric Tons", "factor": Decimal("1.0")},
    "LBS": {"target": "Metric Tons", "factor": Decimal("0.00045359237")},
    "POUND": {"target": "Metric Tons", "factor": Decimal("0.00045359237")},
}

# SAP German Column Headers translation dict
SAP_HEADER_MAPPING = {
    "BUKRS": "company_code",
    "WERKS": "facility_code",
    "MATNR": "material_number",
    "MEINS": "unit",
    "MENGE": "quantity",
    "WRBTR": "amount",
    "WAERS": "currency",
    "ERDAT": "entry_date",
}

class ESGProcessorHandler(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/api/process-sap/":
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not Found")
            return

        # Read the raw content length
        content_length = int(self.headers.get('Content-Length', 0))
        raw_body = self.rfile.read(content_length)

        # Basic multipart/form-data boundary parsing to extract file content
        content_type = self.headers.get('Content-Type', '')
        csv_text = ""
        
        if 'multipart/form-data' in content_type:
            try:
                boundary = content_type.split("boundary=")[1].encode()
                parts = raw_body.split(b"--" + boundary)
                for part in parts:
                    if b"Content-Disposition" in part and b"filename=" in part:
                        # Extract the body of the file part
                        subparts = part.split(b"\r\n\r\n")
                        if len(subparts) > 1:
                            file_content = subparts[1].rsplit(b"\r\n", 1)[0]
                            csv_text = file_content.decode('utf-8')
                            break
            except Exception as e:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": f"Failed to parse multipart request: {str(e)}"}).encode())
                return
        else:
            # Fallback to plain CSV upload directly in post body
            try:
                csv_text = raw_body.decode('utf-8')
            except UnicodeDecodeError:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(b'{"error": "Encoding issue, please use UTF-8"}')
                return

        if not csv_text.strip():
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"error": "CSV file content is empty"}')
            return

        # Parse CSV
        csv_data = io.StringIO(csv_text.strip())
        reader = csv.reader(csv_data)
        
        try:
            headers = next(reader)
        except StopIteration:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"error": "Empty CSV Header row"}')
            return

        headers = [h.strip().upper() for h in headers]
        required_sap_headers = ["WERKS", "MEINS", "MENGE"]
        missing_headers = [req for req in required_sap_headers if req not in headers]
        
        if missing_headers:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "error": f"Missing critical SAP headers: {missing_headers}",
                "validation_log": [f"Failure: Missing required SAP headers {missing_headers}"]
            }).encode())
            return

        col_indices = {headers.index(sap_h): mapped_h for sap_h, mapped_h in SAP_HEADER_MAPPING.items() if sap_h in headers}

        facilities_dimension = {}
        procurement_events_fact = []
        validation_log = []
        
        row_number = 1

        for row in reader:
            row_number += 1
            if not row or all(cell.strip() == "" for cell in row):
                continue

            row_data = {}
            for idx, cell in enumerate(row):
                if idx in col_indices:
                    row_data[col_indices[idx]] = cell.strip()

            werks_code = row_data.get("facility_code")
            raw_unit = row_data.get("unit", "").upper()
            raw_quantity_str = row_data.get("quantity", "0")
            raw_amount_str = row_data.get("amount", "0")
            
            # Join simulation
            facility_id = None
            if not werks_code:
                validation_log.append(f"Row {row_number}: Missing Plant Code (WERKS). Row skipped.")
                continue

            if werks_code in MOCK_FACILITY_DB:
                facility_data = MOCK_FACILITY_DB[werks_code]
                facility_id = facility_data["id"]
                if facility_id not in facilities_dimension:
                    facilities_dimension[facility_id] = {
                        "id": facility_id,
                        "sap_werks_code": werks_code,
                        "name": facility_data["name"],
                        "city": facility_data["city"],
                        "country": facility_data["country"],
                        "region": facility_data["region"]
                    }
            else:
                validation_log.append(f"Row {row_number}: Plant Code '{werks_code}' not found in database. Procurement ignored.")
                continue

            # Parse numbers
            try:
                quantity_val = Decimal(raw_quantity_str.replace(",", ""))
            except InvalidOperation:
                validation_log.append(f"Row {row_number}: Invalid quantity format '{raw_quantity_str}'. Standardized to 0.00.")
                quantity_val = Decimal("0.00")

            try:
                amount_val = Decimal(raw_amount_str.replace(",", ""))
            except InvalidOperation:
                validation_log.append(f"Row {row_number}: Invalid financial amount format '{raw_amount_str}'. Standardized to 0.00.")
                amount_val = Decimal("0.00")

            # Normalization
            normalized_quantity = quantity_val
            target_unit = raw_unit
            
            if not raw_unit:
                validation_log.append(f"Row {row_number}: Missing unit of measure (MEINS). Quantity kept in raw format.")
            elif raw_unit in UNIT_TRANSLATION_MAP:
                unit_meta = UNIT_TRANSLATION_MAP[raw_unit]
                target_unit = unit_meta["target"]
                normalized_quantity = (quantity_val * unit_meta["factor"]).quantize(Decimal("0.0001"))
            else:
                validation_log.append(f"Row {row_number}: Unrecognized SAP unit '{raw_unit}'. Kept as raw value with no ESG conversions applied.")

            # Append fact record
            procurement_fact = {
                "id": len(procurement_events_fact) + 1,
                "facility_id": facility_id,
                "company_code": row_data.get("company_code", "N/A"),
                "material_number": row_data.get("material_number", "UNKNOWN"),
                "raw_quantity": float(quantity_val),
                "raw_unit": raw_unit,
                "normalized_quantity": float(normalized_quantity),
                "normalized_unit": target_unit,
                "spend_amount": float(amount_val),
                "currency": row_data.get("currency", "EUR"),
                "entry_date": row_data.get("entry_date", "1970-01-01")
            }
            procurement_events_fact.append(procurement_fact)

        # Output payload
        response_payload = {
            "metadata": {
                "status": "Success" if not any("skipped" in l.lower() for l in validation_log) else "Partial Success",
                "processed_rows": len(procurement_events_fact),
                "total_rows_evaluated": row_number - 1
            },
            "validation_log": validation_log,
            "data": {
                "facilities": list(facilities_dimension.values()),
                "procurement_events": procurement_events_fact
            }
        }

        # Send JSON response
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(response_payload, indent=4).encode())

    # Enable CORS preflights
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

def run_server():
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("127.0.0.1", PORT), ESGProcessorHandler) as httpd:
        print("=" * 60)
        print(f"  ESG SAP CSV PROCESSOR MOCK SERVER - RUNNING ON PORT {PORT}")
        print("=" * 60)
        print("[*] Listening on http://127.0.0.1:8000/api/process-sap/")
        print("[*] Press Ctrl+C to terminate.")
        print("-" * 60)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n[!] Shutting down server...")

if __name__ == "__main__":
    run_server()
