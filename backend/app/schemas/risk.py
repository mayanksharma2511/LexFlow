from pydantic import BaseModel


class RiskItem(BaseModel):
    title: str
    severity: str
    description: str


class RiskAnalysisResponse(BaseModel):
    risk_score: int
    risk_level: str
    risks: list[RiskItem]
