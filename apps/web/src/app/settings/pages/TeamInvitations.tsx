export function TeamInvitations() {
  const invitations = [
    { email: "alex.m@partner.com", role: "Editor", sent: "2 days ago", status: "Pending" },
    { email: "maria.g@consulting.com", role: "Viewer", sent: "5 days ago", status: "Expired" },
  ];

  return (
    <div className="space-y-6">
      <section className="rounded-lg border bg-card p-5">
        <h3 className="text-sm font-semibold">Pending Invitations</h3>
        <div className="mt-4 overflow-hidden rounded-md border">
          <table className="w-full text-sm">
            <thead className="bg-muted/50">
              <tr>
                <th className="px-4 py-2 text-left text-xs font-medium text-muted-foreground">Email</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-muted-foreground">Role</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-muted-foreground">Sent</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-muted-foreground">Status</th>
                <th className="px-4 py-2 text-right text-xs font-medium text-muted-foreground">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {invitations.map((inv, i) => (
                <tr key={i}>
                  <td className="px-4 py-3 font-medium">{inv.email}</td>
                  <td className="px-4 py-3">{inv.role}</td>
                  <td className="px-4 py-3 text-muted-foreground">{inv.sent}</td>
                  <td className="px-4 py-3">
                    <span className={inv.status === "Pending" ? "text-primary" : "text-muted-foreground"}>{inv.status}</span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button type="button" className="text-xs font-medium text-primary hover:underline">Resend</button>
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
