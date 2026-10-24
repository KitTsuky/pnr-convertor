import axios from "axios";

import { env } from "@/shared/config/env";

export const http = axios.create({
  baseURL: env.VITE_API_BASE_URL,
  timeout: 15_000,
  headers: { Accept: "application/json, application/problem+json" },
});
