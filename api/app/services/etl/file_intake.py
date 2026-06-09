"""Robust CSV/XLSX intake — encoding, delimiter, header row, preamble skipping."""

from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass, field

import pandas as pd

HEADER_HINT_TOKENS = frozenset(
    {
        "customer",
        "vendor",
        "invoice",
        "amount",
        "balance",
        "date",
        "account",
        "sku",
        "quantity",
        "qty",
        "total",
        "name",
        "id",
        "aging",
        "current",
        "posted",
    }
)


@dataclass
class IntakeMetadata:
    encoding: str = "utf-8"
    delimiter: str = ","
    header_row_index: int = 0
    skipped_rows: int = 0
    sheet_name: str | None = None
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "encoding": self.encoding,
            "delimiter": self.delimiter,
            "header_row_index": self.header_row_index,
            "skipped_rows": self.skipped_rows,
            "sheet_name": self.sheet_name,
            "warnings": list(self.warnings),
        }


@dataclass
class IntakeResult:
    dataframe: pd.DataFrame
    metadata: IntakeMetadata


def _decode_bytes(content: bytes) -> tuple[str, str]:
    for enc in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            return content.decode(enc), enc
        except UnicodeDecodeError:
            continue
    return content.decode("latin-1", errors="replace"), "latin-1"


def _detect_delimiter(sample: str) -> str:
    try:
        dialect = csv.Sniffer().sniff(sample[:8192], delimiters=",;\t|")
        return dialect.delimiter
    except csv.Error:
        counts = {d: sample[:4096].count(d) for d in (",", ";", "\t")}
        return max(counts, key=counts.get) if any(counts.values()) else ","


def _tokenize_cell(val: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", val.lower()))


def _score_header_row(cells: list[str]) -> float:
    non_empty = [c.strip() for c in cells if str(c).strip()]
    if len(non_empty) < 2:
        return 0.0

    score = min(len(non_empty) / 4.0, 1.0) * 0.3
    text_cells = 0
    token_hits = 0
    for cell in non_empty:
        s = str(cell).strip()
        if not s:
            continue
        try:
            float(s.replace(",", "").replace("$", ""))
            continue
        except ValueError:
            text_cells += 1
        tokens = _tokenize_cell(s)
        if tokens & HEADER_HINT_TOKENS:
            token_hits += 1

    if text_cells:
        score += (text_cells / len(non_empty)) * 0.35
    if token_hits:
        score += min(token_hits / 3.0, 1.0) * 0.35
    return score


def _find_header_row(lines: list[list[str]], max_scan: int = 20) -> int:
    best_idx = 0
    best_score = -1.0
    limit = min(len(lines), max_scan)
    for i in range(limit):
        row_score = _score_header_row(lines[i])
        if i + 1 < len(lines):
            next_cells = [c for c in lines[i + 1] if str(c).strip()]
            if next_cells and abs(len(next_cells) - len([c for c in lines[i] if str(c).strip()])) <= 2:
                row_score += 0.1
        if row_score > best_score:
            best_score = row_score
            best_idx = i
    return best_idx


def _read_csv_lines(text: str, delimiter: str) -> list[list[str]]:
    reader = csv.reader(io.StringIO(text), delimiter=delimiter)
    return [row for row in reader if any(str(c).strip() for c in row)]


def _clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    df = df.dropna(axis=1, how="all")
    df = df.dropna(axis=0, how="all")
    df = df.reset_index(drop=True)
    return df


def intake_csv(content: bytes) -> IntakeResult:
    text, encoding = _decode_bytes(content)
    delimiter = _detect_delimiter(text)
    lines = _read_csv_lines(text, delimiter)
    if not lines:
        meta = IntakeMetadata(encoding=encoding, delimiter=delimiter, warnings=["empty file"])
        return IntakeResult(dataframe=pd.DataFrame(), metadata=meta)

    header_idx = _find_header_row(lines)
    skipped = header_idx
    header = [str(c).strip() for c in lines[header_idx]]
    data_rows = lines[header_idx + 1 :]
    width = len(header)

    rows: list[list[str]] = []
    for row in data_rows:
        if len(row) < width:
            row = row + [""] * (width - len(row))
        elif len(row) > width:
            row = row[:width]
        if any(str(c).strip() for c in row):
            rows.append(row)

    df = pd.DataFrame(rows, columns=header)
    df = _clean_dataframe(df)

    warnings: list[str] = []
    if skipped > 0:
        warnings.append(f"skipped {skipped} preamble row(s) before header")

    meta = IntakeMetadata(
        encoding=encoding,
        delimiter=delimiter,
        header_row_index=header_idx,
        skipped_rows=skipped,
        warnings=warnings,
    )
    return IntakeResult(dataframe=df, metadata=meta)


def _parse_excel_sheet(xl: pd.ExcelFile, sheet: str) -> IntakeResult | None:
    raw = xl.parse(sheet, header=None)
    raw = raw.dropna(axis=1, how="all").dropna(axis=0, how="all")
    if raw.empty:
        return None

    lines = raw.fillna("").astype(str).values.tolist()
    header_idx = _find_header_row(lines)
    header = [str(c).strip() for c in lines[header_idx]]
    data_rows = lines[header_idx + 1 :]
    width = len(header)
    rows: list[list[str]] = []
    for row in data_rows:
        row = list(row)
        if len(row) < width:
            row = row + [""] * (width - len(row))
        elif len(row) > width:
            row = row[:width]
        if any(str(c).strip() for c in row):
            rows.append(row)

    df = pd.DataFrame(rows, columns=header)
    df = _clean_dataframe(df)
    if df.empty:
        return None

    warnings: list[str] = []
    if header_idx > 0:
        warnings.append(f"sheet '{sheet}': skipped {header_idx} preamble row(s)")

    meta = IntakeMetadata(
        encoding="binary",
        delimiter="",
        header_row_index=header_idx,
        skipped_rows=header_idx,
        sheet_name=sheet,
        warnings=warnings,
    )
    return IntakeResult(dataframe=df, metadata=meta)


def intake_excel(content: bytes, filename: str = "") -> IntakeResult:
    lower = filename.lower()
    if lower.endswith(".xls") and not lower.endswith(".xlsx"):
        raise ValueError(
            "Legacy .xls workbooks require a separate reader; export as .xlsx or CSV instead"
        )

    try:
        xl = pd.ExcelFile(io.BytesIO(content))
    except Exception as e:
        raise ValueError(f"Excel read failed: {e}") from e

    parsed: list[IntakeResult] = []
    for sheet in xl.sheet_names:
        result = _parse_excel_sheet(xl, sheet)
        if result is not None:
            parsed.append(result)

    if not parsed:
        meta = IntakeMetadata(sheet_name=xl.sheet_names[0] if xl.sheet_names else None, warnings=["empty workbook"])
        return IntakeResult(dataframe=pd.DataFrame(), metadata=meta)

    groups: dict[tuple[str, ...], list[IntakeResult]] = {}
    for result in parsed:
        key = tuple(result.dataframe.columns)
        groups.setdefault(key, []).append(result)

    warnings: list[str] = []
    for p in parsed:
        warnings.extend(p.metadata.warnings)

    if len(groups) == 1:
        frames = [r.dataframe for r in parsed]
        df = pd.concat(frames, ignore_index=True)
        if len(parsed) > 1:
            sheet_names = ", ".join(r.metadata.sheet_name or "?" for r in parsed)
            warnings.append(f"merged {len(parsed)} sheets with matching columns: {sheet_names}")
        primary = parsed[0].metadata
        meta = IntakeMetadata(
            encoding=primary.encoding,
            delimiter=primary.delimiter,
            header_row_index=primary.header_row_index,
            skipped_rows=primary.skipped_rows,
            sheet_name=primary.sheet_name,
            warnings=warnings,
        )
        return IntakeResult(dataframe=df, metadata=meta)

    best = max(parsed, key=lambda r: len(r.dataframe))
    skipped = [r.metadata.sheet_name for r in parsed if r is not best]
    warnings.append(
        f"multiple sheet layouts detected; used '{best.metadata.sheet_name}' "
        f"({len(best.dataframe)} rows). Skipped: {', '.join(s for s in skipped if s)}"
    )
    meta = IntakeMetadata(
        encoding=best.metadata.encoding,
        delimiter=best.metadata.delimiter,
        header_row_index=best.metadata.header_row_index,
        skipped_rows=best.metadata.skipped_rows,
        sheet_name=best.metadata.sheet_name,
        warnings=warnings,
    )
    return IntakeResult(dataframe=best.dataframe, metadata=meta)


def intake_file(content: bytes, filename: str) -> IntakeResult:
    lower = filename.lower()
    if lower.endswith(".csv"):
        return intake_csv(content)
    if lower.endswith((".xlsx", ".xls")):
        return intake_excel(content, filename)
    raise ValueError(f"Unsupported file type: {filename}")
