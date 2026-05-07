import { useAuthContext } from "@/contexts/AuthContext";
import { useInvoices } from "@/hooks/useInvoices";
import { CapabilityGate } from "../components/CapabilityGate";

export function BillingInvoices() {
  const { user } = useAuthContext();
  const customerId = user?.tenantId ?? "";
  const { invoices, isLoading, error } = useInvoices(customerId);

  return (
    <CapabilityGate capability="billing">
      <div className="space-y-6">
        <section className="rounded-lg border bg-card p-5">
          <h3 className="text-sm font-semibold">Invoices</h3>
          <p className="text-xs text-muted-foreground">Live invoice history from the billing backend.</p>
          {isLoading ? (
            <div className="mt-4 rounded-md border p-4 text-sm text-muted-foreground">Loading invoices...</div>
          ) : error ? (
            <div className="mt-4 rounded-md border border-destructive/20 bg-destructive/5 p-4 text-sm text-destructive">
              {String(error)}
            </div>
          ) : (
            <div className="mt-4 overflow-hidden rounded-md border">
              <table className="w-full text-sm">
                <thead className="bg-muted/50">
                  <tr>
                    <th className="px-4 py-2 text-left text-xs font-medium text-muted-foreground">Invoice</th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-muted-foreground">Status</th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-muted-foreground">Total</th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-muted-foreground">Issued</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {invoices.length ? invoices.map((invoice) => (
                    <tr key={invoice.id}>
                      <td className="px-4 py-3 font-medium">
                        {invoice.invoice_pdf_url ? (
                          <a href={invoice.invoice_pdf_url} target="_blank" rel="noreferrer" className="hover:underline">
                            {invoice.invoice_number}
                          </a>
                        ) : invoice.invoice_number}
                      </td>
                      <td className="px-4 py-3 text-muted-foreground capitalize">{invoice.status}</td>
                      <td className="px-4 py-3 text-muted-foreground">${invoice.total_dollars.toFixed(2)}</td>
                      <td className="px-4 py-3 text-muted-foreground">{new Date(invoice.created_at).toLocaleDateString()}</td>
                    </tr>
                  )) : (
                    <tr>
                      <td colSpan={4} className="px-4 py-6 text-center text-sm text-muted-foreground">
                        No invoices are available for this tenant.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </div>
    </CapabilityGate>
  );
}
