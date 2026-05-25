"""
Breathe ESG — URL Routing Configuration

Maps standard REST API endpoints to their respective Django view handlers.
"""

from django.urls import path
from backend.utility_allocation import UtilityProRataAllocationView
from backend.views import ProcessSapProcurementView
from backend.travel_emissions import TravelEmissionsView

urlpatterns = [
    # Scope 2 — Utility Pro-Rata Allocation (Purchased Electricity)
    path('api/utility-allocation/', UtilityProRataAllocationView.as_view(), name='utility-allocation'),
    
    # Scope 1 — SAP Procurement Processor (Direct Fuel Ingestion)
    path('api/process-sap/', ProcessSapProcurementView.as_view(), name='process-sap'),
    
    # Scope 3 — Corporate Travel Emissions (Haversine & DEFRA 2023)
    path('api/travel-emissions/', TravelEmissionsView.as_view(), name='travel-emissions'),
]
