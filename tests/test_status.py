"""Tests for CdrStatus resolution logic."""

import pytest

from xfep.parser.cdr import CdrNote
from xfep.parser.status import CdrStatus, resolve_status


class TestResolveStatus:
    """Tests for resolve_status function."""

    @pytest.mark.parametrize(
        ("code", "notes", "expected"),
        [
            # Accepted: code 0, no warning notes
            ("0", [], CdrStatus.ACEPTADO),
            # Accepted: code 0, notes without 4xxx codes
            (
                "0",
                [CdrNote(code=None, text="Some informational note")],
                CdrStatus.ACEPTADO,
            ),
            # Accepted with observations: code 0, 4xxx note
            (
                "0",
                [CdrNote(code="4252", text="Observation text")],
                CdrStatus.ACEPTADO_CON_OBSERVACIONES,
            ),
            # Accepted with observations: code 0, mixed notes (one 4xxx)
            (
                "0",
                [
                    CdrNote(code=None, text="Info"),
                    CdrNote(code="4310", text="Warning"),
                ],
                CdrStatus.ACEPTADO_CON_OBSERVACIONES,
            ),
            # Rejected: code 2100
            ("2100", [], CdrStatus.RECHAZADO),
            # Rejected: code 2000
            ("2000", [], CdrStatus.RECHAZADO),
            # Rejected: code 3000
            ("3000", [], CdrStatus.RECHAZADO),
            # Rejected: even with 4xxx notes, non-zero code means rejected
            (
                "2100",
                [CdrNote(code="4252", text="Irrelevant")],
                CdrStatus.RECHAZADO,
            ),
        ],
        ids=[
            "accepted-no-notes",
            "accepted-info-note-only",
            "accepted-with-4xxx-observation",
            "accepted-with-mixed-notes",
            "rejected-2100",
            "rejected-2000",
            "rejected-3000",
            "rejected-ignores-4xxx-notes",
        ],
    )
    def test_resolve_status(
        self,
        code: str,
        notes: list[CdrNote],
        expected: CdrStatus,
    ) -> None:
        assert resolve_status(code, notes) == expected

    def test_status_values_are_strings(self) -> None:
        """CdrStatus values should be usable as plain strings."""
        assert str(CdrStatus.ACEPTADO) == "ACEPTADO"
        assert f"{CdrStatus.RECHAZADO}" == "RECHAZADO"
