import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"

export function Settings() {
  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h2 className="text-2xl font-semibold tracking-tight text-slate-900 dark:text-zinc-50">Settings</h2>
        <p className="text-sm text-slate-500 dark:text-zinc-400">Manage your account preferences and application settings.</p>
      </div>

      <Tabs defaultValue="general" className="space-y-4">
        <TabsList>
          <TabsTrigger value="general">General</TabsTrigger>
          <TabsTrigger value="notifications">Notifications</TabsTrigger>
          <TabsTrigger value="security">Security</TabsTrigger>
        </TabsList>
        <TabsContent value="general" className="space-y-4">
          <Card className="shadow-sm border-none ring-1 ring-slate-900/5 dark:ring-white/10">
            <CardHeader>
              <CardTitle>Profile</CardTitle>
              <CardDescription>Update your personal information.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="firstName">First Name</Label>
                  <Input id="firstName" defaultValue="Sarah" />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="lastName">Last Name</Label>
                  <Input id="lastName" defaultValue="Analyst" />
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input id="email" defaultValue="sarah@acmecorp.com" disabled />
              </div>
              <Button className="bg-emerald-600 hover:bg-emerald-700 text-white">Save Changes</Button>
            </CardContent>
          </Card>
          <Card className="shadow-sm border-none ring-1 ring-slate-900/5 dark:ring-white/10">
            <CardHeader>
              <CardTitle>Preferences</CardTitle>
              <CardDescription>Manage application appearance and defaults.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label>Theme</Label>
                <div className="flex items-center gap-2">
                  <Button variant="outline" className="flex-1">Light</Button>
                  <Button variant="outline" className="flex-1 bg-slate-100 dark:bg-zinc-800">Dark</Button>
                  <Button variant="outline" className="flex-1">System</Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
        <TabsContent value="notifications">
          <Card className="shadow-sm border-none ring-1 ring-slate-900/5 dark:ring-white/10">
            <CardHeader>
              <CardTitle>Notification Preferences</CardTitle>
              <CardDescription>Choose what you want to be notified about.</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-slate-500">Coming soon.</p>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
