import { Search, Bell } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';

export function Header() {
  return (
    <header className="flex h-16 shrink-0 items-center justify-between border-b px-8 bg-white dark:bg-zinc-950 dark:border-zinc-800">
      <div className="flex flex-1 items-center gap-4">
        <div className="relative w-96">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-slate-500 dark:text-zinc-400" />
          <Input
            type="search"
            placeholder="Search records, facilities, or tasks..."
            className="w-full bg-slate-50 pl-9 border-none shadow-none focus-visible:ring-1 dark:bg-zinc-900"
          />
        </div>
      </div>
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" className="relative">
          <Bell className="h-5 w-5 text-slate-600 dark:text-zinc-400" />
          <span className="absolute top-2 right-2 h-2 w-2 rounded-full bg-rose-500" />
        </Button>
      </div>
    </header>
  );
}
