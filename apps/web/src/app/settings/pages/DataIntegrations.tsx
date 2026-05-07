import Integrations from "@/pages/Integrations";
import { CapabilityGate } from "../components/CapabilityGate";

export function DataIntegrations() {
  return (
    <CapabilityGate capability="integrations">
      <Integrations />
    </CapabilityGate>
  );
}
