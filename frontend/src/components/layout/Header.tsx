'use client'

import * as React from 'react'
import { cn } from '@/lib/utils'
import { Bell, Search, Moon, Sun, Menu } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuTrigger } from '@/components/ui/dropdown-menu'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { Separator } from '@/components/ui/separator'
import { useAuthStore } from '@/store/authStore'
import { useTheme } from '@/context/ThemeContext'

export function Header() {
  const { user } = useAuthStore()
  const { theme, setTheme, resolvedTheme } = useTheme()
  const [searchQuery, setSearchQuery] = React.useState('')

  return (
    <header className='sticky top-0 z-30 flex h-16 shrink-0 items-center gap-4 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 px-4 lg:px-6'>
      <div className='h-10 w-px bg-border lg:hidden' />
      
      <div className='flex flex-1 gap-4'>
        <div className='relative flex-1 max-w-md hidden md:block'>
          <Search className='absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground' />
          <input
            type='search'
            placeholder='Search...'
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className='h-10 w-full rounded-md border border-input bg-background pl-10 pr-4 text-sm focus:outline-none focus:ring-2 focus:ring-ring transition-all'
            aria-label='Search'
          />
        </div>
      </div>

      <div className='flex items-center gap-2'>
        <Button
          variant='ghost'
          size='icon'
          onClick={() => setTheme(resolvedTheme === 'dark' ? 'light' : 'dark')}
          aria-label='Toggle theme'
          className='relative overflow-hidden'
        >
          <Sun className='h-5 w-5 transition-all duration-300' style={{ transform: theme === 'dark' ? 'rotate(-90deg) scale(0)' : 'rotate(0deg) scale(1)' }} />
          <Moon className='absolute h-5 w-5 transition-all duration-300' style={{ transform: theme === 'dark' ? 'rotate(0deg) scale(1)' : 'rotate(90deg) scale(0)' }} />
        </Button>

        <Button variant='ghost' size='icon' aria-label='Notifications' className='relative'>
          <Bell className='h-5 w-5' />
          <span className='absolute -top-1 -right-1 flex h-5 w-5 items-center justify-center rounded-full bg-destructive text-[10px] font-medium text-white'>
            3
          </span>
        </Button>

        {user && (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant='ghost' className='relative h-10 w-10 rounded-full hover:bg-accent transition-colors'>
                <Avatar className='h-10 w-10'>
                  <AvatarImage src={user.avatar_url || undefined} alt={user.full_name || user.email} />
                  <AvatarFallback className='text-xs'>{user.full_name?.[0] || user.email[0].toUpperCase()}</AvatarFallback>
                </Avatar>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align='end' className='w-56 animate-scale-in'>
              <div className='px-2 py-1'>
                <p className='text-sm font-medium'>{user.full_name || user.email}</p>
                <p className='text-xs text-muted-foreground truncate'>{user.email}</p>
              </div>
              <DropdownMenuSeparator />
              <DropdownMenuItem>Profile</DropdownMenuItem>
              <DropdownMenuItem>Settings</DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem className='text-destructive focus:text-destructive'>
                Log out
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        )}
      </div>
    </header>
  )
}
