"""
Breathe ESG — Django ORM Data Models

These models define the persistent data layer for the ESG carbon accounting
platform. They implement a multi-tenant architecture (Organization → Facility →
EmissionRecord) with full audit trail support, emission factor versioning, and
a state-machine workflow for analyst review.

GHG Protocol Boundary: Operational Control approach.
Supported scopes: Scope 1 (direct), Scope 2 (electricity), Scope 3 (travel/supply chain).
"""

from django.db import models
from django.conf import settings
from django.utils import timezone


# =============================================================================
# TENANT LAYER
# =============================================================================

class Organization(models.Model):
    """
    Top-level tenant entity. All data is partitioned by organization.
    Supports multi-tenant SaaS deployment with row-level isolation.
    """
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, db_index=True)
    reporting_currency = models.CharField(max_length=3, default="USD")
    ghg_protocol_boundary = models.CharField(
        max_length=50,
        default="operational_control",
        help_text="GHG Protocol consolidation approach: operational_control | equity_share | financial_control"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Facility(models.Model):
    """
    Physical location entity — factory, office, warehouse, or data center.
    Dimension table referenced by all emission records.
    Maps to SAP WERKS (plant code) for procurement data ingestion.
    """
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="facilities"
    )
    sap_werks_code = models.CharField(
        max_length=20, db_index=True, blank=True,
        help_text="SAP plant code (WERKS field). Used for procurement data joins."
    )
    name = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    region = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["country", "name"]
        unique_together = [("organization", "sap_werks_code")]

    def __str__(self):
        return f"{self.name} ({self.city}, {self.country})"


# =============================================================================
# EMISSION RECORDS — FACT TABLE
# =============================================================================

class EmissionRecord(models.Model):
    """
    Core fact table. One row per discrete emission event after calculation.

    Design decisions:
    - Immutable raw_payload: the original source data is stored as JSON and
      never modified. If a record is recalculated (e.g., after a factor update),
      a NEW record is created and the old one is superseded, preserving audit trail.
    - emission_factor_version: tracks which DEFRA/GHG Protocol version was used
      so historical records are not silently recalculated when factors update.
    - status workflow: PENDING → VALIDATED or ESTIMATED → APPROVED or REJECTED.
      ESTIMATED records (from estimated utility meter reads) require manual sign-off.
    """

    class Scope(models.IntegerChoices):
        SCOPE_1 = 1, "Scope 1 — Direct Emissions (Fuel, Gas)"
        SCOPE_2 = 2, "Scope 2 — Indirect Emissions (Purchased Electricity)"
        SCOPE_3 = 3, "Scope 3 — Value Chain Emissions (Travel, Supply Chain)"

    class SourceType(models.TextChoices):
        UTILITY_ELECTRICITY = "UTILITY",   "Utility Electricity (Green Button ESPI)"
        SAP_PROCUREMENT     = "SAP",       "SAP Procurement CSV"
        CORPORATE_TRAVEL    = "TRAVEL",    "Corporate Travel (Concur/Navan)"

    class Status(models.TextChoices):
        PENDING   = "PENDING",   "Pending — Awaiting analyst review"
        VALIDATED = "VALIDATED", "Validated — Actual meter/source read"
        ESTIMATED = "ESTIMATED", "Estimated — Meter read was estimated; needs reconciliation"
        APPROVED  = "APPROVED",  "Approved — Sign-off complete, eligible for reporting"
        REJECTED  = "REJECTED",  "Rejected — Record excluded from reporting"
        SUPERSEDED = "SUPERSEDED", "Superseded — Replaced by a corrected record"

    # ── Relationships ──────────────────────────────────────────────────────────
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="emission_records"
    )
    facility = models.ForeignKey(
        Facility, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="emission_records",
        help_text="NULL for travel records which are employee-level, not facility-level."
    )
    superseded_by = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="supersedes",
        help_text="Points to the corrected record that replaced this one."
    )

    # ── Classification ─────────────────────────────────────────────────────────
    scope = models.IntegerField(choices=Scope.choices)
    source_type = models.CharField(max_length=20, choices=SourceType.choices)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True
    )

    # ── Billing Period ─────────────────────────────────────────────────────────
    period_start = models.DateField(db_index=True)
    period_end = models.DateField()

    # ── Emission Quantity ──────────────────────────────────────────────────────
    kg_co2e = models.DecimalField(
        max_digits=14, decimal_places=4,
        help_text="CO2 equivalent in kilograms. Always stored in kg; convert to tonnes for reporting."
    )
    # For utility records: stores kWh; for SAP: normalized quantity; for travel: km or nights
    raw_quantity = models.DecimalField(
        max_digits=14, decimal_places=4, null=True, blank=True
    )
    raw_unit = models.CharField(max_length=20, blank=True)

    # ── Emission Factor Versioning ─────────────────────────────────────────────
    emission_factor_version = models.CharField(
        max_length=100,
        default="DEFRA 2023",
        help_text="The emission factor dataset version used for this calculation. "
                  "Records must NOT be silently recalculated when factors update."
    )
    emission_factor_value = models.DecimalField(
        max_digits=10, decimal_places=6, null=True, blank=True,
        help_text="The exact factor applied (kg CO2e per unit) for auditability."
    )

    # ── Source Data Preservation ───────────────────────────────────────────────
    raw_payload = models.JSONField(
        help_text="Immutable original source data (CSV row, API response, etc.). "
                  "Never modified after creation. Required for audit and dispute resolution."
    )

    # ── ESPI-specific fields (utility records) ─────────────────────────────────
    espi_quality_of_reading = models.CharField(
        max_length=5, blank=True,
        help_text="Green Button ESPI qualityOfReading code. '14'=Validated, '8'=Estimated."
    )

    # ── Travel-specific fields ─────────────────────────────────────────────────
    employee_id = models.CharField(
        max_length=50, blank=True, db_index=True,
        help_text="Employee identifier for Scope 3 travel records."
    )
    travel_category = models.CharField(
        max_length=20, blank=True,
        help_text="FLIGHT | HOTEL | GROUND_TRANSPORT"
    )

    # ── Audit Trail ───────────────────────────────────────────────────────────
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="created_emission_records"
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="approved_emission_records"
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    analyst_comment = models.TextField(
        blank=True,
        help_text="Free-text analyst note recorded at approval or rejection."
    )

    class Meta:
        ordering = ["-period_start", "-created_at"]
        indexes = [
            models.Index(fields=["organization", "scope", "period_start"]),
            models.Index(fields=["organization", "status"]),
            models.Index(fields=["organization", "source_type", "period_start"]),
            models.Index(fields=["employee_id", "period_start"]),
        ]

    def __str__(self):
        return (
            f"{self.get_scope_display()} | {self.source_type} | "
            f"{self.period_start} → {self.period_end} | "
            f"{self.kg_co2e} kg CO2e [{self.status}]"
        )

    def approve(self, user, comment: str = ""):
        """Transition record to APPROVED. Records approver identity and timestamp."""
        self.status = self.Status.APPROVED
        self.approved_by = user
        self.approved_at = timezone.now()
        self.analyst_comment = comment
        self.save(update_fields=["status", "approved_by", "approved_at", "analyst_comment", "updated_at"])

    def reject(self, user, comment: str = ""):
        """Transition record to REJECTED with mandatory analyst comment."""
        self.status = self.Status.REJECTED
        self.approved_by = user
        self.approved_at = timezone.now()
        self.analyst_comment = comment
        self.save(update_fields=["status", "approved_by", "approved_at", "analyst_comment", "updated_at"])

    def supersede(self, replacement: "EmissionRecord"):
        """Mark this record as superseded by a corrected replacement."""
        self.status = self.Status.SUPERSEDED
        self.superseded_by = replacement
        self.save(update_fields=["status", "superseded_by", "updated_at"])


# =============================================================================
# DATA INGESTION LOG
# =============================================================================

class IngestionJob(models.Model):
    """
    Tracks each CSV upload or API pull event.
    Provides audit trail of who uploaded what, when, and the outcome.
    """

    class JobStatus(models.TextChoices):
        PROCESSING = "PROCESSING", "Processing"
        COMPLETED  = "COMPLETED",  "Completed"
        PARTIAL    = "PARTIAL",    "Partial — some rows failed"
        FAILED     = "FAILED",     "Failed"

    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="ingestion_jobs"
    )
    source_type = models.CharField(max_length=20, choices=EmissionRecord.SourceType.choices)
    filename = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=JobStatus.choices, default=JobStatus.PROCESSING)
    total_rows = models.IntegerField(default=0)
    processed_rows = models.IntegerField(default=0)
    skipped_rows = models.IntegerField(default=0)
    validation_log = models.JSONField(default=list)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.source_type} | {self.filename} | {self.status} ({self.created_at:%Y-%m-%d})"
