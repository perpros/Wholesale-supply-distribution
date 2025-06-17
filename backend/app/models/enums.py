import enum

class RequestStatus(str, enum.Enum):
    SUBMITTED = "Submitted"
    PENDING_APPROVAL = "Pending Approval"
    APPROVED = "Approved"
    REJECTED = "Rejected"
    PROCESSING = "Processing"
    SHIPPED = "Shipped"
    DELIVERED = "Delivered"
    CANCELLED = "Cancelled"
    ON_HOLD = "On Hold"

class ProductType(str, enum.Enum):
    SOFTWARE = "Software"
    HARDWARE = "Hardware"
    SERVICE = "Service"
    OTHER = "Other"

class ProposalStatus(str, enum.Enum):
    SUBMITTED = "Submitted"
    VIEWED = "Viewed"
    ACCEPTED = "Accepted"
    REJECTED = "Rejected"
    WITHDRAWN = "Withdrawn"
