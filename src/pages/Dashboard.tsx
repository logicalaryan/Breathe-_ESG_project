import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Activity, AlertCircle, FileText, UploadCloud } from "lucide-react"
import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts"

const data = [
  { name: "Jan", scope1: 400, scope2: 240, scope3: 2400 },
  { name: "Feb", scope1: 300, scope2: 139, scope3: 2210 },
  { name: "Mar", scope1: 200, scope2: 980, scope3: 2290 },
  { name: "Apr", scope1: 278, scope2: 390, scope3: 2000 },
  { name: "May", scope1: 189, scope2: 480, scope3: 2181 },
  { name: "Jun", scope1: 239, scope2: 380, scope3: 2500 },
  { name: "Jul", scope1: 349, scope2: 430, scope3: 2100 },
]

export function Dashboard() {
  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-2xl font-semibold tracking-tight text-slate-900 dark:text-zinc-50">Overview</h2>
        <p className="text-sm text-slate-500 dark:text-zinc-400">Track your organization's emissions and reporting status.</p>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Emissions (MT CO2e)</CardTitle>
            <Activity className="h-4 w-4 text-emerald-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-slate-900 dark:text-zinc-50">14,231.89</div>
            <p className="text-xs text-slate-500 mt-1">+2.1% from last month</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pending Reviews</CardTitle>
            <AlertCircle className="h-4 w-4 text-amber-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-slate-900 dark:text-zinc-50">34</div>
            <p className="text-xs text-slate-500 mt-1">Requires analyst attention</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Failed Imports</CardTitle>
            <AlertCircle className="h-4 w-4 text-rose-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-slate-900 dark:text-zinc-50">12</div>
            <p className="text-xs text-slate-500 mt-1">Validation errors detected</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Recent Uploads</CardTitle>
            <UploadCloud className="h-4 w-4 text-slate-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-slate-900 dark:text-zinc-50">8</div>
            <p className="text-xs text-slate-500 mt-1">In the last 7 days</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 md:grid-cols-7">
        <Card className="md:col-span-4 shadow-sm border-none ring-1 ring-slate-900/5 dark:ring-white/10">
          <CardHeader>
            <CardTitle>Emissions Breakdown (YTD)</CardTitle>
          </CardHeader>
          <CardContent className="pl-2">
            <div className="h-[300px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                  <XAxis dataKey="name" stroke="#888888" fontSize={12} tickLine={false} axisLine={false} />
                  <YAxis stroke="#888888" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(value) => `${value}`} />
                  <Tooltip />
                  <Area type="monotone" dataKey="scope3" stackId="1" stroke="#cbd5e1" fill="#f1f5f9" />
                  <Area type="monotone" dataKey="scope2" stackId="1" stroke="#10b981" fill="#d1fae5" />
                  <Area type="monotone" dataKey="scope1" stackId="1" stroke="#047857" fill="#10b981" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
        <Card className="md:col-span-3 shadow-sm border-none ring-1 ring-slate-900/5 dark:ring-white/10">
          <CardHeader>
            <CardTitle>Recent Activity</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              {[
                { title: "SAP Fuel Data (Q2)", status: "Pending Review", time: "2 hours ago", icon: FileText, color: "text-amber-500", bg: "bg-amber-100 dark:bg-amber-500/20" },
                { title: "Utility Bills (March)", status: "Failed Validation", time: "5 hours ago", icon: AlertCircle, color: "text-rose-500", bg: "bg-rose-100 dark:bg-rose-500/20" },
                { title: "Corporate Travel (April)", status: "Approved", time: "1 day ago", icon: Activity, color: "text-emerald-500", bg: "bg-emerald-100 dark:bg-emerald-500/20" },
              ].map((item, i) => (
                <div key={i} className="flex items-center">
                  <div className={`h-9 w-9 rounded-full flex items-center justify-center ${item.bg} mr-4`}>
                    <item.icon className={`h-4 w-4 ${item.color}`} />
                  </div>
                  <div className="flex-1 space-y-1">
                    <p className="text-sm font-medium leading-none">{item.title}</p>
                    <p className="text-sm text-slate-500">{item.status}</p>
                  </div>
                  <div className="text-xs text-slate-500">{item.time}</div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
