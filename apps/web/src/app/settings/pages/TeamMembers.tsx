export function TeamMembers() {
  const members = [
    { name: "Sarah Chen", email: "sarah.chen@axiomrobotics.com", role: "Owner", status: "Active" },
    { name: "James Wilson", email: "james.w@axiomrobotics.com", role: "Admin", status: "Active" },
    { name: "Priya Patel", email: "priya.p@axiomrobotics.com", role: "Editor", status: "Active" },
    { name: "Liam O'Brien", email: "liam.o@axiomrobotics.com", role: "Viewer", status: "Invited" },
  ];

  return (
    <div className="space-y-6">
      <section className="rounded-lg border bg-card p-5">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-semibold">Team Members</h3>
            <p className="text-xs text-muted-foreground">Invite, revoke access, and review active members.</p>
          </div>
          <button type="button" className="inline-flex h-8 items-center rounded-md bg-primary px-3 text-xs font-medium text-primary-foreground hover:opacity-90">Invite user</button>
        </div>
        <div className="mt-4 overflow-hidden rounded-md border">
          <table className="w-full text-sm">
            <thead className="bg-muted/50">
              <tr>
                <th className="px-4 py-2 text-left text-xs font-medium text-muted-foreground">User</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-muted-foreground">Role</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-muted-foreground">Status</th>
                <th className="px-4 py-2 text-right text-xs font-medium text-muted-foreground">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {members.map((m, i) => (
                <tr key={i}>
                  <td className="px-4 py-3">
                    <p className="font-medium">{m.name}</p>
                    <p className="text-xs text-muted-foreground">{m.email}</p>
                  </td>
                  <td className="px-4 py-3">
                    <span className="inline-flex rounded-full border px-2 py-0.5 text-[10px] font-medium">{m.role}</span>
                  </td>
                  <td className="px-4 py-3">
                    <span className={m.status === "Active" ? "text-primary" : "text-muted-foreground"}>{m.status}</span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button type="button" className="text-xs font-medium text-primary hover:underline">Manage</button>
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
