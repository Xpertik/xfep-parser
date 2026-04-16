"""CDR status enum and resolution logic."""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from xfep.parser.cdr import CdrNote


class CdrStatus(StrEnum):
    """SUNAT CDR response status."""

    ACEPTADO = "ACEPTADO"
    ACEPTADO_CON_OBSERVACIONES = "ACEPTADO_CON_OBSERVACIONES"
    RECHAZADO = "RECHAZADO"


def resolve_status(code: str, notes: list[CdrNote]) -> CdrStatus:
    """Derive CdrStatus from ResponseCode and observation notes.

    Rules:
    - code "0" with no 4xxx notes → ACEPTADO
    - code "0" with any 4xxx note  → ACEPTADO_CON_OBSERVACIONES
    - code != "0"                  → RECHAZADO
    """
    code_int = int(code)
    if code_int == 0:
        has_warnings = any(n.code and n.code.startswith("4") for n in notes)
        return (
            CdrStatus.ACEPTADO_CON_OBSERVACIONES
            if has_warnings
            else CdrStatus.ACEPTADO
        )
    return CdrStatus.RECHAZADO
