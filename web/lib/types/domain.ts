/**
 * Unified schema — ETL normalizes all ERP exports into these tables.
 * FastAPI Pydantic models should mirror these field names.
 */

export type Customer = {
  customer_id: string;
  name: string;
};

export type Vendor = {
  vendor_id: string;
  name: string;
};

export type GlTransaction = {
  transaction_id: string;
  account_id: string;
  amount: number;
  posted_at: string;
};

export type Invoice = {
  invoice_id: string;
  customer_id: string;
  amount: number;
  due_date: string;
};

export type InventoryItem = {
  item_id: string;
  sku: string;
  quantity: number;
};

export type WorkOrder = {
  work_order_id: string;
  status: string;
};

export type LaborEntry = {
  entry_id: string;
  work_order_id: string;
  hours: number;
};

export type PurchaseOrder = {
  po_id: string;
  vendor_id: string;
  status: string;
};
