let prismaClient: any = null;

export function getPrismaClient(): any {
  if (!prismaClient) {
    try {
      const { PrismaClient } = require("@prisma/client");
      prismaClient = new PrismaClient({
        log: process.env.NODE_ENV === "development" ? ["query", "error", "warn"] : ["error"],
      });
    } catch (err) {
      // Prisma client not generated yet or no native bindings in local test sandbox
      prismaClient = null;
    }
  }
  return prismaClient;
}

export const prisma = getPrismaClient();
