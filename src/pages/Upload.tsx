import { UploadCloud, FileType, CheckCircle2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Label } from "@/components/ui/label"

export function Upload() {
  return (
    <div className="max-w-3xl mx-auto space-y-8">
      <div>
        <h2 className="text-2xl font-semibold tracking-tight text-slate-900 dark:text-zinc-50">Upload Data</h2>
        <p className="text-sm text-slate-500 dark:text-zinc-400">Securely ingest SAP CSVs, Utility bills, or Corporate Travel data.</p>
      </div>

      <Card className="shadow-sm border-none ring-1 ring-slate-900/5 dark:ring-white/10">
        <CardHeader>
          <CardTitle>Select Data Source</CardTitle>
          <CardDescription>Choose the type of data you are uploading to apply the correct validation rules.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="space-y-2">
            <Label>Data Source / Category</Label>
            <Select>
              <SelectTrigger>
                <SelectValue placeholder="Select a data source" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="sap">SAP Fuel / Procurement (CSV)</SelectItem>
                <SelectItem value="utility">Utility Electricity Data</SelectItem>
                <SelectItem value="travel">Corporate Travel & Expense</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="border-2 border-dashed border-slate-200 dark:border-zinc-800 rounded-xl p-12 text-center hover:bg-slate-50 dark:hover:bg-zinc-900/50 transition-colors cursor-pointer">
            <div className="mx-auto w-16 h-16 bg-slate-100 dark:bg-zinc-800 rounded-full flex items-center justify-center mb-4">
              <UploadCloud className="h-8 w-8 text-emerald-600 dark:text-emerald-500" />
            </div>
            <h3 className="text-lg font-medium text-slate-900 dark:text-zinc-50 mb-1">Click to upload or drag and drop</h3>
            <p className="text-sm text-slate-500 dark:text-zinc-400 max-w-sm mx-auto mb-6">
              Supported formats: CSV, XLSX. Maximum file size: 50MB. Make sure your data matches the required schema.
            </p>
            <Button className="bg-emerald-600 hover:bg-emerald-700 text-white">Select Files</Button>
          </div>

          <div className="bg-slate-50 dark:bg-zinc-900 rounded-lg p-4 flex items-center justify-between border dark:border-zinc-800">
            <div className="flex items-center space-x-3">
              <FileType className="h-8 w-8 text-slate-400" />
              <div>
                <p className="text-sm font-medium text-slate-900 dark:text-zinc-50">sap_procurement_q2_final.csv</p>
                <p className="text-xs text-slate-500">2.4 MB • Uploading... 84%</p>
              </div>
            </div>
            <div className="h-2 w-24 bg-slate-200 dark:bg-zinc-800 rounded-full overflow-hidden">
              <div className="h-full bg-emerald-600 w-[84%]" />
            </div>
          </div>
          
          <div className="bg-emerald-50 dark:bg-emerald-500/10 rounded-lg p-4 flex items-center space-x-3 border border-emerald-100 dark:border-emerald-500/20">
            <CheckCircle2 className="h-5 w-5 text-emerald-600 dark:text-emerald-500" />
            <div>
              <p className="text-sm font-medium text-emerald-800 dark:text-emerald-400">Upload Complete</p>
              <p className="text-xs text-emerald-600 dark:text-emerald-500">1,204 rows successfully processed. 3 rows sent to Review Queue.</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
