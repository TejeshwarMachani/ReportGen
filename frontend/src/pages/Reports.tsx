'use client'

import * as React from 'react'
import { Link, useSearchParams } from 'react-router-dom'
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Skeleton } from '@/components/ui/skeleton'
import { 
  FileText, 
  Plus, 
  Search, 
  Eye, 
  Download, 
  Loader2,
  CheckCircle,
  AlertCircle,
  XCircle,
  Clock,
  ChevronDown,
  ArrowRight,
  Trash2
} from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'

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

interface Dataset {
  id: string
  name: string
}

const TableRowSkeleton = () => (
  <TableRow>
    <TableCell><Skeleton className='h-4 w-3/4' /></TableCell>
    <TableCell><Skeleton className='h-5 w-24' /></TableCell>
    <TableCell><Skeleton className='h-5 w-24' /></TableCell>
    <TableCell><Skeleton className='h-4 w-28' /></TableCell>
    <TableCell className='text-right'><Skeleton className='h-8 w-8' /></TableCell>
  </TableRow>
)

export function ReportsPage() {
  const queryClient = useQueryClient()
  const [searchParams] = useSearchParams()
  const preselectedDataset = searchParams.get('dataset')
  const [searchQuery, setSearchQuery] = React.useState('')
  const [generateDialogOpen, setGenerateDialogOpen] = React.useState(false)
  const [selectedDatasetId, setSelectedDatasetId] = React.useState(preselectedDataset || '')
  const [reportTitle, setReportTitle] = React.useState('')
  const [reportType, setReportType] = React.useState('auto_summary')
  const [exportFormat, setExportFormat] = React.useState<'pdf' | 'docx' | null>(null)
  const [generatingReportId, setGeneratingReportId] = React.useState<string | null>(null)

  const { data: reports, isLoading } = useQuery({
    queryKey: ['reports'],
    queryFn: () => api.get<Report[]>('/reports'),
  })

  const { data: datasets } = useQuery({
    queryKey: ['datasets'],
    queryFn: () => api.get<Dataset[]>('/datasets'),
  })

  const generateMutation = useMutation({
    mutationFn: ({ datasetId, title, type, format }: { datasetId: string; title: string; type: string; format?: string }) =>
      api.post<{ task_id: string; dataset_id: string; status: string }>(\/reports/generate/\\, {
        title,
        report_type: type,
        export_format: format,
      }),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['reports'] })
      toast.success('Report generation started')
      setGenerateDialogOpen(false)
      setReportTitle('')
      setGeneratingReportId(data.task_id || data.dataset_id)
    },
    onError: (error: unknown) => {
      const message = error instanceof Error ? error.message : 'Generation failed'
      toast.error(message)
    },
  })

  const exportMutation = useMutation({
    mutationFn: ({ reportId, format }: { reportId: string; format: 'pdf' | 'docx' }) =>
      api.post<{ download_url: string }>(\/reports/\/export/\\),
    onSuccess: (data) => {
      toast.success('Export ready')
      window.open(data.download_url, '_blank')
    },
    onError: (error: unknown) => {
      const message = error instanceof Error ? error.message : 'Export failed'
      toast.error(message)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.delete(\/reports/\\),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reports'] })
      toast.success('Report deleted')
    },
    onError: (error: unknown) => {
      const message = error instanceof Error ? error.message : 'Delete failed'
      toast.error(message)
    },
  })

  const handleGenerate = () => {
    if (selectedDatasetId) {
      generateMutation.mutate({
        datasetId: selectedDatasetId,
        title: reportTitle || 'Untitled Report',
        type: reportType,
        format: exportFormat || undefined,
      })
    }
  }

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

  const filteredReports = reports?.filter((r) => 
    r.title.toLowerCase().includes(searchQuery.toLowerCase())
  ) || []

  const reportTypes = [
    { value: 'auto_summary', label: 'Auto Summary' },
    { value: 'executive_summary', label: 'Executive Summary' },
    { value: 'detailed_analysis', label: 'Detailed Analysis' },
    { value: 'comparison', label: 'Comparison Report' },
  ]

  return (
    <div className='space-y-6 animate-fade-in'>
      <div className='flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4'>
        <div>
          <h1 className='text-3xl font-bold tracking-tight'>Reports</h1>
          <p className='text-muted-foreground'>View and manage your generated reports</p>
        </div>
        <Dialog open={generateDialogOpen} onOpenChange={setGenerateDialogOpen}>
          <DialogTrigger asChild>
            <Button className='animate-scale-in hover:scale-105 transition-transform'><Plus className='mr-2 h-4 w-4' />Generate Report</Button>
          </DialogTrigger>
          <DialogContent className='animate-scale-in max-w-md'>
            <DialogHeader>
              <DialogTitle>Generate New Report</DialogTitle>
            </DialogHeader>
            <div className='space-y-4 py-4'>
              <div className='space-y-2'>
                <Label htmlFor='report-dataset'>Dataset</Label>
                <Select value={selectedDatasetId} onValueChange={setSelectedDatasetId} disabled={!!preselectedDataset}>
                  <SelectTrigger id='report-dataset'>
                    <SelectValue placeholder='Select a dataset...' />
                  </SelectTrigger>
                  <SelectContent>
                    {datasets?.map((d) => (
                      <SelectItem key={d.id} value={d.id}>{d.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {preselectedDataset && (
                  <p className='text-sm text-muted-foreground'>Dataset pre-selected from Data Sources</p>
                )}
              </div>
              <div className='space-y-2'>
                <Label htmlFor='report-title'>Report Title</Label>
                <Input
                  id='report-title'
                  value={reportTitle}
                  onChange={(e) => setReportTitle(e.target.value)}
                  placeholder='Enter report title (optional)'
                />
              </div>
              <div className='space-y-2'>
                <Label htmlFor='report-type'>Report Type</Label>
                <Select value={reportType} onValueChange={setReportType}>
                  <SelectTrigger id='report-type'>
                    <SelectValue placeholder='Select report type...' />
                  </SelectTrigger>
                  <SelectContent>
                    {reportTypes.map((t) => (
                      <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className='space-y-2'>
                <Label>Export Format (Optional)</Label>
                <div className='flex gap-2'>
                  <Button
                    variant={exportFormat === 'pdf' ? 'default' : 'outline'}
                    onClick={() => setExportFormat(exportFormat === 'pdf' ? null : 'pdf')}
                    className='flex-1'
                  >
                    PDF
                  </Button>
                  <Button
                    variant={exportFormat === 'docx' ? 'default' : 'outline'}
                    onClick={() => setExportFormat(exportFormat === 'docx' ? null : 'docx')}
                    className='flex-1'
                  >
                    DOCX
                  </Button>
                </div>
              </div>
            </div>
            <DialogFooter className='flex justify-end gap-2'>
              <Button variant='outline' onClick={() => setGenerateDialogOpen(false)}>Cancel</Button>
              <Button onClick={handleGenerate} disabled={generateMutation.isPending || !selectedDatasetId}>
                {generateMutation.isPending ? 'Generating...' : 'Generate Report'}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      <Card className='hover-lift'>
        <CardHeader>
          <div className='relative max-w-md'>
            <Search className='absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground' />
            <Input
              placeholder='Search reports...'
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className='pl-10'
            />
          </div>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Title</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead className='text-right'>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {[1, 2, 3, 4, 5].map((i) => (
                  <TableRowSkeleton key={i} style={{ animationDelay: \\ms\ }} />
                ))}
              </TableBody>
            </Table>
          ) : filteredReports.length === 0 ? (
            <div className='text-center py-12 animate-fade-in'>
              <FileText className='mx-auto h-12 w-12 text-muted-foreground' />
              <h3 className='mt-4 text-lg font-medium'>No reports yet</h3>
              <p className='mt-2 text-muted-foreground'>Generate your first report from a dataset</p>
              <Button className='mt-4' onClick={() => setGenerateDialogOpen(true)}>
                <Plus className='mr-2 h-4 w-4' />Generate Report
              </Button>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Title</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead className='text-right'>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredReports.map((report, index) => (
                  <TableRow key={report.id} className='animate-fade-in hover:bg-accent/50 transition-colors' style={{ animationDelay: \\ms\ }}>
                    <TableCell className='font-medium'>{report.title}</TableCell>
                    <TableCell>
                      <Badge variant='outline'>{report.report_type.replace('_', ' ')}</Badge>
                    </TableCell>
                    <TableCell>{getStatusBadge(report.status)}</TableCell>
                    <TableCell>{formatDistanceToNow(new Date(report.created_at), { addSuffix: true })}</TableCell>
                    <TableCell className='text-right'>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant='ghost' size='icon' className='h-8 w-8'>
                            <ChevronDown className='h-4 w-4' />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align='end' className='animate-scale-in'>
                          <DropdownMenuItem asChild>
                            <Link to={\/reports/\\}>
                              <Eye className='mr-2 h-4 w-4' />View Report
                            </Link>
                          </DropdownMenuItem>
                          {report.status === 'completed' && (
                            <>
                              <DropdownMenuSeparator />
                              <DropdownMenuItem onClick={() => exportMutation.mutate({ reportId: report.id, format: 'pdf' })}>
                                <Download className='mr-2 h-4 w-4' />Export PDF
                              </DropdownMenuItem>
                              <DropdownMenuItem onClick={() => exportMutation.mutate({ reportId: report.id, format: 'docx' })}>
                                <Download className='mr-2 h-4 w-4' />Export DOCX
                              </DropdownMenuItem>
                            </>
                          )}
                          <DropdownMenuSeparator />
                          <DropdownMenuItem onClick={() => {
                            if (confirm('Delete this report?')) deleteMutation.mutate(report.id)
                          }} className='text-destructive focus:text-destructive'>
                            <Trash2 className='mr-2 h-4 w-4' />Delete
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
