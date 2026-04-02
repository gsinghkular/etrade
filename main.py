import io
import json
import os
from datetime import datetime
from decimal import Decimal

import openpyxl
from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

SHEET_NAME = "G&L_Collapsed"

# BASE_DIR is set by run.py and points to the bundled resources directory
# when running as a frozen binary, or the project root otherwise.
_base = os.environ.get("BASE_DIR", os.path.dirname(os.path.abspath(__file__)))
_templates_dir = os.path.join(_base, "templates")

app = FastAPI()
templates = Jinja2Templates(directory=_templates_dir)
templates.env.tests["number"] = lambda v: isinstance(v, (int, float, Decimal))
templates.env.tests["fx_rate"] = lambda v: isinstance(v, tuple)


def load_fx_rates(fx_bytes: bytes) -> dict[str, Decimal]:
    data = json.loads(fx_bytes)
    return {
        obs["d"]: Decimal(obs["FXUSDCAD"]["v"])
        for obs in data["observations"]
    }


FxRate = tuple[Decimal, str | None]  # (rate, fallback_date_used | None)


def lookup_fx(rates: dict[str, Decimal], date_str: str | None) -> FxRate | None:
    """Return (rate, fallback_date) for a date string (MM/DD/YYYY).
    fallback_date is None on exact match, or the date string that was used otherwise."""
    if not date_str:
        return None
    try:
        dt = datetime.strptime(str(date_str), "%m/%d/%Y")
    except ValueError:
        return None
    target = dt.strftime("%Y-%m-%d")
    if target in rates:
        return (rates[target], None)
    for d in reversed(sorted(rates)):
        if d < target:
            return (rates[d], d)
    return None


def to_decimal(value: int | float | None) -> Decimal | None:
    """Convert a spreadsheet value to Decimal via str to avoid float imprecision."""
    if value is None:
        return None
    return Decimal(str(value))


def to_cad(usd: int | float | None, fx: FxRate | None) -> Decimal | None:
    if usd is None or fx is None:
        return None
    return to_decimal(usd) * fx[0]


def load_sheet(excel_bytes: bytes, fx_bytes: bytes) -> tuple[list, list[list]]:
    wb = openpyxl.load_workbook(io.BytesIO(excel_bytes), data_only=True)
    ws = wb[SHEET_NAME]
    rows = list(ws.iter_rows(values_only=True))
    headers = [
        h.replace("Adjusted Cost Basis", "ACB") if h else h
        for h in rows[0]
    ]

    rates = load_fx_rates(fx_bytes)

    # Capture all original indices before any insertions
    acquired_idx = headers.index("Date Acquired")
    acb_idx      = headers.index("ACB")
    sold_idx     = headers.index("Date Sold")
    proceeds_idx = headers.index("Total Proceeds")
    adj_gl_idx   = headers.index("Adjusted Gain/Loss")

    # Insert new headers in descending index order to keep earlier indices stable
    insertions = [
        (adj_gl_idx + 1,   "Adjusted Gain/Loss (CAD)"),
        (proceeds_idx + 1, "Total Proceeds (CAD)"),
        (sold_idx + 1,     "FX Rate (Sold)"),
        (acb_idx + 1,      "ACB (CAD)"),
        (acquired_idx + 1, "FX Rate (Acquired)"),
    ]
    for pos, label in insertions:
        headers.insert(pos, label)

    data = []
    for row in rows[1:]:
        if row[0] == "Summary":
            continue
        row = list(row)

        fx_acquired  = lookup_fx(rates, row[acquired_idx])
        fx_sold      = lookup_fx(rates, row[sold_idx])
        acb_cad      = to_cad(row[acb_idx], fx_acquired)
        proceeds_cad = to_cad(row[proceeds_idx], fx_sold)
        adj_gl_cad   = (
            None if proceeds_cad is None or acb_cad is None
            else proceeds_cad - acb_cad
        )

        # Insert in same descending order so original indices remain valid
        row.insert(adj_gl_idx + 1,   adj_gl_cad)
        row.insert(proceeds_idx + 1, proceeds_cad)
        row.insert(sold_idx + 1,     fx_sold)
        row.insert(acb_idx + 1,      acb_cad)
        row.insert(acquired_idx + 1, fx_acquired)

        data.append(row)

    return headers, data


@app.get("/", response_class=HTMLResponse)
def upload_page(request: Request, error: str = ""):
    return templates.TemplateResponse(request, "upload.html", {"error": error})


@app.post("/view", response_class=HTMLResponse)
async def view(
    request: Request,
    excel_file: UploadFile = File(...),
    fx_file: UploadFile = File(...),
):
    try:
        excel_bytes = await excel_file.read()
        fx_bytes    = await fx_file.read()
        headers, data = load_sheet(excel_bytes, fx_bytes)
    except Exception as e:
        return templates.TemplateResponse(
            request, "upload.html", {"error": str(e)}, status_code=400
        )

    return templates.TemplateResponse(
        request,
        "index.html",
        {"headers": headers, "data": data, "sheet": SHEET_NAME},
    )
