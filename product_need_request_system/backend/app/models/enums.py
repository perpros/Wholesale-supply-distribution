"""
Shared Enumeration types for SQLAlchemy models.
"""
import enum

class ProductTypeEnum(enum.Enum):
    """Enumeration for product types in a request."""
    SOFTWARE_LICENSE = "Software License"
    HARDWARE = "Hardware"
    CONSULTING_SERVICE = "Consulting Service"
    OTHER = "Other"

class RequestStatusEnum(enum.Enum):
    """Enumeration for the status of a request."""
    SUBMITTED = "Submitted"  # Initial status when a request is created by an end-user
    APPROVED = "Approved"  # Approved by Admin, open for proposals from suppliers
    REJECTED = "Rejected"  # Rejected by Admin
    PENDING_EVALUATION = "Pending Evaluation" # Request has expired or need met, awaiting admin/system closure
    CLOSED_FULFILLED = "Closed - Fulfilled"  # Need met, proposal selected (if any), and request is closed
    CLOSED_UNFULFILLED = "Closed - Unfulfilled"  # Expired, need not met, and closed (e.g., after renewal period without fulfillment)
    CANCELLED = "Cancelled"  # Cancelled by the End User (if allowed) or an Admin
    EXPIRED = "Expired"  # Past expiration_date, awaiting automated processing (e.g., to PENDING_EVALUATION or CLOSED_UNFULFILLED)

class ProposalStatusEnum(enum.Enum):
    """Enumeration for the status of a proposal."""
    SUBMITTED = "Submitted" # Initial status when a supplier submits a proposal
    # Potential future statuses:
    # ACCEPTED = "Accepted" # Proposal accepted by the request owner/admin
    # REJECTED = "Rejected" # Proposal rejected by the request owner/admin
    # WITHDRAWN = "Withdrawn" # Supplier withdrew the proposal
