import { apiFetch } from "@/lib/api-client";
import type {
  AccessTokenResponse,
  LoginInput,
  RegisterCandidateInput,
  RegisterCompanyInput,
  TokenResponse,
  User,
} from "./types";

export const authApi = {
  registerCompany: (input: RegisterCompanyInput) =>
    apiFetch<TokenResponse>("/auth/register/company", {
      method: "POST",
      body: JSON.stringify(input),
    }),

  registerCandidate: (input: RegisterCandidateInput) =>
    apiFetch<TokenResponse>("/auth/register/candidate", {
      method: "POST",
      body: JSON.stringify(input),
    }),

  login: (input: LoginInput) =>
    apiFetch<TokenResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify(input),
    }),

  refresh: () => apiFetch<AccessTokenResponse>("/auth/refresh", { method: "POST" }),

  logout: () => apiFetch<void>("/auth/logout", { method: "POST" }),

  me: () => apiFetch<User>("/auth/me"),
};
