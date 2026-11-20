import { Route, Routes } from 'react-router-dom'

import { AppShell } from '@/components/layout/app-shell'
import { AuthLayout } from '@/components/layout/auth-layout'
import { PublicOnly, RequireAdmin, RequireAuth } from '@/components/route-guards'
import { Toaster } from '@/components/ui/sonner'
import { AdminAuditPage } from '@/pages/admin/audit-page'
import { AdminUsersPage } from '@/pages/admin/users-page'
import { ApiDocsPage } from '@/pages/api-docs-page'
import { ApiKeysPage } from '@/pages/api-keys-page'
import { ForgotPasswordPage } from '@/pages/auth/forgot-password-page'
import { LoginPage } from '@/pages/auth/login-page'
import { RegisterPage } from '@/pages/auth/register-page'
import { ResendVerificationPage } from '@/pages/auth/resend-verification-page'
import { ResetPasswordPage } from '@/pages/auth/reset-password-page'
import { TwoFactorPage } from '@/pages/auth/two-factor-page'
import { VerifyEmailPage } from '@/pages/auth/verify-email-page'
import { DashboardPage } from '@/pages/dashboard-page'
import { LandingPage } from '@/pages/landing-page'
import { NotFoundPage } from '@/pages/not-found-page'
import { SecurityPage } from '@/pages/security-page'

export default function App() {
  return (
    <>
      <Routes>
        <Route element={<AuthLayout />}>
          <Route element={<PublicOnly />}>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
          </Route>
          <Route path="/forgot-password" element={<ForgotPasswordPage />} />
          <Route path="/reset-password" element={<ResetPasswordPage />} />
          <Route path="/verify-email" element={<VerifyEmailPage />} />
          <Route path="/resend-verification" element={<ResendVerificationPage />} />
          <Route path="/two-factor" element={<TwoFactorPage />} />
        </Route>

        <Route element={<RequireAuth />}>
          <Route element={<AppShell />}>
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/security" element={<SecurityPage />} />
            <Route path="/api-keys" element={<ApiKeysPage />} />
            <Route element={<RequireAdmin />}>
              <Route path="/admin/users" element={<AdminUsersPage />} />
              <Route path="/admin/audit" element={<AdminAuditPage />} />
            </Route>
          </Route>
        </Route>

        <Route path="/" element={<LandingPage />} />
        <Route path="/docs" element={<ApiDocsPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Routes>

      <Toaster position="top-right" richColors closeButton />
    </>
  )
}
