import { Navigate } from "react-router-dom";
import { useAuthContext } from "@/contexts/AuthContext";
import { BillingProvider } from "@/context/BillingContext";

export function BillingRoute({ children }: { children: React.ReactNode }) {
  const { user } = useAuthContext();

  if (!user?.id) {
    return <Navigate to="/home" replace />;
  }

  return <BillingProvider customerId={user.id}>{children}</BillingProvider>;
}
