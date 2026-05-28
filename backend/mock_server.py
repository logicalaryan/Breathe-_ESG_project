import http.server
import socketserver
import csv
import io
import json
import math
import calendar
import os
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from collections import defaultdict

PORT = int(os.environ.get("PORT", 8000))

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
    def do_GET(self):
        """Health check endpoint — returns server status with CORS headers."""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(json.dumps({"status": "ok", "message": "Breathe ESG backend is running."}).encode())

    def do_POST(self):
        # Route: Utility Allocation
        if self.path == "/api/utility-allocation/":
            self.handle_utility_allocation()
            return

        # Route: SAP CSV Processor
        if self.path == "/api/process-sap/":
            self.handle_sap_processor()
            return

        # Route: Corporate Travel Emissions (Scope 3 Category 6)
        if self.path == "/api/travel-emissions/":
            self.handle_travel_emissions()
            return

        # 404
        self.send_response(404)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps({"error": "Not Found"}).encode())


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
        # Optional: is_estimated (bool, default False)
        # Flags record with ESPI qualityOfReading "8" (Estimated) for manual review.
        is_estimated = bool(payload.get('is_estimated', False))

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
                    "qualityOfReading": "8" if is_estimated else "14",
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
                "read_quality": "Estimated - Flagged for Manual Validation" if is_estimated else "Validated",
                "espi_quality_of_reading_code": "8" if is_estimated else "14",
            },
            "allocated_data": espi_usage_summaries
        }
        self.send_success_response(response_payload)

    # ==========================================================================
    # HANDLER: Corporate Travel Emissions  (Scope 3 — Category 6)
    # DEFRA 2023 GHG Conversion Factors | Haversine distance for flights
    # ==========================================================================
    def handle_travel_emissions(self):
        # ── Parse multipart CSV upload ─────────────────────────────────────────
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
                            csv_text = subparts[1].rsplit(b"\r\n", 1)[0].decode('utf-8')
                            break
            except Exception as e:
                self.send_error_response(400, f"Multipart parse error: {str(e)}")
                return
        else:
            try:
                csv_text = raw_body.decode('utf-8')
            except UnicodeDecodeError:
                self.send_error_response(400, "Encoding error. Use UTF-8 CSV.")
                return

        if not csv_text.strip():
            self.send_error_response(400, "CSV file is empty.")
            return

        reader = csv.DictReader(io.StringIO(csv_text.strip()))
        if not reader.fieldnames:
            self.send_error_response(400, "CSV has no headers.")
            return

        required = {"employee_id", "expense_date", "expense_category"}
        normalised_hdrs = {h.strip().lower() for h in reader.fieldnames}
        missing = required - normalised_hdrs
        if missing:
            self.send_error_response(400, f"Missing CSV columns: {sorted(missing)}")
            return

        # ── Emission factor tables (DEFRA 2023) ────────────────────────────────
        FLIGHT_FACTORS = {
            "short_haul": {"economy": 0.25506, "premium_economy": 0.25506,
                           "business": 0.38258, "first": 0.38258},
            "long_haul":  {"economy": 0.19499, "premium_economy": 0.28641,
                           "business": 0.42869, "first": 0.75109},
        }
        TICKET_CLASS_ALIASES = {
            "economy": "economy", "eco": "economy", "y": "economy", "coach": "economy",
            "premium economy": "premium_economy", "premium_economy": "premium_economy",
            "premium": "premium_economy", "w": "premium_economy",
            "business": "business", "business class": "business",
            "bus": "business", "c": "business", "j": "business",
            "first": "first", "first class": "first", "f": "first",
        }
        HOTEL_FACTORS = {
            "uk": 20.8, "europe": 16.5, "north_america": 31.2, "asia": 15.6,
            "middle_east": 24.5, "africa": 22.1, "latin_america": 14.3,
            "oceania": 28.9, "default": 26.4,
        }
        COUNTRY_REGION = {
            "uk": "uk", "united kingdom": "uk", "england": "uk", "scotland": "uk",
            "wales": "uk", "france": "europe", "germany": "europe", "italy": "europe",
            "spain": "europe", "netherlands": "europe", "switzerland": "europe",
            "usa": "north_america", "united states": "north_america",
            "canada": "north_america", "mexico": "north_america",
            "india": "asia", "china": "asia", "japan": "asia", "singapore": "asia",
            "south korea": "asia", "thailand": "asia", "malaysia": "asia",
            "indonesia": "asia", "vietnam": "asia", "philippines": "asia",
            "hong kong": "asia", "bangladesh": "asia", "pakistan": "asia",
            "uae": "middle_east", "united arab emirates": "middle_east",
            "saudi arabia": "middle_east", "qatar": "middle_east",
            "kuwait": "middle_east", "turkey": "middle_east",
            "south africa": "africa", "nigeria": "africa", "kenya": "africa",
            "brazil": "latin_america", "argentina": "latin_america",
            "australia": "oceania", "new zealand": "oceania",
        }
        GROUND_FACTORS = {
            "taxi": 0.14887, "rental_car": 0.19211, "train": 0.03548,
            "bus": 0.02735, "ev": 0.05302, "default": 0.14887,
        }
        VENDOR_MAP = {
            "uber": "taxi", "lyft": "taxi", "bolt": "taxi", "ola": "taxi",
            "grab": "taxi", "gett": "taxi", "addison lee": "taxi",
            "taxi": "taxi", "cab": "taxi",
            "hertz": "rental_car", "avis": "rental_car", "enterprise": "rental_car",
            "budget": "rental_car", "europcar": "rental_car", "sixt": "rental_car",
            "national rail": "train", "trainline": "train", "amtrak": "train",
            "eurostar": "train", "deutsche bahn": "train", "sncf": "train",
            "thameslink": "train", "gwr": "train", "lner": "train", "rail": "train",
            "national express": "bus", "flixbus": "bus", "greyhound": "bus",
            "megabus": "bus", "coach": "bus",
            "tesla": "ev", "electric": "ev",
        }
        AIRPORTS = {
            "LHR": (51.4700,  -0.4543), "LGW": (51.1481,  -0.1903),
            "LCY": (51.5048,  -0.0495), "MAN": (53.3537,  -2.2750),
            "BHX": (52.4539,  -1.7480), "EDI": (55.9500,  -3.3725),
            "GLA": (55.8642,  -4.4331), "CDG": (49.0097,   2.5478),
            "AMS": (52.3086,   4.7639), "FRA": (50.0333,   8.5706),
            "MUC": (48.3538,  11.7861), "ZRH": (47.4647,   8.5492),
            "MAD": (40.4936,  -3.5668), "BCN": (41.2971,   2.0785),
            "FCO": (41.8003,  12.2389), "VIE": (48.1103,  16.5697),
            "BRU": (50.9010,   4.4844), "CPH": (55.6181,  12.6561),
            "OSL": (60.1939,  11.1004), "ARN": (59.6519,  17.9186),
            "HEL": (60.3172,  24.9633), "DUB": (53.4213,  -6.2700),
            "JFK": (40.6413, -73.7781), "EWR": (40.6895, -74.1745),
            "ORD": (41.9742, -87.9073), "LAX": (33.9425,-118.4081),
            "SFO": (37.6213,-122.3790), "SEA": (47.4502,-122.3088),
            "DFW": (32.8998, -97.0403), "MIA": (25.7959, -80.2870),
            "ATL": (33.6407, -84.4277), "BOS": (42.3656, -71.0096),
            "YYZ": (43.6777, -79.6248), "MEX": (19.4363, -99.0721),
            "GRU": (-23.4356,-46.4731), "EZE": (-34.8222,-58.5358),
            "DXB": (25.2532,  55.3657), "AUH": (24.4330,  54.6511),
            "DOH": (25.2731,  51.6082), "RUH": (24.9576,  46.6988),
            "CAI": (30.1219,  31.4056), "JNB": (-26.1392, 28.2460),
            "NBO": ( -1.3192, 36.9275), "LOS": (  6.5774,  3.3214),
            "ADD": (  8.9778, 38.7993), "DEL": (28.5665,  77.1031),
            "BOM": (19.0896,  72.8656), "BLR": (13.1986,  77.7066),
            "MAA": (12.9900,  80.1693), "CCU": (22.6547,  88.4467),
            "HYD": (17.2403,  78.4294), "CMB": ( 7.1808,  79.8841),
            "SIN": ( 1.3644, 103.9915), "KUL": ( 2.7456, 101.7099),
            "BKK": (13.9132, 100.6067), "CGK": (-6.1255, 106.6559),
            "MNL": (14.5086, 121.0194), "SGN": (10.8188, 106.6519),
            "PEK": (40.0799, 116.6031), "PVG": (31.1443, 121.8083),
            "HKG": (22.3080, 113.9185), "TPE": (25.0777, 121.2326),
            "ICN": (37.4602, 126.4407), "NRT": (35.7647, 140.3864),
            "HND": (35.5494, 139.7798), "KIX": (34.4347, 135.2440),
            "SYD": (-33.9399, 151.1753), "MEL": (-37.6690, 144.8410),
            "BNE": (-27.3842, 153.1175), "AKL": (-37.0082, 174.7917),
        }

        def haversine_km(lat1, lon1, lat2, lon2):
            R = 6371.0
            p1, p2 = math.radians(lat1), math.radians(lat2)
            dp = math.radians(lat2 - lat1)
            dl = math.radians(lon2 - lon1)
            a = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
            return 2 * R * math.asin(math.sqrt(a))

        # ── Row processing ─────────────────────────────────────────────────────
        validation_log = []
        processed_records = []
        totals = {"FLIGHT": 0.0, "HOTEL": 0.0, "GROUND_TRANSPORT": 0.0}
        per_employee = {}
        row_number = 1
        skipped_rows = 0
        valid_cats = {"FLIGHT", "HOTEL", "GROUND_TRANSPORT"}

        for raw_row in reader:
            row_number += 1
            row = {k.strip().lower(): (v.strip() if v else "") for k, v in raw_row.items()}
            if not any(row.values()):
                continue

            employee_id  = row.get("employee_id", "UNKNOWN")
            expense_date = row.get("expense_date", "")
            category     = row.get("expense_category", "").strip().upper()
            amount       = row.get("amount", "")
            currency     = row.get("currency", "").upper()

            if category not in valid_cats:
                validation_log.append(
                    f"Row {row_number}: Unknown category '{category}'. Skipped."
                )
                skipped_rows += 1
                continue

            kg_co2e = None
            distance_km = None

            if category == "FLIGHT":
                origin = row.get("origin_iata", "").strip().upper()
                dest   = row.get("destination_iata", "").strip().upper()
                cls_raw = row.get("ticket_class", "economy").strip().lower()
                if origin not in AIRPORTS:
                    validation_log.append(f"Row {row_number} [FLIGHT]: Unknown origin '{origin}'. Skipped.")
                    skipped_rows += 1; continue
                if dest not in AIRPORTS:
                    validation_log.append(f"Row {row_number} [FLIGHT]: Unknown destination '{dest}'. Skipped.")
                    skipped_rows += 1; continue
                lat1, lon1 = AIRPORTS[origin]
                lat2, lon2 = AIRPORTS[dest]
                distance_km = round(haversine_km(lat1, lon1, lat2, lon2), 2)
                ticket_class = TICKET_CLASS_ALIASES.get(cls_raw)
                if ticket_class is None:
                    ticket_class = "economy"
                    validation_log.append(f"Row {row_number} [FLIGHT]: Unknown class '{cls_raw}'. Defaulted to ECONOMY.")
                haul = "short_haul" if distance_km < 1500 else "long_haul"
                factor = FLIGHT_FACTORS[haul][ticket_class]
                kg_co2e = round(distance_km * factor, 4)

            elif category == "HOTEL":
                nights_raw  = row.get("nights", "").strip()
                country_raw = row.get("hotel_country", "").strip().lower()
                if not nights_raw:
                    validation_log.append(f"Row {row_number} [HOTEL]: 'nights' missing. Skipped.")
                    skipped_rows += 1; continue
                try:
                    nights = int(float(nights_raw))
                    if nights <= 0: raise ValueError
                except ValueError:
                    validation_log.append(f"Row {row_number} [HOTEL]: Invalid nights '{nights_raw}'. Skipped.")
                    skipped_rows += 1; continue
                region = COUNTRY_REGION.get(country_raw, "default")
                if region == "default" and country_raw:
                    validation_log.append(
                        f"Row {row_number} [HOTEL]: Country '{country_raw}' not mapped. Used global average."
                    )
                kg_co2e = round(nights * HOTEL_FACTORS[region], 4)

            elif category == "GROUND_TRANSPORT":
                vendor_raw   = row.get("transport_vendor", "").strip().lower()
                dist_raw     = row.get("distance_km", "").strip()
                if not dist_raw:
                    validation_log.append(
                        f"Row {row_number} [GROUND]: 'distance_km' missing. Flagged for manual review."
                    )
                    skipped_rows += 1; continue
                try:
                    dist = float(dist_raw)
                    if dist <= 0: raise ValueError
                except ValueError:
                    validation_log.append(f"Row {row_number} [GROUND]: Invalid distance '{dist_raw}'. Skipped.")
                    skipped_rows += 1; continue
                t_type = None
                for kw, tt in VENDOR_MAP.items():
                    if kw in vendor_raw:
                        t_type = tt; break
                if t_type is None:
                    t_type = "default"
                    validation_log.append(
                        f"Row {row_number} [GROUND]: Vendor '{vendor_raw}' unknown. Used default taxi factor."
                    )
                kg_co2e = round(dist * GROUND_FACTORS[t_type], 4)

            if kg_co2e is None:
                skipped_rows += 1
                continue

            totals[category] = round(totals[category] + kg_co2e, 4)
            if employee_id not in per_employee:
                per_employee[employee_id] = {"FLIGHT": 0.0, "HOTEL": 0.0, "GROUND_TRANSPORT": 0.0}
            per_employee[employee_id][category] = round(
                per_employee[employee_id][category] + kg_co2e, 4
            )

            record = {
                "employee_id": employee_id, "expense_date": expense_date,
                "expense_category": category, "kg_co2e": kg_co2e,
                "amount": amount, "currency": currency,
            }
            if category == "FLIGHT":
                record.update({"origin_iata": row.get("origin_iata","").upper(),
                                "destination_iata": row.get("destination_iata","").upper(),
                                "ticket_class": row.get("ticket_class","").upper(),
                                "distance_km": distance_km})
            elif category == "HOTEL":
                record.update({"hotel_city": row.get("hotel_city",""),
                                "hotel_country": row.get("hotel_country",""),
                                "nights": row.get("nights","")})
            elif category == "GROUND_TRANSPORT":
                record.update({"transport_vendor": row.get("transport_vendor",""),
                                "distance_km": row.get("distance_km","")})
            processed_records.append(record)

        grand_total = round(sum(totals.values()), 4)
        employee_summary = [
            {"employee_id": eid,
             "total_kg_co2e": round(sum(c.values()), 4),
             "flight_kg_co2e": c["FLIGHT"],
             "hotel_kg_co2e": c["HOTEL"],
             "ground_transport_kg_co2e": c["GROUND_TRANSPORT"]}
            for eid, c in per_employee.items()
        ]

        self.send_success_response({
            "metadata": {
                "scope": "Scope 3 — Category 6: Business Travel",
                "emission_standard": "DEFRA 2023 GHG Conversion Factors",
                "distance_method": "Haversine Great-Circle Formula (IATA airport coordinates)",
                "ingestion_method": "CSV File Upload (Concur / Navan export format)",
                "total_rows_evaluated": row_number - 1,
                "rows_processed": len(processed_records),
                "rows_skipped": skipped_rows,
                "grand_total_kg_co2e": grand_total,
                "grand_total_tonnes_co2e": round(grand_total / 1000, 6),
            },
            "totals_by_category": {
                "flight_kg_co2e": totals["FLIGHT"],
                "hotel_kg_co2e": totals["HOTEL"],
                "ground_transport_kg_co2e": totals["GROUND_TRANSPORT"],
            },
            "employee_summary": employee_summary,
            "validation_log": validation_log,
            "processed_records": processed_records,
        })


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
        self.send_header('Access-Control-Allow-Origin', '*')
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
    with socketserver.TCPServer(("0.0.0.0", PORT), ESGProcessorHandler) as httpd:
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
