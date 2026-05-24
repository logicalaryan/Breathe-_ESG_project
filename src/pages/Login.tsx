import { useEffect, useState } from "react"
import { useNavigate } from "react-router-dom"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { LayoutDashboard } from "lucide-react"

export function Login() {
  const navigate = useNavigate()
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")

  useEffect(() => {
    if (localStorage.getItem("isAuthenticated") === "true") {
      navigate("/", { replace: true })
    }
  }, [navigate])

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault()
    localStorage.setItem("isAuthenticated", "true")
    localStorage.setItem("userEmail", email || "sarah@acmecorp.com")

    // Dynamically derive a professional formatted name from the email
    const emailPrefix = (email || "sarah@acmecorp.com").split('@')[0];
    const nameParts = emailPrefix.split(/[._\-+]/);
    const formattedName = nameParts
      .map(part => part.charAt(0).toUpperCase() + part.slice(1))
      .join(' ') + " Analyst";

    localStorage.setItem("userName", formattedName)
    navigate("/")
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 dark:bg-zinc-950 p-4">
      <div className="w-full max-w-[400px] space-y-6">
        <div className="flex flex-col items-center text-center space-y-2">
          <div className="h-12 w-12 rounded-xl bg-emerald-600 flex items-center justify-center text-white mb-4 shadow-lg shadow-emerald-500/20">
            <LayoutDashboard size={24} />
          </div>
          <h1 className="text-2xl font-semibold tracking-tight text-slate-900 dark:text-zinc-50">
            Welcome to Breath ESG
          </h1>
          <p className="text-sm text-slate-500 dark:text-zinc-400">
            Enter your credentials to access your dashboard
          </p>
        </div>

        <form onSubmit={handleLogin} className="bg-white dark:bg-zinc-900 p-8 rounded-2xl shadow-sm border dark:border-zinc-800 space-y-6">
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email">Work Email</Label>
              <Input
                id="email"
                type="email"
                required
                placeholder="sarah@acmecorp.com"
                value={email}
                onChange={e => setEmail(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="password">Password</Label>
                <a href="#" className="text-xs text-emerald-600 hover:text-emerald-500 font-medium">
                  Forgot password?
                </a>
              </div>
              <Input
                id="password"
                type="password"
                required
                placeholder="••••••••"
                value={password}
                onChange={e => setPassword(e.target.value)}
              />
            </div>
          </div>
          <Button type="submit" className="w-full bg-emerald-600 hover:bg-emerald-700 text-white" size="lg">
            Sign In
          </Button>
          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <span className="w-full border-t dark:border-zinc-800" />
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-white dark:bg-zinc-900 px-2 text-slate-500">
                Or continue with
              </span>
            </div>
          </div>
          <Button
            type="button"
            variant="outline"
            className="w-full"
            size="lg"
            onClick={handleLogin}
          >
            Single Sign-On (SSO)
          </Button>
        </form>
      </div>
    </div>
  )
}
