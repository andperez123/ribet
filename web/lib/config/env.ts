import { z } from "zod";

const envSchema = z.object({
  NEXT_PUBLIC_UPLOAD_MODE: z.enum(["mock", "api"]).default("mock"),
  NEXT_PUBLIC_API_URL: z.string().optional().default(""),
  NEXT_PUBLIC_DEMO_URL: z.string().optional().default(""),
  NEXT_PUBLIC_SIGN_IN_URL: z.string().optional().default(""),
});

export type Env = z.infer<typeof envSchema>;

export function getEnv(): Env {
  return envSchema.parse({
    NEXT_PUBLIC_UPLOAD_MODE: process.env.NEXT_PUBLIC_UPLOAD_MODE ?? "mock",
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL ?? "",
    NEXT_PUBLIC_DEMO_URL: process.env.NEXT_PUBLIC_DEMO_URL ?? "",
    NEXT_PUBLIC_SIGN_IN_URL: process.env.NEXT_PUBLIC_SIGN_IN_URL ?? "",
  });
}

export function getDemoUrl(): string {
  const env = getEnv();
  return env.NEXT_PUBLIC_DEMO_URL || "#demo";
}

export function getSignInUrl(): string {
  const env = getEnv();
  return env.NEXT_PUBLIC_SIGN_IN_URL || "/sign-in";
}
