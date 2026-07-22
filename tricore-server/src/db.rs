use sqlx::postgres::PgPoolOptions;
use sqlx::PgPool;
use log::info;

pub async fn create_pool(database_url: &str) -> PgPool {
    PgPoolOptions::new()
        .max_connections(10)
        .connect(database_url)
        .await
        .expect("Failed to create database pool")
}

pub async fn run_migrations(pool: &PgPool) {
    // Ensure gen_random_uuid() is available
    let _ = sqlx::query("CREATE EXTENSION IF NOT EXISTS pgcrypto").execute(pool).await;

    let sqls = vec![
        // ── Trigger function ──
        "CREATE OR REPLACE FUNCTION update_updated_at()
         RETURNS TRIGGER AS $$ BEGIN NEW.updated_at = NOW(); RETURN NEW; END;
         $$ LANGUAGE plpgsql",

        // ── SALES ──
        "CREATE TABLE IF NOT EXISTS categories (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name VARCHAR(100) NOT NULL UNIQUE,
            description TEXT,
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )",
        "CREATE TABLE IF NOT EXISTS users (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            username VARCHAR(100) NOT NULL UNIQUE,
            password_hash VARCHAR(255) NOT NULL,
            role VARCHAR(20) NOT NULL DEFAULT 'salesperson',
            full_name VARCHAR(200) NOT NULL,
            phone VARCHAR(20),
            fingerprint_data TEXT,
            face_data TEXT,
            email VARCHAR(200),
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )",

        "CREATE TABLE IF NOT EXISTS products (
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
        )",

        "CREATE TABLE IF NOT EXISTS orders (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            order_no VARCHAR(50) NOT NULL UNIQUE,
            customer_id UUID NOT NULL,
            salesperson_id UUID,
            merchant_id UUID,
            total_amount NUMERIC(12,2) NOT NULL,
            discount_amount NUMERIC(12,2) NOT NULL DEFAULT 0,
            final_amount NUMERIC(12,2) NOT NULL,
            status VARCHAR(20) NOT NULL DEFAULT 'pending',
            vehicle_info VARCHAR(200),
            driver_info VARCHAR(200),
            notes TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )",

        "CREATE TABLE IF NOT EXISTS order_items (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            order_id UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
            product_id UUID NOT NULL REFERENCES products(id),
            quantity INTEGER NOT NULL,
            unit_price NUMERIC(12,2) NOT NULL,
            subtotal NUMERIC(12,2) NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )",

        "CREATE TABLE IF NOT EXISTS bundle_sales (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            bundle_name VARCHAR(200) NOT NULL,
            salesperson_id UUID NOT NULL,
            merchant_id UUID NOT NULL,
            customer_id UUID,
            total_original_price NUMERIC(12,2) NOT NULL,
            bundle_price NUMERIC(12,2) NOT NULL,
            status VARCHAR(20) NOT NULL DEFAULT 'draft',
            notes TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )",

        "CREATE TABLE IF NOT EXISTS bundle_items (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            bundle_id UUID NOT NULL REFERENCES bundle_sales(id) ON DELETE CASCADE,
            product_id UUID NOT NULL REFERENCES products(id),
            quantity INTEGER NOT NULL,
            unit_price NUMERIC(12,2) NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )",

        "CREATE TABLE IF NOT EXISTS return_orders (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            return_no VARCHAR(50) NOT NULL UNIQUE,
            order_id UUID NOT NULL REFERENCES orders(id),
            salesperson_id UUID NOT NULL,
            reason TEXT NOT NULL,
            total_refund_amount NUMERIC(12,2) NOT NULL,
            status VARCHAR(20) NOT NULL DEFAULT 'pending',
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )",

        "CREATE TABLE IF NOT EXISTS return_items (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            return_id UUID NOT NULL REFERENCES return_orders(id) ON DELETE CASCADE,
            product_id UUID NOT NULL REFERENCES products(id),
            quantity INTEGER NOT NULL,
            refund_amount NUMERIC(12,2) NOT NULL,
            reason_detail TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )",

        // ── OA ──
        "CREATE TABLE IF NOT EXISTS employees (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            employee_no VARCHAR(50) NOT NULL UNIQUE,
            name VARCHAR(100) NOT NULL,
            department VARCHAR(100) NOT NULL DEFAULT '',
            position VARCHAR(100) NOT NULL DEFAULT '',
            email VARCHAR(200) NOT NULL DEFAULT '',
            phone VARCHAR(30),
            password_hash VARCHAR(255) NOT NULL DEFAULT '',
            status VARCHAR(20) NOT NULL DEFAULT 'active',
            role VARCHAR(20) NOT NULL DEFAULT 'user',
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )",

        "CREATE TABLE IF NOT EXISTS workflow_forms (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            creator_id UUID NOT NULL REFERENCES employees(id),
            title VARCHAR(200) NOT NULL,
            description TEXT,
            form_data JSONB NOT NULL DEFAULT '{}',
            status VARCHAR(20) NOT NULL DEFAULT 'pending',
            current_step INTEGER NOT NULL DEFAULT 1,
            total_steps INTEGER NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )",

        "CREATE TABLE IF NOT EXISTS workflow_steps (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            workflow_id UUID NOT NULL REFERENCES workflow_forms(id) ON DELETE CASCADE,
            step_number INTEGER NOT NULL,
            reviewer_id UUID NOT NULL REFERENCES employees(id),
            status VARCHAR(20) NOT NULL DEFAULT 'pending',
            comment TEXT,
            attachment_url VARCHAR(500),
            acted_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE(workflow_id, step_number)
        )",

        "CREATE TABLE IF NOT EXISTS workflow_archives (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            workflow_id UUID NOT NULL UNIQUE,
            archived_data JSONB NOT NULL,
            final_decision VARCHAR(20) NOT NULL,
            archived_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )",

        // ── INVENTORY ──
        "CREATE TABLE IF NOT EXISTS warehouses (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name VARCHAR(200) NOT NULL,
            location VARCHAR(300),
            manager_id UUID REFERENCES employees(id),
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )",

        "CREATE TABLE IF NOT EXISTS stock_in_records (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            stock_in_no VARCHAR(50) NOT NULL UNIQUE,
            order_id UUID REFERENCES orders(id),
            warehouse_id UUID NOT NULL,
            operator_id UUID NOT NULL,
            notes TEXT,
            status VARCHAR(20) NOT NULL DEFAULT 'pending',
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )",

        "CREATE TABLE IF NOT EXISTS stock_in_items (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            stock_in_id UUID NOT NULL REFERENCES stock_in_records(id) ON DELETE CASCADE,
            product_id UUID NOT NULL REFERENCES products(id),
            expected_quantity INTEGER NOT NULL,
            actual_quantity INTEGER NOT NULL,
            unit_price NUMERIC(12,2),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )",

        "CREATE TABLE IF NOT EXISTS stock_out_records (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            stock_out_no VARCHAR(50) NOT NULL UNIQUE,
            order_id UUID REFERENCES orders(id),
            warehouse_id UUID NOT NULL,
            operator_id UUID NOT NULL,
            vehicle_info VARCHAR(200),
            driver_info VARCHAR(200),
            notes TEXT,
            status VARCHAR(20) NOT NULL DEFAULT 'pending',
            shipped_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )",

        "CREATE TABLE IF NOT EXISTS stock_out_items (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            stock_out_id UUID NOT NULL REFERENCES stock_out_records(id) ON DELETE CASCADE,
            product_id UUID NOT NULL REFERENCES products(id),
            quantity INTEGER NOT NULL,
            unit_price NUMERIC(12,2),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )",

        "CREATE TABLE IF NOT EXISTS issues (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            related_type VARCHAR(30) NOT NULL,
            related_id UUID NOT NULL,
            description TEXT NOT NULL,
            severity VARCHAR(20) NOT NULL DEFAULT 'medium',
            status VARCHAR(20) NOT NULL DEFAULT 'open',
            reported_by UUID NOT NULL,
            assigned_to UUID,
            resolution TEXT,
            resolved_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )",

        // ── MASTER DATA ──
        "CREATE TABLE IF NOT EXISTS customers (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(), name VARCHAR(200) NOT NULL,
            contact_person VARCHAR(100), phone VARCHAR(20), email VARCHAR(200),
            address TEXT, notes TEXT, is_active BOOLEAN NOT NULL DEFAULT TRUE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )",

        "CREATE TABLE IF NOT EXISTS departments (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(), name VARCHAR(100) NOT NULL UNIQUE,
            description TEXT, is_active BOOLEAN NOT NULL DEFAULT TRUE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )",

        "CREATE TABLE IF NOT EXISTS positions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(), name VARCHAR(100) NOT NULL,
            department_id UUID REFERENCES departments(id), description TEXT,
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )",

        "CREATE TABLE IF NOT EXISTS vehicles (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(), plate_number VARCHAR(20) NOT NULL UNIQUE,
            model VARCHAR(100), capacity VARCHAR(50), driver_name VARCHAR(100),
            driver_phone VARCHAR(20), status VARCHAR(20) NOT NULL DEFAULT 'available',
            notes TEXT, is_active BOOLEAN NOT NULL DEFAULT TRUE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )",
    ];

    let table_count = sqls.len();
    for sql in sqls {
        let _ = sqlx::query(sql).execute(pool).await;
    }

    // Seed default admin if no employees exist
    let emp_count: (i64,) = sqlx::query_as("SELECT COUNT(*) FROM employees")
        .fetch_one(pool)
        .await
        .unwrap_or((0,));
    if emp_count.0 == 0 {
        let hash = bcrypt::hash("admin123", 10).expect("hash admin password");
        let _ = sqlx::query(
            "INSERT INTO employees (employee_no, name, department, position, email, password_hash, role, status)
             VALUES ('admin', '系统管理员', '管理部', '管理员', 'admin@tricore.local', $1, 'admin', 'active')"
        ).bind(&hash).execute(pool).await;
        info!("seeded default admin user (admin / admin123)");
    }

    // Seed default warehouse if none exist
    let wh_count: (i64,) = sqlx::query_as("SELECT COUNT(*) FROM warehouses")
        .fetch_one(pool)
        .await
        .unwrap_or((0,));
    if wh_count.0 == 0 {
        let _ = sqlx::query(
            "INSERT INTO warehouses (name, location, is_active) VALUES ('默认仓库', '主库区', TRUE)"
        ).execute(pool).await;
        info!("seeded default warehouse");
    }

    info!("schema check complete — {} tables verified", table_count);
}
