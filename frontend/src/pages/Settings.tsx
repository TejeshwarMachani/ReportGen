'use client'

import * as React from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/api/client'
import { toast } from 'react-hot-toast'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Separator } from '@/components/ui/separator'
import { useAuthStore, type User as AuthUser } from '@/store/authStore'
import {
  User,
  Settings,
  Shield,
  Database,
  Bell,
  Palette,
  Loader2,
  Save,
  Check,
  Sun,
  Moon,
  Monitor
} from 'lucide-react'
import { useTheme } from '@/context/ThemeContext'

interface Organization {
  id: string
  name: string
  plan: string
  slug: string
}

export function SettingsPage() {
  const { user, setUser } = useAuthStore()
  const { theme, setTheme, resolvedTheme } = useTheme()
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = React.useState('profile')
  const [isSaving, setIsSaving] = React.useState(false)
  
  // Profile form state
  const [fullName, setFullName] = React.useState(user?.full_name || '')
  const [email, setEmail] = React.useState(user?.email || '')
  
  // Organization form state
  const [orgName, setOrgName] = React.useState('')
  const [orgPlan, setOrgPlan] = React.useState('')

  const { data: org } = useQuery({
    queryKey: ['organization'],
    queryFn: () => api.get<Organization>('/orgs/me'),
  })

  React.useEffect(() => {
    if (org) {
      setOrgName(org.name)
      setOrgPlan(org.plan)
    }
  }, [org])

  const updateProfileMutation = useMutation({
    mutationFn: (data: { full_name: string; email: string }) =>
      api.patch<AuthUser>('/users/me', data),
    onSuccess: (data) => {
      setUser({ ...user!, ...data })
      toast.success('Profile updated')
      setIsSaving(false)
    },
    onError: (error: unknown) => {
      const message = error instanceof Error ? error.message : 'Failed to update profile'
      toast.error(message)
      setIsSaving(false)
    },
  })

  const updateOrgMutation = useMutation({
    mutationFn: (data: { name: string }) => 
      api.patch('/orgs/me', data),
    onSuccess: () => {
      toast.success('Organization updated')
      setIsSaving(false)
    },
    onError: (error: unknown) => {
      const message = error instanceof Error ? error.message : 'Failed to update organization'
      toast.error(message)
      setIsSaving(false)
    },
  })

  const handleProfileSave = () => {
    setIsSaving(true)
    updateProfileMutation.mutate({ full_name: fullName, email })
  }

  const handleOrgSave = () => {
    setIsSaving(true)
    updateOrgMutation.mutate({ name: orgName })
  }

  const themeOptions = [
    { id: 'light', label: 'Light', icon: Sun },
    { id: 'dark', label: 'Dark', icon: Moon },
    { id: 'system', label: 'System', icon: Monitor },
  ]

  return (
    <div className='space-y-6 max-w-4xl animate-fade-in'>
      <div>
        <h1 className='text-3xl font-bold tracking-tight flex items-center gap-2'>
          <Settings className='h-8 w-8 text-primary' />
          Settings
        </h1>
        <p className='text-muted-foreground'>Manage your account and organization settings</p>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className='space-y-4'>
        <TabsList className='grid w-full grid-cols-4 animate-fade-in'>
          <TabsTrigger value='profile'>
            <User className='mr-2 h-4 w-4' />Profile
          </TabsTrigger>
          <TabsTrigger value='organization'>
            <Shield className='mr-2 h-4 w-4' />Organization
          </TabsTrigger>
          <TabsTrigger value='notifications'>
            <Bell className='mr-2 h-4 w-4' />Notifications
          </TabsTrigger>
          <TabsTrigger value='appearance'>
            <Palette className='mr-2 h-4 w-4' />Appearance
          </TabsTrigger>
        </TabsList>

        <TabsContent value='profile' className='animate-fade-in'>
          <Card className='hover-lift'>
            <CardHeader>
              <CardTitle>Profile Information</CardTitle>
              <CardDescription>Update your personal information</CardDescription>
            </CardHeader>
            <CardContent className='space-y-4'>
              <div className='space-y-2'>
                <Label htmlFor='full-name'>Full Name</Label>
                <Input
                  id='full-name'
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder='Enter your full name'
                />
              </div>
              <div className='space-y-2'>
                <Label htmlFor='email'>Email Address</Label>
                <Input
                  id='email'
                  type='email'
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder='Enter your email'
                />
              </div>
              <div className='space-y-2'>
                <Label>Role</Label>
                <Input value={user?.role || 'member'} disabled />
                <p className='text-sm text-muted-foreground'>Contact an admin to change your role</p>
              </div>
              <div className='flex justify-end'>
                <Button onClick={handleProfileSave} disabled={isSaving} className='hover:scale-105 transition-transform'>
                  {isSaving ? <Loader2 className='mr-2 h-4 w-4 animate-spin' /> : <> <Save className='mr-2 h-4 w-4' />Save Changes</> }
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value='organization' className='animate-fade-in'>
          <Card className='hover-lift'>
            <CardHeader>
              <CardTitle>Organization Details</CardTitle>
              <CardDescription>Manage your organization settings</CardDescription>
            </CardHeader>
            <CardContent className='space-y-4'>
              <div className='space-y-2'>
                <Label htmlFor='org-name'>Organization Name</Label>
                <Input
                  id='org-name'
                  value={orgName}
                  onChange={(e) => setOrgName(e.target.value)}
                  placeholder='Enter organization name'
                />
              </div>
              <div className='space-y-2'>
                <Label>Current Plan</Label>
                <div className='flex items-center gap-2'>
                  <Badge variant='outline'>{orgPlan || 'Free'}</Badge>
                  <p className='text-sm text-muted-foreground'>Upgrade your plan to unlock more features</p>
                </div>
              </div>
              <div className='space-y-2'>
                <Label>Organization Slug</Label>
                <Input value={org?.slug || 'your-org'} disabled />
                <p className='text-sm text-muted-foreground'>This is used in your organization URL</p>
              </div>
              <div className='flex justify-end'>
                <Button onClick={handleOrgSave} disabled={isSaving} className='hover:scale-105 transition-transform'>
                  {isSaving ? <Loader2 className='mr-2 h-4 w-4 animate-spin' /> : <> <Save className='mr-2 h-4 w-4' />Save Changes</> }
                </Button>
              </div>
            </CardContent>
          </Card>

          <Card className='mt-6 hover-lift'>
            <CardHeader>
              <CardTitle>Billing & Subscription</CardTitle>
              <CardDescription>Manage your subscription and payment methods</CardDescription>
            </CardHeader>
            <CardContent>
              <div className='text-center py-8'>
                <p className='text-muted-foreground'>Billing integration coming soon</p>
                <Button variant='outline' className='mt-4'>Upgrade Plan</Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value='notifications' className='animate-fade-in'>
          <Card className='hover-lift'>
            <CardHeader>
              <CardTitle>Notification Preferences</CardTitle>
              <CardDescription>Configure how you receive notifications</CardDescription>
            </CardHeader>
            <CardContent className='space-y-6'>
              <div className='space-y-4'>
                <h4 className='font-medium'>Email Notifications</h4>
                <div className='space-y-3'>
                  {[
                    { id: 'report_ready', label: 'Report generation complete', desc: 'Get notified when your reports are ready' },
                    { id: 'forecast_ready', label: 'Forecast complete', desc: 'Get notified when forecasts finish' },
                    { id: 'team_invites', label: 'Team invitations', desc: 'Get notified when invited to organizations' },
                    { id: 'weekly_digest', label: 'Weekly digest', desc: 'Receive a weekly summary of your organization activity' },
                  ].map((item) => (
                    <div key={item.id} className='flex items-center justify-between animate-fade-in'>
                      <div>
                        <p className='font-medium'>{item.label}</p>
                        <p className='text-sm text-muted-foreground'>{item.desc}</p>
                      </div>
                      <label className='relative inline-flex items-center cursor-pointer'>
                        <input type='checkbox' defaultChecked className='sr-only peer' />
                        <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
                      </label>
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value='appearance' className='animate-fade-in'>
          <Card className='hover-lift'>
            <CardHeader>
              <CardTitle>Appearance</CardTitle>
              <CardDescription>Customize how ReportGen looks on your device</CardDescription>
            </CardHeader>
            <CardContent className='space-y-6'>
              <div className='space-y-4'>
                <h4 className='font-medium'>Theme</h4>
                <div className='grid grid-cols-3 gap-4'>
                  {themeOptions.map((t) => (
                    <button
                      key={t.id}
                      onClick={() => setTheme(t.id as 'light' | 'dark' | 'system')}
                      className={`relative p-4 border rounded-lg ${theme === t.id ? 'border-primary bg-accent' : 'hover:border-primary'} transition-colors`}
                    >
                      <div className='text-3xl mb-2'>
                        <t.icon className='h-8 w-8' />
                      </div>
                      <p className='font-medium'>{t.label}</p>
                      {theme === t.id && (
                        <Check className='absolute top-2 right-2 h-5 w-5 text-primary' />
                      )}
                      <input type='radio' name='theme' value={t.id} className='sr-only' checked={theme === t.id} />
                    </button>
                  ))}
                </div>
              </div>
              <Separator />
              <div className='space-y-4'>
                <h4 className='font-medium'>Current Theme: <span className='font-normal capitalize'>{resolvedTheme}</span></h4>
                <p className='text-sm text-muted-foreground'>
                  System preference: {typeof window !== 'undefined' && window.matchMedia('(prefers-color-scheme: dark)').matches ? 'Dark' : 'Light'}
                </p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
