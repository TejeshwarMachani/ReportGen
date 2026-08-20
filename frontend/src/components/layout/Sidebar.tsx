'use client'

import * as React from 'react'
import { cn } from '@/lib/utils'
import { 
  LayoutDashboard, 
  Database, 
  FileText, 
  MessageSquare, 
  TrendingUp, 
  Users, 
  Settings,
  LogOut,
  Menu,
  X,
  ChevronLeft
} from 'lucide-react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuTrigger } from '@/components/ui/dropdown-menu'
import { Separator } from '@/components/ui/separator'
import { useAuthStore } from '@/store/authStore'

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { name: 'Data Sources', href: '/datasets', icon: Database },
  { name: 'Reports', href: '/reports', icon: FileText },
  { name: 'Chat', href: '/chat', icon: MessageSquare },
  { name: 'Forecasts', href: '/forecasts', icon: TrendingUp },
  { name: 'Team', href: '/team', icon: Users },
  { name: 'Settings', href: '/settings', icon: Settings },
]

export function Sidebar() {
  const location = useLocation()
  const navigate = useNavigate()
  const { user, logout } = useAuthStore()
  const [collapsed, setCollapsed] = React.useState(false)
  const [mobileOpen, setMobileOpen] = React.useState(false)

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <>
      <button
        className='lg:hidden fixed top-4 left-4 z-50 bg-background border rounded-lg p-2 transition-transform hover:rotate-90'
        onClick={() => setMobileOpen(!mobileOpen)}
        aria-label='Toggle menu'
      >
        {mobileOpen ? <X className='h-6 w-6' /> : <Menu className='h-6 w-6' />}
      </button>

      <aside
        className={cn(
          'fixed inset-y-0 left-0 z-40 flex h-full w-64 flex-col bg-card border-r sidebar-transition lg:translate-x-0',
          collapsed && 'w-16',
          mobileOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        )}
        aria-label='Sidebar'
      >
        <div className='flex h-16 shrink-0 items-center justify-between border-b px-4'>
          <Link to='/dashboard' className='flex items-center space-x-2'>
            <div className='flex h-8 w-8 items-center justify-center rounded-lg bg-primary'>
              <LayoutDashboard className='h-5 w-5 text-primary-foreground' />
            </div>
            {!collapsed && <span className='font-semibold text-lg animate-fade-in'>ReportGen</span>}
          </Link>
          <button
            className='hidden lg:flex h-8 w-8 items-center justify-center rounded-lg hover:bg-accent transition-colors'
            onClick={() => setCollapsed(!collapsed)}
            aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            {collapsed ? <ChevronLeft className='h-4 w-4 rotate-180' /> : <ChevronLeft className='h-4 w-4' />}
          </button>
        </div>

        <nav className='flex-1 space-y-1 p-4 overflow-y-auto'>
          {navigation.map((item, index) => {
            const isActive = location.pathname === item.href || location.pathname.startsWith(item.href + '/')
            return (
              <Link
                key={item.name}
                to={item.href}
                className={cn(
                  'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-primary text-primary-foreground shadow-sm'
                    : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground',
                  collapsed && 'justify-center'
                )}
                title={collapsed ? item.name : undefined}
                onClick={() => setMobileOpen(false)}
                style={{ animationDelay: `${index * 50}ms` }}
              >
                <item.icon className='h-5 w-5 flex-shrink-0 transition-transform hover:scale-110' aria-hidden='true' />
                {!collapsed && <span className='animate-fade-in'>{item.name}</span>}
              </Link>
            )
          })}
        </nav>

        <div className='border-t p-4'>
          {!collapsed && user && (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <button className='flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm hover:bg-accent transition-colors'>
                  <Avatar className='h-8 w-8'>
                    <AvatarImage src={user.avatar_url || undefined} alt={user.full_name || user.email} />
                    <AvatarFallback>{user.full_name?.[0] || user.email[0].toUpperCase()}</AvatarFallback>
                  </Avatar>
                  <div className='flex-1 text-left truncate'>
                    <p className='font-medium truncate'>{user.full_name || user.email}</p>
                    <p className='text-xs text-muted-foreground truncate'>{user.email}</p>
                  </div>
                </button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align='end' className='w-48 animate-scale-in'>
                <DropdownMenuItem onClick={handleLogout}>
                  <LogOut className='mr-2 h-4 w-4' />
                  Log out
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          )}
          {collapsed && user && (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Avatar className='mx-auto h-8 w-8'>
                  <AvatarImage src={user.avatar_url || undefined} alt={user.full_name || user.email} />
                  <AvatarFallback>{user.full_name?.[0] || user.email[0].toUpperCase()}</AvatarFallback>
                </Avatar>
              </DropdownMenuTrigger>
              <DropdownMenuContent align='end' className='w-48 animate-scale-in'>
                <DropdownMenuItem onClick={handleLogout}>
                  <LogOut className='mr-2 h-4 w-4' />
                  Log out
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          )}
        </div>
      </aside>

      {mobileOpen && (
        <div
          className='fixed inset-0 z-30 bg-black/50 lg:hidden animate-fade-in'
          onClick={() => setMobileOpen(false)}
          aria-hidden='true'
        />
      )}
    </>
  )
}
