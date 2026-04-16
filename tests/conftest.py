"""Programmatic CDR ZIP fixtures for testing."""

from __future__ import annotations

import io
import zipfile

import pytest


def build_cdr_xml(
    *,
    response_code: str = "0",
    description: str = "La Factura numero F001-00000001, ha sido aceptada",
    notes: list[str] | None = None,
    doc_id: str = "F001-00000001",
    doc_type: str = "01",
) -> str:
    """Build a CDR ApplicationResponse XML string."""
    note_elements = ""
    if notes:
        note_elements = "\n".join(
            f'  <cbc:Note><![CDATA[{n}]]></cbc:Note>' for n in notes
        )

    return f"""\
<?xml version="1.0" encoding="UTF-8"?>
<ar:ApplicationResponse
    xmlns:ar="urn:oasis:names:specification:ubl:schema:xsd:ApplicationResponse-2"
    xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
    xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">
{note_elements}
  <cac:DocumentResponse>
    <cac:Response>
      <cbc:ResponseCode>{response_code}</cbc:ResponseCode>
      <cbc:Description><![CDATA[{description}]]></cbc:Description>
    </cac:Response>
    <cac:DocumentReference>
      <cbc:ID>{doc_id}</cbc:ID>
      <cbc:DocumentTypeCode>{doc_type}</cbc:DocumentTypeCode>
    </cac:DocumentReference>
  </cac:DocumentResponse>
</ar:ApplicationResponse>"""


def build_cdr_zip(
    *,
    xml_content: str | None = None,
    filename: str = "R-20123456789-01-F001-00000001.xml",
    **xml_kwargs,
) -> bytes:
    """Build a CDR ZIP archive from XML content or kwargs."""
    if xml_content is None:
        xml_content = build_cdr_xml(**xml_kwargs)

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(filename, xml_content)
    return buf.getvalue()


@pytest.fixture
def valid_cdr_zip() -> bytes:
    """Accepted CDR: code 0, no observations."""
    return build_cdr_zip()


@pytest.fixture
def observed_cdr_zip() -> bytes:
    """Accepted with observations: code 0, 4xxx notes."""
    return build_cdr_zip(
        notes=[
            "4252 - El dato ingresado como atributo del tipo de documento es incorrecto",
            "4310 - El contribuyente no esta afecto al impuesto",
        ],
    )


@pytest.fixture
def rejected_cdr_zip() -> bytes:
    """Rejected CDR: code 2100."""
    return build_cdr_zip(
        response_code="2100",
        description="El comprobante fue registrado previamente",
        notes=["2100 - El comprobante fue registrado previamente"],
    )


@pytest.fixture
def corrupt_zip_bytes() -> bytes:
    """Bytes that are not a valid ZIP."""
    return b"this is not a zip file at all"


@pytest.fixture
def zip_without_xml() -> bytes:
    """Valid ZIP but contains no XML files."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("readme.txt", "no xml here")
    return buf.getvalue()


@pytest.fixture
def zip_with_malformed_xml() -> bytes:
    """Valid ZIP with broken XML inside."""
    return build_cdr_zip(xml_content="<broken><xml", filename="R-broken.xml")
