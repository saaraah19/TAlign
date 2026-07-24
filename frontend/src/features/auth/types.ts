import { z } from "zod";

export type AccountType = "internal" | "candidate";
export type UserStatus = "active" | "invited" | "disabled";

export interface User {
  id: string;
  company_id: string | null;
  account_type: AccountType;
  email: string;
  first_name: string;
  last_name: string;
  avatar_url: string | null;
  status: UserStatus;
  roles: string[];
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface AccessTokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

// Mirrors backend Pydantic validation (app/schemas/auth.py). Client-side
// validation is UX only — the backend remains the source of truth.
export const registerCompanySchema = z.object({
  company_name: z.string().min(2).max(255),
  admin_first_name: z.string().min(1).max(100),
  admin_last_name: z.string().min(1).max(100),
  email: z.string().email(),
  password: z.string().min(8).max(128),
});
export type RegisterCompanyInput = z.infer<typeof registerCompanySchema>;

export const registerCandidateSchema = z.object({
  first_name: z.string().min(1).max(100),
  last_name: z.string().min(1).max(100),
  email: z.string().email(),
  password: z.string().min(8).max(128),
});
export type RegisterCandidateInput = z.infer<typeof registerCandidateSchema>;

export const loginSchema = z.object({
  email: z.string().email(),
  password: z.string().min(1, "Password is required"),
});
export type LoginInput = z.infer<typeof loginSchema>;
