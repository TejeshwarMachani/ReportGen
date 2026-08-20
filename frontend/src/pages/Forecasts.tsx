'use client'

import * as React from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/api/client'
import { toast } from 'react-hot-toast'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from '@/components/ui/dialog'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuTrigger } from '@/components/ui/dropdown-menu'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import { 
  TrendingUp, 
  Plus, 
  Search, 
  Eye, 
  Loader2,
  CheckCircle,
  AlertCircle,
  XCircle,
  Clock,
  ChevronDown,
  Download,
  X
} from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import {
  ChartContainer,
  createChartConfig,
} from '@/components/ui/chart'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, AreaChart, Area } from 'recharts'

interface ForecastJob {
  id: string
  org_id: string
  dataset_id: string
  target_column: string
  date_column: string
  horizon_periods: number
  model_type: string
  status: string
  result_json?: {
    forecast_values?: number[]
    confidence_intervals?: number[][]
    model_params?: Record<string, unknown>
    summary_text?: string
  }
  created_at: string
  completed_at?: string | null
}

interface Dataset {
  id: string
  name: string
  schema_json?: Array<{ column: string; inferred_type: string }>
}

const TableRowSkeleton = ({ style }: React.HTMLAttributes<HTMLTableRowElement>) => (
  <TableRow style={style}>
    <TableCell><Skeleton className='h-4 w-3/4' /></TableCell>
    <TableCell><Skeleton className='h-4 w-1/2' /></TableCell>
    <TableCell><Skeleton className='h-4 w-16' /></TableCell>
    <TableCell><Skeleton className='h-5 w-20' /></TableCell>
    <TableCell><Skeleton className='h-5 w-20' /></TableCell>
    <TableCell><Skeleton className='h-4 w-28' /></TableCell>
    <TableCell className='text-right'><Skeleton className='h-8 w-8' /></TableCell>
  </TableRow>
)

const ForecastChart = ({ job }: { job: ForecastJob }) => {
  const result = job.result_json
  if (!result?.forecast_values || !result?.confidence_intervals) return null

  const config = createChartConfig({
    forecast: { label: 'Forecast', color: 'hsl(var(--primary))' },
    lower: { label: 'Lower Bound', color: 'hsl(var(--muted-foreground))' },
    upper: { label: 'Upper Bound', color: 'hsl(var(--muted-foreground))' },
  })

  const intervals = result.confidence_intervals || []
  const chartData = result.forecast_values.map((value, i) => ({
    period: i + 1,
    forecast: value,
    lower: intervals[i]?.[0] ?? value,
    upper: intervals[i]?.[1] ?? value,
  }))

  return (
    <ChartContainer config={config} className='h-[400px]'>
      <ResponsiveContainer width='100%' height='100%'>
        <AreaChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id='colorForecast' x1='0' y1='0' x2='0' y2='1'>
              <stop offset='5%' stopColor='hsl(var(--primary))' stopOpacity={0.3} />
              <stop offset='95%' stopColor='hsl(var(--primary))' stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray='3 3' />
          <XAxis dataKey='period' />
          <YAxis />
          <Tooltip />
          <Legend />
          <Area type='monotone' dataKey='forecast' stroke='hsl(var(--primary))' fillOpacity={1} fill='url(#colorForecast)' />
          <Area type='monotone' dataKey='lower' stroke='hsl(var(--muted-foreground))' strokeDasharray='5 5' fill='none' />
          <Area type='monotone' dataKey='upper' stroke='hsl(var(--muted-foreground))' strokeDasharray='5 5' fill='none' />
        </AreaChart>
      </ResponsiveContainer>
    </ChartContainer>
  )
}

export function ForecastsPage() {
  const queryClient = useQueryClient()
  const [searchQuery, setSearchQuery] = React.useState('')
  const [forecastDialogOpen, setForecastDialogOpen] = React.useState(false)
  const [selectedDatasetId, setSelectedDatasetId] = React.useState('')
  const [targetColumn, setTargetColumn] = React.useState('')
  const [dateColumn, setDateColumn] = React.useState('')
  const [horizon, setHorizon] = React.useState(12)
  const [modelType, setModelType] = React.useState('prophet')
  const [selectedJob, setSelectedJob] = React.useState<ForecastJob | null>(null)
  const [showJobDetails, setShowJobDetails] = React.useState(false)

  const { data: jobs, isLoading } = useQuery({
    queryKey: ['forecast-jobs'],
    queryFn: () => api.get<ForecastJob[]>('/forecast/jobs'),
  })

  const { data: datasets } = useQuery({
    queryKey: ['datasets'],
    queryFn: () => api.get<Dataset[]>('/datasets'),
  })

  const columns = React.useMemo(() => {
    const dataset = datasets?.find((d) => d.id === selectedDatasetId)
    if (!dataset?.schema_json) return { date: [], numeric: [] }
    return {
      date: dataset.schema_json.filter((c) => 
        ['date', 'datetime', 'timestamp'].includes(c.inferred_type.toLowerCase())
      ).map((c) => c.column),
      numeric: dataset.schema_json.filter((c) => 
        ['number', 'integer', 'float'].includes(c.inferred_type.toLowerCase())
      ).map((c) => c.column),
    }
  }, [datasets, selectedDatasetId])

  const generateMutation = useMutation({
    mutationFn: ({ datasetId, target, date, horizonPeriods, model }: { datasetId: string; target: string; date: string; horizonPeriods: number; model: string }) =>
      api.post<{ job_id: string; status: string }>(`/forecast/generate/${datasetId}`, {
        target_column: target,
        date_column: date,
        horizon: horizonPeriods,
        model_type: model,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['forecast-jobs'] })
      toast.success('Forecast job started')
      setForecastDialogOpen(false)
      setTargetColumn('')
      setDateColumn('')
      setHorizon(12)
    },
    onError: (error: unknown) => {
      const message = error instanceof Error ? error.message : 'Failed to start forecast'
      toast.error(message)
    },
  })

  const handleGenerate = () => {
    if (selectedDatasetId && targetColumn && dateColumn) {
      generateMutation.mutate({
        datasetId: selectedDatasetId,
        target: targetColumn,
        date: dateColumn,
        horizonPeriods: horizon,
        model: modelType,
      })
    }
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'completed':
        return <Badge variant='default'><CheckCircle className='mr-1 h-3 w-3' /> Completed</Badge>
      case 'running':
        return <Badge variant='secondary'><Loader2 className='mr-1 h-3 w-3 animate-spin' /> Running</Badge>
      case 'queued':
        return <Badge variant='secondary'><Clock className='mr-1 h-3 w-3' /> Queued</Badge>
      case 'failed':
        return <Badge variant='destructive'><XCircle className='mr-1 h-3 w-3' /> Failed</Badge>
      default:
        return <Badge variant='outline'>{status}</Badge>
    }
  }

  const filteredJobs = jobs?.filter((j) => 
    j.target_column.toLowerCase().includes(searchQuery.toLowerCase()) ||
    j.model_type.toLowerCase().includes(searchQuery.toLowerCase())
  ) || []

  const modelTypes = [
    { value: 'prophet', label: 'Prophet' },
    { value: 'arima', label: 'ARIMA' },
    { value: 'lstm', label: 'LSTM' },
  ]

  return (
    <div className='space-y-6 animate-fade-in'>
      <div className='flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4'>
        <div>
          <h1 className='text-3xl font-bold tracking-tight flex items-center gap-2'>
            <TrendingUp className='h-8 w-8 text-primary' />
            Forecasts
          </h1>
          <p className='text-muted-foreground'>Time series forecasting on your datasets</p>
        </div>
        <Dialog open={forecastDialogOpen} onOpenChange={setForecastDialogOpen}>
          <DialogTrigger asChild>
            <Button className='animate-scale-in hover:scale-105 transition-transform'><Plus className='mr-2 h-4 w-4' />Run Forecast</Button>
          </DialogTrigger>
          <DialogContent className='animate-scale-in max-w-md'>
            <DialogHeader>
              <DialogTitle>Run New Forecast</DialogTitle>
            </DialogHeader>
            <div className='space-y-4 py-4'>
              <div className='space-y-2'>
                <Label htmlFor='forecast-dataset'>Dataset</Label>
                <Select value={selectedDatasetId} onValueChange={setSelectedDatasetId}>
                  <SelectTrigger id='forecast-dataset'>
                    <SelectValue placeholder='Select a dataset...' />
                  </SelectTrigger>
                  <SelectContent>
                    {datasets?.map((d) => (
                      <SelectItem key={d.id} value={d.id}>{d.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className='space-y-2'>
                <Label htmlFor='target-column'>Target Column (Numeric)</Label>
                <Select value={targetColumn} onValueChange={setTargetColumn} disabled={columns.numeric.length === 0}>
                  <SelectTrigger id='target-column'>
                    <SelectValue placeholder={columns.numeric.length === 0 ? 'Select dataset first' : 'Select target...'} />
                  </SelectTrigger>
                  <SelectContent>
                    {columns.numeric.map((c) => (
                      <SelectItem key={c} value={c}>{c}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className='space-y-2'>
                <Label htmlFor='date-column'>Date Column</Label>
                <Select value={dateColumn} onValueChange={setDateColumn} disabled={columns.date.length === 0}>
                  <SelectTrigger id='date-column'>
                    <SelectValue placeholder={columns.date.length === 0 ? 'Select dataset first' : 'Select date...'} />
                  </SelectTrigger>
                  <SelectContent>
                    {columns.date.map((c) => (
                      <SelectItem key={c} value={c}>{c}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className='grid grid-cols-2 gap-4'>
                <div className='space-y-2'>
                  <Label htmlFor='horizon'>Horizon (Periods)</Label>
                  <Input
                    id='horizon'
                    type='number'
                    min='1'
                    max='100'
                    value={horizon}
                    onChange={(e) => setHorizon(parseInt(e.target.value) || 12)}
                  />
                </div>
                <div className='space-y-2'>
                  <Label htmlFor='model-type'>Model</Label>
                  <Select value={modelType} onValueChange={setModelType}>
                    <SelectTrigger id='model-type'>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {modelTypes.map((m) => (
                        <SelectItem key={m.value} value={m.value}>{m.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </div>
            <DialogFooter className='flex justify-end gap-2'>
              <Button variant='outline' onClick={() => setForecastDialogOpen(false)}>Cancel</Button>
              <Button onClick={handleGenerate} disabled={generateMutation.isPending || !selectedDatasetId || !targetColumn || !dateColumn}>
                {generateMutation.isPending ? 'Starting...' : 'Run Forecast'}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      <Card className='hover-lift'>
        <CardHeader>
          <div className='flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4'>
            <div className='relative max-w-md'>
              <Search className='absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground' />
              <Input
                placeholder='Search forecasts...'
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className='pl-10'
              />
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Target</TableHead>
                  <TableHead>Date Column</TableHead>
                  <TableHead>Horizon</TableHead>
                  <TableHead>Model</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead className='text-right'>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {[1, 2, 3, 4, 5].map((i) => (
                  <TableRowSkeleton key={i} style={{ animationDelay: `${i * 50}ms` }} />
                ))}
              </TableBody>
            </Table>
          ) : filteredJobs.length === 0 ? (
            <div className='text-center py-12 animate-fade-in'>
              <TrendingUp className='mx-auto h-12 w-12 text-muted-foreground' />
              <h3 className='mt-4 text-lg font-medium'>No forecasts yet</h3>
              <p className='mt-2 text-muted-foreground'>Run your first forecast on a time series dataset</p>
              <Button className='mt-4' onClick={() => setForecastDialogOpen(true)}>
                <Plus className='mr-2 h-4 w-4' />Run Forecast
              </Button>
            </div>
          ) : (
            <>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Target</TableHead>
                    <TableHead>Date Column</TableHead>
                    <TableHead>Horizon</TableHead>
                    <TableHead>Model</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Created</TableHead>
                    <TableHead className='text-right'>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredJobs.map((job, index) => (
                    <TableRow key={job.id} className='animate-fade-in hover:bg-accent/50 transition-colors' style={{ animationDelay: `${index * 50}ms` }}>
                      <TableCell className='font-medium'>{job.target_column}</TableCell>
                      <TableCell>{job.date_column}</TableCell>
                      <TableCell>{job.horizon_periods}</TableCell>
                      <TableCell>
                        <Badge variant='outline'>{job.model_type}</Badge>
                      </TableCell>
                      <TableCell>{getStatusBadge(job.status)}</TableCell>
                      <TableCell>{formatDistanceToNow(new Date(job.created_at), { addSuffix: true })}</TableCell>
                      <TableCell className='text-right'>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant='ghost' size='icon' className='h-8 w-8'>
                              <ChevronDown className='h-4 w-4' />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align='end' className='animate-scale-in'>
                            <DropdownMenuItem onClick={() => { setSelectedJob(job); setShowJobDetails(true); }}>
                              <Eye className='mr-2 h-4 w-4' />View Details
                            </DropdownMenuItem>
                            {job.status === 'completed' && (
                              <DropdownMenuItem>
                                <Download className='mr-2 h-4 w-4' />Export Results
                              </DropdownMenuItem>
                            )}
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
              
              {showJobDetails && selectedJob && (
                <div className='fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 animate-fade-in'>
                  <Card className='w-full max-w-4xl max-h-[90vh] overflow-hidden animate-scale-in'>
                    <CardHeader>
                      <div className='flex items-center justify-between'>
                        <div>
                          <CardTitle>Forecast: {selectedJob.target_column}</CardTitle>
                          <p className='text-sm text-muted-foreground'>{selectedJob.date_column} · {selectedJob.model_type} · {selectedJob.horizon_periods} periods</p>
                        </div>
                        <Button variant='ghost' size='icon' onClick={() => { setShowJobDetails(false); setSelectedJob(null); }}>
                          <X className='h-4 w-4' />
                        </Button>
                      </div>
                    </CardHeader>
                    <CardContent className='p-0'>
                      <div className='p-6'>
                        <ForecastChart job={selectedJob} />
                        {selectedJob.result_json?.summary_text && (
                          <div className='mt-4 p-4 bg-muted rounded-lg animate-fade-in'>
                            <h4 className='font-medium mb-2'>Summary</h4>
                            <p className='text-sm text-muted-foreground'>{selectedJob.result_json.summary_text}</p>
                          </div>
                        )}
                        {selectedJob.result_json?.model_params && (
                          <div className='mt-4 animate-fade-in'>
                            <h4 className='font-medium mb-2'>Model Parameters</h4>
                            <pre className='text-xs bg-muted p-4 rounded overflow-auto'>{JSON.stringify(selectedJob.result_json.model_params, null, 2)}</pre>
                          </div>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
