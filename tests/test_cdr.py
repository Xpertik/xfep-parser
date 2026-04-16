"""Tests for parse_cdr function."""

import pytest

from xfep.parser import (
    CdrNote,
    CdrParseError,
    CdrResponse,
    CdrStatus,
    InvalidXmlError,
    InvalidZipError,
    parse_cdr,
)
from tests.conftest import build_cdr_zip


class TestParseCdrHappyPath:
    """Happy path tests for parse_cdr."""

    def test_accepted_cdr(self, valid_cdr_zip: bytes) -> None:
        """Accepted CDR returns correct fields and ACEPTADO status."""
        result = parse_cdr(valid_cdr_zip)

        assert isinstance(result, CdrResponse)
        assert result.code == "0"
        assert "aceptada" in result.description.lower()
        assert result.status == CdrStatus.ACEPTADO
        assert result.document_id == "F001-00000001"
        assert result.document_type == "01"
        assert result.notes == []

    def test_accepted_with_observations(self, observed_cdr_zip: bytes) -> None:
        """CDR with 4xxx notes returns ACEPTADO_CON_OBSERVACIONES."""
        result = parse_cdr(observed_cdr_zip)

        assert result.code == "0"
        assert result.status == CdrStatus.ACEPTADO_CON_OBSERVACIONES
        assert len(result.notes) == 2
        assert result.notes[0].code == "4252"
        assert result.notes[1].code == "4310"

    def test_rejected_cdr(self, rejected_cdr_zip: bytes) -> None:
        """Rejected CDR returns RECHAZADO status."""
        result = parse_cdr(rejected_cdr_zip)

        assert result.code == "2100"
        assert result.status == CdrStatus.RECHAZADO
        assert len(result.notes) == 1
        assert result.notes[0].code == "2100"


class TestParseCdrErrors:
    """Error handling tests for parse_cdr."""

    def test_empty_bytes_raises(self) -> None:
        """Empty bytes raises CdrParseError."""
        with pytest.raises(CdrParseError, match="Empty input"):
            parse_cdr(b"")

    def test_non_zip_raises(self, corrupt_zip_bytes: bytes) -> None:
        """Non-ZIP bytes raises InvalidZipError."""
        with pytest.raises(InvalidZipError, match="Invalid ZIP"):
            parse_cdr(corrupt_zip_bytes)

    def test_zip_without_xml_raises(self, zip_without_xml: bytes) -> None:
        """ZIP with no XML files raises InvalidZipError."""
        with pytest.raises(InvalidZipError, match="no XML"):
            parse_cdr(zip_without_xml)

    def test_malformed_xml_raises(self, zip_with_malformed_xml: bytes) -> None:
        """ZIP with malformed XML raises InvalidXmlError."""
        with pytest.raises(InvalidXmlError, match="Malformed XML"):
            parse_cdr(zip_with_malformed_xml)

    def test_xml_missing_response_code_raises(self) -> None:
        """XML without ResponseCode raises InvalidXmlError."""
        xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<ar:ApplicationResponse
    xmlns:ar="urn:oasis:names:specification:ubl:schema:xsd:ApplicationResponse-2"
    xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
    xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">
  <cac:DocumentResponse>
    <cac:Response>
      <cbc:Description>No code here</cbc:Description>
    </cac:Response>
  </cac:DocumentResponse>
</ar:ApplicationResponse>"""
        cdr_zip = build_cdr_zip(xml_content=xml)
        with pytest.raises(InvalidXmlError, match="Missing ResponseCode"):
            parse_cdr(cdr_zip)


class TestParseCdrEdgeCases:
    """Edge case tests for parse_cdr."""

    def test_multiple_notes_extraction(self) -> None:
        """Multiple notes are all extracted."""
        cdr_zip = build_cdr_zip(
            notes=[
                "4252 - Observation one",
                "4310 - Observation two",
                "Some note without code",
            ],
        )
        result = parse_cdr(cdr_zip)

        assert len(result.notes) == 3
        assert result.notes[0] == CdrNote(code="4252", text="Observation one")
        assert result.notes[1] == CdrNote(code="4310", text="Observation two")
        assert result.notes[2] == CdrNote(
            code=None, text="Some note without code"
        )

    def test_note_without_dash_has_no_code(self) -> None:
        """A note without 'code - text' format gets code=None."""
        cdr_zip = build_cdr_zip(notes=["Just a plain note"])
        result = parse_cdr(cdr_zip)

        assert len(result.notes) == 1
        assert result.notes[0].code is None
        assert result.notes[0].text == "Just a plain note"

    def test_missing_document_reference(self) -> None:
        """Missing DocumentReference fields default to None."""
        xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<ar:ApplicationResponse
    xmlns:ar="urn:oasis:names:specification:ubl:schema:xsd:ApplicationResponse-2"
    xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
    xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">
  <cac:DocumentResponse>
    <cac:Response>
      <cbc:ResponseCode>0</cbc:ResponseCode>
      <cbc:Description>Aceptada</cbc:Description>
    </cac:Response>
  </cac:DocumentResponse>
</ar:ApplicationResponse>"""
        cdr_zip = build_cdr_zip(xml_content=xml)
        result = parse_cdr(cdr_zip)

        assert result.document_id is None
        assert result.document_type is None
        assert result.status == CdrStatus.ACEPTADO

    def test_cdr_response_is_frozen(self, valid_cdr_zip: bytes) -> None:
        """CdrResponse instances are immutable."""
        result = parse_cdr(valid_cdr_zip)
        with pytest.raises(AttributeError):
            result.code = "999"  # type: ignore[misc]

    def test_error_hierarchy(self) -> None:
        """InvalidZipError and InvalidXmlError are subtypes of CdrParseError."""
        assert issubclass(InvalidZipError, CdrParseError)
        assert issubclass(InvalidXmlError, CdrParseError)
