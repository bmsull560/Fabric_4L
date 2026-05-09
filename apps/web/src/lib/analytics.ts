import { logError } from "./telemetry";

const ANALYTICS_SCRIPT_ID = "fabric-analytics-script";

export function installAnalytics(): void {
  const endpoint = import.meta.env.VITE_ANALYTICS_ENDPOINT;
  const websiteId = import.meta.env.VITE_ANALYTICS_WEBSITE_ID;

  if (!endpoint || !websiteId || typeof document === "undefined") {
    return;
  }

  try {
    const scriptUrl = new URL("/umami", endpoint);
    if (!["https:", "http:"].includes(scriptUrl.protocol)) {
      throw new Error(`Unsupported analytics protocol: ${scriptUrl.protocol}`);
    }

    if (document.getElementById(ANALYTICS_SCRIPT_ID)) {
      return;
    }

    const script = document.createElement("script");
    script.id = ANALYTICS_SCRIPT_ID;
    script.defer = true;
    script.src = scriptUrl.toString();
    script.dataset.websiteId = websiteId;
    document.body.appendChild(script);
  } catch (error) {
    logError("Analytics configuration ignored", {
      error: error instanceof Error ? error.message : String(error),
    });
  }
}
