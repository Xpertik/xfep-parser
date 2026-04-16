# xfep-parser

Parser de CDR (Constancia de Recepción) para Facturación Electrónica Perú.

Extrae y parsea la respuesta ApplicationResponse de SUNAT desde archivos ZIP con XML UBL 2.1.

## Instalación

```bash
pip install -e ".[dev]"
```

## Uso

```python
from xfep.parser import parse_cdr, CdrStatus

response = parse_cdr(cdr_zip_bytes)
print(response.status)       # CdrStatus.ACEPTADO
print(response.code)         # "0"
print(response.description)  # "La Factura..."
print(response.notes)        # [CdrNote(code="4252", text="...")]
```
