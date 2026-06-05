"""
Resume parser — extracts structured sections from PDF, DOCX, and text files.

Heuristic approach: detect section headers by keyword matching, then group
lines into sections. Intentionally deterministic — no LLM dependency,
reproducible output, no API cost per parse.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from .models import (
    EducationEntry,
    ExperienceEntry,
    ParsedResume,
    SectionType,
)


# Section header detection — case-insensitive, allows common variants
SECTION_PATTERNS: dict[SectionType, list[re.Pattern]] = {
    SectionType.CONTACT: [
        re.compile(r"^\s*contact(\s+info(rmation)?)?\s*:?\s*$", re.IGNORECASE),
    ],
    SectionType.SUMMARY: [
        re.compile(r"^\s*(professional\s+)?summary\s*:?\s*$", re.IGNORECASE),
        re.compile(r"^\s*profile\s*:?\s*$", re.IGNORECASE),
        re.compile(r"^\s*objective\s*:?\s*$", re.IGNORECASE),
    ],
    SectionType.EXPERIENCE: [
        re.compile(r"^\s*(work\s+)?experience\s*:?\s*$", re.IGNORECASE),
        re.compile(r"^\s*employment(\s+history)?\s*:?\s*$", re.IGNORECASE),
        re.compile(r"^\s*professional\s+experience\s*:?\s*$", re.IGNORECASE),
        re.compile(r"^\s*career\s+history\s*:?\s*$", re.IGNORECASE),
    ],
    SectionType.EDUCATION: [
        re.compile(r"^\s*education(\s+and\s+qualifications)?\s*:?\s*$", re.IGNORECASE),
        re.compile(r"^\s*academic\s+background\s*:?\s*$", re.IGNORECASE),
    ],
    SectionType.SKILLS: [
        re.compile(r"^\s*(technical\s+)?skills\s*:?\s*$", re.IGNORECASE),
        re.compile(r"^\s*core\s+competencies\s*:?\s*$", re.IGNORECASE),
        re.compile(r"^\s*expertise\s*:?\s*$", re.IGNORECASE),
    ],
    SectionType.CERTIFICATIONS: [
        re.compile(r"^\s*certifications?\s*:?\s*$", re.IGNORECASE),
        re.compile(r"^\s*licenses?\s+(and\s+certifications?)?\s*:?\s*$", re.IGNORECASE),
    ],
    SectionType.PROJECTS: [
        re.compile(r"^\s*projects?\s*:?\s*$", re.IGNORECASE),
        re.compile(r"^\s*key\s+projects\s*:?\s*$", re.IGNORECASE),
    ],
    SectionType.LANGUAGES: [
        re.compile(r"^\s*languages?\s*:?\s*$", re.IGNORECASE),
    ],
    SectionType.INTERESTS: [
        re.compile(r"^\s*interests?\s*:?\s*$", re.IGNORECASE),
        re.compile(r"^\s*hobbies\s*:?\s*$", re.IGNORECASE),
    ],
    SectionType.REFERENCES: [
        re.compile(r"^\s*references?\s*:?\s*$", re.IGNORECASE),
    ],
}


def _detect_section_type(line: str) -> Optional[SectionType]:
    """Return SectionType if line is a known section header, else None."""
    for section_type, patterns in SECTION_PATTERNS.items():
        for pat in patterns:
            if pat.match(line):
                return section_type
    return None


def _extract_text_from_pdf(path: Path) -> str:
    """Extract plain text from a PDF using pdfplumber."""
    try:
        import pdfplumber  # type: ignore
    except ImportError as e:
        raise ImportError(
            "pdfplumber is required for PDF parsing. Install with: pip install pdfplumber"
        ) from e
    text_parts: list[str] = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            text_parts.append(text)
    return "\n".join(text_parts)


def _extract_text_from_docx(path: Path) -> str:
    """Extract plain text from a DOCX using python-docx."""
    try:
        from docx import Document  # type: ignore
    except ImportError as e:
        raise ImportError(
            "python-docx is required for DOCX parsing. Install with: pip install python-docx"
        ) from e
    doc = Document(path)
    paragraphs = [p.text for p in doc.paragraphs if p.text]
    return "\n".join(paragraphs)


def _extract_text(path: Path) -> str:
    """Dispatch to the right extractor based on file extension."""
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return _extract_text_from_pdf(path)
    if suffix in {".docx", ".doc"}:
        return _extract_text_from_docx(path)
    if suffix in {".txt", ".md"}:
        return path.read_text(encoding="utf-8", errors="replace")
    return path.read_text(encoding="utf-8", errors="replace")


def _split_into_sections(text: str) -> list[tuple[SectionType, str]]:
    """Split resume text into (section_type, section_text) tuples."""
    lines = text.splitlines()
    sections: list[tuple[SectionType, str]] = []
    current_type: SectionType = SectionType.UNKNOWN
    current_buf: list[str] = []

    def flush() -> None:
        nonlocal current_type, current_buf
        if current_buf:
            sections.append((current_type, "\n".join(current_buf).strip()))
            current_buf = []

    for line in lines:
        detected = _detect_section_type(line)
        if detected is not None:
            flush()
            current_type = detected
        else:
            current_buf.append(line)
    flush()
    return sections


def _parse_experience(text: str) -> list[ExperienceEntry]:
    """Heuristic experience entry extraction."""
    entries: list[ExperienceEntry] = []
    blocks = re.split(r"\n\s*\n", text)
    date_pat = re.compile(
        r"(\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s*)?"
        r"(\d{4})\s*[-–to]+\s*"
        r"((?:(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s*)?"
        r"(?:\d{4}|Present|Current|Now))",
        re.IGNORECASE,
    )
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        lines = [ln for ln in block.splitlines() if ln.strip()]
        if not lines:
            continue
        title_company = lines[0]
        rest = " ".join(lines[1:]).strip()
        m = date_pat.search(rest or block)
        if m:
            start = m.group(2)
            end = m.group(3)
            description = rest[: m.start()].strip() + " " + rest[m.end() :].strip()
        else:
            start, end = "Unknown", "Unknown"
            description = rest
        entries.append(
            ExperienceEntry(
                title=title_company,
                company="",
                start=start,
                end=end,
                description=description,
            )
        )
    return entries


def _parse_education(text: str) -> list[EducationEntry]:
    """Heuristic education entry extraction."""
    entries: list[EducationEntry] = []
    blocks = re.split(r"\n\s*\n", text)
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        lines = [ln for ln in block.splitlines() if ln.strip()]
        if not lines:
            continue
        entries.append(
            EducationEntry(
                institution=lines[0],
                degree=" ".join(lines[1:]).strip() if len(lines) > 1 else "",
            )
        )
    return entries


def _extract_skills(text: str) -> list[str]:
    """Extract a list of skills from a skills section."""
    skills: list[str] = []
    for line in text.splitlines():
        cleaned = re.sub(r"^\s*[-•*·]\s*", "", line).strip()
        if not cleaned:
            continue
        for skill in re.split(r"[,;|]", cleaned):
            skill = skill.strip()
            if skill and len(skill) < 60:
                skills.append(skill)
    return skills


def _extract_email(text: str) -> Optional[str]:
    m = re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", text)
    return m.group(0) if m else None


def _extract_phone(text: str) -> Optional[str]:
    m = re.search(r"(\+?\d[\d\s().-]{7,}\d)", text)
    return m.group(0) if m else None


def _extract_name(text: str) -> Optional[str]:
    """The first non-empty line is usually the candidate's name."""
    for line in text.splitlines():
        line = line.strip()
        if line and len(line) < 80 and not _detect_section_type(line):
            return line
    return None


def parse_resume(path: str | Path) -> ParsedResume:
    """Parse a resume file into a structured ParsedResume object."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Resume file not found: {p}")
    text = _extract_text(p)
    return parse_resume_text(text)


def parse_resume_text(text: str) -> ParsedResume:
    """Parse a resume from raw text (no file I/O)."""
    sections = _split_into_sections(text)
    name = _extract_name(text)
    email = _extract_email(text)
    phone = _extract_phone(text)
    skills: list[str] = []
    experience: list[ExperienceEntry] = []
    education: list[EducationEntry] = []
    summary: Optional[str] = None
    for section_type, section_text in sections:
        if section_type == SectionType.SUMMARY:
            summary = section_text
        elif section_type == SectionType.SKILLS:
            skills = _extract_skills(section_text)
        elif section_type == SectionType.EXPERIENCE:
            experience = _parse_experience(section_text)
        elif section_type == SectionType.EDUCATION:
            education = _parse_education(section_text)
    return ParsedResume(
        name=name,
        email=email,
        phone=phone,
        summary=summary,
        skills=skills,
        experience=experience,
        education=education,
        raw_text=text,
    )
