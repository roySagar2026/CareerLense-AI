"""Skill taxonomy: canonical names, aliases, families and phrase finding."""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache

from app.nlp.taxonomy_data import TAXONOMY_TEXT

# Single-letter / ambiguous language names only count in a list-like context.
BARE_CONTEXT_SKILLS = ("C", "R", "Go")

_LEFT = r"(?<![A-Za-z0-9_])"
_RIGHT = r"(?![A-Za-z0-9_])"
_BARE_LIST_PREFIX = re.compile(r"(?:^|[,;/|:•(\n])\s*$")
_BARE_WORD_PREFIX = re.compile(
    r"\b(?:with|in|and|or|of|using|like|including|as|use|uses|used|languages?|know|knows|knowing|"
    r"write|writing|written|code|coding|program|programming|proficient|fluent|familiar|plus|build|built)\s+$",
    re.I,
)
_BARE_LIST_SUFFIX = re.compile(r"\s*(?:$|[,;/|)\n]|\.?\s*$|\.\s*\n)|\s+(?:and|or)\b", re.I)
_URL_RE = re.compile(r"https?://\S+|www\.\S+|\S+@\S+\.\S+|\b(?:github|linkedin|gitlab)\.com/\S*", re.I)


@dataclass(frozen=True)
class Skill:
    canonical: str
    category: str
    aliases: tuple[str, ...]
    family: str | None
    implies: tuple[str, ...]
    case_sensitive: bool


@dataclass(frozen=True)
class Mention:
    canonical: str
    surface: str
    start: int
    end: int


def _alias_pattern(alias: str) -> str:
    return re.escape(alias).replace(r"\ ", r"[\s\-]+")


def _parse(text: str) -> dict[str, Skill]:
    skills: dict[str, Skill] = {}
    for raw in text.strip().splitlines():
        if not raw.strip() or raw.startswith("#"):
            continue
        parts = [p.strip() for p in raw.split("|")]
        parts += [""] * (5 - len(parts))
        name, category, aliases_raw, family, implies_raw = parts[:5]
        case_sensitive = name.startswith("!")
        name = name.lstrip("!")
        aliases = tuple(a.strip() for a in aliases_raw.split(",") if a.strip())
        implies = tuple(i.strip() for i in implies_raw.split(",") if i.strip())
        skills[name] = Skill(name, category, aliases, family or None, implies, case_sensitive)
    return skills


class Taxonomy:
    def __init__(self, text: str = TAXONOMY_TEXT) -> None:
        self.skills = _parse(text)
        self.alias_to_canonical: dict[str, str] = {}  # lower-case key (case-insensitive)
        self.cs_alias_to_canonical: dict[str, str] = {}  # exact key (case-sensitive)
        self.families: dict[str, list[str]] = {}
        self.implied_by: dict[str, list[str]] = {}
        ci_patterns: list[str] = []
        cs_patterns: list[str] = []

        for skill in self.skills.values():
            if skill.family:
                self.families.setdefault(skill.family, []).append(skill.canonical)
            for target in skill.implies:
                self.implied_by.setdefault(target, []).append(skill.canonical)
            forms = [skill.canonical, *skill.aliases]
            for form in forms:
                if skill.canonical in BARE_CONTEXT_SKILLS and form == skill.canonical:
                    continue  # handled by the contextual finder
                alias_cs = skill.case_sensitive or form.startswith("!")
                clean = form.lstrip("!")
                if alias_cs:
                    self.cs_alias_to_canonical[clean] = skill.canonical
                    cs_patterns.append(clean)
                else:
                    self.alias_to_canonical[clean.lower()] = skill.canonical
                    ci_patterns.append(clean)

        self._ci_re = self._compile(ci_patterns, re.I)
        self._cs_re = self._compile(cs_patterns, 0)

    @staticmethod
    def _compile(patterns: list[str], flags: int) -> re.Pattern[str] | None:
        if not patterns:
            return None
        ordered = sorted(set(patterns), key=len, reverse=True)
        body = "|".join(_alias_pattern(p) for p in ordered)
        return re.compile(f"{_LEFT}(?:{body}){_RIGHT}", flags)

    # ------------------------------------------------------------------ lookup
    def get(self, canonical: str) -> Skill | None:
        return self.skills.get(canonical)

    def category_of(self, canonical: str) -> str:
        skill = self.skills.get(canonical)
        return skill.category if skill else "other"

    def resolve(self, term: str) -> str | None:
        """Canonical name for an exact alias (case-insensitive unless the alias is case-sensitive)."""
        term = re.sub(r"\s+", " ", term.strip())
        if term in self.cs_alias_to_canonical:
            return self.cs_alias_to_canonical[term]
        key = term.lower()
        if key in self.alias_to_canonical:
            return self.alias_to_canonical[key]
        return self.skills[term].canonical if term in self.skills else None

    def related(self, canonical: str) -> list[str]:
        """Same-family skills (related, NOT equivalent)."""
        skill = self.skills.get(canonical)
        if not skill or not skill.family:
            return []
        return [c for c in self.families[skill.family] if c != canonical]

    def same_family(self, a: str, b: str) -> bool:
        sa, sb = self.skills.get(a), self.skills.get(b)
        return bool(sa and sb and sa.family and sa.family == sb.family)

    def all_forms(self, canonical: str) -> list[str]:
        skill = self.skills.get(canonical)
        if not skill:
            return [canonical]
        return [skill.canonical, *[a.lstrip("!") for a in skill.aliases]]

    # ----------------------------------------------------------------- finding
    def find(self, text: str) -> list[Mention]:
        """All skill mentions in `text` (URLs and emails are ignored)."""
        cleaned = _URL_RE.sub(lambda m: " " * len(m.group()), text)
        found: list[Mention] = []
        taken: list[tuple[int, int]] = []

        def overlaps(start: int, end: int) -> bool:
            return any(start < e and end > s for s, e in taken)

        for pattern, ci in ((self._cs_re, False), (self._ci_re, True)):
            if pattern is None:
                continue
            for match in pattern.finditer(cleaned):
                surface = match.group()
                canonical = self.resolve(surface) if ci else self.cs_alias_to_canonical.get(surface)
                if canonical and not overlaps(match.start(), match.end()):
                    taken.append((match.start(), match.end()))
                    found.append(Mention(canonical, surface, match.start(), match.end()))
        for name in BARE_CONTEXT_SKILLS:
            for match in re.finditer(rf"{_LEFT}{re.escape(name)}(?![A-Za-z0-9_+#.])", cleaned):
                if overlaps(match.start(), match.end()):
                    continue
                before, after = cleaned[: match.start()], cleaned[match.end() :]
                list_context = _BARE_LIST_PREFIX.search(before) and _BARE_LIST_SUFFIX.match(after)
                if list_context or _BARE_WORD_PREFIX.search(before):
                    taken.append((match.start(), match.end()))
                    found.append(Mention(name, name, match.start(), match.end()))
        found.sort(key=lambda m: m.start)
        return found


@lru_cache(maxsize=1)
def get_taxonomy() -> Taxonomy:
    return Taxonomy()
