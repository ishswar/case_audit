from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class CaseInfo(BaseModel):
    case_number: str
    product_version: str
    product_name: str
    customer_name: str
    severity: str
    status: str
    date_created: datetime
    date_closed: datetime
    subject: str
    case_owner: str

class AuditRatings(BaseModel):
    initial_response: int
    problem_diagnosis: int
    technical_accuracy: int
    solution_quality: int
    communication: int
    overall_experience: int

class AuditReport(BaseModel):
    case_info: CaseInfo
    ratings: AuditRatings
    initial_response_feedback: str
    problem_diagnosis_feedback: str
    technical_accuracy_feedback: str
    solution_feedback: str
    communication_feedback: str
    overall_feedback: str
    recommendations: str
    case_summary: Optional[str] = ""  # A quick highlight of the case - what was the issue and how it was solved 