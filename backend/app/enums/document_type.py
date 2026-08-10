from enum import Enum


class DocumentType(str, Enum):
    PETITION = "PETITION"
    AFFIDAVIT = "AFFIDAVIT"
    EVIDENCE = "EVIDENCE"
    CONTRACT = "CONTRACT"
    NOTICE = "NOTICE"
    JUDGMENT = "JUDGMENT"
    OTHER = "OTHER"
