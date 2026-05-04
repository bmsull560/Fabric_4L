export function BillingPaymentMethods() {
  return (
    <div className="space-y-6">
      <section className="rounded-lg border bg-card p-5">
        <h3 className="text-sm font-semibold">Payment Methods</h3>
        <div className="mt-4 space-y-2">
          <div className="flex items-center justify-between rounded-md border p-3">
            <div className="flex items-center gap-3">
              <div className="h-8 w-12 rounded border bg-muted" />
              <div>
                <p className="text-sm font-medium">•••• 4242</p>
                <p className="text-xs text-muted-foreground">Expires 12/26</p>
              </div>
            </div>
            <span className="text-[10px] font-medium uppercase tracking-wider text-primary">Default</span>
          </div>
          <button type="button" className="inline-flex h-9 items-center rounded-md border px-4 text-sm font-medium hover:bg-accent">Add payment method</button>
        </div>
      </section>

      <section className="rounded-lg border bg-card p-5">
        <h3 className="text-sm font-semibold">Billing Contact</h3>
        <div className="mt-4 grid gap-3 sm:grid-cols-2">
          <div>
            <label className="text-xs font-medium">Name</label>
            <input className="mt-1 h-9 w-full rounded-md border bg-background px-3 text-sm" placeholder="Billing contact name" />
          </div>
          <div>
            <label className="text-xs font-medium">Email</label>
            <input className="mt-1 h-9 w-full rounded-md border bg-background px-3 text-sm" placeholder="billing@company.com" />
          </div>
        </div>
      </section>
    </div>
  );
}
