-- Add vehicle & driver tracking to orders
ALTER TABLE orders ADD COLUMN IF NOT EXISTS vehicle_info VARCHAR(200);
ALTER TABLE orders ADD COLUMN IF NOT EXISTS driver_info VARCHAR(200);
