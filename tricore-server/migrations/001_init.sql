-- TriCore 001: Initial schema — idempotent (safe to re-run)

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN NEW.updated_at = NOW(); RETURN NEW; END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- SALES DOMAIN
-- ============================================================

DROP TABLE IF EXISTS return_items CASCADE;
DROP TABLE IF EXISTS return_orders CASCADE;
DROP TABLE IF EXISTS bundle_items CASCADE;
DROP TABLE IF EXISTS bundle_sales CASCADE;
DROP TABLE IF EXISTS order_items CASCADE;
DROP TABLE IF EXISTS stock_out_items CASCADE;
DROP TABLE IF EXISTS stock_in_items CASCADE;
DROP TABLE IF EXISTS stock_out_records CASCADE;
DROP TABLE IF EXISTS stock_in_records CASCADE;
DROP TABLE IF EXISTS issues CASCADE;
DROP TABLE IF EXISTS workflow_archives CASCADE;
DROP TABLE IF EXISTS workflow_steps CASCADE;
DROP TABLE IF EXISTS workflow_forms CASCADE;
DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS warehouses CASCADE;
DROP TABLE IF EXISTS products CASCADE;
DROP TABLE IF EXISTS employees CASCADE;
DROP TABLE IF EXISTS users CASCADE;

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('merchant', 'customer', 'salesperson')),
    full_name VARCHAR(200) NOT NULL,
    phone VARCHAR(20),
    fingerprint_data TEXT,
    face_data TEXT,
    email VARCHAR(200),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
DROP TRIGGER IF EXISTS trg_users_updated_at ON users;
CREATE TRIGGER trg_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TABLE IF NOT EXISTS products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sku VARCHAR(100) NOT NULL UNIQUE,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    original_price NUMERIC(12,2) NOT NULL,
    surprise_discount_percent NUMERIC(5,2) NOT NULL DEFAULT 0,
    subsidized_price NUMERIC(12,2),
    quantity INTEGER NOT NULL DEFAULT 0,
    unit VARCHAR(20) NOT NULL DEFAULT '件',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    category VARCHAR(100),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_products_sku ON products(sku);
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
DROP TRIGGER IF EXISTS trg_products_updated_at ON products;
CREATE TRIGGER trg_products_updated_at BEFORE UPDATE ON products FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TABLE IF NOT EXISTS orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_no VARCHAR(50) NOT NULL UNIQUE,
    customer_id UUID NOT NULL REFERENCES users(id),
    salesperson_id UUID REFERENCES users(id),
    merchant_id UUID REFERENCES users(id),
    total_amount NUMERIC(12,2) NOT NULL,
    discount_amount NUMERIC(12,2) NOT NULL DEFAULT 0,
    final_amount NUMERIC(12,2) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'confirmed', 'processing', 'shipped', 'delivered', 'cancelled')),
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_orders_customer_id ON orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_salesperson_id ON orders(salesperson_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at DESC);
DROP TRIGGER IF EXISTS trg_orders_updated_at ON orders;
CREATE TRIGGER trg_orders_updated_at BEFORE UPDATE ON orders FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TABLE IF NOT EXISTS order_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    product_id UUID NOT NULL REFERENCES products(id),
    quantity INTEGER NOT NULL,
    unit_price NUMERIC(12,2) NOT NULL,
    subtotal NUMERIC(12,2) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_order_items_product_id ON order_items(product_id);

CREATE TABLE IF NOT EXISTS bundle_sales (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bundle_name VARCHAR(200) NOT NULL,
    salesperson_id UUID NOT NULL REFERENCES users(id),
    merchant_id UUID NOT NULL REFERENCES users(id),
    customer_id UUID REFERENCES users(id),
    total_original_price NUMERIC(12,2) NOT NULL,
    bundle_price NUMERIC(12,2) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'draft'
        CHECK (status IN ('draft', 'active', 'completed', 'cancelled')),
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_bundle_sales_salesperson_id ON bundle_sales(salesperson_id);
DROP TRIGGER IF EXISTS trg_bundle_sales_updated_at ON bundle_sales;
CREATE TRIGGER trg_bundle_sales_updated_at BEFORE UPDATE ON bundle_sales FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TABLE IF NOT EXISTS bundle_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bundle_id UUID NOT NULL REFERENCES bundle_sales(id) ON DELETE CASCADE,
    product_id UUID NOT NULL REFERENCES products(id),
    quantity INTEGER NOT NULL,
    unit_price NUMERIC(12,2) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_bundle_items_bundle_id ON bundle_items(bundle_id);

CREATE TABLE IF NOT EXISTS return_orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    return_no VARCHAR(50) NOT NULL UNIQUE,
    order_id UUID NOT NULL REFERENCES orders(id),
    salesperson_id UUID NOT NULL REFERENCES users(id),
    reason TEXT NOT NULL,
    total_refund_amount NUMERIC(12,2) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'approved', 'rejected', 'completed')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_return_orders_order_id ON return_orders(order_id);
DROP TRIGGER IF EXISTS trg_return_orders_updated_at ON return_orders;
CREATE TRIGGER trg_return_orders_updated_at BEFORE UPDATE ON return_orders FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TABLE IF NOT EXISTS return_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    return_id UUID NOT NULL REFERENCES return_orders(id) ON DELETE CASCADE,
    product_id UUID NOT NULL REFERENCES products(id),
    quantity INTEGER NOT NULL,
    refund_amount NUMERIC(12,2) NOT NULL,
    reason_detail TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_return_items_return_id ON return_items(return_id);

-- ============================================================
-- OA DOMAIN
-- ============================================================

CREATE TABLE IF NOT EXISTS employees (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_no VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    department VARCHAR(100) NOT NULL,
    position VARCHAR(100) NOT NULL,
    email VARCHAR(200) NOT NULL UNIQUE,
    phone VARCHAR(20),
    password_hash VARCHAR(255) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active'
        CHECK (status IN ('active', 'inactive')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_employees_department ON employees(department);
DROP TRIGGER IF EXISTS trg_employees_updated_at ON employees;
CREATE TRIGGER trg_employees_updated_at BEFORE UPDATE ON employees FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TABLE IF NOT EXISTS workflow_forms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    creator_id UUID NOT NULL REFERENCES employees(id),
    title VARCHAR(200) NOT NULL,
    description TEXT,
    form_data JSONB NOT NULL DEFAULT '{}',
    status VARCHAR(20) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'in_progress', 'approved', 'rejected', 'archived')),
    current_step INTEGER NOT NULL DEFAULT 1,
    total_steps INTEGER NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_workflow_forms_creator_id ON workflow_forms(creator_id);
CREATE INDEX IF NOT EXISTS idx_workflow_forms_status ON workflow_forms(status);
CREATE INDEX IF NOT EXISTS idx_workflow_forms_form_data ON workflow_forms USING GIN(form_data);
DROP TRIGGER IF EXISTS trg_workflow_forms_updated_at ON workflow_forms;
CREATE TRIGGER trg_workflow_forms_updated_at BEFORE UPDATE ON workflow_forms FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TABLE IF NOT EXISTS workflow_steps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID NOT NULL REFERENCES workflow_forms(id) ON DELETE CASCADE,
    step_number INTEGER NOT NULL,
    reviewer_id UUID NOT NULL REFERENCES employees(id),
    status VARCHAR(20) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'approved', 'rejected')),
    comment TEXT,
    attachment_url VARCHAR(500),
    acted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(workflow_id, step_number)
);
CREATE INDEX IF NOT EXISTS idx_workflow_steps_workflow_id ON workflow_steps(workflow_id);
CREATE INDEX IF NOT EXISTS idx_workflow_steps_reviewer_id ON workflow_steps(reviewer_id);
CREATE INDEX IF NOT EXISTS idx_workflow_steps_status ON workflow_steps(status);
DROP TRIGGER IF EXISTS trg_workflow_steps_updated_at ON workflow_steps;
CREATE TRIGGER trg_workflow_steps_updated_at BEFORE UPDATE ON workflow_steps FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TABLE IF NOT EXISTS workflow_archives (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID NOT NULL UNIQUE,
    archived_data JSONB NOT NULL,
    final_decision VARCHAR(20) NOT NULL CHECK (final_decision IN ('approved', 'rejected')),
    archived_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_workflow_archives_workflow_id ON workflow_archives(workflow_id);

-- ============================================================
-- INVENTORY DOMAIN
-- ============================================================

CREATE TABLE IF NOT EXISTS warehouses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    location VARCHAR(300),
    manager_id UUID REFERENCES employees(id),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
DROP TRIGGER IF EXISTS trg_warehouses_updated_at ON warehouses;
CREATE TRIGGER trg_warehouses_updated_at BEFORE UPDATE ON warehouses FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TABLE IF NOT EXISTS stock_in_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    stock_in_no VARCHAR(50) NOT NULL UNIQUE,
    order_id UUID REFERENCES orders(id),
    warehouse_id UUID NOT NULL REFERENCES warehouses(id),
    operator_id UUID NOT NULL REFERENCES employees(id),
    notes TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'verified', 'completed')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_stock_in_records_order_id ON stock_in_records(order_id);
CREATE INDEX IF NOT EXISTS idx_stock_in_records_warehouse_id ON stock_in_records(warehouse_id);
DROP TRIGGER IF EXISTS trg_stock_in_records_updated_at ON stock_in_records;
CREATE TRIGGER trg_stock_in_records_updated_at BEFORE UPDATE ON stock_in_records FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TABLE IF NOT EXISTS stock_in_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    stock_in_id UUID NOT NULL REFERENCES stock_in_records(id) ON DELETE CASCADE,
    product_id UUID NOT NULL REFERENCES products(id),
    expected_quantity INTEGER NOT NULL,
    actual_quantity INTEGER NOT NULL,
    unit_price NUMERIC(12,2),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_stock_in_items_stock_in_id ON stock_in_items(stock_in_id);

CREATE TABLE IF NOT EXISTS stock_out_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    stock_out_no VARCHAR(50) NOT NULL UNIQUE,
    order_id UUID REFERENCES orders(id),
    warehouse_id UUID NOT NULL REFERENCES warehouses(id),
    operator_id UUID NOT NULL REFERENCES employees(id),
    vehicle_info VARCHAR(200),
    driver_info VARCHAR(200),
    notes TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'shipped', 'delivered')),
    shipped_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_stock_out_records_order_id ON stock_out_records(order_id);
CREATE INDEX IF NOT EXISTS idx_stock_out_records_warehouse_id ON stock_out_records(warehouse_id);
DROP TRIGGER IF EXISTS trg_stock_out_records_updated_at ON stock_out_records;
CREATE TRIGGER trg_stock_out_records_updated_at BEFORE UPDATE ON stock_out_records FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TABLE IF NOT EXISTS stock_out_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    stock_out_id UUID NOT NULL REFERENCES stock_out_records(id) ON DELETE CASCADE,
    product_id UUID NOT NULL REFERENCES products(id),
    quantity INTEGER NOT NULL,
    unit_price NUMERIC(12,2),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_stock_out_items_stock_out_id ON stock_out_items(stock_out_id);

CREATE TABLE IF NOT EXISTS issues (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    related_type VARCHAR(30) NOT NULL CHECK (related_type IN ('stock_in', 'stock_out', 'order', 'product')),
    related_id UUID NOT NULL,
    description TEXT NOT NULL,
    severity VARCHAR(20) NOT NULL DEFAULT 'medium'
        CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    status VARCHAR(20) NOT NULL DEFAULT 'open'
        CHECK (status IN ('open', 'in_progress', 'resolved', 'closed')),
    reported_by UUID NOT NULL REFERENCES employees(id),
    assigned_to UUID REFERENCES employees(id),
    resolution TEXT,
    resolved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_issues_related ON issues(related_type, related_id);
CREATE INDEX IF NOT EXISTS idx_issues_status ON issues(status);
DROP TRIGGER IF EXISTS trg_issues_updated_at ON issues;
CREATE TRIGGER trg_issues_updated_at BEFORE UPDATE ON issues FOR EACH ROW EXECUTE FUNCTION update_updated_at();
