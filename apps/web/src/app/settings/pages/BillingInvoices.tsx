export function BillingInvoices() {
  const invoices = [
    { id: "INV-2025-001", date: "Sep 12, 2025", amount: "$249.00", status: "Paid" },
    { id: "INV-2025-002", date: "Aug 12, 2025", amount: "$249.00", status: "Paid" },
    { id: "INV-2025-003", date: "Jul 12, 2025", amount: "$249.00", status: "Paid" },
  ];

  return (
    <div className="space-y-6">
      <section className="rounded-lg border bg-card p-5">
        <h3 className="text-sm font-semibold">Invoice History</h3>
        <div className="mt-4 overflow-hidden rounded-md border">
          <table className="w-full text-sm">
            <thead className="bg-muted/50">
              <tr>
                <th className="px-4 py-2 text-left text-xs font-medium text-muted-foreground">Invoice</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-muted-foreground">Date</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-muted-foreground">Amount</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-muted-foreground">Status</th>
                <th className="px-4 py-2 text-right text-xs font-medium text-muted-foreground">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {invoices.map((inv) => (
                <tr key={inv.id}>
                  <td className="px-4 py-3 font-medium">{inv.id}</td>
                  <td className="px-4 py-3 text-muted-foreground">{inv.date}</td>
                  <td className="px-4 py-3">{inv.amount}</td>
                  <td className="px-4 py-3">
                    <span className="inline-flex rounded-full bg-primary/10 px-2 py-0.5 text-[10px] font-medium text-primary">{inv.status}</span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button type="button" className="text-xs font-medium text-primary hover:underline">Download</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
