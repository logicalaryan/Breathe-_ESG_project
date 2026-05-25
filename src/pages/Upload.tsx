import { useState, useRef } from "react"
import { UploadCloud, FileType, CheckCircle2, AlertCircle, Loader2, X, ChevronDown, ChevronUp } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"

// Mock server base URL — update to Django server URL in production
const API_BASE = "http://127.0.0.1:8000"

const ENDPOINTS: Record<string, string> = {
  sap:     "/api/process-sap/",
  utility: "/api/utility-allocation/",
  travel:  "/api/travel-emissions/",
}

const SOURCE_LABELS: Record<string, string> = {
  sap:     "SAP Fuel / Procurement (Scope 1)",
  utility: "Utility Electricity Data (Scope 2)",
  travel:  "Corporate Travel & Expense (Scope 3)",
}

type UploadState = "idle" | "uploading" | "success" | "error"

interface ApiResponse {
  metadata?: Record<string, unknown>
  validation_log?: string[]
  [key: string]: unknown
}

export function Upload() {
  const [source, setSource]           = useState<string>("")
  const [file, setFile]               = useState<File | null>(null)
  const [uploadState, setUploadState] = useState<UploadState>("idle")
  const [response, setResponse]       = useState<ApiResponse | null>(null)
  const [errorMsg, setErrorMsg]       = useState<string>("")
  const [showLogs, setShowLogs]       = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files?.[0] ?? null
    setFile(selected)
    setUploadState("idle")
    setResponse(null)
    setErrorMsg("")
  }

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    const dropped = e.dataTransfer.files?.[0] ?? null
    setFile(dropped)
    setUploadState("idle")
    setResponse(null)
  }

  const handleSubmit = async () => {
    if (!source) { setErrorMsg("Please select a data source."); return }
    if (!file)   { setErrorMsg("Please select a file to upload."); return }

    // Utility allocation expects JSON, all others expect multipart
    const isJson = source === "utility"

    setUploadState("uploading")
    setErrorMsg("")
    setResponse(null)

    try {
      let res: Response

      if (isJson) {
        // For utility billing: read CSV to extract values, or accept JSON directly
        // For demo: send file as multipart and let server parse it
        const formData = new FormData()
        formData.append("file", file)
        res = await fetch(`${API_BASE}${ENDPOINTS[source]}`, {
          method: "POST",
          body: formData,
        })
      } else {
        const formData = new FormData()
        formData.append("file", file)
        res = await fetch(`${API_BASE}${ENDPOINTS[source]}`, {
          method: "POST",
          body: formData,
        })
      }

      const data: ApiResponse = await res.json()

      if (res.ok) {
        setUploadState("success")
        setResponse(data)
      } else {
        setUploadState("error")
        setErrorMsg((data as { error?: string }).error ?? "Server returned an error.")
      }
    } catch (err) {
      setUploadState("error")
      setErrorMsg(
        "Could not connect to the backend server. " +
        "Start the mock server with: python backend/mock_server.py"
      )
    }
  }

  const resetUpload = () => {
    setFile(null)
    setUploadState("idle")
    setResponse(null)
    setErrorMsg("")
    setShowLogs(false)
    if (fileInputRef.current) fileInputRef.current.value = ""
  }

  const meta = response?.metadata as Record<string, unknown> | undefined
  const logs = response?.validation_log ?? []

  return (
    <div className="max-w-3xl mx-auto space-y-8">
      <div>
        <h2 className="text-2xl font-semibold tracking-tight text-slate-900 dark:text-zinc-50">Upload Data</h2>
        <p className="text-sm text-slate-500 dark:text-zinc-400">
          Securely ingest SAP CSVs, utility bills, or corporate travel expense reports.
        </p>
      </div>

      <Card className="shadow-sm border-none ring-1 ring-slate-900/5 dark:ring-white/10">
        <CardHeader>
          <CardTitle>Select Data Source</CardTitle>
          <CardDescription>
            Choose the emission scope to apply the correct validation rules and emission factors.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">

          {/* Source selector */}
          <div className="space-y-2">
            <Label>Data Source / GHG Protocol Scope</Label>
            <Select value={source} onValueChange={setSource}>
              <SelectTrigger>
                <SelectValue placeholder="Select a data source" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="sap">SAP Fuel / Procurement (Scope 1 — Direct Emissions)</SelectItem>
                <SelectItem value="utility">Utility Electricity Data (Scope 2 — Purchased Energy)</SelectItem>
                <SelectItem value="travel">Corporate Travel &amp; Expense (Scope 3 Cat. 6 — Business Travel)</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Drop zone */}
          <div
            className="border-2 border-dashed border-slate-200 dark:border-zinc-800 rounded-xl p-12 text-center hover:bg-slate-50 dark:hover:bg-zinc-900/50 transition-colors cursor-pointer"
            onDrop={handleDrop}
            onDragOver={e => e.preventDefault()}
            onClick={() => fileInputRef.current?.click()}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv"
              className="hidden"
              onChange={handleFileChange}
            />
            <div className="mx-auto w-16 h-16 bg-slate-100 dark:bg-zinc-800 rounded-full flex items-center justify-center mb-4">
              <UploadCloud className="h-8 w-8 text-emerald-600 dark:text-emerald-500" />
            </div>
            <h3 className="text-lg font-medium text-slate-900 dark:text-zinc-50 mb-1">
              Click to upload or drag and drop
            </h3>
            <p className="text-sm text-slate-500 dark:text-zinc-400 max-w-sm mx-auto mb-6">
              Supported format: CSV. Maximum file size: 50MB.
            </p>
            <Button
              type="button"
              className="bg-emerald-600 hover:bg-emerald-700 text-white"
              onClick={e => { e.stopPropagation(); fileInputRef.current?.click() }}
            >
              Select File
            </Button>
          </div>

          {/* Selected file display */}
          {file && uploadState !== "success" && (
            <div className="bg-slate-50 dark:bg-zinc-900 rounded-lg p-4 flex items-center justify-between border dark:border-zinc-800">
              <div className="flex items-center space-x-3">
                <FileType className="h-8 w-8 text-slate-400" />
                <div>
                  <p className="text-sm font-medium text-slate-900 dark:text-zinc-50">{file.name}</p>
                  <p className="text-xs text-slate-500">{(file.size / 1024).toFixed(1)} KB</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Badge variant="outline" className="text-xs text-slate-500">
                  {source ? SOURCE_LABELS[source] : "No source selected"}
                </Badge>
                <Button variant="ghost" size="icon" className="h-7 w-7" onClick={resetUpload}>
                  <X className="h-4 w-4 text-slate-400" />
                </Button>
              </div>
            </div>
          )}

          {/* Error message */}
          {errorMsg && (
            <div className="bg-rose-50 dark:bg-rose-900/20 border border-rose-200 dark:border-rose-700 rounded-lg p-4 flex items-start gap-3">
              <AlertCircle className="h-5 w-5 text-rose-500 shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-rose-800 dark:text-rose-300">Upload Error</p>
                <p className="text-xs text-rose-600 dark:text-rose-400 mt-0.5">{errorMsg}</p>
              </div>
            </div>
          )}

          {/* Submit button */}
          {file && uploadState !== "success" && (
            <Button
              className="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-semibold"
              onClick={handleSubmit}
              disabled={uploadState === "uploading"}
            >
              {uploadState === "uploading" ? (
                <><Loader2 className="h-4 w-4 mr-2 animate-spin" /> Processing...</>
              ) : (
                <><UploadCloud className="h-4 w-4 mr-2" /> Upload &amp; Process</>
              )}
            </Button>
          )}

          {/* Success panel */}
          {uploadState === "success" && response && (
            <div className="space-y-4">
              <div className="bg-emerald-50 dark:bg-emerald-500/10 rounded-lg p-4 flex items-start space-x-3 border border-emerald-100 dark:border-emerald-500/20">
                <CheckCircle2 className="h-5 w-5 text-emerald-600 dark:text-emerald-500 shrink-0 mt-0.5" />
                <div className="flex-1 space-y-1">
                  <p className="text-sm font-medium text-emerald-800 dark:text-emerald-400">
                    Upload Complete
                  </p>
                  {meta && (
                    <div className="text-xs text-emerald-700 dark:text-emerald-500 space-y-0.5">
                      {meta["rows_processed"] !== undefined && (
                        <p>{String(meta["rows_processed"])} rows processed successfully.</p>
                      )}
                      {meta["rows_skipped"] !== undefined && Number(meta["rows_skipped"]) > 0 && (
                        <p>{String(meta["rows_skipped"])} rows skipped — see validation log below.</p>
                      )}
                      {meta["grand_total_kg_co2e"] !== undefined && (
                        <p className="font-semibold">
                          Total emissions: {Number(meta["grand_total_kg_co2e"]).toLocaleString()} kg CO₂e
                          ({Number(meta["grand_total_tonnes_co2e"]).toFixed(3)} t CO₂e)
                        </p>
                      )}
                      {meta["total_kwh_distributed"] !== undefined && (
                        <p className="font-semibold">
                          Total kWh allocated: {Number(meta["total_kwh_distributed"]).toLocaleString()} kWh
                        </p>
                      )}
                      {meta["processed_rows"] !== undefined && (
                        <p>{String(meta["processed_rows"])} rows normalized.</p>
                      )}
                      {meta["emission_standard"] !== undefined && (
                        <p className="text-[11px] text-emerald-600/70">
                          Standard: {String(meta["emission_standard"])}
                        </p>
                      )}
                    </div>
                  )}
                </div>
              </div>

              {/* Validation log */}
              {logs.length > 0 && (
                <div className="border dark:border-zinc-800 rounded-lg overflow-hidden">
                  <button
                    className="w-full flex items-center justify-between px-4 py-3 text-sm font-medium text-slate-700 dark:text-zinc-300 bg-slate-50 dark:bg-zinc-900/60 hover:bg-slate-100 dark:hover:bg-zinc-800 transition-colors"
                    onClick={() => setShowLogs(v => !v)}
                  >
                    <span className="flex items-center gap-2">
                      <AlertCircle className="h-4 w-4 text-amber-500" />
                      Validation Log ({logs.length} notice{logs.length !== 1 ? "s" : ""})
                    </span>
                    {showLogs ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                  </button>
                  {showLogs && (
                    <ul className="divide-y dark:divide-zinc-800 text-xs">
                      {logs.map((log, i) => (
                        <li key={i} className="px-4 py-2.5 text-slate-600 dark:text-zinc-400 font-mono">
                          {log}
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              )}

              <Button variant="outline" className="w-full" onClick={resetUpload}>
                Upload Another File
              </Button>
            </div>
          )}

        </CardContent>
      </Card>
    </div>
  )
}
