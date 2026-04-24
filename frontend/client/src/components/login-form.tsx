import { useState, useMemo, useId } from "react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Alert, AlertDescription } from "@/components/ui/alert"
import {
  Loader2, AlertCircle, Shield, Database, FileText, BarChart3,
  Eye, EyeOff, CheckCircle,
} from "lucide-react"

// ── Value Visualization (right panel) ────────────────────────────────────────
function ValueVisualization() {
  return (
    <div className="flex h-full flex-col items-center justify-center gap-8 p-8">
      <div className="text-center">
        <h2 className="text-xl font-semibold text-white leading-tight mb-2">
          Build a defensible business case — automatically.
        </h2>
        <p className="text-sm text-white/60 leading-relaxed">
          From discovery to boardroom approval, Value Fabric transforms inputs
          into quantified, evidence-backed value.
        </p>
      </div>
      <div className="flex justify-center gap-6">
        {[
          { Icon: Database, label: "CRM" },
          { Icon: FileText, label: "Transcripts" },
          { Icon: BarChart3, label: "Benchmarks" },
        ].map(({ Icon, label }) => (
          <div key={label} className="flex flex-col items-center gap-2">
            <div className="w-10 h-10 rounded-lg bg-white/10 flex items-center justify-center">
              <Icon className="w-5 h-5 text-white/70" aria-hidden="true" />
            </div>
            <span className="text-[10px] text-white/50 uppercase tracking-wider">{label}</span>
          </div>
        ))}
      </div>
      <div className="relative flex items-center justify-center">
        <div className="absolute w-48 h-48 rounded-full border border-white/10" />
        <div className="relative z-10 text-center">
          <p className="text-[10px] text-white/50 uppercase tracking-widest mb-2">Annual Value</p>
          <p className="text-3xl font-bold text-white tracking-tight">$2.4M</p>
          <div className="mt-3 inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-500/20 border border-emerald-500/30">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
            <span className="text-[10px] font-medium text-emerald-400">Confidence: 82%</span>
          </div>
        </div>
      </div>
      <div className="flex justify-center gap-6">
        {[
          { color: "bg-violet-400", label: "Revenue Uplift" },
          { color: "bg-white/60", label: "Cost Savings" },
          { color: "bg-amber-400", label: "Risk Reduction" },
        ].map(({ color, label }) => (
          <div key={label} className="flex items-center gap-2">
            <span className={cn("w-2 h-2 rounded-full", color)} />
            <span className="text-[10px] text-white/60 uppercase tracking-wider">{label}</span>
          </div>
        ))}
      </div>
      <div className="flex items-start gap-3 px-4 py-3 rounded-lg bg-white/5 border border-white/10 max-w-xs">
        <Shield className="w-4 h-4 text-white/50 flex-shrink-0 mt-0.5" aria-hidden="true" />
        <p className="text-[10px] text-white/50 leading-relaxed">
          Every projection is linked to source data and validated assumptions for total auditability.
        </p>
      </div>
    </div>
  )
}

// ── SVG Icons ────────────────────────────────────────────────────────────────
function GoogleIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" aria-hidden="true">
      <path
        d="M12.48 10.92v3.28h7.84c-.24 1.84-.853 3.187-1.787 4.133-1.147 1.147-2.933 2.4-6.053 2.4-4.827 0-8.6-3.893-8.6-8.72s3.773-8.72 8.6-8.72c2.6 0 4.507 1.027 5.907 2.347l2.307-2.307C18.747 1.44 16.133 0 12.48 0 5.867 0 .307 5.387.307 12s5.56 12 12.173 12c3.573 0 6.267-1.173 8.373-3.36 2.16-2.16 2.84-5.213 2.84-7.667 0-.76-.053-1.467-.173-2.053H12.48z"
        fill="currentColor"
      />
    </svg>
  )
}

function MicrosoftIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" aria-hidden="true">
      <path d="M0 0h11.5v11.5H0V0zm12.5 0H24v11.5H12.5V0zM0 12.5h11.5V24H0V12.5zm12.5 0H24V24H12.5V12.5z" fill="currentColor" />
    </svg>
  )
}

// ── Password toggle hook ─────────────────────────────────────────────────────
function usePasswordToggle() {
  const [visible, setVisible] = useState(false)
  const toggle = () => setVisible(v => !v)
  const inputType = visible ? "text" : "password"
  const Icon = visible ? EyeOff : Eye
  const label = visible ? "Hide password" : "Show password"
  return { visible, toggle, inputType, Icon, label } as const
}

// ── Password strength meter ──────────────────────────────────────────────────
function getPasswordStrength(pw: string): { score: number; label: string; color: string } {
  let score = 0
  if (pw.length >= 8) score++
  if (pw.length >= 12) score++
  if (/[a-z]/.test(pw) && /[A-Z]/.test(pw)) score++
  if (/\d/.test(pw)) score++
  if (/[^a-zA-Z0-9]/.test(pw)) score++

  if (score <= 1) return { score, label: "Weak", color: "bg-destructive" }
  if (score <= 2) return { score, label: "Fair", color: "bg-amber-500" }
  if (score <= 3) return { score, label: "Good", color: "bg-yellow-500" }
  return { score, label: "Strong", color: "bg-emerald-500" }
}

function PasswordStrength({ password }: { password: string }) {
  const strength = getPasswordStrength(password)
  if (!password) return null
  return (
    <div className="space-y-1" aria-live="polite">
      <div className="flex gap-1">
        {[1, 2, 3, 4].map(i => (
          <div
            key={i}
            className={cn(
              "h-1 flex-1 rounded-full transition-colors",
              i <= Math.ceil(strength.score * 4 / 5) ? strength.color : "bg-muted"
            )}
          />
        ))}
      </div>
      <p className="text-xs text-muted-foreground">{strength.label}</p>
    </div>
  )
}

// ═══════════════════════════════════════════════════════════════════════════════
// LoginForm — shadcn login-04 layout + OIDC SSO + a11y
// ═══════════════════════════════════════════════════════════════════════════════

/** Props for LoginForm. SSO buttons trigger `onSSOProvider` with a provider key. */
interface LoginFormProps extends React.ComponentProps<"div"> {
  /** Email + password submit handler */
  onLogin?: (email: string, password: string) => Promise<void>
  /** SSO provider button handler — receives "google" | "microsoft" */
  onSSOProvider?: (provider: string) => void
  /** Dev-only bypass button */
  onDevBypass?: () => void
  isLoading?: boolean
  error?: string | null
  successMessage?: string | null
}

export function LoginForm({
  className,
  onLogin,
  onSSOProvider,
  onDevBypass,
  isLoading = false,
  error: externalError = null,
  successMessage = null,
  ...props
}: LoginFormProps) {
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [localError, setLocalError] = useState<string | null>(null)
  const pwToggle = usePasswordToggle()
  const errorId = useId()

  const error = externalError || localError

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLocalError(null)

    if (!email.trim()) {
      setLocalError("Please enter your email address")
      return
    }
    if (!password.trim()) {
      setLocalError("Please enter your password")
      return
    }

    try {
      await onLogin?.(email.trim(), password)
    } catch (err) {
      // Don't clear email on error (UX best practice)
      setLocalError(err instanceof Error ? err.message : "Incorrect password. Please try again or reset it below.")
    }
  }

  return (
    <div className={cn("flex flex-col gap-6", className)} {...props}>
      <Card className="overflow-hidden">
        <CardContent className="grid p-0 md:grid-cols-2">
          <form className="p-6 md:p-8" onSubmit={handleSubmit} noValidate>
            <div className="flex flex-col gap-6">
              <div className="flex flex-col items-center text-center">
                <h1 className="text-2xl font-bold" data-testid="login-heading">Welcome back</h1>
                <p className="text-balance text-muted-foreground">
                  Login to your Value Fabric account
                </p>
              </div>

              {successMessage && (
                <Alert variant="default" className="bg-emerald-500/10 text-emerald-700 border-emerald-500/20" role="status">
                  <CheckCircle className="h-4 w-4 text-emerald-500" aria-hidden="true" />
                  <AlertDescription>{successMessage}</AlertDescription>
                </Alert>
              )}

              {error && (
                <Alert variant="destructive" role="alert" id={errorId}>
                  <AlertCircle className="h-4 w-4" aria-hidden="true" />
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}

              <div className="grid gap-2">
                <Label htmlFor="login-email">Email</Label>
                <Input
                  id="login-email"
                  data-testid="login-email"
                  type="email"
                  placeholder="you@company.com"
                  autoComplete="username"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  disabled={isLoading}
                  required
                  autoFocus
                  aria-describedby={error ? errorId : undefined}
                />
              </div>

              <div className="grid gap-2">
                <div className="flex items-center">
                  <Label htmlFor="login-password">Password</Label>
                  <a
                    href="#"
                    className="ml-auto text-sm underline-offset-2 hover:underline"
                  >
                    Forgot your password?
                  </a>
                </div>
                <div className="relative">
                  <Input
                    id="login-password"
                    data-testid="login-password"
                    type={pwToggle.inputType}
                    autoComplete="current-password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    disabled={isLoading}
                    required
                    className="pr-10"
                    aria-describedby={error ? errorId : undefined}
                  />
                  <button
                    type="button"
                    data-testid="password-toggle"
                    onClick={pwToggle.toggle}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                    aria-label={pwToggle.label}
                    tabIndex={-1}
                  >
                    <pwToggle.Icon className="h-4 w-4" />
                  </button>
                </div>
              </div>

              <Button type="submit" data-testid="login-submit" className="w-full" disabled={isLoading}>
                {isLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" aria-hidden="true" />
                    Signing in...
                  </>
                ) : (
                  "Login"
                )}
              </Button>

              <div className="relative text-center text-sm after:absolute after:inset-0 after:top-1/2 after:z-0 after:flex after:items-center after:border-t after:border-border">
                <span className="relative z-10 bg-background px-2 text-muted-foreground">
                  Or continue with
                </span>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <Button
                  variant="outline"
                  data-testid="sso-google"
                  className="w-full"
                  type="button"
                  disabled={isLoading}
                  onClick={() => onSSOProvider?.("google")}
                >
                  <GoogleIcon />
                  <span className="ml-2">Google</span>
                </Button>
                <Button
                  variant="outline"
                  data-testid="sso-microsoft"
                  className="w-full"
                  type="button"
                  disabled={isLoading}
                  onClick={() => onSSOProvider?.("microsoft")}
                >
                  <MicrosoftIcon />
                  <span className="ml-2">Microsoft</span>
                </Button>
              </div>

              {import.meta.env.DEV && onDevBypass && (
                <Button
                  variant="ghost"
                  type="button"
                  size="sm"
                  className="w-full text-xs text-muted-foreground hover:text-primary"
                  onClick={onDevBypass}
                >
                  Development Bypass
                </Button>
              )}

              <div className="text-center text-sm">
                Don&apos;t have an account?{" "}
                <a href="/signup" data-testid="link-to-signup" className="underline underline-offset-4">
                  Sign up
                </a>
              </div>
            </div>
          </form>
          <div className="relative hidden bg-slate-900 md:block">
            <div className="absolute inset-0 bg-gradient-to-br from-slate-800/50 via-slate-900 to-slate-950" />
            <div className="relative z-10 h-full">
              <ValueVisualization />
            </div>
          </div>
        </CardContent>
      </Card>
      <div className="text-balance text-center text-xs text-muted-foreground [&_a]:underline [&_a]:underline-offset-4 hover:[&_a]:text-primary">
        By clicking continue, you agree to our <a href="#">Terms of Service</a>{" "}
        and <a href="#">Privacy Policy</a>.
      </div>
    </div>
  )
}

// ═══════════════════════════════════════════════════════════════════════════════
// SignupForm — shadcn login-04 layout + password strength + a11y
// ═══════════════════════════════════════════════════════════════════════════════

/** Props for SignupForm. SSO buttons trigger `onSSOProvider`. */
interface SignupFormProps extends React.ComponentProps<"div"> {
  onSignup?: (data: { email: string; password: string }) => Promise<void>
  onSSOProvider?: (provider: string) => void
  isLoading?: boolean
  error?: string | null
}

export function SignupForm({
  className,
  onSignup,
  onSSOProvider,
  isLoading = false,
  error: externalError = null,
  ...props
}: SignupFormProps) {
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [localError, setLocalError] = useState<string | null>(null)
  const pwToggle = usePasswordToggle()
  const errorId = useId()
  const strengthId = useId()

  const error = externalError || localError
  const strength = useMemo(() => getPasswordStrength(password), [password])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLocalError(null)

    if (!email.trim()) {
      setLocalError("Please enter your email address")
      return
    }
    if (!password.trim()) {
      setLocalError("Please enter a password")
      return
    }
    if (password.length < 8) {
      setLocalError("Password must be at least 8 characters")
      return
    }
    if (strength.score <= 1) {
      setLocalError("Password is too weak. Add uppercase letters, numbers, or symbols.")
      return
    }

    try {
      await onSignup?.({ email: email.trim(), password })
    } catch (err) {
      setLocalError(err instanceof Error ? err.message : "Registration failed. Please try again.")
    }
  }

  return (
    <div className={cn("flex flex-col gap-6", className)} {...props}>
      <Card className="overflow-hidden">
        <CardContent className="grid p-0 md:grid-cols-2">
          <form className="p-6 md:p-8" onSubmit={handleSubmit} noValidate>
            <div className="flex flex-col gap-6">
              <div className="flex flex-col items-center text-center">
                <h1 className="text-2xl font-bold" data-testid="signup-heading">Create your account</h1>
                <p className="text-balance text-muted-foreground">
                  Get started with Value Fabric — it&apos;s free
                </p>
              </div>

              {error && (
                <Alert variant="destructive" role="alert" id={errorId}>
                  <AlertCircle className="h-4 w-4" aria-hidden="true" />
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}

              <div className="grid gap-2">
                <Label htmlFor="signup-email">Email</Label>
                <Input
                  id="signup-email"
                  data-testid="signup-email"
                  type="email"
                  placeholder="you@company.com"
                  autoComplete="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  disabled={isLoading}
                  required
                  autoFocus
                  aria-describedby={error ? errorId : undefined}
                />
              </div>

              <div className="grid gap-2">
                <Label htmlFor="signup-password">Password</Label>
                <div className="relative">
                  <Input
                    id="signup-password"
                    data-testid="signup-password"
                    type={pwToggle.inputType}
                    autoComplete="new-password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    disabled={isLoading}
                    required
                    className="pr-10"
                    aria-describedby={cn(strengthId, error ? errorId : "")}
                  />
                  <button
                    type="button"
                    data-testid="signup-password-toggle"
                    onClick={pwToggle.toggle}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                    aria-label={pwToggle.label}
                    tabIndex={-1}
                  >
                    <pwToggle.Icon className="h-4 w-4" />
                  </button>
                </div>
                <div id={strengthId}>
                  <PasswordStrength password={password} />
                  {!password && (
                    <p className="text-xs text-muted-foreground">Must be at least 8 characters.</p>
                  )}
                </div>
              </div>

              <Button type="submit" data-testid="signup-submit" className="w-full" disabled={isLoading}>
                {isLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" aria-hidden="true" />
                    Creating account...
                  </>
                ) : (
                  "Create Account"
                )}
              </Button>

              <div className="relative text-center text-sm after:absolute after:inset-0 after:top-1/2 after:z-0 after:flex after:items-center after:border-t after:border-border">
                <span className="relative z-10 bg-background px-2 text-muted-foreground">
                  Or continue with
                </span>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <Button
                  variant="outline"
                  className="w-full"
                  type="button"
                  disabled={isLoading}
                  onClick={() => onSSOProvider?.("google")}
                >
                  <GoogleIcon />
                  <span className="ml-2">Google</span>
                </Button>
                <Button
                  variant="outline"
                  className="w-full"
                  type="button"
                  disabled={isLoading}
                  onClick={() => onSSOProvider?.("microsoft")}
                >
                  <MicrosoftIcon />
                  <span className="ml-2">Microsoft</span>
                </Button>
              </div>

              <div className="text-center text-sm">
                Already have an account?{" "}
                <a href="/login" className="underline underline-offset-4">
                  Sign in
                </a>
              </div>
            </div>
          </form>
          <div className="relative hidden bg-slate-900 md:block">
            <div className="absolute inset-0 bg-gradient-to-br from-slate-800/50 via-slate-900 to-slate-950" />
            <div className="relative z-10 h-full">
              <ValueVisualization />
            </div>
          </div>
        </CardContent>
      </Card>
      <div className="text-balance text-center text-xs text-muted-foreground [&_a]:underline [&_a]:underline-offset-4 hover:[&_a]:text-primary">
        By clicking continue, you agree to our <a href="#">Terms of Service</a>{" "}
        and <a href="#">Privacy Policy</a>.
      </div>
    </div>
  )
}
