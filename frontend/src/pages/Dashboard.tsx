'use client'

import * as React from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { api } from '@/api/client'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { 
  Database, 
  FileText, 
  MessageSquare, 
  TrendingUp, 
  Plus,
  ArrowRight,
  Clock,
  CheckCircle,
  AlertCircle,
  XCircle
} from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'

interface DashboardStats {
  org_id: string
  organization_name: string
  total_datasets: number
  total_reports: number
  total_forecasts: number
  recent_activity: Array<{
    id: string
    type: 'dataset' | 'report' | 'forecast'
    title: string
    created_at: string
    status: string
  }>
  role: string
}

interface Dataset {
  id: string
  name: string
  source_type: string
  row_count: number
  status: string
  created_at: string
}

const StatCardSkeleton = () => (
  <Card className='animate-fade-in'>
    <CardHeader className='flex flex-row items-center justify-between space-y-0 pb-2'>
      <Skeleton className='h-4 w-24' />
      <Skeleton className='h-4 w-4 rounded' />
    </CardHeader>
    <CardContent>
      <Skeleton className='h-8 w-16' />
      <Skeleton className='h-3 w-32' />
    </CardContent>
  </Card>
)

const ActivityItemSkeleton = () => (
  <div className='animate-pulse flex items-center gap-4 p-3'>
    <Skeleton className='h-10 w-10 rounded-lg' />
    <div className='flex-1 min-w-0'>
      <Skeleton className='h-4 w-3/4 rounded mb-1' />
      <Skeleton className='h-3 w-1/2 rounded' />
    </div>
    <Skeleton className='h-5 w-20 rounded' />
  </div>
)

const DatasetItemSkeleton = () => (
  <div className='animate-pulse flex items-center gap-3 p-2'>
    <Skeleton className='h-10 w-10 rounded-lg' />
    <div className='flex-1 min-w-0'>
      <Skeleton className='h-4 w-3/4 rounded mb-1' />
      <Skeleton className='h-3 w-1/2 rounded' />
    </div>
    <Skeleton className='h-5 w-20 rounded' />
  </div>
)

export function DashboardPage() {
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['dashboard'],
    queryFn: () => api.get<DashboardStats>('/dashboard'),
  })

  const { data: datasets, isLoading: datasetsLoading } = useQuery({
    queryKey: ['datasets'],
    queryFn: () => api.get<Dataset[]>('/datasets'),
  })

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'ready':
      case 'completed':
        return <Badge variant='default'><CheckCircle className='mr-1 h-3 w-3' /> {status}</Badge>
      case 'processing':
      case 'generating':
      case 'queued':
        return <Badge variant='secondary'><Clock className='mr-1 h-3 w-3' /> {status}</Badge>
      case 'error':
      case 'failed':
        return <Badge variant='destructive'><XCircle className='mr-1 h-3 w-3' /> {status}</Badge>
      default:
        return <Badge variant='outline'>{status}</Badge>
    }
  }

  const getActivityIcon = (type: string) => {
    switch (type) {
      case 'dataset':
        return <Database className='h-4 w-4 text-blue-500' />
      case 'report':
        return <FileText className='h-4 w-4 text-green-500' />
      case 'forecast':
        return <TrendingUp className='h-4 w-4 text-purple-500' />
      default:
        return <Database className='h-4 w-4' />
    }
  }

  if (statsLoading) {
    return (
      <div className='space-y-6 animate-fade-in'>
        <div className='flex items-center justify-between'>
          <div>
            <Skeleton className='h-8 w-48' />
            <Skeleton className='h-4 w-64 mt-2' />
          </div>
          <div className='flex gap-2'>
            <Skeleton className='h-10 w-32' />
            <Skeleton className='h-10 w-32' />
          </div>
        </div>

        <div className='grid gap-4 md:grid-cols-2 lg:grid-cols-4'>
          {[1, 2, 3, 4].map((i) => (
            <StatCardSkeleton key={i} style={{ animationDelay: \\ms\ }} />
          ))}
        </div>

        <div className='grid gap-4 md:grid-cols-2 lg:grid-cols-7'>
          <Card className='col-span-4'>
            <CardHeader>
              <Skeleton className='h-6 w-32' />
            </CardHeader>
            <CardContent>
              <div className='space-y-4'>
                {[1, 2, 3, 4, 5].map((i) => (
                  <ActivityItemSkeleton key={i} style={{ animationDelay: \\ms\ }} />
                ))}
              </div>
            </CardContent>
          </Card>

          <Card className='col-span-3'>
            <CardHeader className='flex flex-row items-center justify-between'>
              <Skeleton className='h-6 w-32' />
              <Skeleton className='h-8 w-24' />
            </CardHeader>
            <CardContent>
              <div className='space-y-3'>
                {[1, 2, 3].map((i) => (
                  <DatasetItemSkeleton key={i} style={{ animationDelay: \\ms\ }} />
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    )
  }

  return (
    <div className='space-y-6 animate-fade-in'>
      <div className='flex items-center justify-between'>
        <div>
          <h1 className='text-3xl font-bold tracking-tight'>{stats?.organization_name || 'Dashboard'}</h1>
          <p className='text-muted-foreground'>Overview of your organization's data and reports</p>
        </div>
        <div className='flex gap-2'>
          <Button asChild>
            <Link to='/datasets'><Plus className='mr-2 h-4 w-4' />Add Dataset</Link>
          </Button>
          <Button variant='outline' asChild>
            <Link to='/reports/generate'><FileText className='mr-2 h-4 w-4' />Generate Report</Link>
          </Button>
        </div>
      </div>

      <div className='grid gap-4 md:grid-cols-2 lg:grid-cols-4'>
        <Card className='hover-lift'>
          <CardHeader className='flex flex-row items-center justify-between space-y-0 pb-2'>
            <CardTitle className='text-sm font-medium'>Datasets</CardTitle>
            <Database className='h-4 w-4 text-muted-foreground' />
          </CardHeader>
          <CardContent>
            <div className='text-2xl font-bold'>{stats?.total_datasets || 0}</div>
            <p className='text-xs text-muted-foreground'>Total datasets uploaded</p>
          </CardContent>
        </Card>
        <Card className='hover-lift'>
          <CardHeader className='flex flex-row items-center justify-between space-y-0 pb-2'>
            <CardTitle className='text-sm font-medium'>Reports</CardTitle>
            <FileText className='h-4 w-4 text-muted-foreground' />
          </CardHeader>
          <CardContent>
            <div className='text-2xl font-bold'>{stats?.total_reports || 0}</div>
            <p className='text-xs text-muted-foreground'>Total reports generated</p>
          </CardContent>
        </Card>
        <Card className='hover-lift'>
          <CardHeader className='flex flex-row items-center justify-between space-y-0 pb-2'>
            <CardTitle className='text-sm font-medium'>Forecasts</CardTitle>
            <TrendingUp className='h-4 w-4 text-muted-foreground' />
          </CardHeader>
          <CardContent>
            <div className='text-2xl font-bold'>{stats?.total_forecasts || 0}</div>
            <p className='text-xs text-muted-foreground'>Total forecasts run</p>
          </CardContent>
        </Card>
        <Card className='hover-lift'>
          <CardHeader className='flex flex-row items-center justify-between space-y-0 pb-2'>
            <CardTitle className='text-sm font-medium'>Your Role</CardTitle>
            <Badge variant='outline'>{stats?.role || 'member'}</Badge>
          </CardHeader>
          <CardContent>
            <div className='text-2xl font-bold capitalize'>{stats?.role || 'member'}</div>
            <p className='text-xs text-muted-foreground'>Organization permission level</p>
          </CardContent>
        </Card>
      </div>

      <div className='grid gap-4 md:grid-cols-2 lg:grid-cols-7'>
        <Card className='col-span-4 hover-lift'>
          <CardHeader>
            <CardTitle>Recent Activity</CardTitle>
          </CardHeader>
          <CardContent>
            <div className='space-y-4'>
              {stats?.recent_activity?.slice(0, 5).map((activity, index) => (
                <Link 
                  key={activity.id} 
                  to={\/\s/\\} 
                  className='flex items-center gap-4 p-3 hover:bg-accent rounded-lg transition-colors animate-fade-in'
                  style={{ animationDelay: \\ms\ }}
                >
                  <div className='flex h-10 w-10 items-center justify-center rounded-lg bg-muted'>{getActivityIcon(activity.type)}</div>
                  <div className='flex-1 min-w-0'>
                    <p className='text-sm font-medium truncate'>{activity.title}</p>
                    <p className='text-xs text-muted-foreground'>{formatDistanceToNow(new Date(activity.created_at), { addSuffix: true })}</p>
                  </div>
                  {getStatusBadge(activity.status)}
                  <ArrowRight className='h-4 w-4 text-muted-foreground' />
                </Link>
              ))}
              {(stats?.recent_activity?.length || 0) === 0 && (
                <div className='text-center py-8 text-muted-foreground'>
                  <p>No recent activity</p>
                  <Button asChild variant='ghost' className='mt-2'>
                    <Link to='/datasets'><Plus className='mr-2 h-4 w-4' />Upload your first dataset</Link>
                  </Button>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        <Card className='col-span-3 hover-lift'>
          <CardHeader className='flex flex-row items-center justify-between'>
            <CardTitle>Recent Datasets</CardTitle>
            <Button asChild variant='ghost' size='sm'>
              <Link to='/datasets'>View all <ArrowRight className='ml-1 h-3 w-3' /></Link>
            </Button>
          </CardHeader>
          <CardContent>
            <div className='space-y-3'>
              {datasetsLoading ? (
                [...Array(3)].map((_, i) => (
                  <DatasetItemSkeleton key={i} style={{ animationDelay: \\ms\ }} />
                ))
              ) : datasets?.slice(0, 5).map((dataset, index) => (
                <Link 
                  key={dataset.id} 
                  to={\/datasets/\\} 
                  className='flex items-center gap-3 p-2 hover:bg-accent rounded-lg transition-colors animate-fade-in'
                  style={{ animationDelay: \\ms\ }}
                >
                  <div className='flex h-10 w-10 items-center justify-center rounded-lg bg-muted'>
                    <Database className='h-5 w-5 text-muted-foreground' />
                  </div>
                  <div className='flex-1 min-w-0'>
                    <p className='text-sm font-medium truncate'>{dataset.name}</p>
                    <p className='text-xs text-muted-foreground'>{dataset.row_count.toLocaleString()} rows · {dataset.source_type.toUpperCase()}</p>
                  </div>
                  {getStatusBadge(dataset.status)}
                </Link>
              ))}
              {(datasets?.length || 0) === 0 && !datasetsLoading && (
                <div className='text-center py-6 text-muted-foreground'>
                  <p>No datasets yet</p>
                  <Button asChild variant='ghost' className='mt-2'>
                    <Link to='/datasets'><Plus className='mr-2 h-4 w-4' />Upload a dataset</Link>
                  </Button>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
