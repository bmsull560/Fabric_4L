# Mobile Navigation Integration

## Overview

The mobile navigation system replaces the standard 240px desktop sidebar with a **persistent 80px icon rail** on viewports below the `md` breakpoint (768px). It explicitly avoids hamburger menus and sheet overlays per the mobile UX requirements.

## Components

### 1. `MobilePersistentSidebar`

Location: `frontend/client/src/components/navigation/MobilePersistentSidebar.tsx`

**Props:**

| Prop | Type | Required | Description |
|------|------|----------|-------------|
| `currentTier` | `UserTier` | Yes | The user's raw tier (`standard` / `advanced` / `admin`) |
| `effectiveTier` | `UserTier` | Yes | Tier after advanced-mode overlay is applied |
| `onTierChange` | `(tier: UserTier) => void` | Yes | Callback when user manually changes tier |
| `isAdvancedModeEnabled` | `boolean` | Yes | Whether advanced mode toggle is on |
| `onAdvancedModeToggle` | `(enabled: boolean) => void` | Yes | Callback to toggle advanced mode |
| `navItems` | `NavItem[]` | Yes | Navigation spine data (re-export `NAV_SPINE` from `TieredNav`) |
| `accounts` | `Account[]` | Yes | List of accounts for the picker |
| `selectedAccountId` | `string \| null` | Yes | Currently selected account ID |
| `onSelectAccount` | `(accountId: string) => void` | Yes | Called when user picks an account |
| `isAccountsLoading` | `boolean` | No | Loading state for accounts fetch |
| `accountsError` | `Error \| null` | No | Error state for accounts fetch |
| `onCreateAccount` | `() => void` | No | Optional callback to create a new account |
| `user` | `{ name?: string; email?: string } \| null` | No | Current user for footer avatar menu |
| `onSignOut` | `() => void` | No | Sign-out callback |

**Behavior:**
- Always visible on mobile (`flex md:hidden` controlled by parent)
- Fixed width `w-20` (80px)
- Touch-friendly buttons with `min-h-[56px]`
- Child nav items expand inline with smooth animation (respects `prefers-reduced-motion`)
- ScrollArea handles overflow for long nav lists

### 2. `AccountPicker`

Location: `frontend/client/src/components/navigation/AccountPicker.tsx`

**Props:**

| Prop | Type | Required | Description |
|------|------|----------|-------------|
| `accounts` | `Account[]` | Yes | Accounts to display |
| `selectedAccountId` | `string \| null` | Yes | Selected account ID |
| `onSelectAccount` | `(id: string) => void` | Yes | Selection callback |
| `onCreateAccount` | `() => void` | No | Create account callback |
| `isLoading` | `boolean` | No | Loading spinner state |
| `error` | `Error \| null` | No | Error message state |
| `variant` | `"compact" \| "full"` | No | Visual density (`compact` for mobile rail) |
| `className` | `string` | No | Additional Tailwind classes |

**Accessibility:**
- Uses `@radix-ui/react-dropdown-menu` for keyboard navigation
- `aria-label` describes current selection state
- Search input inside dropdown with live filtering
- Focus trapping managed by Radix

## Integration into AppShell

`AppShell.tsx` has been updated to render both sidebars side-by-side, using Tailwind breakpoints to toggle visibility:

```tsx
<div className="flex flex-1 overflow-hidden">
  {/* Desktop */}
  <div className="hidden md:block">
    <TieredNav ... />
  </div>

  {/* Mobile */}
  <div className="flex md:hidden">
    <MobilePersistentSidebar ... />
  </div>

  <main className="flex-1 overflow-y-auto bg-background">
    {children}
  </main>
</div>
```

The main content area automatically flexes to fill remaining space; no extra padding math is required.

## Tailwind Breakpoints

| Breakpoint | Sidebar | Width |
|------------|---------|-------|
| `< 768px` (default) | `MobilePersistentSidebar` | 80px |
| `>= 768px` (`md:`) | `TieredNav` | 240px |

## State Management

- **Selected account**: `useAccountContextStore` (Zustand + persist)
- **Accounts list**: `useAccounts({ page_size: 100 })` (TanStack Query)
- **Auth user**: `useAuthContext()`
- **Tier / advanced mode**: Existing `useUserTierStore` + internal AppShell state

## Performance Notes

- `AppShell` remains wrapped in `React.memo` with a custom equality function; the shell only re-renders when tier props change.
- `MobilePersistentSidebar` fetches accounts via React Query, so data is cached and deduplicated across the app.
- `ScrollArea` virtualizes long nav lists to keep DOM weight low.
- CSS transitions respect `prefers-reduced-motion`.

## Touch & Accessibility

- All tap targets are >= 44px (nav buttons are 56px min height).
- Active page indicated with `aria-current="page"`.
- Expandable sections use `aria-expanded`.
- Color contrast meets WCAG 2.1 AA via existing design tokens.
