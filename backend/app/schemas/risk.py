from pydantic import BaseModel


class RiskItem(BaseModel):
    title: str
    severity: str
    description: str


class RiskAnalysisResponse(BaseModel):
    risk_score: int | None = None  # None when the analysis could not be run
    risk_level: str
    risks: list[RiskItem]
    note: str | None = None
