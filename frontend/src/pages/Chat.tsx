'use client'

import * as React from 'react'
import { useSearchParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/api/client'
import { toast } from 'react-hot-toast'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import { 
  MessageSquare, 
  Send, 
  Loader2, 
  Database, 
  BarChart3,
  Table as TableIcon,
  X,
  Copy,
  Check
} from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'

interface Dataset {
  id: string
  name: string
  schema_json?: Record<string, unknown>[]
}

interface ChatResponse {
  response: string
  statements?: Array<{ type: string; field?: string; op?: string }>
  results?: Array<{ summary?: string; data?: unknown; error?: string }>
  dataset_summary?: { columns?: string[] }
}

interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  statements?: Array<{ type: string; field?: string; op?: string }>
  results?: Array<{ summary?: string; data?: unknown; error?: string }>
  created_at: string
}

const MessageSkeleton = () => (
  <div className='flex gap-3 animate-pulse'>
    <div className='flex h-10 w-10 items-center justify-center rounded-full bg-muted flex-shrink-0' />
    <div className='flex-1 space-y-2'>
      <Skeleton className='h-4 w-1/4' />
      <Skeleton className='h-4 w-1/2' />
      <Skeleton className='h-3 w-3/4' />
    </div>
  </div>
)

export function ChatPage() {
  const [searchParams] = useSearchParams()
  const preselectedDataset = searchParams.get('dataset')
  const queryClient = useQueryClient()
  const [selectedDatasetId, setSelectedDatasetId] = React.useState(preselectedDataset || '')
  const [message, setMessage] = React.useState('')
  const [messages, setMessages] = React.useState<ChatMessage[]>([])
  const [isLoading, setIsLoading] = React.useState(false)
  const [showQuery, setShowQuery] = React.useState<string | null>(null)

  const { data: datasets } = useQuery({
    queryKey: ['datasets'],
    queryFn: () => api.get<Dataset[]>('/datasets'),
  })

  const sendMutation = useMutation({
    mutationFn: ({ message, datasetId }: { message: string; datasetId: string }) =>
      api.post<ChatResponse>('/chat/message', { message, dataset_id: datasetId }),
    onSuccess: (data) => {
      setMessages((prev) => [
        ...prev,
        { id: Date.now().toString(), role: 'user', content: message, created_at: new Date().toISOString() },
        { 
          id: (Date.now() + 1).toString(), 
          role: 'assistant', 
          content: data.response, 
          statements: data.statements,
          results: data.results,
          created_at: new Date().toISOString() 
        },
      ])
      setMessage('')
      setIsLoading(false)
    },
    onError: (error: unknown) => {
      const msg = error instanceof Error ? error.message : 'Failed to send message'
      toast.error(msg)
      setIsLoading(false)
    },
  })

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault()
    if (!message.trim() || !selectedDatasetId || isLoading) return
    setIsLoading(true)
    sendMutation.mutate({ message, datasetId: selectedDatasetId })
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
    toast.success('Copied to clipboard')
  }

  return (
    <div className='h-[calc(100vh-200px)] flex flex-col animate-fade-in'>
      <div className='flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6'>
        <div>
          <h1 className='text-3xl font-bold tracking-tight flex items-center gap-2'>
            <MessageSquare className='h-8 w-8 text-primary' />
            Chat with Data
          </h1>
          <p className='text-muted-foreground'>Ask questions about your data in plain English</p>
        </div>
        <div className='w-full sm:w-64'>
          <Label htmlFor='chat-dataset' className='block mb-1'>Select Dataset</Label>
          <Select value={selectedDatasetId} onValueChange={setSelectedDatasetId}>
            <SelectTrigger id='chat-dataset' disabled={!!preselectedDataset}>
              <SelectValue placeholder='Choose a dataset...' />
            </SelectTrigger>
            <SelectContent>
              {datasets?.map((d) => (
                <SelectItem key={d.id} value={d.id}>{d.name}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          {preselectedDataset && (
            <p className='text-sm text-muted-foreground mt-1'>Dataset pre-selected from Data Sources</p>
          )}
        </div>
      </div>

      <Card className='flex-1 flex flex-col min-h-0 hover-lift'>
        <CardHeader className='pb-2'>
          <CardTitle className='text-lg'>Conversation</CardTitle>
        </CardHeader>
        <CardContent className='flex-1 min-h-0 p-0'>
          <ScrollArea className='h-full p-4'>
            <div className='space-y-6'>
              {messages.length === 0 ? (
                <div className='flex flex-col items-center justify-center h-full text-center text-muted-foreground'>
                  <MessageSquare className='h-16 w-16 mb-4 opacity-50' />
                  <h3 className='text-lg font-medium'>No messages yet</h3>
                  <p className='mt-1'>Select a dataset and start asking questions</p>
                  <div className='mt-4 flex flex-wrap gap-2 justify-center'>
                    {[
                      'Total revenue by month',
                      'Top 5 products by sales',
                      'Show trend for sales',
                      'Average order value',
                    ].map((suggestion, i) => (
                      <Button
                        key={i}
                        variant='outline'
                        size='sm'
                        className='animate-fade-in'
                        style={{ animationDelay: `${i * 50}ms` }}
                        onClick={() => { setMessage(suggestion); handleSend({ preventDefault: () => {} } as React.FormEvent) }}
                      >
                        {suggestion}
                      </Button>
                    ))}
                  </div>
                </div>
              ) : (
                messages.map((msg, index) => (
                  <div
                    key={msg.id}
                    className='flex gap-3 animate-fade-in'
                    style={{ animationDelay: `${index * 50}ms` }}
                  >
                    <div className='flex h-10 w-10 items-center justify-center rounded-full flex-shrink-0'>
                      {msg.role === 'user' ? (
                        <MessageSquare className='h-4 w-4' />
                      ) : (
                        <Database className='h-4 w-4 text-muted-foreground' />
                      )}
                    </div>
                    <div className='max-w-[70%]'>
                      <div className='inline-block px-4 py-2 rounded-2xl'>
                        <p className='text-sm whitespace-pre-wrap'>{msg.content}</p>
                      </div>
                      {(msg.statements && msg.statements.length > 0) && (
                        <div className='mt-2 space-y-1'>
                          {msg.statements.map((stmt, i) => (
                            <div key={i} className='flex items-center gap-2 text-xs text-muted-foreground'>
                              <Badge variant='outline' className='text-xs'>{stmt.type}</Badge>
                              {stmt.field && <span>{stmt.field}</span>}
                              {stmt.op && <span>{stmt.op}</span>}
                              <Button 
                                variant='ghost' 
                                size='icon' 
                                className='h-6 w-6 p-0 hover:scale-110 transition-transform'
                                onClick={() => setShowQuery(JSON.stringify(stmt, null, 2))}
                              >
                                <TableIcon className='h-3 w-3' />
                              </Button>
                            </div>
                          ))}
                        </div>
                      )}
                      {(msg.results && msg.results.length > 0) && (
                        <div className='mt-2 space-y-1'>
                          {msg.results.map((result, i) => (
                            <div key={i} className='text-xs text-muted-foreground font-mono bg-background p-2 rounded border max-h-40 overflow-auto animate-fade-in'>
                              {result.error ? (
                                <span className='text-destructive'>Error: {result.error}</span>
                              ) : result.data ? (
                                <pre>{JSON.stringify(result.data, null, 2)}</pre>
                              ) : result.summary ? (
                                result.summary
                              ) : null}
                            </div>
                          ))}
                        </div>
                      )}
                      <p className='mt-1 text-xs text-muted-foreground'>{formatDistanceToNow(new Date(msg.created_at), { addSuffix: true })}</p>
                    </div>
                  </div>
                ))
              )}
              {isLoading && <MessageSkeleton />}
            </div>
          </ScrollArea>
          
          <div className='border-t p-4'>
            <form onSubmit={handleSend} className='flex gap-2'>
              <Input
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder={selectedDatasetId ? 'Ask a question about your data...' : 'Select a dataset first'}
                disabled={!selectedDatasetId || isLoading}
                className='flex-1'
                onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(e); }}}
              />
              <Button type='submit' disabled={!message.trim() || !selectedDatasetId || isLoading} size='lg' className='hover:scale-105 transition-transform'>
                {isLoading ? <Loader2 className='h-4 w-4 animate-spin' /> : <Send className='h-4 w-4' />}
              </Button>
            </form>
            <p className='mt-2 text-xs text-muted-foreground text-center'>
              Try: \"Total revenue by month\", \"Top 5 products\", \"Show trend for sales\"
            </p>
          </div>
        </CardContent>
      </Card>

      {showQuery && (
        <div className='fixed inset-0 z-50 flex items-center justify-center bg-black/50 animate-fade-in'>
          <Card className='w-full max-w-md max-h-[80vh] animate-scale-in'>
            <CardHeader>
              <div className='flex items-center justify-between'>
                <CardTitle>Query Details</CardTitle>
                <Button variant='ghost' size='icon' onClick={() => setShowQuery(null)}>
                  <X className='h-4 w-4' />
                </Button>
              </div>
            </CardHeader>
            <CardContent className='p-0'>
              <div className='p-4 bg-muted rounded-lg font-mono text-xs overflow-auto max-h-[60vh]'>
                <pre>{showQuery}</pre>
              </div>
              <div className='flex justify-end gap-2 p-4'>
                <Button variant='outline' onClick={() => { copyToClipboard(showQuery); setShowQuery(null); }}>
                  <Copy className='mr-2 h-4 w-4' />Copy
                </Button>
                <Button onClick={() => setShowQuery(null)}>Close</Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}
