from enum import StrEnum
class Role(StrEnum):
    ADMIN='admin'
    BEEKEEPER='beekeeper'
    VIEWER='viewer'
class CareKind(StrEnum):
    FEED='feed'
    REQUEEN='requeen'
class CareState(StrEnum):
    PLANNED='planned'
    EXECUTED='executed'
    RECHECKED='rechecked'
    NEEDS_REQUEEN='needs_requeen'
    CLOSED='closed'
    CANCELLED='cancelled'
class VisitState(StrEnum):
    RECORDED='recorded'
    SCREENING='screening'
    SCREENED='screened'
    CARING='caring'
    FOLLOWUP='followup'
    NEEDS_REQUEEN='needs_requeen'
    RETEST_PENDING='retest_pending'
    CLOSED='closed'
    STALE='stale'
    BLOCKED='blocked'
class RetestState(StrEnum):
    PENDING='pending'
    RESOLVED='resolved'
