"""Decides how strongly a resume sentence evidences a skill.

Levels: demonstrated (used in a described piece of work) > listed (claimed in a skills
list, summary or certification) > mentioned (weak/incidental). A keyword that merely
appears in an unrelated or aspirational sentence is never a demonstrated skill.
"""

from __future__ import annotations

import re

EVIDENCE_RANK = {"demonstrated": 3, "listed": 2, "mentioned": 1}
EVIDENCE_CREDIT = {"demonstrated": 1.0, "listed": 0.7, "mentioned": 0.35}

_USAGE_VERBS = (
    "built|build|building|developed|develop|developing|implemented|implement|implementing|designed|"
    "design|designing|deployed|deploy|deploying|used|using|use|wrote|written|writing|created|create|"
    "creating|integrated|integrate|integrating|optimized|optimised|optimizing|automated|automate|"
    "automating|migrated|migrate|configured|configure|maintained|maintain|managed|manage|led|lead|"
    "tested|test|testing|engineered|architected|launched|delivered|shipped|containerized|containerised|"
    "trained|analyzed|analysed|improved|reduced|increased|refactored|set up|setup|provisioned|"
    "monitored|debugged|scaled|queried|visualized|visualised|leveraged|utilized|utilised|applied|"
    "constructed|produced|executed|performed|collaborated|worked|working|experience"
)
_USAGE_RE = re.compile(rf"\b(?:{_USAGE_VERBS})\b", re.I)
_WEAK_RE = re.compile(
    r"\b(?:learning|currently learning|want to learn|wants to learn|interested in|exploring|"
    r"plan(?:ning)? to|studying|beginner|basic knowledge|aspir\w+|looking to|yet to|no experience)\b",
    re.I,
)
_TECH_LINE_RE = re.compile(
    r"^\s*(?:tech(?:nologies| stack)?|stack|tools?|environment|built with|technologies used|tools used)\s*[:\-–]",
    re.I,
)

WORK_SECTIONS = {"experience", "projects"}
LIST_SECTIONS = {"skills", "summary", "certifications", "achievements"}


def is_tech_line(text: str) -> bool:
    return bool(_TECH_LINE_RE.match(text))


def classify_evidence(text: str, section_type: str, is_bullet: bool) -> str:
    """Evidence level for a skill mentioned in `text` inside `section_type`."""
    if _WEAK_RE.search(text):
        return "mentioned"
    if section_type == "skills":
        return "listed"
    if section_type in WORK_SECTIONS:
        if is_tech_line(text):
            return "demonstrated"
        words = len(text.split())
        if _USAGE_RE.search(text) and words >= 3:
            return "demonstrated"
        if is_bullet and words >= 8:
            return "demonstrated"
        return "listed"
    if section_type in LIST_SECTIONS:
        return "listed"
    return "mentioned"
