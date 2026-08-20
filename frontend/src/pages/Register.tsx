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

const registerSchema = z.object({
  email: z.string().email('Invalid email address'),
  password: z.string().min(8, 'Password must be at least 8 characters'),
  confirmPassword: z.string(),
  full_name: z.string().min(2, 'Name must be at least 2 characters'),
  org_name: z.string().min(2, 'Organization name must be at least 2 characters'),
}).refine((data) => data.password === data.confirmPassword, {
  message: 'Passwords do not match',
  path: ['confirmPassword'],
})

type RegisterFormData = z.infer<typeof registerSchema>

export function RegisterPage() {
  const navigate = useNavigate()
  const { register: registerUser, isLoading } = useAuthStore()
  const [showPassword, setShowPassword] = React.useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
  })

  const onSubmit = async (data: RegisterFormData) => {
    try {
      await registerUser({
        email: data.email,
        password: data.password,
        full_name: data.full_name,
        org_name: data.org_name,
      })
      toast.success('Account created successfully!')
      navigate('/dashboard')
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : 'Registration failed'
      toast.error(message)
    }
  }

  return (
    <div className='min-h-screen flex items-center justify-center bg-muted/50 px-4 py-12'>
      <Card className='w-full max-w-md animate-scale-in'>
        <CardHeader className='text-center'>
          <div className='mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-lg bg-primary'>
            <LayoutDashboard className='h-7 w-7 text-primary-foreground' />
          </div>
          <CardTitle className='text-2xl'>Create your account</CardTitle>
          <CardDescription>Start generating business reports in minutes</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit(onSubmit)} className='space-y-4'>
            <div className='space-y-2'>
              <Label htmlFor='full_name'>Full Name</Label>
              <Input
                id='full_name'
                type='text'
                placeholder='John Doe'
                {...register('full_name')}
                disabled={isLoading}
                aria-invalid={!!errors.full_name}
              />
              {errors.full_name && (
                <p className='text-sm text-destructive'>{errors.full_name.message}</p>
              )}
            </div>
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
              <Label htmlFor='org_name'>Organization Name</Label>
              <Input
                id='org_name'
                type='text'
                placeholder='Acme Inc.'
                {...register('org_name')}
                disabled={isLoading}
                aria-invalid={!!errors.org_name}
              />
              {errors.org_name && (
                <p className='text-sm text-destructive'>{errors.org_name.message}</p>
              )}
            </div>
            <div className='space-y-2'>
              <Label htmlFor='password'>Password</Label>
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
            <div className='space-y-2'>
              <Label htmlFor='confirmPassword'>Confirm Password</Label>
              <Input
                id='confirmPassword'
                type={showPassword ? 'text' : 'password'}
                placeholder='\u2022\u2022\u2022\u2022\u2022\u2022\u2022\u2022'
                {...register('confirmPassword')}
                disabled={isLoading}
                aria-invalid={!!errors.confirmPassword}
              />
              {errors.confirmPassword && (
                <p className='text-sm text-destructive'>{errors.confirmPassword.message}</p>
              )}
            </div>
            <Button type='submit' className='w-full' disabled={isLoading}>
              {isLoading ? 'Creating account...' : 'Create account'}
            </Button>
          </form>
        </CardContent>
        <CardFooter className='flex flex-col gap-4'>
          <p className='text-center text-sm text-muted-foreground'>
            Already have an account?{' '}
            <Link to='/login' className='text-primary hover:underline font-medium'>
              Sign in
            </Link>
          </p>
        </CardFooter>
      </Card>
    </div>
  )
}
