pub struct Config {
    pub database_url: String,
    pub server_host: String,
    pub server_port: u16,
    pub jwt_secret: String,
    pub upload_dir: String,
    pub snapshot_interval_secs: u64,
}

impl Config {
    pub fn from_env() -> Self {
        Self {
            database_url: std::env::var("DATABASE_URL")
                .expect("DATABASE_URL must be set"),
            server_host: std::env::var("SERVER_HOST")
                .unwrap_or_else(|_| "0.0.0.0".into()),
            server_port: std::env::var("SERVER_PORT")
                .unwrap_or_else(|_| "8080".into())
                .parse()
                .expect("SERVER_PORT must be a valid port number"),
            jwt_secret: std::env::var("JWT_SECRET")
                .unwrap_or_else(|_| "tricore-dev-secret-2026".into()),
            upload_dir: std::env::var("UPLOAD_DIR")
                .unwrap_or_else(|_| "./uploads".into()),
            snapshot_interval_secs: std::env::var("SNAPSHOT_INTERVAL_SECS")
                .unwrap_or_else(|_| "3600".into())
                .parse()
                .unwrap_or(3600),
        }
    }
}
