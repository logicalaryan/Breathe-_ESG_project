import { useState } from "react"
import { Link } from "react-router-dom"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { 
  Activity, 
  AlertCircle, 
  FileText, 
  UploadCloud, 
  Flame, 
  Zap, 
  Plane, 
  Sparkles, 
  BarChart3,
  RefreshCw
} from "lucide-react"
import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis, YAxis, CartesianGrid } from "recharts"

const chartData = [
  { name: "Jan", scope1: 400, scope2: 240, scope3: 2400 },
  { name: "Feb", scope1: 300, scope2: 139, scope3: 2210 },
  { name: "Mar", scope1: 200, scope2: 980, scope3: 2290 },
  { name: "Apr", scope1: 278, scope2: 390, scope3: 2000 },
  { name: "May", scope1: 189, scope2: 480, scope3: 2181 },
  { name: "Jun", scope1: 239, scope2: 380, scope3: 2500 },
  { name: "Jul", scope1: 349, scope2: 430, scope3: 2100 },
]

interface TooltipProps {
  active?: boolean;
  payload?: any[];
  label?: string;
}

function CustomTooltip({ active, payload, label }: TooltipProps) {
  if (active && payload && payload.length) {
    return (
      <div className="bg-white dark:bg-zinc-900 border border-slate-100 dark:border-zinc-800 p-4 rounded-xl shadow-xl space-y-3 min-w-[260px] animate-in fade-in slide-in-from-bottom-2 duration-200">
        <div className="text-xs font-semibold text-slate-400 dark:text-zinc-500 uppercase tracking-wider">
          Month of {label}
        </div>
        <div className="space-y-2">
          {payload.map((item, index) => {
            let labelText = "";
            let categoryName = "";
            let colorDot = "";
            let trend = "";
            let trendColor = "";

            if (item.name === "scope1") {
              labelText = "Direct (Fuel Usage)";
              categoryName = "Scope 1";
              colorDot = "bg-emerald-800 dark:bg-emerald-600";
              trend = "↓ 4% this month";
              trendColor = "text-emerald-600 dark:text-emerald-400";
            } else if (item.name === "scope2") {
              labelText = "Indirect (Electricity)";
              categoryName = "Scope 2";
              colorDot = "bg-emerald-500";
              trend = "↑ 8% this month";
              trendColor = "text-rose-600 dark:text-rose-400";
            } else {
              labelText = "Value Chain (Travel)";
              categoryName = "Scope 3";
              colorDot = "bg-emerald-200 dark:bg-emerald-800/80";
              trend = "Stable YTD";
              trendColor = "text-slate-500 dark:text-zinc-400";
            }

            return (
              <div key={index} className="flex flex-col space-y-0.5 border-b border-slate-50 dark:border-zinc-800/50 pb-2 last:border-b-0 last:pb-0">
                <div className="flex items-center justify-between text-sm">
                  <div className="flex items-center gap-2">
                    <span className={`h-2.5 w-2.5 rounded-full ${colorDot}`} />
                    <span className="text-slate-700 dark:text-zinc-300 font-medium">{labelText}</span>
                  </div>
                  <span className="text-slate-900 dark:text-white font-bold">{item.value.toLocaleString()} MT</span>
                </div>
                <div className="flex items-center justify-between text-[11px] pl-4.5">
                  <span className="text-slate-400 dark:text-zinc-500 font-medium">{categoryName}</span>
                  <span className={`font-semibold flex items-center gap-0.5 ${trendColor}`}>
                    {trend}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    );
  }
  return null;
}

export function Dashboard() {
  const [showEmptyState, setShowEmptyState] = useState(false)

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h2 className="text-3xl font-bold tracking-tight text-slate-900 dark:text-zinc-50">Operational Overview</h2>
          <p className="text-sm text-slate-500 dark:text-zinc-400 mt-1">
            Plain-language sustainability metrics and compliance tracking for non-technical ESG analysts.
          </p>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <Button 
            variant="outline" 
            size="sm"
            onClick={() => setShowEmptyState(!showEmptyState)}
            className="text-xs bg-white dark:bg-zinc-900 text-slate-700 dark:text-zinc-300 hover:bg-slate-50 border dark:border-zinc-800 flex items-center gap-2"
          >
            <RefreshCw size={12} className={showEmptyState ? "animate-spin" : ""} />
            Toggle View: {showEmptyState ? "Active Data" : "Empty State"}
          </Button>
        </div>
      </div>

      {/* Primary KPI Summary Cards */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        <Card className="border-none shadow-sm ring-1 ring-slate-100 dark:ring-zinc-800/80 bg-white dark:bg-zinc-900">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-xs font-semibold tracking-wider text-slate-400 uppercase">Total Footprint</CardTitle>
            <Activity className="h-4 w-4 text-emerald-600 dark:text-emerald-500" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-slate-900 dark:text-zinc-50">14,231.89</div>
            <div className="flex items-center gap-1.5 mt-1.5">
              <span className="text-[11px] font-bold bg-rose-50 text-rose-600 dark:bg-rose-950/30 dark:text-rose-400 px-1.5 py-0.5 rounded flex items-center gap-0.5">
                ↑ 2.1%
              </span>
              <span className="text-[11px] text-slate-400 dark:text-zinc-500 font-medium">vs trailing 30 days</span>
            </div>
          </CardContent>
        </Card>
        <Card className="border-none shadow-sm ring-1 ring-slate-100 dark:ring-zinc-800/80 bg-white dark:bg-zinc-900">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-xs font-semibold tracking-wider text-slate-400 uppercase">Pending Audits</CardTitle>
            <AlertCircle className="h-4 w-4 text-amber-500" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-slate-900 dark:text-zinc-50">34</div>
            <div className="flex items-center gap-1.5 mt-1.5">
              <span className="text-[11px] font-bold bg-amber-50 text-amber-700 dark:bg-amber-950/30 dark:text-amber-400 px-1.5 py-0.5 rounded">
                Action Required
              </span>
              <span className="text-[11px] text-slate-400 dark:text-zinc-500 font-medium">Validation review queue</span>
            </div>
          </CardContent>
        </Card>
        <Card className="border-none shadow-sm ring-1 ring-slate-100 dark:ring-zinc-800/80 bg-white dark:bg-zinc-900">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-xs font-semibold tracking-wider text-slate-400 uppercase">Failed Validations</CardTitle>
            <AlertCircle className="h-4 w-4 text-rose-500" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-slate-900 dark:text-zinc-50">12</div>
            <div className="flex items-center gap-1.5 mt-1.5">
              <span className="text-[11px] font-bold bg-rose-50 text-rose-600 dark:bg-rose-950/30 dark:text-rose-400 px-1.5 py-0.5 rounded">
                High Risk
              </span>
              <span className="text-[11px] text-slate-400 dark:text-zinc-500 font-medium">Suspect entries detected</span>
            </div>
          </CardContent>
        </Card>
        <Card className="border-none shadow-sm ring-1 ring-slate-100 dark:ring-zinc-800/80 bg-white dark:bg-zinc-900">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-xs font-semibold tracking-wider text-slate-400 uppercase">Recent Files</CardTitle>
            <UploadCloud className="h-4 w-4 text-slate-400 dark:text-zinc-500" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-slate-900 dark:text-zinc-50">8</div>
            <div className="flex items-center gap-1.5 mt-1.5">
              <span className="text-[11px] font-bold bg-emerald-50 text-emerald-700 dark:bg-emerald-950/30 dark:text-emerald-400 px-1.5 py-0.5 rounded">
                Active Uploads
              </span>
              <span className="text-[11px] text-slate-400 dark:text-zinc-500 font-medium">Imported in last 7 days</span>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 md:grid-cols-7">
        {/* Main Chart Section */}
        <Card className="md:col-span-4 border-none shadow-sm ring-1 ring-slate-100 dark:ring-zinc-800/80 bg-white dark:bg-zinc-900 overflow-hidden flex flex-col justify-between">
          <CardHeader className="border-b border-slate-50 dark:border-zinc-800/50 pb-4">
            <div className="flex items-start justify-between gap-4">
              <div>
                <CardTitle className="text-lg font-bold text-slate-900 dark:text-zinc-50">Emissions Trend Analysis</CardTitle>
                <CardDescription className="text-xs text-slate-400 dark:text-zinc-500 mt-0.5">
                  Direct & indirect operational footprint breakdowns across active calendar months.
                </CardDescription>
              </div>
              <span className="text-[10px] font-semibold bg-emerald-50 dark:bg-emerald-950/30 text-emerald-700 dark:text-emerald-400 px-2 py-0.5 rounded-full flex items-center gap-1">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
                Live Data
              </span>
            </div>
          </CardHeader>

          {showEmptyState ? (
            /* ANALYST EMPTY STATE */
            <CardContent className="py-12 flex flex-col items-center justify-center text-center space-y-4 flex-1">
              <div className="h-16 w-16 rounded-2xl bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400 flex items-center justify-center shadow-inner border border-emerald-100/50 dark:border-emerald-900/30">
                <BarChart3 size={32} />
              </div>
              <div className="space-y-1.5 max-w-[340px]">
                <h3 className="text-base font-bold text-slate-900 dark:text-zinc-50">No emissions data uploaded yet</h3>
                <p className="text-xs text-slate-400 dark:text-zinc-500 leading-relaxed">
                  Your environmental impact trends will show up here. Upload your utility bills, SAP procurements, or travel sheets to build your Scope 1, 2, and 3 insights.
                </p>
              </div>
              <Button asChild size="sm" className="bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-semibold px-4 py-2 mt-2 shadow-sm">
                <Link to="/upload" className="flex items-center gap-2">
                  <UploadCloud size={14} />
                  Upload First Dataset
                </Link>
              </Button>
            </CardContent>
          ) : (
            /* ACTIVE GRAPH STATE */
            <CardContent className="pt-6 space-y-6 flex-1 flex flex-col justify-between">
              {/* Premium monthly category trend summary blocks */}
              <div className="grid grid-cols-3 gap-2.5 sm:gap-4">
                <div className="bg-emerald-50/20 dark:bg-emerald-950/10 border border-emerald-100/20 dark:border-emerald-900/20 p-3 rounded-xl space-y-1">
                  <div className="flex items-center justify-between text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                    <span className="flex items-center gap-1">
                      <Flame size={12} className="text-emerald-800 dark:text-emerald-400" />
                      Fuel (S1)
                    </span>
                    <span className="text-emerald-600 dark:text-emerald-400 font-extrabold">↓ 4%</span>
                  </div>
                  <div className="text-lg font-bold text-slate-900 dark:text-zinc-50">1,944 <span className="text-[10px] text-slate-400 dark:text-zinc-500 font-normal">MT</span></div>
                  <div className="text-[10px] text-slate-400 dark:text-zinc-500 font-medium">Direct Fuel Usage</div>
                </div>

                <div className="bg-emerald-50/20 dark:bg-emerald-950/10 border border-emerald-100/20 dark:border-emerald-900/20 p-3 rounded-xl space-y-1">
                  <div className="flex items-center justify-between text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                    <span className="flex items-center gap-1">
                      <Zap size={12} className="text-emerald-500" />
                      Electric (S2)
                    </span>
                    <span className="text-rose-600 dark:text-rose-400 font-extrabold">↑ 8%</span>
                  </div>
                  <div className="text-lg font-bold text-slate-900 dark:text-zinc-50">3,118 <span className="text-[10px] text-slate-400 dark:text-zinc-500 font-normal">MT</span></div>
                  <div className="text-[10px] text-slate-400 dark:text-zinc-500 font-medium">Indirect Grid Power</div>
                </div>

                <div className="bg-emerald-50/20 dark:bg-emerald-950/10 border border-emerald-100/20 dark:border-emerald-900/20 p-3 rounded-xl space-y-1">
                  <div className="flex items-center justify-between text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                    <span className="flex items-center gap-1">
                      <Plane size={12} className="text-emerald-300 dark:text-emerald-500" />
                      Travel (S3)
                    </span>
                    <span className="text-slate-400 dark:text-zinc-500 font-extrabold">Stable</span>
                  </div>
                  <div className="text-lg font-bold text-slate-900 dark:text-zinc-50">15,681 <span className="text-[10px] text-slate-400 dark:text-zinc-500 font-normal">MT</span></div>
                  <div className="text-[10px] text-slate-400 dark:text-zinc-500 font-medium">Business Value Chain</div>
                </div>
              </div>

              {/* Area Chart with gradients */}
              <div className="h-[280px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
                    <defs>
                      <linearGradient id="colorScope1" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#064e3b" stopOpacity={0.4}/>
                        <stop offset="95%" stopColor="#064e3b" stopOpacity={0}/>
                      </linearGradient>
                      <linearGradient id="colorScope2" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
                        <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                      </linearGradient>
                      <linearGradient id="colorScope3" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#a7f3d0" stopOpacity={0.25}/>
                        <stop offset="95%" stopColor="#a7f3d0" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f8fafc" className="dark:stroke-zinc-800/30" vertical={false} />
                    <XAxis 
                      dataKey="name" 
                      stroke="#94a3b8" 
                      fontSize={11} 
                      tickLine={false} 
                      axisLine={false} 
                      dy={10}
                    />
                    <YAxis 
                      stroke="#94a3b8" 
                      fontSize={11} 
                      tickLine={false} 
                      axisLine={false} 
                      tickFormatter={(value) => `${value.toLocaleString()}`} 
                      dx={-5}
                    />
                    <Tooltip content={<CustomTooltip />} cursor={{ stroke: '#e2e8f0', strokeWidth: 1 }} />
                    <Area 
                      type="monotone" 
                      dataKey="scope3" 
                      stackId="1" 
                      stroke="#34d399" 
                      strokeWidth={2}
                      fillOpacity={1} 
                      fill="url(#colorScope3)" 
                    />
                    <Area 
                      type="monotone" 
                      dataKey="scope2" 
                      stackId="1" 
                      stroke="#10b981" 
                      strokeWidth={2}
                      fillOpacity={1} 
                      fill="url(#colorScope2)" 
                    />
                    <Area 
                      type="monotone" 
                      dataKey="scope1" 
                      stackId="1" 
                      stroke="#047857" 
                      strokeWidth={2}
                      fillOpacity={1} 
                      fill="url(#colorScope1)" 
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>

              {/* Insight panel */}
              <div className="bg-emerald-50/10 dark:bg-emerald-950/5 border border-emerald-100/10 dark:border-emerald-900/20 p-4 rounded-xl space-y-3">
                <h4 className="text-xs font-bold text-emerald-800 dark:text-emerald-400 flex items-center gap-1.5 uppercase tracking-wider">
                  <Sparkles size={13} />
                  ESG Analyst Operational Insights
                </h4>
                <div className="grid gap-2.5 text-xs text-slate-600 dark:text-zinc-300">
                  <div className="flex items-start gap-2">
                    <span className="h-1.5 w-1.5 rounded-full bg-emerald-700 mt-1.5 shrink-0" />
                    <p>
                      <strong className="text-slate-800 dark:text-white font-semibold">Direct Fuel Usage down 4%</strong>: Spurred by operational optimization and route consolidation across regional logistics fleets.
                    </p>
                  </div>
                  <div className="flex items-start gap-2">
                    <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 mt-1.5 shrink-0" />
                    <p>
                      <strong className="text-slate-800 dark:text-white font-semibold">Electricity emissions increased 8% this month</strong>: Driven by seasonal climate control demands at the central fabrication hub.
                    </p>
                  </div>
                  <div className="flex items-start gap-2">
                    <span className="h-1.5 w-1.5 rounded-full bg-emerald-300 mt-1.5 shrink-0" />
                    <p>
                      <strong className="text-slate-800 dark:text-white font-semibold">Travel emissions stable</strong>: Value-chain travel impact remained strictly flat YTD due to active virtual-first meeting guidelines.
                    </p>
                  </div>
                </div>
              </div>
            </CardContent>
          )}
        </Card>

        {/* Recent Activity Section */}
        <Card className="md:col-span-3 border-none shadow-sm ring-1 ring-slate-100 dark:ring-zinc-800/80 bg-white dark:bg-zinc-900 overflow-hidden flex flex-col">
          <CardHeader className="border-b border-slate-50 dark:border-zinc-800/50 pb-4">
            <CardTitle className="text-lg font-bold text-slate-900 dark:text-zinc-50">Recent Activities</CardTitle>
            <CardDescription className="text-xs text-slate-400 dark:text-zinc-500 mt-0.5">
              Live operational log of uploaded datasets and validation checks.
            </CardDescription>
          </CardHeader>
          <CardContent className="pt-6 flex-1">
            <div className="space-y-6">
              {[
                { title: "SAP Fuel Procurement (Q2)", status: "Pending Review", time: "2 hours ago", icon: FileText, color: "text-amber-500", bg: "bg-amber-100/50 dark:bg-amber-500/10" },
                { title: "Grid Utility Bills (March)", status: "Failed Validation", time: "5 hours ago", icon: AlertCircle, color: "text-rose-500", bg: "bg-rose-100/50 dark:bg-rose-500/10" },
                { title: "Corporate Travel Log (April)", status: "Approved", time: "1 day ago", icon: Activity, color: "text-emerald-500", bg: "bg-emerald-100/50 dark:bg-emerald-500/10" },
              ].map((item, i) => (
                <div key={i} className="flex items-start sm:items-center">
                  <div className={`h-9 w-9 rounded-xl flex items-center justify-center ${item.bg} mr-4 shrink-0`}>
                    <item.icon className={`h-4.5 w-4.5 ${item.color}`} />
                  </div>
                  <div className="flex-1 min-w-0 space-y-0.5">
                    <p className="text-xs font-semibold text-slate-800 dark:text-zinc-200 truncate">{item.title}</p>
                    <p className="text-[11px] text-slate-400 dark:text-zinc-400">{item.status}</p>
                  </div>
                  <div className="text-[10px] text-slate-400 dark:text-zinc-500 whitespace-nowrap ml-2">{item.time}</div>
                </div>
              ))}
            </div>

            {/* Additional operational summaries */}
            <div className="mt-8 border-t border-slate-50 dark:border-zinc-800/50 pt-6 space-y-4">
              <h5 className="text-[11px] font-bold text-slate-400 dark:text-zinc-500 uppercase tracking-wider">Compliance Status</h5>
              <div className="space-y-3">
                <div>
                  <div className="flex items-center justify-between text-xs mb-1">
                    <span className="text-slate-600 dark:text-zinc-300 font-medium">Reporting Completion</span>
                    <span className="text-slate-900 dark:text-white font-bold">82%</span>
                  </div>
                  <div className="w-full bg-slate-100 dark:bg-zinc-800 h-1.5 rounded-full overflow-hidden">
                    <div className="bg-emerald-600 h-1.5 rounded-full" style={{ width: "82%" }} />
                  </div>
                </div>
                <div>
                  <div className="flex items-center justify-between text-xs mb-1">
                    <span className="text-slate-600 dark:text-zinc-300 font-medium">Audit Verification Rate</span>
                    <span className="text-slate-900 dark:text-white font-bold">94%</span>
                  </div>
                  <div className="w-full bg-slate-100 dark:bg-zinc-800 h-1.5 rounded-full overflow-hidden">
                    <div className="bg-emerald-500 h-1.5 rounded-full" style={{ width: "94%" }} />
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
