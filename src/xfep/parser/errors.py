"""CDR parsing error hierarchy."""


class CdrParseError(Exception):
    """Base error for CDR parsing failures."""


class InvalidZipError(CdrParseError):
    """Raised when input bytes are not a valid ZIP archive."""


class InvalidXmlError(CdrParseError):
    """Raised when the ZIP does not contain valid ApplicationResponse XML."""
