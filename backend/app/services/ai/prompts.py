"""Prompts sent to the language model.

Every prompt that produces findings (clauses, risks) requires a word-for-word quote from
the document, so that LexFlow can check each finding against the text (see grounding.py).
"""

# Clause types the extractor looks for. Names follow the CUAD dataset's categories, so the
# extractor can be evaluated against CUAD's lawyer-labelled contracts.
CLAUSE_TYPES: dict[str, str] = {
    "Effective Date": "The date when the contract takes effect.",
    "Expiration Date": "When the contract's initial term ends.",
    "Renewal Term": "How the contract renews after the initial term, including automatic renewals.",
    "Governing Law": "Which state's or country's law governs the contract.",
    "Termination For Convenience": "A right to end the contract without cause, usually with notice.",
    "Anti-Assignment": "Consent or notice needed before a party can assign the contract to someone else.",
    "Exclusivity": "An exclusive dealing commitment, or a ban on selling to or working with others.",
    "Non-Compete": "A restriction on a party competing with the other party or operating in a market.",
    "Cap On Liability": "A limit on the amount of damages a party can be liable for.",
    "Insurance": "A requirement for a party to hold insurance.",
    "Audit Rights": "A right to audit the other party's books, records or premises.",
    "License Grant": "A licence granted by one party to the other.",
    "Change Of Control": "Rights or consequences triggered if a party is acquired or merges.",
    "Minimum Commitment": "A minimum amount a party must buy or pay for per period.",
}

_CLAUSE_LIST = "\n".join(f"- {name}: {description}" for name, description in CLAUSE_TYPES.items())


CLASSIFICATION_PROMPT = """
You classify legal documents. Return ONLY JSON:

{"document_type": "", "confidence": 0.0}

document_type must be one of: NDA, Employment Contract, Lease Agreement, Service Agreement,
Purchase Agreement, License Agreement, Distribution Agreement, Invoice, Court Order, Affidavit,
Legal Notice, Other.

confidence is your own estimate between 0 and 1. You are given the start of the document.
"""


SECTION_NOTES_PROMPT = """
You are reading one section of a longer legal document. Write brief factual notes on this
section only: parties, dates, amounts, obligations, rights, and anything unusual. Use short
bullet points. Do not guess about parts of the document you have not been shown.
"""


SUMMARY_PROMPT = """
Summarise the legal document (or the notes on each of its sections) in Markdown with these
headings: Purpose, Parties, Important dates, Main obligations, Points to review.

Be factual and do not invent information. If something is not stated, write "Not stated".
"""


CLAUSE_EXTRACTION_PROMPT = f"""
You are reading one section of a legal contract. Find the clauses of these types in THIS
section:

{_CLAUSE_LIST}

Return ONLY JSON:

{{
  "parties": ["names of the parties to the contract, if this section names them"],
  "clauses": [
    {{"type": "one of the types above", "quote": "", "explanation": ""}}
  ]
}}

Rules:
- "quote" must be copied word for word from the section: the sentence or sentences that
  contain the clause. Do not paraphrase, shorten with "...", or combine separate passages.
- "explanation" is one short sentence in plain English.
- Only include clauses that are actually in this section. An empty list is a valid answer.
"""


RISK_ANALYSIS_PROMPT = """
You are reviewing one section of a legal contract for terms a lawyer should look at closely
(for example one-sided obligations, uncapped liability, automatic renewal, broad
restrictions, short notice periods, or missing protections).

Return ONLY JSON:

{
  "risk_score": 0,
  "risks": [
    {"title": "", "severity": "Low", "description": "", "quote": ""}
  ]
}

Rules:
- risk_score is your judgement from 0 (nothing notable) to 100 (serious concerns) for THIS section.
- severity is Low, Medium or High.
- "quote" must be copied word for word from the section and show the term you are describing.
- Only report terms that are actually in this section. An empty list is a valid answer.
"""


COMPARISON_SUMMARY_PROMPT = """
You are given the passages that differ between an old and a new version of a legal document
(found by a text comparison). Summarise in at most five sentences what changed and why it
might matter. Only describe the changes you are shown.
"""


CASE_SYNTHESIS_PROMPT = """
You are given summaries of the documents in a legal case. Return ONLY JSON:

{
  "overall_risk_score": 0,
  "overall_risk_level": "Low",
  "executive_summary": "",
  "key_issues": [],
  "recommended_actions": []
}

Rules:
- overall_risk_score is your judgement from 0 to 100; overall_risk_level is Low, Medium or High.
- executive_summary is under 150 words.
- key_issues and recommended_actions must be based only on the summaries you are given.
"""
