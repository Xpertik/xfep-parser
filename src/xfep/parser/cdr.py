"""CDR (Constancia de Recepción) parser for SUNAT ApplicationResponse."""

from __future__ import annotations

import io
import re
import zipfile
from dataclasses import dataclass, field

from lxml import etree

from xfep.parser._namespaces import NS
from xfep.parser.errors import CdrParseError, InvalidXmlError, InvalidZipError
from xfep.parser.status import CdrStatus, resolve_status

_NOTE_PATTERN = re.compile(r"^(\d+)\s*-\s*(.+)$", re.DOTALL)


@dataclass(frozen=True, slots=True)
class CdrNote:
    """A single note from the CDR response."""

    code: str | None
    text: str


@dataclass(frozen=True, slots=True)
class CdrResponse:
    """Parsed CDR response from SUNAT."""

    code: str
    description: str
    status: CdrStatus
    notes: list[CdrNote] = field(default_factory=list)
    document_id: str | None = None
    document_type: str | None = None


def _extract_xml_from_zip(cdr_bytes: bytes) -> bytes:
    """Extract the first XML file from a CDR ZIP archive."""
    if not cdr_bytes:
        raise CdrParseError("Empty input bytes")

    try:
        with zipfile.ZipFile(io.BytesIO(cdr_bytes)) as zf:
            xml_files = [n for n in zf.namelist() if n.lower().endswith(".xml")]
            if not xml_files:
                raise InvalidZipError("ZIP archive contains no XML files")
            return zf.read(xml_files[0])
    except zipfile.BadZipFile as exc:
        raise InvalidZipError(f"Invalid ZIP archive: {exc}") from exc


def _parse_note(text: str) -> CdrNote:
    """Parse a note string into CdrNote.

    Format: "4252 - Some observation text" → CdrNote(code="4252", text="Some observation text")
    If no dash separator, code=None and text=full string.
    """
    match = _NOTE_PATTERN.match(text.strip())
    if match:
        return CdrNote(code=match.group(1), text=match.group(2).strip())
    return CdrNote(code=None, text=text.strip())


def _xpath_text(tree: etree._Element, xpath: str) -> str | None:
    """Extract text from the first XPath match, or None."""
    elements = tree.xpath(xpath, namespaces=NS)
    if elements:
        text = elements[0].text if hasattr(elements[0], "text") else str(elements[0])
        return text.strip() if text else None
    return None


def parse_cdr(cdr_bytes: bytes) -> CdrResponse:
    """Parse a SUNAT CDR ZIP into a CdrResponse.

    Args:
        cdr_bytes: Raw bytes of the CDR ZIP file.

    Returns:
        CdrResponse with all extracted fields and derived status.

    Raises:
        CdrParseError: If the input is empty.
        InvalidZipError: If the input is not a valid ZIP or contains no XML.
        InvalidXmlError: If the XML is malformed or missing required elements.
    """
    xml_bytes = _extract_xml_from_zip(cdr_bytes)

    try:
        tree = etree.fromstring(xml_bytes)
    except etree.XMLSyntaxError as exc:
        raise InvalidXmlError(f"Malformed XML: {exc}") from exc

    # Extract response code and description
    code = _xpath_text(
        tree, ".//cac:DocumentResponse/cac:Response/cbc:ResponseCode"
    )
    if code is None:
        raise InvalidXmlError("Missing ResponseCode in ApplicationResponse")

    description = (
        _xpath_text(
            tree, ".//cac:DocumentResponse/cac:Response/cbc:Description"
        )
        or ""
    )

    # Extract notes
    note_elements = tree.xpath(".//cbc:Note", namespaces=NS)
    notes = [_parse_note(el.text) for el in note_elements if el.text]

    # Extract document reference
    document_id = _xpath_text(
        tree, ".//cac:DocumentResponse/cac:DocumentReference/cbc:ID"
    )
    document_type = _xpath_text(
        tree,
        ".//cac:DocumentResponse/cac:DocumentReference/cbc:DocumentTypeCode",
    )

    # Resolve status
    status = resolve_status(code, notes)

    return CdrResponse(
        code=code,
        description=description,
        status=status,
        notes=notes,
        document_id=document_id,
        document_type=document_type,
    )
