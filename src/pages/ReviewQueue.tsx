import { useState, useMemo } from "react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table"
import {
  Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle,
} from "@/components/ui/sheet"
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select"
import {
  Search, AlertTriangle, Check, X, CheckCircle2, XCircle, Clock, ChevronRight, Inbox,
} from "lucide-react"

type Status = "Pending Review" | "Suspicious" | "Failed" | "Approved" | "Rejected"

type EsgRecord = {
  id: string
  source: string
  facility: string
  date: string
  amount: string
  unit: string
  emissions: string
  status: Status
  reason: string
  comments: string
}



const initialData: EsgRecord[] = [
  { id: "REQ-001", source: "SAP Fuel", facility: "Plant A – Mumbai", date: "Oct 24, 2024", amount: "5,420", unit: "gallons", emissions: "48.2 MT", status: "Suspicious", reason: "Variance > 50% from historical average", comments: "" },
  { id: "REQ-002", source: "Utility Bill", facility: "HQ – Bangalore", date: "Oct 24, 2024", amount: "N/A", unit: "—", emissions: "N/A", status: "Failed", reason: "Missing meter ID in uploaded file", comments: "" },
  { id: "REQ-003", source: "Corp Travel", facility: "Regional Office", date: "Oct 23, 2024", amount: "12", unit: "flights", emissions: "8.4 MT", status: "Pending Review", reason: "Requires manual sign-off per policy", comments: "" },
  { id: "REQ-004", source: "SAP Fuel", facility: "Plant B – Pune", date: "Oct 22, 2024", amount: "1,200", unit: "gallons", emissions: "10.6 MT", status: "Suspicious", reason: "Possible duplicate entry detected", comments: "" },
  { id: "REQ-005", source: "Utility Bill", facility: "Warehouse – Delhi", date: "Oct 21, 2024", amount: "45,000", unit: "kWh", emissions: "18.9 MT", status: "Pending Review", reason: "Requires manual sign-off per policy", comments: "" },
  { id: "REQ-006", source: "Corp Travel", facility: "Sales Team – Chennai", date: "Oct 20, 2024", amount: "3", unit: "flights", emissions: "2.1 MT", status: "Approved", reason: "Reviewed and verified by analyst", comments: "Confirmed with travel team." },
  { id: "REQ-007", source: "SAP Fuel", facility: "Plant C – Hyderabad", date: "Oct 19, 2024", amount: "890", unit: "gallons", emissions: "7.9 MT", status: "Rejected", reason: "Duplicate of REQ-003 confirmed", comments: "Rejected after cross-check." },
]

const STATUS_COLORS: { [k in Status]: string } = {
  "Suspicious":    "bg-amber-50 text-amber-700 border-amber-200",
  "Failed":        "bg-rose-50 text-rose-700 border-rose-200",
  "Pending Review":"bg-slate-100 text-slate-600 border-slate-200",
  "Approved":      "bg-emerald-50 text-emerald-700 border-emerald-200",
  "Rejected":      "bg-red-50 text-red-600 border-red-200",
}

const STATUS_ICON: { [k in Status]: React.ReactNode } = {
  "Suspicious":    <AlertTriangle className="h-3 w-3 mr-1" />,
  "Failed":        <XCircle className="h-3 w-3 mr-1" />,
  "Pending Review":<Clock className="h-3 w-3 mr-1" />,
  "Approved":      <CheckCircle2 className="h-3 w-3 mr-1" />,
  "Rejected":      <X className="h-3 w-3 mr-1" />,
}

export function ReviewQueue() {
  const [records, setRecords] = useState<EsgRecord[]>(initialData)
  const [search, setSearch] = useState("")
  const [filterStatus, setFilterStatus] = useState<string>("all")
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [openRecord, setOpenRecord] = useState<EsgRecord | null>(null)
  const [draftComment, setDraftComment] = useState("")
  const [toast, setToast] = useState<{ msg: string; type: "success" | "error" } | null>(null)

  const showToast = (msg: string, type: "success" | "error" = "success") => {
    setToast({ msg, type })
    setTimeout(() => setToast(null), 3000)
  }

  const updateStatus = (ids: string[], status: Status, comment?: string) => {
    setRecords(prev => prev.map(r =>
      ids.includes(r.id)
        ? { ...r, status, comments: comment !== undefined ? comment : r.comments }
        : r
    ))
  }

  const filtered = useMemo(() => {
    const q = search.toLowerCase()
    return records.filter(r => {
      const matchSearch = !q || r.id.toLowerCase().includes(q) || r.source.toLowerCase().includes(q) || r.facility.toLowerCase().includes(q)
      const matchStatus = filterStatus === "all" || r.status === filterStatus
      return matchSearch && matchStatus
    })
  }, [records, search, filterStatus])

  const allSelected = filtered.length > 0 && filtered.every(r => selected.has(r.id))
  const someSelected = filtered.some(r => selected.has(r.id))
  const selectedIds = [...selected]

  const toggleAll = () => {
    if (allSelected) {
      setSelected(prev => { const s = new Set(prev); filtered.forEach(r => s.delete(r.id)); return s })
    } else {
      setSelected(prev => { const s = new Set(prev); filtered.forEach(r => s.add(r.id)); return s })
    }
  }

  const toggleRow = (id: string) => {
    setSelected(prev => { const s = new Set(prev); s.has(id) ? s.delete(id) : s.add(id); return s })
  }

  const handleBulkApprove = () => {
    const ids = selectedIds.filter(id => {
      const r = records.find(x => x.id === id)
      return r && r.status !== "Approved"
    })
    if (!ids.length) return showToast("No eligible rows selected.", "error")
    updateStatus(ids, "Approved")
    setSelected(new Set())
    showToast(`${ids.length} record${ids.length > 1 ? "s" : ""} approved.`)
  }

  const handleBulkReject = () => {
    const ids = selectedIds.filter(id => {
      const r = records.find(x => x.id === id)
      return r && r.status !== "Rejected"
    })
    if (!ids.length) return showToast("No eligible rows selected.", "error")
    updateStatus(ids, "Rejected")
    setSelected(new Set())
    showToast(`${ids.length} record${ids.length > 1 ? "s" : ""} rejected.`, "error")
  }

  const openDrawer = (record: EsgRecord) => {
    setOpenRecord(record)
    setDraftComment(record.comments)
  }

  const handleDrawerApprove = () => {
    if (!openRecord) return
    updateStatus([openRecord.id], "Approved", draftComment)
    showToast(`${openRecord.id} approved.`)
    setOpenRecord(null)
  }

  const handleDrawerReject = () => {
    if (!openRecord) return
    updateStatus([openRecord.id], "Rejected", draftComment)
    showToast(`${openRecord.id} rejected.`, "error")
    setOpenRecord(null)
  }

  const activeFilterCount = (filterStatus !== "all" ? 1 : 0) + (search ? 1 : 0)

  return (
    <div className="space-y-6">
      {/* Toast */}
      {toast && (
        <div className={`fixed top-5 right-5 z-50 flex items-center gap-3 px-4 py-3 rounded-lg shadow-lg text-sm font-medium transition-all ${toast.type === "success" ? "bg-emerald-600 text-white" : "bg-rose-600 text-white"}`}>
          {toast.type === "success" ? <CheckCircle2 className="h-4 w-4" /> : <XCircle className="h-4 w-4" />}
          {toast.msg}
        </div>
      )}

      <div>
        <h2 className="text-2xl font-semibold tracking-tight text-slate-900 dark:text-zinc-50">Review Queue</h2>
        <p className="text-sm text-slate-500 dark:text-zinc-400">Resolve validation errors and approve suspicious emissions records.</p>
      </div>

      {/* Toolbar */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="relative w-72">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-slate-400" />
            <Input
              placeholder="Search by ID, source, or facility..."
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="pl-9 bg-white dark:bg-zinc-900"
            />
          </div>
          <Select value={filterStatus} onValueChange={setFilterStatus}>
            <SelectTrigger className="w-44 bg-white dark:bg-zinc-900">
              <SelectValue placeholder="Filter by status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Statuses</SelectItem>
              <SelectItem value="Pending Review">Pending Review</SelectItem>
              <SelectItem value="Suspicious">Suspicious</SelectItem>
              <SelectItem value="Failed">Failed</SelectItem>
              <SelectItem value="Approved">Approved</SelectItem>
              <SelectItem value="Rejected">Rejected</SelectItem>
            </SelectContent>
          </Select>
          {activeFilterCount > 0 && (
            <Button variant="ghost" size="sm" className="text-slate-500 gap-1" onClick={() => { setSearch(""); setFilterStatus("all") }}>
              <X className="h-3 w-3" /> Clear filters
            </Button>
          )}
        </div>
        <div className="flex gap-2">
          {someSelected && (
            <span className="text-sm text-slate-500 self-center">{selectedIds.length} selected</span>
          )}
          <Button
            variant="outline"
            disabled={!someSelected}
            onClick={handleBulkReject}
            className="text-rose-600 hover:text-rose-700 hover:bg-rose-50 disabled:opacity-40"
          >
            <X className="h-4 w-4 mr-1" /> Reject Selected
          </Button>
          <Button
            disabled={!someSelected}
            onClick={handleBulkApprove}
            className="bg-emerald-600 hover:bg-emerald-700 text-white disabled:opacity-40"
          >
            <Check className="h-4 w-4 mr-1" /> Approve Selected
          </Button>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white dark:bg-zinc-900 rounded-xl border dark:border-zinc-800 shadow-sm overflow-hidden">
        <Table>
          <TableHeader className="bg-slate-50 dark:bg-zinc-900/80 border-b dark:border-zinc-800">
            <TableRow>
              <TableHead className="w-12 text-center">
                <input
                  type="checkbox"
                  className="rounded border-slate-300 cursor-pointer"
                  checked={allSelected}
                  ref={el => { if (el) el.indeterminate = someSelected && !allSelected }}
                  onChange={toggleAll}
                />
              </TableHead>
              <TableHead className="font-semibold">Record ID</TableHead>
              <TableHead className="font-semibold">Source</TableHead>
              <TableHead className="font-semibold">Facility</TableHead>
              <TableHead className="font-semibold">Amount</TableHead>
              <TableHead className="font-semibold">Est. Emissions</TableHead>
              <TableHead className="font-semibold">Status</TableHead>
              <TableHead className="text-right font-semibold">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filtered.length === 0 ? (
              <TableRow>
                <TableCell colSpan={8} className="py-20 text-center">
                  <div className="flex flex-col items-center gap-3 text-slate-400">
                    <Inbox className="h-10 w-10 opacity-40" />
                    <p className="font-medium text-slate-500">No records match your filters</p>
                    <p className="text-sm">Try adjusting your search or clearing filters.</p>
                  </div>
                </TableCell>
              </TableRow>
            ) : filtered.map(row => (
              <TableRow
                key={row.id}
                className={`hover:bg-slate-50 dark:hover:bg-zinc-800/50 transition-colors ${selected.has(row.id) ? "bg-emerald-50/40 dark:bg-emerald-900/10" : ""}`}
              >
                <TableCell className="text-center">
                  <input
                    type="checkbox"
                    className="rounded border-slate-300 cursor-pointer"
                    checked={selected.has(row.id)}
                    onChange={() => toggleRow(row.id)}
                  />
                </TableCell>
                <TableCell className="font-mono font-medium text-slate-900 dark:text-zinc-50">{row.id}</TableCell>
                <TableCell className="text-slate-600 dark:text-zinc-300">{row.source}</TableCell>
                <TableCell className="text-slate-500 text-sm">{row.facility}</TableCell>
                <TableCell className="tabular-nums">
                  {row.amount} <span className="text-slate-400 text-xs">{row.unit}</span>
                </TableCell>
                <TableCell className="tabular-nums font-medium">{row.emissions}</TableCell>
                <TableCell>
                  <Badge variant="outline" className={`inline-flex items-center text-xs ${STATUS_COLORS[row.status]}`}>
                    {STATUS_ICON[row.status]}
                    {row.status}
                  </Badge>
                </TableCell>
                <TableCell className="text-right">
                  <div className="flex items-center justify-end gap-1">
                    {row.status !== "Approved" && row.status !== "Rejected" && (
                      <>
                        <Button
                          variant="ghost" size="icon"
                          className="h-8 w-8 text-emerald-600 hover:text-emerald-700 hover:bg-emerald-50"
                          title="Quick Approve"
                          onClick={() => { updateStatus([row.id], "Approved"); showToast(`${row.id} approved.`) }}
                        >
                          <Check className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost" size="icon"
                          className="h-8 w-8 text-rose-500 hover:text-rose-600 hover:bg-rose-50"
                          title="Quick Reject"
                          onClick={() => { updateStatus([row.id], "Rejected"); showToast(`${row.id} rejected.`, "error") }}
                        >
                          <X className="h-4 w-4" />
                        </Button>
                      </>
                    )}
                    <Button
                      variant="outline" size="sm"
                      className="text-slate-600 gap-1 ml-1"
                      onClick={() => openDrawer(row)}
                    >
                      Details <ChevronRight className="h-3 w-3" />
                    </Button>
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
        {filtered.length > 0 && (
          <div className="px-4 py-3 border-t dark:border-zinc-800 text-xs text-slate-400 flex justify-between">
            <span>Showing {filtered.length} of {records.length} records</span>
            <span>{records.filter(r => r.status === "Pending Review" || r.status === "Suspicious" || r.status === "Failed").length} pending action</span>
          </div>
        )}
      </div>

      {/* Detail Drawer */}
      <Sheet open={!!openRecord} onOpenChange={open => !open && setOpenRecord(null)}>
        <SheetContent className="w-full sm:max-w-lg overflow-y-auto flex flex-col gap-0 p-0">
          {openRecord && (
            <>
              <SheetHeader className="px-6 py-5 border-b dark:border-zinc-800">
                <div className="flex items-center justify-between">
                  <SheetTitle className="text-base">Record Details</SheetTitle>
                  <Badge variant="outline" className={`text-xs ${STATUS_COLORS[openRecord.status]}`}>
                    {STATUS_ICON[openRecord.status]}{openRecord.status}
                  </Badge>
                </div>
                <SheetDescription className="font-mono text-xs">{openRecord.id} · {openRecord.source}</SheetDescription>
              </SheetHeader>

              <div className="flex-1 px-6 py-5 space-y-6">
                {/* Key data */}
                <div className="grid grid-cols-2 gap-x-6 gap-y-4 text-sm">
                  {[
                    ["Facility", openRecord.facility],
                    ["Date", openRecord.date],
                    ["Reported Amount", `${openRecord.amount} ${openRecord.unit}`],
                    ["Est. Emissions", openRecord.emissions],
                    ["Data Source", openRecord.source],
                  ].map(([label, value]) => (
                    <div key={label}>
                      <span className="text-xs font-medium text-slate-400 uppercase tracking-wide block mb-0.5">{label}</span>
                      <span className="font-medium text-slate-900 dark:text-zinc-50">{value}</span>
                    </div>
                  ))}
                </div>

                {/* Warning banner */}
                <div className={`rounded-lg p-4 border text-sm space-y-1 ${
                  openRecord.status === "Approved"
                    ? "bg-emerald-50 border-emerald-200 dark:bg-emerald-900/20 dark:border-emerald-700"
                    : openRecord.status === "Rejected"
                    ? "bg-red-50 border-red-200 dark:bg-red-900/20 dark:border-red-700"
                    : "bg-amber-50 border-amber-200 dark:bg-amber-900/20 dark:border-amber-700"
                }`}>
                  <h4 className="font-semibold flex items-center gap-2 text-slate-800 dark:text-zinc-100">
                    <AlertTriangle className="h-4 w-4 text-amber-500" />
                    Validation Note
                  </h4>
                  <p className="text-slate-600 dark:text-zinc-300">{openRecord.reason}.</p>
                  {openRecord.status !== "Approved" && openRecord.status !== "Rejected" && (
                    <p className="text-slate-500 dark:text-zinc-400 text-xs pt-1">Please verify with the facility manager before approving.</p>
                  )}
                </div>

                {/* Raw data preview */}
                <div>
                  <p className="text-xs font-medium text-slate-400 uppercase tracking-wide mb-2">Raw Data Fields</p>
                  <div className="rounded-lg border dark:border-zinc-800 divide-y dark:divide-zinc-800 text-sm">
                    {[
                      ["record_id", openRecord.id],
                      ["data_source", openRecord.source],
                      ["reported_quantity", openRecord.amount],
                      ["unit", openRecord.unit],
                      ["co2e_estimate", openRecord.emissions],
                      ["upload_date", openRecord.date],
                    ].map(([k, v]) => (
                      <div key={k} className="flex justify-between px-3 py-2">
                        <span className="font-mono text-xs text-slate-400">{k}</span>
                        <span className="font-mono text-xs text-slate-800 dark:text-zinc-100">{v}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Analyst comment */}
                <div className="space-y-2">
                  <Label className="text-sm font-medium">Analyst Comment</Label>
                  <textarea
                    className="w-full min-h-[90px] p-3 text-sm rounded-lg border border-slate-200 dark:border-zinc-700 bg-white dark:bg-zinc-900 resize-none focus:outline-none focus:ring-2 focus:ring-emerald-500"
                    placeholder="Add notes about your review decision…"
                    value={draftComment}
                    onChange={e => setDraftComment(e.target.value)}
                  />
                </div>
              </div>

              {/* Footer actions */}
              <div className="px-6 py-4 border-t dark:border-zinc-800 flex justify-end gap-3 bg-slate-50 dark:bg-zinc-900/60">
                {openRecord.status !== "Approved" && openRecord.status !== "Rejected" ? (
                  <>
                    <Button variant="outline" className="text-rose-600 hover:bg-rose-50 hover:text-rose-700" onClick={handleDrawerReject}>
                      <X className="h-4 w-4 mr-1" /> Reject Record
                    </Button>
                    <Button className="bg-emerald-600 hover:bg-emerald-700 text-white" onClick={handleDrawerApprove}>
                      <Check className="h-4 w-4 mr-1" /> Approve Record
                    </Button>
                  </>
                ) : (
                  <Button variant="outline" onClick={() => {
                    updateStatus([openRecord.id], openRecord.status, draftComment)
                    setOpenRecord(null)
                    showToast("Comment saved.")
                  }}>
                    Save Comment
                  </Button>
                )}
              </div>
            </>
          )}
        </SheetContent>
      </Sheet>
    </div>
  )
}
