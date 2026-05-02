export function DataVariables() {
  const variables = [
    { name: "Loaded_Annual_Cost", type: "Currency", scope: "Tenant", source: "ERP" },
    { name: "Plant_Cycle_Time", type: "Duration", scope: "Tenant", source: "MES" },
    { name: "Defect_Rate", type: "Percentage", scope: "Account", source: "Manual" },
    { name: "Customer_Acquisition_Cost", type: "Currency", scope: "Account", source: "CRM" },
  ];

  return (
    <div className="space-y-6">
      <section className="rounded-lg border bg-card p-5">
        <h3 className="text-sm font-semibold">Variable Registry</h3>
        <p className="text-xs text-muted-foreground">Reusable variables and custom fields used across formulas.</p>
        <div className="mt-4 overflow-hidden rounded-md border">
          <table className="w-full text-sm">
            <thead className="bg-muted/50">
              <tr>
                <th className="px-4 py-2 text-left text-xs font-medium text-muted-foreground">Variable</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-muted-foreground">Type</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-muted-foreground">Scope</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-muted-foreground">Source</th>
                <th className="px-4 py-2 text-right text-xs font-medium text-muted-foreground">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {variables.map((v) => (
                <tr key={v.name}>
                  <td className="px-4 py-3 font-medium">{v.name}</td>
                  <td className="px-4 py-3 text-muted-foreground">{v.type}</td>
                  <td className="px-4 py-3 text-muted-foreground">{v.scope}</td>
                  <td className="px-4 py-3 text-muted-foreground">{v.source}</td>
                  <td className="px-4 py-3 text-right">
                    <button type="button" className="text-xs font-medium text-primary hover:underline">Edit</button>
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
