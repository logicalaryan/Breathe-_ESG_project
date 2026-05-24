import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"

const auditLogs = [
  { id: "LOG-001", action: "Approved Record REQ-001", user: "Sarah Analyst", date: "Oct 24, 2024 14:32:01", details: "Manual override: variance verified with supplier." },
  { id: "LOG-002", action: "Rejected Record REQ-002", user: "John Doe", date: "Oct 24, 2024 10:15:22", details: "Missing mandatory meter ID." },
  { id: "LOG-003", action: "Uploaded SAP Fuel Data", user: "System (API)", date: "Oct 23, 2024 02:00:00", details: "Processed 1,204 rows, 5 failed." },
  { id: "LOG-004", action: "Updated Settings", user: "Admin", date: "Oct 22, 2024 16:45:11", details: "Changed default reporting currency to USD." },
]

export function AuditHistory() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-semibold tracking-tight text-slate-900 dark:text-zinc-50">Audit History</h2>
        <p className="text-sm text-slate-500 dark:text-zinc-400">View a chronological log of all actions, approvals, and data changes.</p>
      </div>

      <div className="bg-white dark:bg-zinc-900 rounded-xl border dark:border-zinc-800 shadow-sm overflow-hidden">
        <Table>
          <TableHeader className="bg-slate-50 dark:bg-zinc-900 border-b dark:border-zinc-800">
            <TableRow>
              <TableHead>Log ID</TableHead>
              <TableHead>Timestamp</TableHead>
              <TableHead>User / System</TableHead>
              <TableHead>Action</TableHead>
              <TableHead>Details</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {auditLogs.map((log) => (
              <TableRow key={log.id} className="hover:bg-slate-50 dark:hover:bg-zinc-800/50">
                <TableCell className="font-medium text-slate-900 dark:text-zinc-50">{log.id}</TableCell>
                <TableCell className="text-slate-500 whitespace-nowrap">{log.date}</TableCell>
                <TableCell>{log.user}</TableCell>
                <TableCell className="font-medium">{log.action}</TableCell>
                <TableCell className="text-slate-500 max-w-xs truncate" title={log.details}>
                  {log.details}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  )
}
