'use client'

import * as React from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { toast } from 'react-hot-toast'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { api } from '@/api/client'
import { LayoutDashboard, Mail, ArrowLeft } from 'lucide-react'

const forgotPasswordSchema = z.object({
  email: z.string().email('Invalid email address'),
})

type ForgotPasswordFormData = z.infer<typeof forgotPasswordSchema>

export function ForgotPasswordPage() {
  const navigate = useNavigate()
  const [isLoading, setIsLoading] = React.useState(false)
  const [step, setStep] = React.useState<'email' | 'success'>('email')

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<ForgotPasswordFormData>({
    resolver: zodResolver(forgotPasswordSchema),
  })

  const onSubmit = async (data: ForgotPasswordFormData) => {
    setIsLoading(true)
    try {
      await api.post('/auth/forgot-password', { email: data.email })
      setStep('success')
      toast.success('Password reset email sent!')
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : 'Failed to send reset email'
      toast.error(message)
    } finally {
      setIsLoading(false)
    }
  }

  if (step === 'success') {
    return (
      <div className='min-h-screen flex items-center justify-center bg-muted/50 px-4'>
        <Card className='w-full max-w-md'>
          <CardHeader className='text-center'>
            <div className='mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-lg bg-green-500'>
              <Mail className='h-7 w-7 text-white' />
            </div>
            <CardTitle className='text-2xl'>Check your email</CardTitle>
            <CardDescription>
              We've sent password reset instructions to your email address.
            </CardDescription>
          </CardHeader>
          <CardContent className='text-center'>
            <p className='text-muted-foreground mb-6'>
              If you don't see the email, check your spam folder or try again.
            </p>
            <Button asChild variant='outline' className='w-full'>
              <Link to='/login'>
                <ArrowLeft className='mr-2 h-4 w-4' />
                Back to Sign In
              </Link>
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className='min-h-screen flex items-center justify-center bg-muted/50 px-4'>
      <Card className='w-full max-w-md'>
        <CardHeader className='text-center'>
          <Link to='/' className='inline-flex mb-4'>
            <div className='flex h-12 w-12 items-center justify-center rounded-lg bg-primary'>
              <LayoutDashboard className='h-7 w-7 text-primary-foreground' />
            </div>
          </Link>
          <CardTitle className='text-2xl'>Forgot password?</CardTitle>
          <CardDescription>
            Enter your email and we'll send you reset instructions
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit(onSubmit)} className='space-y-4'>
            <div className='space-y-2'>
              <Label htmlFor='email'>Email</Label>
              <Input
                id='email'
                type='email'
                placeholder='you@example.com'
                {...register('email')}
                disabled={isLoading}
                aria-invalid={!!errors.email}
              />
              {errors.email && (
                <p className='text-sm text-destructive'>{errors.email.message}</p>
              )}
            </div>
            <Button type='submit' className='w-full' disabled={isLoading}>
              {isLoading ? 'Sending...' : 'Send reset link'}
            </Button>
          </form>
        </CardContent>
        <CardFooter className='flex flex-col gap-4'>
          <p className='text-center text-sm text-muted-foreground'>
            Remember your password?{' '}
            <Link to='/login' className='text-primary hover:underline font-medium'>
              Sign in
            </Link>
          </p>
        </CardFooter>
      </Card>
    </div>
  )
}
