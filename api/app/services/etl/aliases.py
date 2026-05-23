"""Column alias normalization — maps ERP-specific headers to canonical names."""

COLUMN_ALIASES: dict[str, list[str]] = {
    "customer_id": ["customer id", "cust id", "customer_number", "customer no", "client", "cust#"],
    "customer_name": ["customer name", "customer", "name", "client name"],
    "vendor_id": ["vendor id", "vendor no", "vendor_number", "vendor#", "supplier id"],
    "vendor_name": ["vendor name", "vendor", "supplier", "supplier name"],
    "invoice_id": ["invoice", "invoice no", "invoice number", "inv no", "document"],
    "amount": ["amount", "balance", "open balance", "open amount", "total", "invoice amount"],
    "days_overdue": ["days overdue", "days past due", "age days", "days", "overdue days"],
    "aging_bucket": ["aging bucket", "bucket", "aging", "age category"],
    "account_id": ["account", "account id", "gl account", "acct", "account no", "account number"],
    "account_name": ["account name", "description", "account description"],
    "posted_at": ["date", "posting date", "posted", "transaction date", "trans date"],
    "sku": ["sku", "part number", "part no", "item", "item number", "part#"],
    "item_id": ["item id", "item no", "inventory id", "part id"],
    "quantity": ["quantity", "qty", "on hand", "onhand", "qty on hand"],
    "gl_account": ["gl account", "inventory account", "acct"],
}


def normalize_columns(columns: list[str]) -> dict[str, str]:
    """Map original column names to canonical field names."""
    mapping: dict[str, str] = {}
    cols_lower = {str(c).lower().strip(): c for c in columns}

    for canonical, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            for col_lower, col_orig in cols_lower.items():
                if alias in col_lower or col_lower in alias:
                    mapping[col_orig] = canonical
                    break
            if canonical in mapping.values():
                break

    return mapping


def rename_dataframe(df, column_map: dict[str, str]):
    return df.rename(columns={k: v for k, v in column_map.items() if k in df.columns})
