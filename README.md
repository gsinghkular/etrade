# E*Trade G&L Viewer

A web application for viewing and analyzing E*Trade Gains & Losses spreadsheet data with USD → CAD currency conversion.

## What It Does

Upload your E*Trade `.xlsx` export and a Bank of Canada FX rates `.json` file to get an interactive table that shows:

- All sell transactions with key columns visible by default
- USD → CAD conversions for Adjusted Cost Basis, Total Proceeds, and Adjusted Gain/Loss
- Exchange rates looked up by transaction date (acquisition and sale), with the actual date shown when an exact rate isn't available (e.g. weekends or holidays)
- Colour-coded gain/loss values (green for gains, red for losses)

## Required Files

### 1. E*Trade Excel Export (`.xlsx`)

Export your Gains & Losses report from E*Trade as an Excel file. The app expects a sheet named **`G&L_Collapsed`** with the standard E*Trade column layout.

A demo file (`demo.xlsx`) is included in the repo with fictional data so you can try the app without using real data.

### 2. FX Rates JSON (`.json`)

Download the USD/CAD daily exchange rate history from the Bank of Canada:

[https://www.bankofcanada.ca/valet/observations/FXUSDCAD/json](https://www.bankofcanada.ca/valet/observations/FXUSDCAD/json)

The file should contain an `observations` array in this format:

```json
{
  "observations": [
    { "d": "2025-01-02", "FXUSDCAD": { "v": "1.4418" } },
    ...
  ]
}
```

## Using the App

### Standalone Binary (no installation required)

Download the pre-built binary for your platform from the [Releases](../../releases) page.

**macOS:**
```bash
# Make executable if needed
chmod +x etrade-gl-macos

./etrade-gl-macos
```

**Windows:** Double-click `etrade-gl-windows.exe` or run from the command prompt:
```bat
etrade-gl-windows.exe
```

The app will start a local server and automatically open `http://127.0.0.1:8111` in your browser.

### Uploading Files

1. On the landing page, upload your E*Trade `.xlsx` file
2. Upload your FX rates `.json` file
3. Click **View G&L Data**

### Table Features

| Control | Description |
|---|---|
| **Show all columns** | Toggle visibility of all extra columns beyond the default view |
| **Download CSV** | Export the default columns as a CSV file |
| **Download Full CSV** | Export all columns as a CSV file |

### Default Columns

The table shows these columns by default:

- Quantity
- Date Acquired · FX Rate (Acquired)
- ACB · ACB (CAD) · ACB Per Share
- Date Sold · FX Rate (Sold)
- Total Proceeds · Total Proceeds (CAD) · Proceeds Per Share
- Adjusted Gain/Loss · Adjusted Gain/Loss (CAD)

All remaining columns from the original spreadsheet are available via the **Show all columns** toggle.

### FX Rate Display

- **Exact rate** — shown as a plain number, e.g. `1.4225`
- **Fallback rate** — shown with the date that was used, e.g. `1.4207 (2025-02-21)`, when no rate exists for the exact date (weekends, holidays)

### CAD Calculations

CAD values are computed using `Decimal` arithmetic for full precision:

| Column | Formula |
|---|---|
| ACB (CAD) | ACB × FX Rate (Acquired) |
| Total Proceeds (CAD) | Total Proceeds × FX Rate (Sold) |
| Adjusted Gain/Loss (CAD) | Total Proceeds (CAD) − ACB (CAD) |

Adjusted Gain/Loss (CAD) is derived component-wise (not by multiplying the USD gain/loss by a single rate) to accurately reflect the different exchange rates at acquisition and sale.

---

## Building and Running Manually

### Prerequisites

- Python 3.10+

### Setup

```bash
# Clone the repository
git clone <repo-url>
cd etrade

# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate        # macOS / Linux
# venv\Scripts\activate         # Windows

# Install dependencies
pip install -r requirements.txt
```

### Run the Dev Server

```bash
uvicorn main:app --reload --port 8111
```

Then open [http://localhost:8111](http://localhost:8111) in your browser.

### Build a Standalone Binary

```bash
pip install pyinstaller
bash build.sh
```

The binary is output to `dist/etrade-gl` (macOS/Linux) or `dist/etrade-gl.exe` (Windows).

> PyInstaller must be run on the target platform — you cannot cross-compile. To build a Windows binary, run `build.sh` (or the equivalent `pyinstaller etrade-gl.spec`) on a Windows machine.
