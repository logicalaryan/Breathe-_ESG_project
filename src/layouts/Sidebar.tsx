import { NavLink } from 'react-router-dom';
import { LayoutDashboard, UploadCloud, CheckSquare, History, Settings } from 'lucide-react';
import { cn } from '@/lib/utils';

const navigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'Upload Data', href: '/upload', icon: UploadCloud },
  { name: 'Review Queue', href: '/review', icon: CheckSquare },
  { name: 'Audit History', href: '/audit', icon: History },
  { name: 'Settings', href: '/settings', icon: Settings },
];

export function Sidebar() {
  return (
    <div className="flex flex-col w-64 bg-slate-50 border-r min-h-screen dark:bg-zinc-950 dark:border-zinc-800">
      <div className="flex h-16 shrink-0 items-center px-6 border-b dark:border-zinc-800">
        <div className="flex items-center gap-2 font-semibold tracking-tight text-lg text-emerald-700 dark:text-emerald-500">
          <div className="h-6 w-6 rounded-md bg-emerald-600 dark:bg-emerald-500 text-white flex items-center justify-center">
             <LayoutDashboard size={14} />
          </div>
          Breath ESG
        </div>
      </div>
      <nav className="flex-1 px-4 py-4 space-y-1">
        {navigation.map((item) => (
          <NavLink
            key={item.name}
            to={item.href}
            className={({ isActive }) =>
              cn(
                'group flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors',
                isActive
                  ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-500'
                  : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900 dark:text-zinc-400 dark:hover:bg-zinc-900 dark:hover:text-zinc-50'
              )
            }
          >
            <item.icon
              className="mr-3 h-5 w-5 shrink-0 opacity-75"
              aria-hidden="true"
            />
            {item.name}
          </NavLink>
        ))}
      </nav>
      <div className="p-4 border-t dark:border-zinc-800">
        <div className="flex items-center gap-3">
          <div className="h-8 w-8 rounded-full bg-slate-200 dark:bg-zinc-800 flex items-center justify-center text-xs font-medium">
            SA
          </div>
          <div className="flex flex-col">
            <span className="text-sm font-medium text-slate-900 dark:text-zinc-50">Sarah Analyst</span>
            <span className="text-xs text-slate-500 dark:text-zinc-400">sarah@acmecorp.com</span>
          </div>
        </div>
      </div>
    </div>
  );
}
