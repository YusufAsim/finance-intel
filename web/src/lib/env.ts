/** Base urls come from the environment so the build is deployment neutral. */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "/api";
const AGENT_BASE_URL = import.meta.env.VITE_AGENT_BASE_URL ?? "";

export const env = {
  apiBaseUrl: API_BASE_URL.replace(/\/$/, ""),
  agentBaseUrl: AGENT_BASE_URL.replace(/\/$/, ""),
};
