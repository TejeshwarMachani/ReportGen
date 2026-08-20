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
  Users, 
  Plus, 
  Mail, 
  UserPlus,
  Shield,
  UserCheck,
  UserX,
  ChevronDown,
  Loader2,
  MoreHorizontal
} from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'

interface TeamMember {
  id: string
  email: string
  full_name: string | null
  role: string
  is_active: boolean
  created_at: string
}

interface InviteRequest {
  email: string
  role: string
}

const TableRowSkeleton = () => (
  <TableRow>
    <TableCell><Skeleton className='h-4 w-1/2' /></TableCell>
    <TableCell><Skeleton className='h-5 w-20' /></TableCell>
    <TableCell><Skeleton className='h-5 w-20' /></TableCell>
    <TableCell><Skeleton className='h-4 w-28' /></TableCell>
    <TableCell className='text-right'><Skeleton className='h-8 w-8' /></TableCell>
  </TableRow>
)

export function TeamPage() {
  const queryClient = useQueryClient()
  const [inviteDialogOpen, setInviteDialogOpen] = React.useState(false)
  const [inviteEmail, setInviteEmail] = React.useState('')
  const [inviteRole, setInviteRole] = React.useState('member')

  const { data: members, isLoading } = useQuery({
    queryKey: ['team-members'],
    queryFn: () => api.get<TeamMember[]>('/team'),
  })

  const inviteMutation = useMutation({
    mutationFn: (data: InviteRequest) => api.post('/team/invite', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['team-members'] })
      toast.success('Invitation sent')
      setInviteDialogOpen(false)
      setInviteEmail('')
    },
    onError: (error: unknown) => {
      const message = error instanceof Error ? error.message : 'Failed to send invitation'
      toast.error(message)
    },
  })

  const updateRoleMutation = useMutation({
    mutationFn: ({ userId, role }: { userId: string; role: string }) => 
      api.patch(\/team/\/role\, { new_role: role }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['team-members'] })
      toast.success('Role updated')
    },
    onError: (error: unknown) => {
      const message = error instanceof Error ? error.message : 'Failed to update role'
      toast.error(message)
    },
  })

  const removeMutation = useMutation({
    mutationFn: (userId: string) => api.delete(\/team/\\),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['team-members'] })
      toast.success('User removed')
    },
    onError: (error: unknown) => {
      const message = error instanceof Error ? error.message : 'Failed to remove user'
      toast.error(message)
    },
  })

  const getRoleBadge = (role: string) => {
    switch (role) {
      case 'owner':
        return <Badge variant='default'><Shield className='mr-1 h-3 w-3' /> Owner</Badge>
      case 'admin':
        return <Badge variant='secondary'><UserCheck className='mr-1 h-3 w-3' /> Admin</Badge>
      case 'member':
        return <Badge variant='outline'><Users className='mr-1 h-3 w-3' /> Member</Badge>
      case 'viewer':
        return <Badge variant='outline'><UserCheck className='mr-1 h-3 w-3' /> Viewer</Badge>
      default:
        return <Badge variant='outline'>{role}</Badge>
    }
  }

  const handleInvite = () => {
    if (inviteEmail.trim()) {
      inviteMutation.mutate({ email: inviteEmail, role: inviteRole })
    }
  }

  const handleRoleChange = (userId: string, newRole: string) => {
    updateRoleMutation.mutate({ userId, role: newRole })
  }

  const handleRemove = (userId: string, email: string) => {
    if (confirm(\Are you sure you want to remove \ from the organization?\)) {
      removeMutation.mutate(userId)
    }
  }

  const roles = [
    { value: 'owner', label: 'Owner', icon: Shield },
    { value: 'admin', label: 'Admin', icon: UserCheck },
    { value: 'member', label: 'Member', icon: Users },
    { value: 'viewer', label: 'Viewer', icon: UserCheck },
  ]

  return (
    <div className='space-y-6 animate-fade-in'>
      <div className='flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4'>
        <div>
          <h1 className='text-3xl font-bold tracking-tight flex items-center gap-2'>
            <Users className='h-8 w-8 text-primary' />
            Team Management
          </h1>
          <p className='text-muted-foreground'>Manage organization members and their roles</p>
        </div>
        <Dialog open={inviteDialogOpen} onOpenChange={setInviteDialogOpen}>
          <DialogTrigger asChild>
            <Button className='animate-scale-in hover:scale-105 transition-transform'><UserPlus className='mr-2 h-4 w-4' />Invite Member</Button>
          </DialogTrigger>
          <DialogContent className='animate-scale-in'>
            <DialogHeader>
              <DialogTitle>Invite Team Member</DialogTitle>
            </DialogHeader>
            <div className='space-y-4 py-4'>
              <div className='space-y-2'>
                <Label htmlFor='invite-email'>Email Address</Label>
                <Input
                  id='invite-email'
                  type='email'
                  placeholder='colleague@example.com'
                  value={inviteEmail}
                  onChange={(e) => setInviteEmail(e.target.value)}
                />
              </div>
              <div className='space-y-2'>
                <Label htmlFor='invite-role'>Role</Label>
                <Select value={inviteRole} onValueChange={setInviteRole}>
                  <SelectTrigger id='invite-role'>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {roles.filter(r => r.value !== 'owner').map((r) => (
                      <SelectItem key={r.value} value={r.value}>{r.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
            <DialogFooter className='flex justify-end gap-2'>
              <Button variant='outline' onClick={() => { setInviteDialogOpen(false); setInviteEmail(''); }}>Cancel</Button>
              <Button onClick={handleInvite} disabled={inviteMutation.isPending || !inviteEmail.trim()}>
                {inviteMutation.isPending ? 'Sending...' : 'Send Invitation'}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      <Card className='hover-lift'>
        <CardHeader>
          <CardTitle>Team Members</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Member</TableHead>
                  <TableHead>Role</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Joined</TableHead>
                  <TableHead className='text-right'>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {[1, 2, 3, 4, 5].map((i) => (
                  <TableRowSkeleton key={i} style={{ animationDelay: \ms }} />
                ))}
              </TableBody>
            </Table>
          ) : members?.length === 0 ? (
            <div className='text-center py-12 animate-fade-in'>
              <Users className='mx-auto h-12 w-12 text-muted-foreground' />
              <h3 className='mt-4 text-lg font-medium'>No team members yet</h3>
              <p className='mt-2 text-muted-foreground'>Invite colleagues to collaborate on reports and data</p>
              <Button className='mt-4' onClick={() => setInviteDialogOpen(true)}>
                <UserPlus className='mr-2 h-4 w-4' />Invite Member
              </Button>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Member</TableHead>
                  <TableHead>Role</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Joined</TableHead>
                  <TableHead className='text-right'>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {members?.map((member, index) => (
                  <TableRow key={member.id} className='animate-fade-in hover:bg-accent/50 transition-colors' style={{ animationDelay: \ms }}>
                    <TableCell>
                      <div className='flex items-center gap-3'>
                        <div className='flex h-10 w-10 items-center justify-center rounded-full bg-muted'>
                          <span className='font-medium text-muted-foreground'>
                            {member.full_name?.[0] || member.email[0].toUpperCase()}
                          </span>
                        </div>
                        <div>
                          <p className='font-medium'>{member.full_name || member.email}</p>
                          <p className='text-sm text-muted-foreground'>{member.email}</p>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant='outline' size='sm' className='gap-1 hover:scale-105 transition-transform'>
                            {member.role.charAt(0).toUpperCase() + member.role.slice(1)}
                            <ChevronDown className='h-3 w-3' />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align='end' className='animate-scale-in'>
                          {roles.map((role) => (
                            <DropdownMenuItem 
                              key={role.value}
                              onClick={() => handleRoleChange(member.id, role.value)} 
                              disabled={member.role === role.value}
                            >
                              <role.icon className='mr-2 h-4 w-4' />
                              {role.label}
                            </DropdownMenuItem>
                          ))}
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </TableCell>
                    <TableCell>
                      <Badge variant={member.is_active ? 'default' : 'secondary'} className='animate-scale-in'>
                        {member.is_active ? 'Active' : 'Inactive'}
                      </Badge>
                    </TableCell>
                    <TableCell>{formatDistanceToNow(new Date(member.created_at), { addSuffix: true })}</TableCell>
                    <TableCell className='text-right'>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant='ghost' size='icon' className='h-8 w-8'>
                            <MoreHorizontal className='h-4 w-4' />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align='end' className='animate-scale-in'>
                          <DropdownMenuItem onClick={() => handleRemove(member.id, member.email)} className='text-destructive focus:text-destructive'>
                            <UserX className='mr-2 h-4 w-4' />Remove from Organization
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
