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
    let sqls = vec![
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
        "ALTER TABLE orders ADD COLUMN IF NOT EXISTS vehicle_info VARCHAR(200)",
        "ALTER TABLE orders ADD COLUMN IF NOT EXISTS driver_info VARCHAR(200)",
    ];
    for sql in sqls {
        let _ = sqlx::query(sql).execute(pool).await;
    }
    info!("schema check complete");
}
