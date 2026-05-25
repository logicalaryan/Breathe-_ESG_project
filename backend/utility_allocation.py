import calendar
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.parsers import JSONParser
from rest_framework import status
from collections import defaultdict

class UtilityProRataAllocationView(APIView):
    """
    Django REST Framework View for Utility Carbon Accounting.

    GHG Protocol Classification: Scope 2 — Indirect Emissions from Purchased Electricity.
    Source: GHG Protocol Corporate Accounting and Reporting Standard (WRI/WBCSD).
    Consolidation approach: Operational Control.

    Handles the ingestion of raw utility electricity bills and performs a strict
    daily pro-rata allocation of energy consumption across calendar months.
    Output is aligned to the Green Button ESPI (Energy Services Provider Interface)
    UsageSummary standard (NAESB REQ.18).
    """
    parser_classes = [JSONParser]

    def post(self, request, *args, **kwargs):
        # =====================================================================
        # [WHAT I CHOSE NOT TO BUILD - EXPLICIT EXCLUSIONS]
        #
        # 1. OAuth 2.0 Authentication: 
        #    In a real production environment, this endpoint would be protected 
        #    by `@permission_classes([IsAuthenticated])` and require a valid 
        #    Bearer token. I am explicitly mocking the auth layer here to save 
        #    time and focus purely on the deterministic allocation logic.
        #
        # 2. PDF OCR Document Extraction: 
        #    Real utility bills almost always arrive as PDFs. Building a computer 
        #    vision/OCR pipeline (e.g., using AWS Textract or Tesseract) to 
        #    extract the start_date, end_date, and total_kwh is omitted here. 
        #    We assume the upstream OCR layer has already successfully parsed 
        #    the PDF into the clean JSON payload that we are receiving below.
        #
        # [WHAT IS INCLUDED - ESTIMATED READ FLAGGING]
        #    Utility meters sometimes produce estimated reads (e.g., when a 
        #    physical inspection is missed). Per the Green Button ESPI standard,
        #    qualityOfReading code "8" = Estimated and "14" = Validated.
        #    Rather than rejecting estimated reads (which would create data gaps),
        #    we accept them and flag each ESPI UsageSummary accordingly so 
        #    downstream auditors and ESG reviewers can apply manual validation.
        # =====================================================================

        payload = request.data
        start_date_str = payload.get('start_date')
        end_date_str = payload.get('end_date')
        total_kwh_raw = payload.get('total_kwh')
        # Optional field: is_estimated (bool, default False)
        # When True, ESPI qualityOfReading is set to "8" (Estimated) instead
        # of "14" (Validated), flagging the record for manual review.
        is_estimated = bool(payload.get('is_estimated', False))

        if not all([start_date_str, end_date_str, total_kwh_raw]):
            return JsonResponse(
                {"error": "Missing required fields: start_date, end_date, or total_kwh"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Standardizing date parsing (assuming YYYY-MM-DD input, or parsing specific strings)
            # For flexibility in this assessment, we'll parse standard ISO formats
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
            total_kwh = Decimal(str(total_kwh_raw))
        except ValueError as e:
            return JsonResponse(
                {"error": f"Data format error: {str(e)}. Use YYYY-MM-DD for dates."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if end_date < start_date:
            return JsonResponse(
                {"error": "end_date must be strictly after start_date."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # 1. Calculate Total Days (Inclusive of start and end date as is standard for utility ledgers)
        total_days = (end_date - start_date).days + 1
        
        if total_days <= 0:
            return JsonResponse({"error": "Invalid date range"}, status=status.HTTP_400_BAD_REQUEST)

        # 2. Calculate Daily Pro-Rata Rate
        # We divide the total consumption by the exact number of billed days.
        daily_kwh = total_kwh / Decimal(total_days)

        # 3. Allocate to Calendar Month Buckets
        # Iterating day-by-day guarantees 100% precision for leap years and varying month lengths.
        monthly_buckets = defaultdict(Decimal)
        current_date = start_date
        
        while current_date <= end_date:
            month_key = current_date.strftime("%Y-%m") # e.g., "2023-11"
            monthly_buckets[month_key] += daily_kwh
            current_date += timedelta(days=1)

        # 4. Map to Green Button ESPI 'UsageSummary' Standard
        # The ESPI Standard represents energy in specific UOMs (Unit of Measure).
        # uom 72 = Watt-hours (Wh). 1 kWh = 1,000 Wh. 
        # We translate kWh into standard Wh base units to align with strict ESPI compliance.
        espi_usage_summaries = []
        
        for month_key, kwh_val in monthly_buckets.items():
            # Round to 2 decimal places for initial precision, then convert to base Watt-hours
            rounded_kwh = kwh_val.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            watt_hours = int(rounded_kwh * Decimal('1000'))
            
            # Reconstruct the exact overlapping start and end dates for this specific month bucket
            year, month = map(int, month_key.split('-'))
            _, last_day_of_month = calendar.monthrange(year, month)
            
            bucket_start_date = max(start_date, datetime(year, month, 1).date())
            bucket_end_date = min(end_date, datetime(year, month, last_day_of_month).date())
            
            # ESPI billingPeriod expects duration in seconds and start in epoch time
            bucket_duration_seconds = int((bucket_end_date - bucket_start_date + timedelta(days=1)).total_seconds())
            bucket_start_epoch = int(datetime(bucket_start_date.year, bucket_start_date.month, bucket_start_date.day).timestamp())

            usage_summary = {
                "UsageSummary": {
                    "billingPeriod": {
                        "duration": bucket_duration_seconds,
                        "start": bucket_start_epoch
                    },
                    "overallConsumption": {
                        "powerOfTenMultiplier": "0",  # Base unit
                        "uom": "72",                  # ESPI code for Watt-hours (Wh)
                        "value": watt_hours
                    },
                    # ESPI qualityOfReading: "8" = Estimated (needs manual review),
                    # "14" = Validated (actual meter read, audit-safe).
                    "qualityOfReading": "8" if is_estimated else "14",
                    "statusTimeStamp": int(datetime.now().timestamp()),
                    "description": f"Pro-rata allocated consumption for {bucket_start_date.strftime('%B %Y')}"
                }
            }
            espi_usage_summaries.append(usage_summary)

        # 5. Output Response
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

        return JsonResponse(response_payload, status=status.HTTP_200_OK)
