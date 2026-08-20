'use client'

import * as React from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { api } from '@/api/client'
import { toast } from 'react-hot-toast'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Skeleton } from '@/components/ui/skeleton'
import { 
  ArrowLeft, 
  Download, 
  FileText, 
  BarChart3,
  Loader2,
  CheckCircle,
  XCircle,
  Clock,
  Database
} from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import {
  ChartContainer,
  createChartConfig,
} from '@/components/ui/chart'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, LineChart, Line, AreaChart, Area } from 'recharts'

interface Report {
  id: string
  title: string
  dataset_id: string
  report_type: string
  status: string
  narrative_text?: string | null
  computed_stats_json?: Record<string, unknown> | null
  charts_json?: unknown[] | null
  created_at: string
  generated_at?: string | null
  export_format?: string | null
}

const StatCardSkeleton = () => (
  <Card className='animate-pulse'>
    <CardContent className='pt-6'>
      <Skeleton className='h-3 w-1/2' />
      <Skeleton className='h-8 w-1/4 mt-2' />
    </CardContent>
  </Card>
)

const ChartSkeleton = () => (
  <Card className='animate-pulse'>
    <CardContent className='pt-6 h-[300px]'>
      <Skeleton className='h-full w-full rounded' />
    </CardContent>
  </Card>
)

const NarrativeSkeleton = () => (
  <Card className='animate-pulse'>
    <CardContent className='pt-6 prose max-w-none'>
      <Skeleton className='h-4 w-full mb-2' />
      <Skeleton className='h-4 w-3/4 mb-2' />
      <Skeleton className='h-4 w-1/2 mb-2' />
      <Skeleton className='h-4 w-5/6 mb-2' />
      <Skeleton className='h-4 w-full mb-2' />
    </CardContent>
  </Card>
)

export function ReportDetailPage() {
  const { id } = useParams<{ id: string }>()
  const [exportFormat, setExportFormat] = React.useState<'pdf' | 'docx' | null>(null)

  const { data: report, isLoading } = useQuery({
    queryKey: ['report', id],
    queryFn: () => api.get<Report>(\/reports/\\),
    enabled: !!id,
  })

  const exportMutation = React.useCallback(
    async (format: 'pdf' | 'docx') => {
      try {
        const result = await api.post<{ download_url: string }>(\/reports/\/export/\\)
        toast.success('Export ready')
        window.open(result.download_url, '_blank')
      } catch (error: unknown) {
        const message = error instanceof Error ? error.message : 'Export failed'
        toast.error(message)
      }
    },
    [id]
  )

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'completed':
        return <Badge variant='default'><CheckCircle className='mr-1 h-3 w-3' /> Completed</Badge>
      case 'generating':
        return <Badge variant='secondary'><Loader2 className='mr-1 h-3 w-3 animate-spin' /> Generating</Badge>
      case 'queued':
        return <Badge variant='secondary'><Clock className='mr-1 h-3 w-3' /> Queued</Badge>
      case 'failed':
        return <Badge variant='destructive'><XCircle className='mr-1 h-3 w-3' /> Failed</Badge>
      default:
        return <Badge variant='outline'>{status}</Badge>
    }
  }

  if (isLoading) {
    return (
      <div className='space-y-6 animate-fade-in'>
        <div className='flex items-center gap-4'>
          <Button variant='ghost' size='icon' onClick={() => window.history.back()}>
            <ArrowLeft className='h-4 w-4' />
          </Button>
          <div className='animate-pulse space-y-2'>
            <Skeleton className='h-8 w-64' />
            <Skeleton className='h-4 w-96' />
          </div>
        </div>
        <div className='grid gap-4 md:grid-cols-2 lg:grid-cols-4'>
          {[1, 2, 3, 4].map((i) => (
            <StatCardSkeleton key={i} style={{ animationDelay: \ms }} />
          ))}
        </div>
        <div className='space-y-6'>
          <NarrativeSkeleton />
          <ChartSkeleton />
          <ChartSkeleton />
        </div>
      </div>
    )
  }

  if (!report) {
    return (
      <div className='text-center py-12 animate-fade-in'>
        <FileText className='mx-auto h-12 w-12 text-muted-foreground' />
        <h3 className='mt-4 text-lg font-medium'>Report not found</h3>
        <Button variant='outline' className='mt-4' onClick={() => window.history.back()}>
          <ArrowLeft className='mr-2 h-4 w-4' />Back to Reports
        </Button>
      </div>
    )
  }

  const stats = report.computed_stats_json as Record<string, unknown> | null
  const charts = report.charts_json as unknown[] | null

  const StatCard = ({ label, value }: { label: string; value: string | number }) => (
    <Card className='hover-lift'>
      <CardContent className='pt-6'>
        <p className='text-sm text-muted-foreground'>{label}</p>
        <p className='text-2xl font-bold'>{value}</p>
      </CardContent>
    </Card>
  )

  const renderChart = (chart: unknown) => {
    const c = chart as { type: string; data: unknown[]; config?: Record<string, unknown> }
    if (!c.data || c.data.length === 0) return null

    const config = createChartConfig({
      value: { label: 'Value', color: 'hsl(var(--primary))' },
    })

    switch (c.type) {
      case 'bar':
        return (
          <ChartContainer config={config} className='h-[300px]'>
            <ResponsiveContainer width='100%' height='100%'>
              <BarChart data={c.data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray='3 3' />
                <XAxis dataKey={c.config?.xKey || 'category'} />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey={c.config?.yKey || 'value'} fill='hsl(var(--primary))' radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </ChartContainer>
        )
      case 'line':
        return (
          <ChartContainer config={config} className='h-[300px]'>
            <ResponsiveContainer width='100%' height='100%'>
              <LineChart data={c.data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray='3 3' />
                <XAxis dataKey={c.config?.xKey || 'category'} />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line type='monotone' dataKey={c.config?.yKey || 'value'} stroke='hsl(var(--primary))' strokeWidth={2} dot={{ r: 4 }} />
              </LineChart>
            </ResponsiveContainer>
          </ChartContainer>
        )
      case 'area':
        return (
          <ChartContainer config={config} className='h-[300px]'>
            <ResponsiveContainer width='100%' height='100%'>
              <AreaChart data={c.data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id='colorArea' x1='0' y1='0' x2='0' y2='1'>
                    <stop offset='5%' stopColor='hsl(var(--primary))' stopOpacity={0.3} />
                    <stop offset='95%' stopColor='hsl(var(--primary))' stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray='3 3' />
                <XAxis dataKey={c.config?.xKey || 'category'} />
                <YAxis />
                <Tooltip />
                <Legend />
                <Area type='monotone' dataKey={c.config?.yKey || 'value'} stroke='hsl(var(--primary))' fill='url(#colorArea)' />
              </AreaChart>
            </ResponsiveContainer>
          </ChartContainer>
        )
      default:
        return null
    }
  }

  return (
    <div className='space-y-6 animate-fade-in'>
      <div className='flex items-center gap-4'>
        <Button variant='ghost' size='icon' onClick={() => window.history.back()}>
          <ArrowLeft className='h-4 w-4' />
        </Button>
        <div>
          <h1 className='text-3xl font-bold tracking-tight'>{report.title}</h1>
          <p className='text-muted-foreground'>
            {report.report_type.replace('_', ' ')} • {formatDistanceToNow(new Date(report.created_at), { addSuffix: true })}
          </p>
        </div>
        <div className='flex-1' />
        <div className='flex items-center gap-2'>
          {getStatusBadge(report.status)}
          {report.status === 'completed' && (
            <>
              <Button variant='outline' onClick={() => { setExportFormat('pdf'); exportMutation('pdf'); }} className='hover:scale-105 transition-transform'>
                <Download className='mr-2 h-4 w-4' />PDF
              </Button>
              <Button variant='outline' onClick={() => { setExportFormat('docx'); exportMutation('docx'); }} className='hover:scale-105 transition-transform'>
                <Download className='mr-2 h-4 w-4' />DOCX
              </Button>
            </>
          )}
        </div>
      </div>

      {report.status !== 'completed' && (
        <Card className='hover-lift'>
          <CardContent className='pt-6 text-center py-12'>
            <Loader2 className='mx-auto h-12 w-12 animate-spin text-primary' />
            <h3 className='mt-4 text-lg font-medium'>Report is being generated</h3>
            <p className='mt-2 text-muted-foreground'>This usually takes a few moments. You can navigate away and come back later.</p>
          </CardContent>
        </Card>
      )}

      {report.status === 'completed' && (
        <>
          {stats && Object.keys(stats).length > 0 && (
            <div className='grid gap-4 md:grid-cols-2 lg:grid-cols-4'>
              {Object.entries(stats).map(([key, value], index) => (
                <StatCard key={key} label={key.replace(/_/g, ' ')} value={value as string | number} style={{ animationDelay: \ms }} />
              ))}
            </div>
          )}

          <Tabs defaultValue='narrative' className='space-y-4'>
            <TabsList>
              <TabsTrigger value='narrative'>
                <FileText className='mr-2 h-4 w-4' />Narrative
              </TabsTrigger>
              {charts && charts.length > 0 && (
                <TabsTrigger value='charts'>
                  <BarChart3 className='mr-2 h-4 w-4' />Charts
                </TabsTrigger>
              )}
              <TabsTrigger value='data'>
                <Database className='mr-2 h-4 w-4' />Raw Data
              </TabsTrigger>
            </TabsList>

            <TabsContent value='narrative' className='pt-4 animate-fade-in'>
              <Card className='hover-lift'>
                <CardContent className='pt-6 prose max-w-none'>
                  {report.narrative_text ? (
                    <div dangerouslySetInnerHTML={{ __html: report.narrative_text.replace(/\n/g, '<br />') }} />
                  ) : (
                    <p className='text-muted-foreground'>No narrative generated</p>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value='charts' className='pt-4 animate-fade-in'>
              {charts && charts.length > 0 ? (
                <div className='space-y-6'>
                  {charts.map((chart, i) => (
                    <Card key={i} className='hover-lift' style={{ animationDelay: \ms }}>
                      <CardContent className='pt-6'>
                        {renderChart(chart)}
                      </CardContent>
                    </Card>
                  ))}
                </div>
              ) : (
                <Card className='hover-lift'>
                  <CardContent className='pt-6 text-center py-12'>
                    <BarChart3 className='mx-auto h-12 w-12 text-muted-foreground' />
                    <p className='mt-4 text-muted-foreground'>No charts available</p>
                  </CardContent>
                </Card>
              )}
            </TabsContent>

            <TabsContent value='data' className='pt-4 animate-fade-in'>
              <Card className='hover-lift'>
                <CardHeader>
                  <CardTitle>Computed Statistics</CardTitle>
                </CardHeader>
                <CardContent>
                  <pre className='bg-muted p-4 rounded-lg overflow-auto text-sm max-h-96'>{JSON.stringify(stats, null, 2)}</pre>
                </CardContent>
              </Card>
              {charts && charts.length > 0 && (
                <Card className='mt-4 hover-lift'>
                  <CardHeader>
                    <CardTitle>Chart Data</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <pre className='bg-muted p-4 rounded-lg overflow-auto text-sm max-h-96'>{JSON.stringify(charts, null, 2)}</pre>
                  </CardContent>
                </Card>
              )}
            </TabsContent>
          </Tabs>
        </>
      )}
    </div>
  )
}
