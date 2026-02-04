'use client';

import { useRouter } from 'next/navigation';
import { useEffect } from 'react';
import LoginForm from '@/components/auth/LoginForm';
import { useAuth } from '@/lib/auth-context';

export default function LoginPage() {
  const router = useRouter();
  const { isAuthenticated, isLoading } = useAuth();

  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      router.push('/dashboard');
    }
  }, [isAuthenticated, isLoading, router]);

  if (isLoading) {
    return (
      <div
        className="min-h-screen flex items-center justify-center"
        style={{ background: 'var(--color-bg-primary)' }}
      >
        <div className="relative">
          <div
            className="w-12 h-12 rounded-full animate-spin"
            style={{
              border: '3px solid var(--color-bg-tertiary)',
              borderTopColor: 'var(--color-accent)'
            }}
          />
        </div>
      </div>
    );
  }

  return (
    <div
      className="min-h-screen flex bg-mesh noise-bg"
      style={{ background: 'var(--color-bg-primary)' }}
    >
      {/* Left Panel - Branding */}
      <div className="hidden lg:flex lg:w-1/2 relative overflow-hidden">
        {/* Gradient Overlay */}
        <div
          className="absolute inset-0"
          style={{
            background: `
              radial-gradient(ellipse at 30% 20%, rgba(0, 212, 255, 0.15) 0%, transparent 50%),
              radial-gradient(ellipse at 70% 80%, rgba(0, 255, 136, 0.1) 0%, transparent 50%)
            `
          }}
        />

        {/* Content */}
        <div className="relative z-10 flex flex-col justify-between p-12 w-full">
          {/* Logo */}
          <div className="flex items-center gap-3">
            <div
              className="w-12 h-12 rounded-xl flex items-center justify-center"
              style={{ background: 'var(--gradient-accent)' }}
            >
              <svg className="w-6 h-6" style={{ color: 'var(--color-bg-primary)' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <span className="text-xl font-semibold" style={{ color: 'var(--color-text-primary)' }}>
              LLM Council
            </span>
          </div>

          {/* Hero Text */}
          <div className="max-w-md">
            <h1
              className="text-5xl font-bold leading-tight tracking-tight mb-6"
              style={{ color: 'var(--color-text-primary)' }}
            >
              Orchestrate
              <br />
              <span className="text-gradient">AI Intelligence</span>
            </h1>
            <p className="text-lg leading-relaxed" style={{ color: 'var(--color-text-secondary)' }}>
              Multi-agent collaboration platform for enterprise AI.
              Harness the power of multiple LLMs working together.
            </p>
          </div>

          {/* Features */}
          <div className="space-y-4">
            {[
              { icon: '⚡', text: 'Multiple LLMs in parallel' },
              { icon: '🔍', text: 'RAG-augmented responses' },
              { icon: '🎯', text: 'Peer review consensus' },
            ].map((feature, i) => (
              <div
                key={i}
                className="flex items-center gap-3 animate-slide-in-left"
                style={{ animationDelay: `${i * 100 + 300}ms` }}
              >
                <span className="text-2xl">{feature.icon}</span>
                <span style={{ color: 'var(--color-text-secondary)' }}>{feature.text}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Decorative Elements */}
        <div
          className="absolute -right-32 top-1/4 w-64 h-64 rounded-full blur-3xl"
          style={{ background: 'var(--color-accent-muted)' }}
        />
        <div
          className="absolute -left-32 bottom-1/4 w-64 h-64 rounded-full blur-3xl"
          style={{ background: 'var(--color-success-muted)' }}
        />
      </div>

      {/* Right Panel - Form */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-8">
        <div className="w-full max-w-md animate-scale-in">
          {/* Mobile Logo */}
          <div className="lg:hidden flex items-center justify-center gap-3 mb-10">
            <div
              className="w-10 h-10 rounded-xl flex items-center justify-center"
              style={{ background: 'var(--gradient-accent)' }}
            >
              <svg className="w-5 h-5" style={{ color: 'var(--color-bg-primary)' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <span className="text-lg font-semibold" style={{ color: 'var(--color-text-primary)' }}>
              LLM Council
            </span>
          </div>

          {/* Header */}
          <div className="text-center mb-8">
            <h2
              className="text-2xl font-bold tracking-tight"
              style={{ color: 'var(--color-text-primary)' }}
            >
              Welcome back
            </h2>
            <p className="mt-2" style={{ color: 'var(--color-text-muted)' }}>
              Sign in to access your dashboard
            </p>
          </div>

          {/* Form Card */}
          <div
            className="rounded-2xl p-8"
            style={{
              background: 'var(--color-bg-secondary)',
              border: '1px solid var(--color-border)',
              boxShadow: 'var(--shadow-lg)'
            }}
          >
            <LoginForm onSwitchToRegister={() => router.push('/register')} />
          </div>

          {/* Footer */}
          <p className="text-center mt-6 text-sm" style={{ color: 'var(--color-text-muted)' }}>
            Don&apos;t have an account?{' '}
            <button
              onClick={() => router.push('/register')}
              className="font-medium transition-colors"
              style={{ color: 'var(--color-accent)' }}
            >
              Sign up
            </button>
          </p>
        </div>
      </div>
    </div>
  );
}
