'use client'

import * as React from 'react'
import { Link, useNavigate } from 'react-router-dom'
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
import { Skeleton } from '@/components/ui/skeleton'
import { 
  Database, 
  Plus, 
  Search, 
  Upload, 
  Eye, 
  Edit, 
  Trash2, 
  Download,
  Loader2,
  AlertCircle,
  CheckCircle,
  XCircle,
  FileText,
  ChevronDown,
  MessageSquare
} from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'

interface Dataset {
  id: string
  name: string
  source_type: string
  schema_json: Record<string, unknown> | null
  row_count: number
  status: string
  created_at: string
  error_message?: string | null
}

const TableRowSkeleton = ({ style }: React.HTMLAttributes<HTMLTableRowElement>) => (
  <TableRow style={style}>
    <TableCell><Skeleton className='h-4 w-3/4' /></TableCell>
    <TableCell><Skeleton className='h-5 w-16' /></TableCell>
    <TableCell><Skeleton className='h-4 w-20' /></TableCell>
    <TableCell><Skeleton className='h-5 w-24' /></TableCell>
    <TableCell><Skeleton className='h-4 w-28' /></TableCell>
    <TableCell className='text-right'><Skeleton className='h-8 w-8' /></TableCell>
  </TableRow>
)

export function DatasetsPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [searchQuery, setSearchQuery] = React.useState('')
  const [uploadDialogOpen, setUploadDialogOpen] = React.useState(false)
  const [uploadingFile, setUploadingFile] = React.useState<File | null>(null)
  const [uploadProgress, setUploadProgress] = React.useState(0)
  const [datasetName, setDatasetName] = React.useState('')

  const { data: datasets, isLoading } = useQuery({
    queryKey: ['datasets'],
    queryFn: () => api.get<Dataset[]>('/datasets'),
  })

  const uploadMutation = useMutation({
    mutationFn: ({ file, name }: { file: File; name: string }) => 
      api.upload<Dataset>('/datasets/upload', file, setUploadProgress),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['datasets'] })
      toast.success('Dataset uploaded successfully')
      setUploadDialogOpen(false)
      setUploadingFile(null)
      setDatasetName('')
      setUploadProgress(0)
    },
    onError: (error: unknown) => {
      const message = error instanceof Error ? error.message : 'Upload failed'
      toast.error(message)
      setUploadingFile(null)
      setUploadProgress(0)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.delete(`/datasets/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['datasets'] })
      toast.success('Dataset deleted')
    },
    onError: (error: unknown) => {
      const message = error instanceof Error ? error.message : 'Delete failed'
      toast.error(message)
    },
  })

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      setUploadingFile(file)
      setDatasetName(file.name.replace(/\.[^/.]+$/, ''))
    }
  }

  const handleUpload = () => {
    if (uploadingFile) {
      uploadMutation.mutate({ file: uploadingFile, name: datasetName })
    }
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'ready':
        return <Badge variant='default'><CheckCircle className='mr-1 h-3 w-3' /> Ready</Badge>
      case 'processing':
        return <Badge variant='secondary'><Loader2 className='mr-1 h-3 w-3 animate-spin' /> Processing</Badge>
      case 'uploading':
        return <Badge variant='secondary'><Upload className='mr-1 h-3 w-3' /> Uploading</Badge>
      case 'error':
        return <Badge variant='destructive'><AlertCircle className='mr-1 h-3 w-3' /> Error</Badge>
      default:
        return <Badge variant='outline'>{status}</Badge>
    }
  }

  const filteredDatasets = datasets?.filter((d) => 
    d.name.toLowerCase().includes(searchQuery.toLowerCase())
  ) || []

  return (
    <div className='space-y-6 animate-fade-in'>
      <div className='flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4'>
        <div>
          <h1 className='text-3xl font-bold tracking-tight'>Data Sources</h1>
          <p className='text-muted-foreground'>Manage your uploaded datasets</p>
        </div>
        <Dialog open={uploadDialogOpen} onOpenChange={setUploadDialogOpen}>
          <DialogTrigger asChild>
            <Button className='animate-scale-in hover:scale-105 transition-transform'><Plus className='mr-2 h-4 w-4' />Upload Dataset</Button>
          </DialogTrigger>
          <DialogContent className='animate-scale-in'>
            <DialogHeader>
              <DialogTitle>Upload Dataset</DialogTitle>
            </DialogHeader>
            <div className='space-y-4 py-4'>
              {!uploadingFile ? (
                <div className='border-2 border-dashed border-border rounded-lg p-8 text-center hover:border-primary transition-colors'>
                  <Upload className='mx-auto h-12 w-12 text-muted-foreground' />
                  <p className='mt-4 text-sm text-muted-foreground'>Drag & drop a CSV file, or click to browse</p>
                  <Input type='file' accept='.csv' onChange={handleFileChange} className='sr-only' id='file-upload' />
                  <Button variant='outline' className='mt-4' onClick={() => document.getElementById('file-upload')?.click()}>
                    Browse Files
                  </Button>
                </div>
              ) : (
                <div className='space-y-4'>
                  <div className='flex items-center gap-3'>
                    <Database className='h-10 w-10 text-primary' />
                    <div className='flex-1'>
                      <p className='font-medium'>{uploadingFile.name}</p>
                      <p className='text-sm text-muted-foreground'>{(uploadingFile.size / 1024 / 1024).toFixed(2)} MB</p>
                    </div>
                  </div>
                  <div className='space-y-2'>
                    <Label htmlFor='dataset-name'>Dataset Name</Label>
                    <Input
                      id='dataset-name'
                      value={datasetName}
                      onChange={(e) => setDatasetName(e.target.value)}
                      placeholder='Enter dataset name'
                    />
                  </div>
                  <div className='space-y-2'>
                    <div className='flex justify-between text-sm'>
                      <span>Upload Progress</span>
                      <span>{uploadProgress}%</span>
                    </div>
                    <div className='h-2 bg-muted rounded-full overflow-hidden'>
                      <div 
                        className='h-full bg-primary transition-all duration-300' 
                        style={{ width: `${uploadProgress}%` }}
                      />
                    </div>
                  </div>
                  <div className='flex justify-end gap-2'>
                    <Button variant='outline' onClick={() => { setUploadingFile(null); setUploadProgress(0); }}>Cancel</Button>
                    <Button onClick={handleUpload} disabled={uploadMutation.isPending || uploadProgress < 100}>
                      {uploadMutation.isPending ? 'Uploading...' : 'Upload'}
                    </Button>
                  </div>
                </div>
              )}
            </div>
          </DialogContent>
        </Dialog>
      </div>

      <Card className='hover-lift'>
        <CardHeader>
          <div className='flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4'>
            <div className='relative max-w-md flex-1'>
              <Search className='absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground' />
              <Input
                placeholder='Search datasets...'
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
                  <TableHead>Name</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Rows</TableHead>
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
          ) : filteredDatasets.length === 0 ? (
            <div className='text-center py-12 animate-fade-in'>
              <Database className='mx-auto h-12 w-12 text-muted-foreground' />
              <h3 className='mt-4 text-lg font-medium'>No datasets found</h3>
              <p className='mt-2 text-muted-foreground'>Get started by uploading your first dataset</p>
              <Button className='mt-4' onClick={() => setUploadDialogOpen(true)}>
                <Plus className='mr-2 h-4 w-4' />Upload Dataset
              </Button>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Rows</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead className='text-right'>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredDatasets.map((dataset, index) => (
                  <TableRow key={dataset.id} className='animate-fade-in hover:bg-accent/50 transition-colors' style={{ animationDelay: `${index * 50}ms` }}>
                    <TableCell className='font-medium'>{dataset.name}</TableCell>
                    <TableCell>
                      <Badge variant='outline'>{dataset.source_type.toUpperCase()}</Badge>
                    </TableCell>
                    <TableCell>{dataset.row_count.toLocaleString()}</TableCell>
                    <TableCell>{getStatusBadge(dataset.status)}</TableCell>
                    <TableCell>{formatDistanceToNow(new Date(dataset.created_at), { addSuffix: true })}</TableCell>
                    <TableCell className='text-right'>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant='ghost' size='icon' className='h-8 w-8'>
                            <ChevronDown className='h-4 w-4' />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align='end' className='animate-scale-in'>
                          <DropdownMenuItem asChild>
                            <Link to={`/datasets/${dataset.id}`}>
                              <Eye className='mr-2 h-4 w-4' />View Details
                            </Link>
                          </DropdownMenuItem>
                          <DropdownMenuItem asChild>
                            <Link to={`/reports/generate?dataset=${dataset.id}`}>
                              <FileText className='mr-2 h-4 w-4' />Generate Report
                            </Link>
                          </DropdownMenuItem>
                          <DropdownMenuItem asChild>
                            <Link to={`/chat?dataset=${dataset.id}`}>
                              <MessageSquare className='mr-2 h-4 w-4' />Chat with Data
                            </Link>
                          </DropdownMenuItem>
                          <DropdownMenuSeparator />
                          <DropdownMenuItem onClick={() => {
                            if (confirm('Are you sure you want to delete this dataset?')) {
                              deleteMutation.mutate(dataset.id)
                            }
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
