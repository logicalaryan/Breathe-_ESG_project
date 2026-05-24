import csv
import io
import json
from decimal import Decimal, InvalidOperation
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser
from rest_framework import status

# =====================================================================
# Database Simulation: Mapped Facility Dimension Records
# In production, this would be a query like: Facility.objects.all()
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
    # Liquids -> Normalized to Liters (L)
    "GAL": {"target": "Liters", "factor": Decimal("3.78541")},
    "GALLON": {"target": "Liters", "factor": Decimal("3.78541")},
    "L": {"target": "Liters", "factor": Decimal("1.0")},
    "LITRE": {"target": "Liters", "factor": Decimal("1.0")},
    "LTR": {"target": "Liters", "factor": Decimal("1.0")},
    "BBL": {"target": "Liters", "factor": Decimal("158.987")},
    "BARREL": {"target": "Liters", "factor": Decimal("158.987")},
    "M3": {"target": "Liters", "factor": Decimal("1000.0")},
    
    # Solids/Mass -> Normalized to Metric Tons (MT)
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

class ProcessSapProcurementView(APIView):
    """
    Django REST Framework View to ingest, translate, normalize, and validate
    messy SAP procurement CSVs for non-technical ESG analysts.
    
    Expected CSV format may contain headers like:
    BUKRS, WERKS, MATNR, MEINS, MENGE, WRBTR, WAERS, ERDAT
    """
    parser_classes = [MultiPartParser]

    def post(self, request, *args, **kwargs):
        # 1. Retrieve the file from request
        csv_file = request.FILES.get('file')
        if not csv_file:
            return JsonResponse(
                {"error": "No file uploaded. Please upload a valid SAP CSV file."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 2. Safety check for file extension
        if not csv_file.name.endswith('.csv'):
            return JsonResponse(
                {"error": "Invalid file format. Only CSV files are supported."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 3. Read and decode the raw CSV stream
        try:
            file_data = csv_file.read().decode('utf-8')
            csv_data = io.StringIO(file_data)
        except UnicodeDecodeError:
            return JsonResponse(
                {"error": "Encoding issue. Please ensure the file is saved in UTF-8 format."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 4. Standard CSV reader initialization
        reader = csv.reader(csv_data)
        try:
            headers = next(reader)
        except StopIteration:
            return JsonResponse(
                {"error": "The uploaded CSV file is empty."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Trim whitespace from headers
        headers = [h.strip().upper() for h in headers]

        # Validate that essential columns exist
        required_sap_headers = ["WERKS", "MEINS", "MENGE"]
        missing_headers = [req for req in required_sap_headers if req not in headers]
        if missing_headers:
            return JsonResponse(
                {
                    "error": f"Missing critical SAP headers in file: {', '.join(missing_headers)}",
                    "validation_log": [f"Failure: Missing required SAP headers {missing_headers}"]
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create column indices mapping
        col_indices = {headers.index(sap_h): mapped_h for sap_h, mapped_h in SAP_HEADER_MAPPING.items() if sap_h in headers}

        # 5. Core state for normalized output (PostgreSQL model layout separation)
        facilities_dimension = {}  # Unique facility entities (WERKS lookups)
        procurement_events_fact = []  # Normalized transactional facts
        validation_log = []  # Detailed, analyst-friendly logs
        
        row_number = 1  # 1-based index (Header was row 1, data starts at row 2)

        for row in reader:
            row_number += 1
            if not row or all(cell.strip() == "" for cell in row):
                continue  # Skip empty lines gracefully

            row_data = {}
            # Build initial translated dictionary from columns
            for idx, cell in enumerate(row):
                if idx in col_indices:
                    row_data[col_indices[idx]] = cell.strip()

            # Retrieve critical fields
            werks_code = row_data.get("facility_code")
            raw_unit = row_data.get("unit", "").upper()
            raw_quantity_str = row_data.get("quantity", "0")
            raw_amount_str = row_data.get("amount", "0")
            
            # --- VALIDATION AND JOIN: WERKS against Facility Dimension ---
            facility_id = None
            if not werks_code:
                validation_log.append(
                    f"Row {row_number}: Missing Plant Code (WERKS). Row skipped."
                )
                continue

            if werks_code in MOCK_FACILITY_DB:
                facility_data = MOCK_FACILITY_DB[werks_code]
                facility_id = facility_data["id"]
                # Cache the lookups to output a clean Dimension dictionary
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
                validation_log.append(
                    f"Row {row_number}: Plant Code '{werks_code}' not found in database. Procurement ignored."
                )
                continue

            # --- PARSE NUMERICS ---
            try:
                quantity_val = Decimal(raw_quantity_str.replace(",", ""))
            except InvalidOperation:
                validation_log.append(
                    f"Row {row_number}: Invalid quantity format '{raw_quantity_str}'. Standardized to 0.00."
                )
                quantity_val = Decimal("0.00")

            try:
                amount_val = Decimal(raw_amount_str.replace(",", ""))
            except InvalidOperation:
                validation_log.append(
                    f"Row {row_number}: Invalid financial amount format '{raw_amount_str}'. Standardized to 0.00."
                )
                amount_val = Decimal("0.00")

            # --- TRANSFORMATION AND NORMALIZATION: Unit Conversions ---
            normalized_quantity = quantity_val
            target_unit = raw_unit
            
            if not raw_unit:
                validation_log.append(
                    f"Row {row_number}: Missing unit of measure (MEINS). Quantity kept in raw format."
                )
            elif raw_unit in UNIT_TRANSLATION_MAP:
                unit_meta = UNIT_TRANSLATION_MAP[raw_unit]
                target_unit = unit_meta["target"]
                normalized_quantity = (quantity_val * unit_meta["factor"]).quantize(Decimal("0.0001"))
            else:
                validation_log.append(
                    f"Row {row_number}: Unrecognized SAP unit '{raw_unit}'. Kept as raw value with no ESG conversions applied."
                )

            # --- FACT TABLE DATA MODEL ASSEMBLY ---
            # Model matches PostgreSQL relational schema structure with foreign key relations
            procurement_fact = {
                "id": len(procurement_events_fact) + 1,
                "facility_id": facility_id,  # FOREIGN KEY referencing Facility Dimension
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

        # 6. Response Construction in Highly Normalized Format
        response_payload = {
            "metadata": {
                "status": "Success" if not any("skipped" in l.lower() for l in validation_log) else "Partial Success",
                "processed_rows": len(procurement_events_fact),
                "total_rows_evaluated": row_number - 1
            },
            "validation_log": validation_log,
            "data": {
                "facilities": list(facilities_dimension.values()),  # The dimension table data
                "procurement_events": procurement_events_fact        # The fact table records referencing facility IDs
            }
        }

        return JsonResponse(response_payload, status=status.HTTP_200_OK)
