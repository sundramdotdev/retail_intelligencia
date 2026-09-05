import dotenv from "dotenv";
dotenv.config();

export const config = {
  port: parseInt(process.env.DATA_SERVICE_PORT || "5000", 10),
  host: process.env.DATA_SERVICE_HOST || "0.0.0.0",
  databaseUrl: process.env.DATABASE_URL || "postgresql://retail_user:retail_pass@localhost:5432/retail_intelligencia?schema=public",
  internalSecret: process.env.INTERNAL_SERVICE_SECRET || "internal_data_secret_2026",
  environment: process.env.NODE_ENV || "development",
};
