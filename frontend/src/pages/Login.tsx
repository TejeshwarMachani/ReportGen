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
import { useAuthStore } from '@/store/authStore'
import { LayoutDashboard } from 'lucide-react'

const loginSchema = z.object({
  email: z.string().email('Invalid email address'),
  password: z.string().min(8, 'Password must be at least 8 characters'),
})

type LoginFormData = z.infer<typeof loginSchema>

export function LoginPage() {
  const navigate = useNavigate()
  const { login, isLoading } = useAuthStore()
  const [showPassword, setShowPassword] = React.useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
  })

  const onSubmit = async (data: LoginFormData) => {
    try {
      await login(data.email, data.password)
      toast.success('Welcome back!')
      navigate('/dashboard')
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : 'Invalid credentials'
      toast.error(message)
    }
  }

  return (
    <div className='min-h-screen flex items-center justify-center bg-muted/50 px-4'>
      <Card className='w-full max-w-md animate-scale-in'>
        <CardHeader className='text-center'>
          <div className='mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-lg bg-primary'>
            <LayoutDashboard className='h-7 w-7 text-primary-foreground' />
          </div>
          <CardTitle className='text-2xl'>Welcome back</CardTitle>
          <CardDescription>Sign in to your ReportGen account</CardDescription>
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
            <div className='space-y-2'>
              <div className='flex items-center justify-between'>
                <Label htmlFor='password'>Password</Label>
                <Link to='/forgot-password' className='text-sm text-primary hover:underline'>
                  Forgot password?
                </Link>
              </div>
              <Input
                id='password'
                type={showPassword ? 'text' : 'password'}
                placeholder='\u2022\u2022\u2022\u2022\u2022\u2022\u2022\u2022'
                {...register('password')}
                disabled={isLoading}
                aria-invalid={!!errors.password}
              />
              {errors.password && (
                <p className='text-sm text-destructive'>{errors.password.message}</p>
              )}
              <label className='flex items-center gap-2 text-sm'>
                <input
                  type='checkbox'
                  checked={showPassword}
                  onChange={(e) => setShowPassword(e.target.checked)}
                  className='rounded border-input'
                />
                Show password
              </label>
            </div>
            <Button type='submit' className='w-full' disabled={isLoading}>
              {isLoading ? 'Signing in...' : 'Sign in'}
            </Button>
          </form>
        </CardContent>
        <CardFooter className='flex flex-col gap-4'>
          <p className='text-center text-sm text-muted-foreground'>
            Don't have an account?{' '}
            <Link to='/register' className='text-primary hover:underline font-medium'>
              Sign up
            </Link>
          </p>
        </CardFooter>
      </Card>
    </div>
  )
}
