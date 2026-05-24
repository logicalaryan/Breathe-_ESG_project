import http.server
import socketserver
import csv
import io
import json
import calendar
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from collections import defaultdict

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
        # Route: Utility Allocation
        if self.path == "/api/utility-allocation/":
            self.handle_utility_allocation()
            return

        # Route: SAP CSV Processor
        if self.path == "/api/process-sap/":
            self.handle_sap_processor()
            return

        # 404
        self.send_response(404)
        self.end_headers()
        self.wfile.write(b"Not Found")

    def handle_utility_allocation(self):
        content_length = int(self.headers.get('Content-Length', 0))
        raw_body = self.rfile.read(content_length)

        try:
            payload = json.loads(raw_body.decode('utf-8'))
        except json.JSONDecodeError:
            self.send_error_response(400, "Invalid JSON payload")
            return

        start_date_str = payload.get('start_date')
        end_date_str = payload.get('end_date')
        total_kwh_raw = payload.get('total_kwh')

        if not all([start_date_str, end_date_str, total_kwh_raw]):
            self.send_error_response(400, "Missing required fields: start_date, end_date, or total_kwh")
            return

        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
            total_kwh = Decimal(str(total_kwh_raw))
        except ValueError as e:
            self.send_error_response(400, f"Data format error: {str(e)}. Use YYYY-MM-DD for dates.")
            return

        if end_date < start_date:
            self.send_error_response(400, "end_date must be strictly after start_date.")
            return

        total_days = (end_date - start_date).days + 1
        if total_days <= 0:
            self.send_error_response(400, "Invalid date range")
            return

        daily_kwh = total_kwh / Decimal(total_days)
        monthly_buckets = defaultdict(Decimal)
        current_date = start_date
        
        while current_date <= end_date:
            month_key = current_date.strftime("%Y-%m")
            monthly_buckets[month_key] += daily_kwh
            current_date += timedelta(days=1)

        espi_usage_summaries = []
        
        for month_key, kwh_val in monthly_buckets.items():
            rounded_kwh = kwh_val.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            watt_hours = int(rounded_kwh * Decimal('1000'))
            year, month = map(int, month_key.split('-'))
            _, last_day_of_month = calendar.monthrange(year, month)
            
            bucket_start_date = max(start_date, datetime(year, month, 1).date())
            bucket_end_date = min(end_date, datetime(year, month, last_day_of_month).date())
            
            bucket_duration_seconds = int((bucket_end_date - bucket_start_date + timedelta(days=1)).total_seconds())
            bucket_start_epoch = int(datetime(bucket_start_date.year, bucket_start_date.month, bucket_start_date.day).timestamp())

            usage_summary = {
                "UsageSummary": {
                    "billingPeriod": {
                        "duration": bucket_duration_seconds,
                        "start": bucket_start_epoch
                    },
                    "overallConsumption": {
                        "powerOfTenMultiplier": "0",
                        "uom": "72",
                        "value": watt_hours
                    },
                    "qualityOfReading": "14",
                    "statusTimeStamp": int(datetime.now().timestamp()),
                    "description": f"Pro-rata allocated consumption for {bucket_start_date.strftime('%B %Y')}"
                }
            }
            espi_usage_summaries.append(usage_summary)

        response_payload = {
            "metadata": {
                "algorithm": "Daily Pro-Rata Allocation",
                "total_days_evaluated": total_days,
                "total_kwh_distributed": float(total_kwh),
            },
            "allocated_data": espi_usage_summaries
        }
        self.send_success_response(response_payload)


    def handle_sap_processor(self):
        content_length = int(self.headers.get('Content-Length', 0))
        raw_body = self.rfile.read(content_length)

        content_type = self.headers.get('Content-Type', '')
        csv_text = ""
        
        if 'multipart/form-data' in content_type:
            try:
                boundary = content_type.split("boundary=")[1].encode()
                parts = raw_body.split(b"--" + boundary)
                for part in parts:
                    if b"Content-Disposition" in part and b"filename=" in part:
                        subparts = part.split(b"\r\n\r\n")
                        if len(subparts) > 1:
                            file_content = subparts[1].rsplit(b"\r\n", 1)[0]
                            csv_text = file_content.decode('utf-8')
                            break
            except Exception as e:
                self.send_error_response(400, f"Failed to parse multipart request: {str(e)}")
                return
        else:
            try:
                csv_text = raw_body.decode('utf-8')
            except UnicodeDecodeError:
                self.send_error_response(400, "Encoding issue, please use UTF-8")
                return

        if not csv_text.strip():
            self.send_error_response(400, "CSV file content is empty")
            return

        csv_data = io.StringIO(csv_text.strip())
        reader = csv.reader(csv_data)
        
        try:
            headers = next(reader)
        except StopIteration:
            self.send_error_response(400, "Empty CSV Header row")
            return

        headers = [h.strip().upper() for h in headers]
        required_sap_headers = ["WERKS", "MEINS", "MENGE"]
        missing_headers = [req for req in required_sap_headers if req not in headers]
        
        if missing_headers:
            self.send_success_response({
                "error": f"Missing critical SAP headers: {missing_headers}",
                "validation_log": [f"Failure: Missing required SAP headers {missing_headers}"]
            }, status_code=400)
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
                validation_log.append(f"Row {row_number}: Plant Code is missing")
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
                validation_log.append(f"Row {row_number}: Plant Code {werks_code} not found in database")
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
                validation_log.append(f"Row {row_number}: Unit is missing")
            elif raw_unit in UNIT_TRANSLATION_MAP:
                unit_meta = UNIT_TRANSLATION_MAP[raw_unit]
                target_unit = unit_meta["target"]
                normalized_quantity = (quantity_val * unit_meta["factor"]).quantize(Decimal("0.0001"))
            else:
                validation_log.append(f"Row {row_number}: Unit {raw_unit} is unrecognized")

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
        self.send_success_response(response_payload)

    def send_error_response(self, code, message):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"error": message}).encode())

    def send_success_response(self, payload, status_code=200):
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(payload, indent=4).encode())

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
        print(f"  ESG MOCK SERVER - RUNNING ON PORT {PORT}")
        print("=" * 60)
        print("[*] Listening on:")
        print("    - http://127.0.0.1:8000/api/process-sap/")
        print("    - http://127.0.0.1:8000/api/utility-allocation/")
        print("[*] Press Ctrl+C to terminate.")
        print("-" * 60)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n[!] Shutting down server...")

if __name__ == "__main__":
    run_server()
