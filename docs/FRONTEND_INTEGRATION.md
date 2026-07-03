# Forest Management System — Frontend Implementation Guide

> **Audience:** Frontend engineers implementing the Next.js / React client.  
> **Backend:** Django REST Framework (DRF) with Token + Session authentication.  
> **Goal:** Provide a complete, feature-level blueprint so any frontend developer can build the application without guessing.  
> **Last updated:** 2026-06-24

---

## Table of Contents

1. [Overview & Goals](#1-overview--goals)
2. [Tech Stack](#2-tech-stack)
3. [Backend API Summary](#3-backend-api-summary)
4. [Feature Modules](#4-feature-modules)
5. [Architecture & Folder Structure](#5-architecture--folder-structure)
6. [Step-by-Step Project Setup](#6-step-by-step-project-setup)
7. [Core Implementation](#7-core-implementation)
8. [Authentication Implementation](#8-authentication-implementation)
9. [API Modules](#9-api-modules)
10. [React Query Hooks](#10-react-query-hooks)
11. [Component Implementation Guide](#11-component-implementation-guide)
12. [Forms & Validation](#12-forms--validation)
13. [Tables, Lists, Pagination, Search & Filter](#13-tables-lists-pagination-search--filter)
14. [Error Handling Strategy](#14-error-handling-strategy)
15. [Role-Based Access Control](#15-role-based-access-control)
16. [PDF Downloads & Reports](#16-pdf-downloads--reports)
17. [Notifications & Toast](#17-notifications--toast)
18. [Optimistic Updates](#18-optimistic-updates)
19. [Dashboard Widgets](#19-dashboard-widgets)
20. [Responsive Design](#20-responsive-design)
21. [Testing](#21-testing)
22. [Performance](#22-performance)
23. [Security](#23-security)
24. [Deployment](#24-deployment)
25. [Appendix A: Full API Reference](#appendix-a-full-api-reference)
26. [Appendix B: TypeScript Types](#appendix-b-typescript-types)
27. [Appendix C: Environment Variables](#appendix-c-environment-variables)
28. [Appendix D: Known Backend Gaps](#appendix-d-known-backend-gaps)

---

## 1. Overview & Goals

This guide describes how to build the frontend for the Forest Management System. The application is an internal dashboard used by:

- **Committee officers / admins** — full read/write access
- **Members** — view own household data, limited actions
- **Sub-committee members** — view household data, some write actions
- **DFO viewers** — read-only access to all data

The frontend must support:

- Secure authentication and session management
- Role-based navigation and UI elements
- CRUD operations for all backend modules
- Advanced tables with pagination, search, filtering, and sorting
- Forms with client-side and server-side validation
- PDF receipt/report download and viewing
- Dashboard widgets with summary statistics
- Toast notifications and global error handling
- Responsive layout for desktop and tablet

---

## 2. Tech Stack

| Concern | Technology | Version | Purpose |
|---------|------------|---------|---------|
| Framework | Next.js (App Router) | 14+ or 15+ | SSR, SSG, API route proxy, file routing |
| Language | TypeScript | 5+ | Type safety |
| Styling | Tailwind CSS | 3.4+ | Utility-first CSS |
| UI Components | shadcn/ui + Radix UI | latest | Accessible, composable primitives |
| Icons | Lucide React | latest | Consistent iconography |
| Server State | TanStack Query (React Query) | v5 | Data fetching, caching, mutations |
| Client State | Zustand | v4+ | Auth, sidebar, small UI state |
| Forms | React Hook Form + Zod | v7+ / v3+ | Performant forms + schema validation |
| HTTP Client | Axios | v1.7+ | Interceptors, typed requests, blob downloads |
| Tables | TanStack Table | v8 | Sorting, filtering, pagination |
| Date Handling | date-fns | v3+ | Formatting, parsing |
| Charts (optional) | Recharts | v2+ | Dashboard charts |
| PDF Viewing | react-pdf or pdf-lib | latest | In-app PDF preview |
| Notifications | Sonner | latest | Toast notifications |
| Testing | Vitest + React Testing Library + MSW | latest | Unit and integration tests |

---

## 3. Backend API Summary

All API endpoints share the base path `/api/v1/<app>/`.

### Authentication

> **For complete request/response types and permissions see `API_DATA_TYPES.md`.**

- **Token auth:** `Authorization: Token <key>`
- **Session auth:** session cookie + CSRF token
- **Current user:** `GET /api/v1/core/users/me/`
- **Login:** `POST /api/v1/core/auth/login/` returns `{ token, user }`
- **Logout:** `POST /api/v1/core/auth/logout/` invalidates the token
- **Important:** these endpoints are now available in the backend.

### Pagination

DRF uses `LimitOffsetPagination` with default `PAGE_SIZE = 100`.

```json
{
  "count": 150,
  "next": "http://localhost:8000/api/v1/members/members/?limit=100&offset=100",
  "previous": null,
  "results": []
}
```

### Filtering, Search, Ordering

```http
GET /api/v1/members/members/?membership_status=active&limit=20&offset=0
GET /api/v1/members/members/?search=ram
GET /api/v1/members/members/?ordering=-date_joined
```

### Error response shapes

```json
// Validation error (400)
{ "email": ["This field is required."], "non_field_errors": ["..."] }

// Generic error
{ "detail": "Authentication credentials were not provided." }
```

---

## 4. Feature Modules

This section lists every feature the frontend must implement, module by module.

### 4.1 Authentication

- Login page with email and password
- Logout
- Forgot password link (placeholder until backend supports it)
- Protected routes redirect to `/login`
- Persist session across reloads

### 4.2 Dashboard

Dashboard is the landing page after login. It should display:

- Summary cards:
  - Total active members
  - Total households
  - Pending harvest requests
  - Total stock value / available stock
  - Visitor entries today
  - Cash balance
  - Pending offense reports
- Quick action buttons:
  - Register new member
  - Create harvest request
  - Record sale
  - Log visitor entry
- Recent activity list (latest 10 receipts, harvest requests, or audit logs)
- Low stock alerts (species with quantity below threshold)
- Committee quota status widget

### 4.3 Members Management

**Households**
- List households with search by head name / tole
- Filter by wealth class, tole, status
- Create household
- Edit household
- View household detail with linked members
- Delete household (with confirmation)

**Members**
- List members with search by name / citizenship number
- Filter by membership type, membership status, household wealth class
- Create member (must select or create household first)
- Edit member
- View member profile
- Delete member
- Renew membership (trigger billing workflow)

**Membership Renewals**
- List renewals
- Filter by fiscal year, fee tier
- View renewal detail
- Trigger renewal from member profile

### 4.4 Forest Management

**Forest Blocks**
- List blocks
- Filter by block name
- Create / edit / delete block
- View block detail

**Species**
- List species
- Search by species name
- Create / edit / delete species

**Operational Plans**
- List plans
- Filter by valid from / valid to dates
- Create / edit / delete plan

**Tree Counts**
- List tree counts
- Filter by species and block
- Search by species name / block name
- Create / edit / delete tree count
- View remaining count per species/block

### 4.5 Harvest Requests

- List harvest requests
- Filter by source type, status, species, requested date
- Search by member name, species name, operation name
- Create harvest request
- View harvest request detail
- Approve harvest request (committee officer only)
- Reject harvest request with notes (committee officer only)

### 4.6 Inventory

**Stock Ledgers**
- List ledgers
- Filter by species, grade
- View available quantity

**Stock Transactions**
- List transactions
- Filter by stock, transaction type, reference type

**Price Rates**
- List price rates
- Filter by species, grade, buyer type
- Create / edit / delete price rate

**Sales**
- List sales
- Filter by buyer type, species, grade, payment status
- Search by buyer name / member name
- Record new sale (creates receipt and stock transaction)
- View sale detail with receipt link

### 4.7 Visitors

**Visitor Fee Rates**
- List fee rates
- Create / edit / delete fee rate

**Visitor Entries**
- List entries
- Filter by entry date, visit purpose, fee waived
- Log visitor entry and collect fee (creates receipt)

**Official Guests**
- List official guests
- Filter by visit start/end dates
- Search by visitor name / designation
- Create / edit / delete official guest

### 4.8 Billing

**Receipts**
- List receipts
- Filter by reference type, issued date
- Search by receipt number
- View receipt detail
- Download receipt PDF
- Regenerate PDF if missing

**Fee Collections**
- List fee collections
- Filter by fee type, payment status, member
- Search by member name / citizenship number
- Create / edit fee collection

### 4.9 Governance

**Committee Members**
- List committee members
- Create / edit / delete
- View quota status

**Elections**
- List elections
- Create / edit / delete

**Candidates**
- List candidates
- Create / edit / delete

**Subcommittees**
- List subcommittees
- Create / edit / delete

**Oath Records**
- List oath records
- Create / edit / delete

**No-Confidence Motions**
- List motions
- Create / edit / delete

**Handover Records**
- List handover records
- Create / edit / delete

### 4.10 Fund Management

**Fund Allocation Rules**
- List rules
- Create / edit / delete

**Bank Accounts**
- List accounts
- Create / edit / delete
- Manage signatories (JSON list of committee member IDs)

**Cash Transactions**
- List transactions
- Filter by type, source/purpose
- Create / edit / delete
- Show committee approval flag

**Audits**
- List audits
- Filter by fiscal year, audit tier
- Create / edit / delete

**Public Audits**
- List public audits
- Filter by fiscal year, assembly approval
- Create / edit / delete

### 4.11 Livelihood

**Revolving Fund Loans**
- List loans
- Filter by status, issue date
- Create / edit / delete
- Restrict to poor households

**Livelihood Program Records**
- List programs
- Filter by program type, program date
- Create / edit / delete

**Poverty Group Agreements**
- List agreements
- Filter by status
- Search by subgroup name
- Create / edit / delete

### 4.12 Offense & Patrol

**Offense Reports**
- List reports
- Filter by status, offense type, report date
- Search by accused name / offense type
- Create / edit / delete
- Resolve offense (fine paid, escalated, dismissed)

**Evidence Items**
- List evidence
- Filter by offense, item type
- Create / edit / delete

**Hearing Records**
- List hearings
- Filter by offense, hearing date
- Create / edit / delete

**Informant Rewards**
- List rewards (read-only)
- Filter by offense, informant

**Patrol Logs**
- List patrol logs
- Filter by watcher, patrol date
- Create / edit / delete

### 4.13 Reports

Each report supports JSON view and PDF export.

- Tree count report
- Harvest summary
- Stock register
- Sales summary
- Visitor entries
- Fund & audit
- Governance
- Livelihood
- Offense
- Annual DFO report

### 4.14 System Settings

- View and edit system configuration
- Fields: membership fees, fiscal year, fund allocation %, cash approval limits, audit threshold, offense reward %, governance thresholds, committee quotas

---

## 5. Architecture & Folder Structure

Create the project with the following structure:

```text
forest-frontend/
├── .env.local
├── .env.example
├── next.config.js
├── tailwind.config.ts
├── tsconfig.json
├── components.json          # shadcn/ui config
├── package.json
├── public/
│   └── logo.svg
├── src/
│   ├── app/
│   │   ├── (auth)/
│   │   │   ├── layout.tsx
│   │   │   └── login/
│   │   │       └── page.tsx
│   │   ├── (dashboard)/
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx
│   │   │   ├── members/
│   │   │   │   ├── page.tsx
│   │   │   │   ├── [id]/
│   │   │   │   │   └── page.tsx
│   │   │   │   └── new/
│   │   │   │       └── page.tsx
│   │   │   ├── households/
│   │   │   ├── harvest/
│   │   │   ├── inventory/
│   │   │   ├── visitors/
│   │   │   ├── billing/
│   │   │   ├── governance/
│   │   │   ├── fund/
│   │   │   ├── livelihood/
│   │   │   ├── offense/
│   │   │   ├── reports/
│   │   │   └── settings/
│   │   ├── api/
│   │   │   ├── auth/
│   │   │   │   ├── login/
│   │   │   │   │   └── route.ts
│   │   │   │   ├── logout/
│   │   │   │   │   └── route.ts
│   │   │   │   └── me/
│   │   │   │       └── route.ts
│   │   │   └── proxy/
│   │   │       └── [...path]/
│   │   │           └── route.ts
│   │   ├── error.tsx
│   │   ├── not-found.tsx
│   │   └── loading.tsx
│   ├── components/
│   │   ├── ui/               # shadcn/ui components
│   │   ├── layout/
│   │   │   ├── app-shell.tsx
│   │   │   ├── sidebar.tsx
│   │   │   ├── topbar.tsx
│   │   │   └── mobile-nav.tsx
│   │   ├── data-table/
│   │   │   ├── data-table.tsx
│   │   │   ├── pagination.tsx
│   │   │   ├── column-header.tsx
│   │   │   └── toolbar.tsx
│   │   ├── forms/
│   │   │   ├── form-input.tsx
│   │   │   ├── form-select.tsx
│   │   │   ├── form-date-picker.tsx
│   │   │   └── form-textarea.tsx
│   │   ├── auth/
│   │   │   ├── login-form.tsx
│   │   │   └── protected-route.tsx
│   │   ├── dashboard/
│   │   │   ├── stat-card.tsx
│   │   │   ├── recent-activity.tsx
│   │   │   └── quick-actions.tsx
│   │   ├── members/
│   │   ├── harvest/
│   │   ├── inventory/
│   │   └── ...
│   ├── hooks/
│   │   ├── use-auth.ts
│   │   ├── use-role.ts
│   │   ├── use-toast.ts
│   │   ├── use-table-params.ts
│   │   ├── use-members.ts
│   │   ├── use-member-mutations.ts
│   │   └── ...
│   ├── lib/
│   │   ├── api/
│   │   │   ├── client.ts
│   │   │   ├── auth.ts
│   │   │   ├── core.ts
│   │   │   ├── members.ts
│   │   │   ├── forest.ts
│   │   │   ├── harvest.ts
│   │   │   ├── inventory.ts
│   │   │   ├── visitors.ts
│   │   │   ├── billing.ts
│   │   │   ├── governance.ts
│   │   │   ├── fund.ts
│   │   │   ├── livelihood.ts
│   │   │   ├── offense.ts
│   │   │   └── reports.ts
│   │   ├── query-client.ts
│   │   ├── query-keys.ts
│   │   ├── errors.ts
│   │   ├── pagination.ts
│   │   ├── utils.ts
│   │   └── constants.ts
│   ├── schemas/
│   │   ├── auth.schema.ts
│   │   ├── member.schema.ts
│   │   ├── household.schema.ts
│   │   └── ...
│   ├── stores/
│   │   └── auth-store.ts
│   ├── types/
│   │   └── api.ts
│   └── styles/
│       └── globals.css
```

---

## 6. Step-by-Step Project Setup

### 6.1 Initialize Next.js project

```bash
npx shadcn@latest init --yes --template next --base-color stone
```

### 6.2 Install dependencies

```bash
npm install @tanstack/react-query @tanstack/react-query-devtools zustand axios react-hook-form @hookform/resolvers zod sonner lucide-react date-fns @tanstack/react-table recharts
npm install -D @tanstack/eslint-plugin-query vitest @testing-library/react @testing-library/jest-dom @testing-library/user-event msw jsdom
```

### 6.3 Configure shadcn components

```bash
npx shadcn add button card input label select table dialog dropdown-menu sheet badge avatar skeleton form tabs toast sonner date-picker pagination
```

### 6.4 Configure environment variables

Create `.env.local`:

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api
API_BASE_URL=http://localhost:8000/api
NEXT_PUBLIC_APP_NAME=Forest Management System
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

---

## 7. Core Implementation

### 7.1 TypeScript types

Create `src/types/api.ts`:

```ts
export type UserRole =
  | 'committee_officer'
  | 'member'
  | 'sub_committee_member'
  | 'dfo_viewer'
  | 'admin';

export interface User {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  role: UserRole;
  is_active: boolean;
  date_joined: string;
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface Household {
  id: number;
  household_head_name: string;
  tole: string;
  wealth_class: 'poor' | 'medium' | 'rich';
  status: 'active' | 'inactive';
  created_at: string;
  updated_at: string;
}

export interface Member {
  id: number;
  full_name: string;
  citizenship_no: string;
  membership_type: string;
  membership_status: 'active' | 'inactive' | 'pending' | 'suspended';
  household: number;
  household_name?: string;
  phone?: string;
  email?: string;
  date_joined: string;
  created_at: string;
  updated_at: string;
}

export interface ApiValidationError {
  [field: string]: string[];
}
```

### 7.2 Error handling utility

Create `src/lib/errors.ts`:

```ts
import { AxiosError } from 'axios';

export class ApiError extends Error {
  status: number;
  fieldErrors: Record<string, string[]>;

  constructor(
    message: string,
    status: number,
    fieldErrors: Record<string, string[]> = {}
  ) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.fieldErrors = fieldErrors;
  }

  static fromAxios(error: AxiosError<unknown>): ApiError {
    const status = error.response?.status ?? 0;
    const data = error.response?.data;

    if (typeof data === 'string') {
      return new ApiError(data || error.message, status);
    }

    if (data && typeof data === 'object') {
      const obj = data as Record<string, unknown>;
      const detail = obj.detail;
      const message = Array.isArray(detail)
        ? detail.join(' ')
        : typeof detail === 'string'
        ? detail
        : 'Something went wrong';

      const fieldErrors: Record<string, string[]> = {};
      for (const [key, value] of Object.entries(obj)) {
        if (key === 'detail') continue;
        fieldErrors[key] = Array.isArray(value)
          ? value.map(String)
          : [String(value)];
      }

      return new ApiError(message, status, fieldErrors);
    }

    return new ApiError(error.message || 'Network error', status);
  }
}

export function getErrorMessage(error: unknown): string {
  if (error instanceof ApiError) return error.message;
  if (error instanceof Error) return error.message;
  return 'An unexpected error occurred';
}
```

### 7.3 Axios client

Create `src/lib/api/client.ts`:

```ts
import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';
import { useAuthStore } from '@/stores/auth-store';
import { ApiError } from '@/lib/errors';

export const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_BASE_URL || '/api',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
});

apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = useAuthStore.getState().token;
  if (token && config.headers) {
    config.headers.Authorization = `Token ${token}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError<unknown>) => {
    if (error.response?.status === 401) {
      useAuthStore.getState().logout();
      if (typeof window !== 'undefined') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(ApiError.fromAxios(error));
  }
);
```

### 7.4 Query keys

Create `src/lib/query-keys.ts`:

```ts
export const queryKeys = {
  auth: {
    me: ['auth', 'me'] as const,
  },
  dashboard: {
    summary: ['dashboard', 'summary'] as const,
    recentActivity: ['dashboard', 'recent-activity'] as const,
  },
  core: {
    systemConfig: ['core', 'system-config'] as const,
  },
  households: {
    list: (filters: Record<string, unknown>) =>
      ['households', 'list', filters] as const,
    detail: (id: number | string) =>
      ['households', 'detail', id] as const,
  },
  members: {
    list: (filters: Record<string, unknown>) =>
      ['members', 'list', filters] as const,
    detail: (id: number | string) =>
      ['members', 'detail', id] as const,
  },
  forest: {
    blocks: (filters: Record<string, unknown>) =>
      ['forest', 'blocks', filters] as const,
    species: (filters: Record<string, unknown>) =>
      ['forest', 'species', filters] as const,
    operationalPlans: (filters: Record<string, unknown>) =>
      ['forest', 'operational-plans', filters] as const,
    treeCounts: (filters: Record<string, unknown>) =>
      ['forest', 'tree-counts', filters] as const,
  },
  harvest: {
    list: (filters: Record<string, unknown>) =>
      ['harvest', 'list', filters] as const,
    detail: (id: number | string) =>
      ['harvest', 'detail', id] as const,
  },
  inventory: {
    ledgers: (filters: Record<string, unknown>) =>
      ['inventory', 'ledgers', filters] as const,
    transactions: (filters: Record<string, unknown>) =>
      ['inventory', 'transactions', filters] as const,
    priceRates: (filters: Record<string, unknown>) =>
      ['inventory', 'price-rates', filters] as const,
    sales: (filters: Record<string, unknown>) =>
      ['inventory', 'sales', filters] as const,
  },
  visitors: {
    feeRates: (filters: Record<string, unknown>) =>
      ['visitors', 'fee-rates', filters] as const,
    entries: (filters: Record<string, unknown>) =>
      ['visitors', 'entries', filters] as const,
    officialGuests: (filters: Record<string, unknown>) =>
      ['visitors', 'official-guests', filters] as const,
  },
  billing: {
    receipts: (filters: Record<string, unknown>) =>
      ['billing', 'receipts', filters] as const,
    feeCollections: (filters: Record<string, unknown>) =>
      ['billing', 'fee-collections', filters] as const,
  },
  governance: {
    committeeMembers: (filters: Record<string, unknown>) =>
      ['governance', 'committee-members', filters] as const,
    elections: (filters: Record<string, unknown>) =>
      ['governance', 'elections', filters] as const,
    candidates: (filters: Record<string, unknown>) =>
      ['governance', 'candidates', filters] as const,
    subcommittees: (filters: Record<string, unknown>) =>
      ['governance', 'subcommittees', filters] as const,
    oathRecords: (filters: Record<string, unknown>) =>
      ['governance', 'oath-records', filters] as const,
    noConfidenceMotions: (filters: Record<string, unknown>) =>
      ['governance', 'no-confidence-motions', filters] as const,
    handoverRecords: (filters: Record<string, unknown>) =>
      ['governance', 'handover-records', filters] as const,
  },
  fund: {
    allocationRules: (filters: Record<string, unknown>) =>
      ['fund', 'allocation-rules', filters] as const,
    bankAccounts: (filters: Record<string, unknown>) =>
      ['fund', 'bank-accounts', filters] as const,
    cashTransactions: (filters: Record<string, unknown>) =>
      ['fund', 'cash-transactions', filters] as const,
    audits: (filters: Record<string, unknown>) =>
      ['fund', 'audits', filters] as const,
    publicAudits: (filters: Record<string, unknown>) =>
      ['fund', 'public-audits', filters] as const,
  },
  livelihood: {
    revolvingLoans: (filters: Record<string, unknown>) =>
      ['livelihood', 'revolving-loans', filters] as const,
    programRecords: (filters: Record<string, unknown>) =>
      ['livelihood', 'program-records', filters] as const,
    povertyGroupAgreements: (filters: Record<string, unknown>) =>
      ['livelihood', 'poverty-group-agreements', filters] as const,
  },
  offense: {
    reports: (filters: Record<string, unknown>) =>
      ['offense', 'reports', filters] as const,
    evidence: (filters: Record<string, unknown>) =>
      ['offense', 'evidence', filters] as const,
    hearings: (filters: Record<string, unknown>) =>
      ['offense', 'hearings', filters] as const,
    informantRewards: (filters: Record<string, unknown>) =>
      ['offense', 'informant-rewards', filters] as const,
    patrolLogs: (filters: Record<string, unknown>) =>
      ['offense', 'patrol-logs', filters] as const,
  },
  reports: {
    byType: (type: string, params: Record<string, unknown>) =>
      ['reports', type, params] as const,
  },
};
```

### 7.5 Query client setup

Create `src/lib/query-client.ts`:

```ts
import { QueryClient } from '@tanstack/react-query';

export function makeQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 60 * 1000,
        refetchOnWindowFocus: false,
        retry: (failureCount, error: unknown) => {
          if ((error as { status?: number })?.status === 401) return false;
          return failureCount < 2;
        },
      },
    },
  });
}

let browserQueryClient: QueryClient | undefined;

export function getQueryClient() {
  if (typeof window === 'undefined') return makeQueryClient();
  if (!browserQueryClient) browserQueryClient = makeQueryClient();
  return browserQueryClient;
}
```

### 7.6 Auth store

Create `src/stores/auth-store.ts`:

```ts
import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { User } from '@/types/api';

interface AuthState {
  token: string | null;
  user: User | null;
  isHydrated: boolean;
  setAuth: (token: string, user: User) => void;
  logout: () => void;
  setHydrated: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      isHydrated: false,
      setAuth: (token, user) => set({ token, user }),
      logout: () => set({ token: null, user: null }),
      setHydrated: () => set({ isHydrated: true }),
    }),
    {
      name: 'forest-auth',
      onRehydrateStorage: () => (state) => {
        state?.setHydrated();
      },
    }
  )
);
```

### 7.7 Providers component

Create `src/components/providers.tsx`:

```tsx
'use client';
import { useState } from 'react';
import { QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { Toaster } from '@/components/ui/sonner';
import { getQueryClient } from '@/lib/query-client';

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(() => getQueryClient());

  return (
    <QueryClientProvider client={queryClient}>
      {children}
      <Toaster position="top-right" richColors />
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
}
```

### 7.8 Layout shell

Create `src/components/layout/app-shell.tsx`:

```tsx
'use client';
import { Sidebar } from './sidebar';
import { Topbar } from './topbar';

export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-screen bg-stone-50">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <Topbar />
        <main className="flex-1 overflow-y-auto p-6">{children}</main>
      </div>
    </div>
  );
}
```

### 7.9 Sidebar navigation

Create `src/components/layout/sidebar.tsx`:

```tsx
'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard,
  Users,
  TreePine,
  Axe,
  Package,
  Ticket,
  Receipt,
  Landmark,
  Wallet,
  HeartHandshake,
  ShieldAlert,
  FileBarChart,
  Settings,
} from 'lucide-react';
import { cn } from '@/lib/utils';

const navItems = [
  { label: 'Dashboard', href: '/', icon: LayoutDashboard },
  { label: 'Members', href: '/members', icon: Users },
  { label: 'Households', href: '/households', icon: Users },
  { label: 'Forest', href: '/forest', icon: TreePine },
  { label: 'Harvest', href: '/harvest', icon: Axe },
  { label: 'Inventory', href: '/inventory', icon: Package },
  { label: 'Visitors', href: '/visitors', icon: Ticket },
  { label: 'Billing', href: '/billing', icon: Receipt },
  { label: 'Governance', href: '/governance', icon: Landmark },
  { label: 'Fund', href: '/fund', icon: Wallet },
  { label: 'Livelihood', href: '/livelihood', icon: HeartHandshake },
  { label: 'Offense', href: '/offense', icon: ShieldAlert },
  { label: 'Reports', href: '/reports', icon: FileBarChart },
  { label: 'Settings', href: '/settings', icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="hidden w-64 flex-col border-r bg-white md:flex">
      <div className="flex h-16 items-center border-b px-6 font-bold">
        Forest Mgmt
      </div>
      <nav className="flex-1 space-y-1 p-4">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                'flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors',
                isActive
                  ? 'bg-stone-100 text-stone-900'
                  : 'text-stone-600 hover:bg-stone-50'
              )}
            >
              <Icon className="h-4 w-4" />
              {item.label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
```

---

## 8. Authentication Implementation

### 8.1 Login schema

Create `src/schemas/auth.schema.ts`:

```ts
import { z } from 'zod';

export const loginSchema = z.object({
  email: z.string().email('Please enter a valid email'),
  password: z.string().min(6, 'Password must be at least 6 characters'),
});

export type LoginInput = z.infer<typeof loginSchema>;
```

### 8.2 Auth API

Create `src/lib/api/auth.ts`:

```ts
import { apiClient } from './client';
import type { User } from '@/types/api';

export interface LoginResponse {
  token: string;
  user: User;
}

export const authApi = {
  login: (data: { email: string; password: string }) =>
    apiClient.post<LoginResponse>('/v1/auth/login/', data).then((r) => r.data),

  logout: () => apiClient.post('/v1/auth/logout/').then((r) => r.data),

  me: () => apiClient.get<User>('/v1/core/users/me/').then((r) => r.data),
};
```

### 8.3 Login hook

Create `src/hooks/use-login.ts`:

```ts
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import { authApi } from '@/lib/api/auth';
import { useAuthStore } from '@/stores/auth-store';
import { toast } from 'sonner';

export function useLogin() {
  const queryClient = useQueryClient();
  const router = useRouter();
  const setAuth = useAuthStore((s) => s.setAuth);

  return useMutation({
    mutationFn: authApi.login,
    onSuccess: ({ token, user }) => {
      setAuth(token, user);
      queryClient.setQueryData(['auth', 'me'], user);
      toast.success(`Welcome back, ${user.first_name}`);
      router.push('/');
    },
    onError: (error) => {
      toast.error(error.message || 'Login failed. Please try again.');
    },
  });
}
```

### 8.4 Current user hook

Create `src/hooks/use-auth.ts`:

```ts
import { useQuery } from '@tanstack/react-query';
import { authApi } from '@/lib/api/auth';
import { useAuthStore } from '@/stores/auth-store';
import { queryKeys } from '@/lib/query-keys';

export function useAuth() {
  const { token, user: storedUser, logout, isHydrated } = useAuthStore();

  const { data: user, isLoading } = useQuery({
    queryKey: queryKeys.auth.me,
    queryFn: authApi.me,
    enabled: Boolean(token) && isHydrated,
    initialData: storedUser,
    staleTime: 5 * 60 * 1000,
  });

  return { user, isLoading, isAuthenticated: Boolean(user), logout };
}
```

### 8.5 Login form component

Create `src/components/auth/login-form.tsx`:

```tsx
'use client';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Button } from '@/components/ui/button';
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import { loginSchema, LoginInput } from '@/schemas/auth.schema';
import { useLogin } from '@/hooks/use-login';

export function LoginForm() {
  const login = useLogin();
  const form = useForm<LoginInput>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: '', password: '' },
  });

  return (
    <Form {...form}>
      <form
        onSubmit={form.handleSubmit((values) => login.mutate(values))}
        className="space-y-4"
      >
        <FormField
          control={form.control}
          name="email"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Email</FormLabel>
              <FormControl>
                <Input type="email" placeholder="you@example.com" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name="password"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Password</FormLabel>
              <FormControl>
                <Input type="password" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <Button type="submit" className="w-full" disabled={login.isPending}>
          {login.isPending ? 'Signing in...' : 'Sign in'}
        </Button>
      </form>
    </Form>
  );
}
```

### 8.6 Protected route / layout

Create `src/components/auth/protected-route.tsx`:

```tsx
'use client';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';
import { useAuth } from '@/hooks/use-auth';

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.replace('/login');
    }
  }, [isLoading, isAuthenticated, router]);

  if (isLoading) return <div>Loading...</div>;
  if (!isAuthenticated) return null;

  return <>{children}</>;
}
```

---

## 9. API Modules

Create one file per backend app under `src/lib/api/`. Each file exports an object with typed methods.

### 9.1 Members API

Create `src/lib/api/members.ts`:

```ts
import { apiClient } from './client';
import type { Member, Household, PaginatedResponse } from '@/types/api';

export const householdsApi = {
  list: (params?: Record<string, unknown>) =>
    apiClient.get<PaginatedResponse<Household>>('/v1/members/households/', {
      params,
    }),
  get: (id: number | string) =>
    apiClient.get<Household>(`/v1/members/households/${id}/`),
  create: (data: Partial<Household>) =>
    apiClient.post<Household>('/v1/members/households/', data),
  update: (id: number | string, data: Partial<Household>) =>
    apiClient.patch<Household>(`/v1/members/households/${id}/`, data),
  delete: (id: number | string) =>
    apiClient.delete(`/v1/members/households/${id}/`),
};

export const membersApi = {
  list: (params?: Record<string, unknown>) =>
    apiClient.get<PaginatedResponse<Member>>('/v1/members/members/', {
      params,
    }),
  get: (id: number | string) =>
    apiClient.get<Member>(`/v1/members/members/${id}/`),
  create: (data: Partial<Member>) =>
    apiClient.post<Member>('/v1/members/members/', data),
  update: (id: number | string, data: Partial<Member>) =>
    apiClient.patch<Member>(`/v1/members/members/${id}/`, data),
  delete: (id: number | string) =>
    apiClient.delete(`/v1/members/members/${id}/`),
};
```

### 9.2 Harvest API

Create `src/lib/api/harvest.ts`:

```ts
import { apiClient } from './client';
import type { HarvestRequest, PaginatedResponse } from '@/types/api';

export const harvestApi = {
  list: (params?: Record<string, unknown>) =>
    apiClient.get<PaginatedResponse<HarvestRequest>>(
      '/v1/harvest/requests/',
      { params }
    ),
  get: (id: number | string) =>
    apiClient.get<HarvestRequest>(`/v1/harvest/requests/${id}/`),
  create: (data: Partial<HarvestRequest>) =>
    apiClient.post<HarvestRequest>('/v1/harvest/requests/', data),
  update: (id: number | string, data: Partial<HarvestRequest>) =>
    apiClient.patch<HarvestRequest>(`/v1/harvest/requests/${id}/`, data),
  delete: (id: number | string) =>
    apiClient.delete(`/v1/harvest/requests/${id}/`),
  approve: (id: number | string) =>
    apiClient.post<{ status: string }>(`/v1/harvest/requests/${id}/approve/`),
  reject: (id: number | string, notes: string) =>
    apiClient.post<{ status: string }>(
      `/v1/harvest/requests/${id}/reject/`,
      { notes }
    ),
};
```

### 9.3 Inventory API

Create `src/lib/api/inventory.ts`:

```ts
import { apiClient } from './client';
import type {
  StockLedger,
  StockTransaction,
  PriceRate,
  Sale,
  PaginatedResponse,
} from '@/types/api';

export const inventoryApi = {
  ledgers: {
    list: (params?: Record<string, unknown>) =>
      apiClient.get<PaginatedResponse<StockLedger>>(
        '/v1/inventory/ledgers/',
        { params }
      ),
  },
  transactions: {
    list: (params?: Record<string, unknown>) =>
      apiClient.get<PaginatedResponse<StockTransaction>>(
        '/v1/inventory/transactions/',
        { params }
      ),
  },
  priceRates: {
    list: (params?: Record<string, unknown>) =>
      apiClient.get<PaginatedResponse<PriceRate>>(
        '/v1/inventory/price-rates/',
        { params }
      ),
    create: (data: Partial<PriceRate>) =>
      apiClient.post<PriceRate>('/v1/inventory/price-rates/', data),
    update: (id: number | string, data: Partial<PriceRate>) =>
      apiClient.patch<PriceRate>(`/v1/inventory/price-rates/${id}/`, data),
    delete: (id: number | string) =>
      apiClient.delete(`/v1/inventory/price-rates/${id}/`),
  },
  sales: {
    list: (params?: Record<string, unknown>) =>
      apiClient.get<PaginatedResponse<Sale>>('/v1/inventory/sales/', {
        params,
      }),
    record: (data: Partial<Sale>) =>
      apiClient.post<Sale>('/v1/inventory/sales/record/', data),
  },
};
```

### 9.4 Billing API

Create `src/lib/api/billing.ts`:

```ts
import { apiClient } from './client';
import type { Receipt, FeeCollection, PaginatedResponse } from '@/types/api';

export const billingApi = {
  receipts: {
    list: (params?: Record<string, unknown>) =>
      apiClient.get<PaginatedResponse<Receipt>>('/v1/billing/receipts/', {
        params,
      }),
    get: (receiptNo: string) =>
      apiClient.get<Receipt>(`/v1/billing/receipts/${receiptNo}/`),
    download: (receiptNo: string) =>
      apiClient.get<Blob>(`/v1/billing/receipts/${receiptNo}/download/`, {
        responseType: 'blob',
      }),
    regenerate: (receiptNo: string) =>
      apiClient.post<{ status: string }>(
        `/v1/billing/receipts/${receiptNo}/regenerate/`
      ),
  },
  feeCollections: {
    list: (params?: Record<string, unknown>) =>
      apiClient.get<PaginatedResponse<FeeCollection>>(
        '/v1/billing/fee-collections/',
        { params }
      ),
  },
};
```

### 9.5 Reports API

Create `src/lib/api/reports.ts`:

```ts
import { apiClient } from './client';

export type ReportType =
  | 'tree-count'
  | 'harvest'
  | 'stock-register'
  | 'sales'
  | 'visitor-entries'
  | 'fund-audit'
  | 'governance'
  | 'livelihood'
  | 'offense'
  | 'annual-dfo';

export const reportsApi = {
  get: (type: ReportType, params?: Record<string, unknown>) =>
    apiClient.get<unknown>(`/v1/reports/${type}/`, { params }),
  downloadPdf: (type: ReportType, params?: Record<string, unknown>) =>
    apiClient.get<Blob>(`/v1/reports/${type}/?export=pdf`, {
      params,
      responseType: 'blob',
    }),
};
```

---

## 10. React Query Hooks

### 10.1 Members hooks

Create `src/hooks/use-members.ts`:

```ts
import { useQuery } from '@tanstack/react-query';
import { membersApi, householdsApi } from '@/lib/api/members';
import { queryKeys } from '@/lib/query-keys';
import type { Member, Household, PaginatedResponse } from '@/types/api';

export function useMembers(filters: Record<string, unknown> = {}) {
  return useQuery<PaginatedResponse<Member>>({
    queryKey: queryKeys.members.list(filters),
    queryFn: async () => (await membersApi.list(filters)).data,
  });
}

export function useMember(id: number | string) {
  return useQuery<Member>({
    queryKey: queryKeys.members.detail(id),
    queryFn: async () => (await membersApi.get(id)).data,
    enabled: Boolean(id),
  });
}

export function useHouseholds(filters: Record<string, unknown> = {}) {
  return useQuery<PaginatedResponse<Household>>({
    queryKey: queryKeys.households.list(filters),
    queryFn: async () => (await householdsApi.list(filters)).data,
  });
}
```

### 10.2 Member mutations

Create `src/hooks/use-member-mutations.ts`:

```ts
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { membersApi, householdsApi } from '@/lib/api/members';
import { queryKeys } from '@/lib/query-keys';
import { toast } from 'sonner';
import type { Member, Household } from '@/types/api';

export function useCreateMember() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: membersApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['members', 'list'] });
      toast.success('Member created successfully');
    },
    onError: (error) => toast.error(error.message),
  });
}

export function useUpdateMember() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Member> }) =>
      membersApi.update(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: ['members', 'list'] });
      queryClient.invalidateQueries({ queryKey: ['members', 'detail', id] });
      toast.success('Member updated');
    },
    onError: (error) => toast.error(error.message),
  });
}

export function useDeleteMember() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: membersApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['members', 'list'] });
      toast.success('Member deleted');
    },
    onError: (error) => toast.error(error.message),
  });
}

export function useCreateHousehold() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: householdsApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['households', 'list'] });
      toast.success('Household created');
    },
    onError: (error) => toast.error(error.message),
  });
}
```

### 10.3 Harvest hooks

Create `src/hooks/use-harvest.ts`:

```ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { harvestApi } from '@/lib/api/harvest';
import { queryKeys } from '@/lib/query-keys';
import { toast } from 'sonner';
import type { HarvestRequest, PaginatedResponse } from '@/types/api';

export function useHarvestRequests(filters: Record<string, unknown> = {}) {
  return useQuery<PaginatedResponse<HarvestRequest>>({
    queryKey: queryKeys.harvest.list(filters),
    queryFn: async () => (await harvestApi.list(filters)).data,
  });
}

export function useHarvestRequest(id: number | string) {
  return useQuery<HarvestRequest>({
    queryKey: queryKeys.harvest.detail(id),
    queryFn: async () => (await harvestApi.get(id)).data,
    enabled: Boolean(id),
  });
}

export function useApproveHarvestRequest() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number | string) => harvestApi.approve(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ['harvest', 'list'] });
      queryClient.invalidateQueries({ queryKey: ['harvest', 'detail', id] });
      toast.success('Harvest request approved');
    },
    onError: (error) => toast.error(error.message),
  });
}

export function useRejectHarvestRequest() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, notes }: { id: string; notes: string }) =>
      harvestApi.reject(id, notes),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: ['harvest', 'list'] });
      queryClient.invalidateQueries({ queryKey: ['harvest', 'detail', id] });
      toast.success('Harvest request rejected');
    },
    onError: (error) => toast.error(error.message),
  });
}
```

---

## 11. Component Implementation Guide

### 11.1 Reusable data table

Use TanStack Table with shadcn/ui styling. Create `src/components/data-table/data-table.tsx`:

```tsx
'use client';
import {
  useReactTable,
  getCoreRowModel,
  getPaginationRowModel,
  flexRender,
  type ColumnDef,
} from '@tanstack/react-table';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Button } from '@/components/ui/button';

interface DataTableProps<TData, TValue> {
  columns: ColumnDef<TData, TValue>[];
  data: TData[];
  pageCount?: number;
  onPageChange?: (page: number) => void;
}

export function DataTable<TData, TValue>({
  columns,
  data,
}: DataTableProps<TData, TValue>) {
  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
  });

  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          {table.getHeaderGroups().map((headerGroup) => (
            <TableRow key={headerGroup.id}>
              {headerGroup.headers.map((header) => (
                <TableHead key={header.id}>
                  {header.isPlaceholder
                    ? null
                    : flexRender(
                        header.column.columnDef.header,
                        header.getContext()
                      )}
                </TableHead>
              ))}
            </TableRow>
          ))}
        </TableHeader>
        <TableBody>
          {table.getRowModel().rows.length ? (
            table.getRowModel().rows.map((row) => (
              <TableRow key={row.id}>
                {row.getVisibleCells().map((cell) => (
                  <TableCell key={cell.id}>
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </TableCell>
                ))}
              </TableRow>
            ))
          ) : (
            <TableRow>
              <TableCell colSpan={columns.length} className="h-24 text-center">
                No results.
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
    </div>
  );
}
```

### 11.2 Members list page

Create `src/app/(dashboard)/members/page.tsx`:

```tsx
'use client';
import { useMemo, useState } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { ColumnDef } from '@tanstack/react-table';
import { Plus } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { DataTable } from '@/components/data-table/data-table';
import { Pagination } from '@/components/data-table/pagination';
import { useMembers } from '@/hooks/use-members';
import { getPaginationParams, getPageCount } from '@/lib/pagination';
import { useRole } from '@/hooks/use-role';
import { useTableParams } from '@/hooks/use-table-params';
import type { Member } from '@/types/api';

const PAGE_SIZE = 20;

export default function MembersPage() {
  const { searchParams, setParam } = useTableParams();
  const page = Number(searchParams.get('page') || '1');
  const search = searchParams.get('search') || '';
  const status = searchParams.get('status') || '';
  const { canWrite } = useRole();

  const filters = {
    ...getPaginationParams(page, PAGE_SIZE),
    search,
    membership_status: status || undefined,
  };

  const { data, isLoading } = useMembers(filters);

  const columns = useMemo<ColumnDef<Member>[]>(
    () => [
      { accessorKey: 'full_name', header: 'Name' },
      { accessorKey: 'citizenship_no', header: 'Citizenship No' },
      { accessorKey: 'membership_type', header: 'Type' },
      {
        accessorKey: 'membership_status',
        header: 'Status',
        cell: ({ row }) => (
          <span className="capitalize">{row.original.membership_status}</span>
        ),
      },
      {
        id: 'actions',
        cell: ({ row }) => (
          <Button asChild variant="ghost" size="sm">
            <Link href={`/members/${row.original.id}`}>View</Link>
          </Button>
        ),
      },
    ],
    []
  );

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Members</h1>
        {canWrite && (
          <Button asChild>
            <Link href="/members/new">
              <Plus className="mr-2 h-4 w-4" /> Add Member
            </Link>
          </Button>
        )}
      </div>

      <div className="flex gap-2">
        <Input
          placeholder="Search by name or citizenship no..."
          value={search}
          onChange={(e) => setParam('search', e.target.value)}
          className="max-w-sm"
        />
        <Select
          value={status}
          onValueChange={(value) => setParam('status', value)}
        >
          <SelectTrigger className="w-40">
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="">All</SelectItem>
            <SelectItem value="active">Active</SelectItem>
            <SelectItem value="inactive">Inactive</SelectItem>
            <SelectItem value="pending">Pending</SelectItem>
            <SelectItem value="suspended">Suspended</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {isLoading ? (
        <div>Loading...</div>
      ) : (
        <>
          <DataTable columns={columns} data={data?.results || []} />
          <Pagination
            page={page}
            pageCount={getPageCount(data?.count || 0, PAGE_SIZE)}
            onPageChange={(p) => setParam('page', String(p))}
          />
        </>
      )}
    </div>
  );
}
```

### 11.3 Member detail page

Create `src/app/(dashboard)/members/[id]/page.tsx`:

```tsx
'use client';
import { useParams } from 'next/navigation';
import { useMember } from '@/hooks/use-members';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { format } from 'date-fns';

export default function MemberDetailPage() {
  const params = useParams();
  const id = params.id as string;
  const { data: member, isLoading } = useMember(id);

  if (isLoading) return <div>Loading...</div>;
  if (!member) return <div>Member not found</div>;

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">{member.full_name}</h1>
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Membership Info</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <p>
              <strong>Status:</strong>{' '}
              <Badge variant="outline">{member.membership_status}</Badge>
            </p>
            <p>
              <strong>Type:</strong> {member.membership_type}
            </p>
            <p>
              <strong>Citizenship:</strong> {member.citizenship_no}
            </p>
            <p>
              <strong>Joined:</strong>{' '}
              {format(new Date(member.date_joined), 'PPP')}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Contact</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <p>
              <strong>Phone:</strong> {member.phone || '—'}
            </p>
            <p>
              <strong>Email:</strong> {member.email || '—'}
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
```

---

## 12. Forms & Validation

### 12.1 Member schema

Create `src/schemas/member.schema.ts`:

```ts
import { z } from 'zod';

export const memberSchema = z.object({
  full_name: z.string().min(1, 'Full name is required'),
  citizenship_no: z.string().min(1, 'Citizenship number is required'),
  membership_type: z.string().min(1, 'Membership type is required'),
  membership_status: z.enum(['active', 'inactive', 'pending', 'suspended']),
  household: z.number({ required_error: 'Household is required' }),
  phone: z.string().optional(),
  email: z.string().email().optional().or(z.literal('')),
});

export type MemberInput = z.infer<typeof memberSchema>;
```

### 12.2 Member form

Create `src/components/members/member-form.tsx`:

```tsx
'use client';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Button } from '@/components/ui/button';
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { memberSchema, MemberInput } from '@/schemas/member.schema';
import { useHouseholds } from '@/hooks/use-members';
import { ApiError } from '@/lib/errors';
import { toast } from 'sonner';

interface MemberFormProps {
  defaultValues?: Partial<MemberInput>;
  onSubmit: (data: MemberInput) => Promise<void>;
  submitLabel?: string;
}

export function MemberForm({
  defaultValues,
  onSubmit,
  submitLabel = 'Save',
}: MemberFormProps) {
  const form = useForm<MemberInput>({
    resolver: zodResolver(memberSchema),
    defaultValues: {
      full_name: '',
      citizenship_no: '',
      membership_type: '',
      membership_status: 'active',
      phone: '',
      email: '',
      ...defaultValues,
    },
  });

  const { data: households } = useHouseholds({ limit: 100 });

  const handleSubmit = form.handleSubmit(async (values) => {
    try {
      await onSubmit(values);
    } catch (error) {
      if (error instanceof ApiError) {
        for (const [field, messages] of Object.entries(error.fieldErrors)) {
          form.setError(field as keyof MemberInput, {
            type: 'manual',
            message: messages.join(', '),
          });
        }
        toast.error(error.message);
      }
    }
  });

  return (
    <Form {...form}>
      <form onSubmit={handleSubmit} className="space-y-4 max-w-xl">
        <FormField
          control={form.control}
          name="full_name"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Full Name</FormLabel>
              <FormControl>
                <Input {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name="citizenship_no"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Citizenship Number</FormLabel>
              <FormControl>
                <Input {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name="household"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Household</FormLabel>
              <Select
                value={String(field.value)}
                onValueChange={(value) => field.onChange(Number(value))}
              >
                <FormControl>
                  <SelectTrigger>
                    <SelectValue placeholder="Select household" />
                  </SelectTrigger>
                </FormControl>
                <SelectContent>
                  {households?.results.map((h) => (
                    <SelectItem key={h.id} value={String(h.id)}>
                      {h.household_head_name} — {h.tole}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name="membership_type"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Membership Type</FormLabel>
              <FormControl>
                <Input {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name="membership_status"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Status</FormLabel>
              <Select value={field.value} onValueChange={field.onChange}>
                <FormControl>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                </FormControl>
                <SelectContent>
                  <SelectItem value="active">Active</SelectItem>
                  <SelectItem value="inactive">Inactive</SelectItem>
                  <SelectItem value="pending">Pending</SelectItem>
                  <SelectItem value="suspended">Suspended</SelectItem>
                </SelectContent>
              </Select>
              <FormMessage />
            </FormItem>
          )}
        />
        <Button type="submit" disabled={form.formState.isSubmitting}>
          {form.formState.isSubmitting ? 'Saving...' : submitLabel}
        </Button>
      </form>
    </Form>
  );
}
```

---

## 13. Tables, Lists, Pagination, Search & Filter

### 13.1 Pagination component

Create `src/components/data-table/pagination.tsx`:

```tsx
'use client';
import { Button } from '@/components/ui/button';

interface PaginationProps {
  page: number;
  pageCount: number;
  onPageChange: (page: number) => void;
}

export function Pagination({ page, pageCount, onPageChange }: PaginationProps) {
  return (
    <div className="flex items-center justify-end gap-2">
      <Button
        variant="outline"
        size="sm"
        disabled={page <= 1}
        onClick={() => onPageChange(page - 1)}
      >
        Previous
      </Button>
      <span className="text-sm text-stone-600">
        Page {page} of {pageCount || 1}
      </span>
      <Button
        variant="outline"
        size="sm"
        disabled={page >= pageCount}
        onClick={() => onPageChange(page + 1)}
      >
        Next
      </Button>
    </div>
  );
}
```

### 13.2 Table params hook

Create `src/hooks/use-table-params.ts`:

```ts
'use client';
import { useRouter, useSearchParams } from 'next/navigation';

export function useTableParams() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const setParam = (key: string, value: string | null) => {
    const params = new URLSearchParams(searchParams.toString());
    if (value) params.set(key, value);
    else params.delete(key);
    // Reset to page 1 when filters change
    if (key !== 'page') params.delete('page');
    router.push(`?${params.toString()}`);
  };

  return { searchParams, setParam };
}
```

### 13.3 Pagination utility

Create `src/lib/pagination.ts`:

```ts
export const DEFAULT_PAGE_SIZE = 20;

export function getPaginationParams(page: number, pageSize = DEFAULT_PAGE_SIZE) {
  return {
    limit: pageSize,
    offset: (page - 1) * pageSize,
  };
}

export function getPageCount(total: number, pageSize = DEFAULT_PAGE_SIZE) {
  return Math.ceil(total / pageSize);
}
```

---

## 14. Error Handling Strategy

### 14.1 Levels of error handling

1. **Global:** React error boundaries (`app/error.tsx`) catch render errors.
2. **API layer:** Axios interceptor normalizes all errors to `ApiError`.
3. **Query layer:** React Query `error` state drives UI.
4. **Form layer:** `ApiError.fieldErrors` map to form fields.
5. **Mutation layer:** `onError` shows toast.

### 14.2 Error alert component

Create `src/components/ui/error-alert.tsx`:

```tsx
import { AlertCircle } from 'lucide-react';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';

export function ErrorAlert({ message }: { message?: string }) {
  return (
    <Alert variant="destructive">
      <AlertCircle className="h-4 w-4" />
      <AlertTitle>Error</AlertTitle>
      <AlertDescription>{message || 'Something went wrong'}</AlertDescription>
    </Alert>
  );
}
```

### 14.3 Global error boundary

Create `src/app/error.tsx`:

```tsx
'use client';
import { useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { toast } from 'sonner';

export default function ErrorBoundary({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    toast.error(error.message || 'An unexpected error occurred');
  }, [error]);

  return (
    <div className="flex h-[50vh] flex-col items-center justify-center gap-4">
      <h2 className="text-xl font-semibold">Something went wrong</h2>
      <p className="text-stone-600">{error.message}</p>
      <Button onClick={reset}>Try again</Button>
    </div>
  );
}
```

---

## 15. Role-Based Access Control

### 15.1 Role hook

Create `src/hooks/use-role.ts`:

```ts
import { useAuth } from '@/hooks/use-auth';

export function useRole() {
  const { user } = useAuth();
  const role = user?.role;

  return {
    role,
    isAdmin: role === 'admin',
    isCommitteeOfficer: role === 'committee_officer' || role === 'admin',
    isMember: role === 'member',
    isSubCommittee: role === 'sub_committee_member',
    isDfoViewer: role === 'dfo_viewer',
    canWrite: role === 'committee_officer' || role === 'admin',
    canReadAll: role !== 'member' && role !== 'sub_committee_member',
  };
}
```

### 15.2 Permission guard component

Create `src/components/auth/permission-guard.tsx`:

```tsx
'use client';
import { useRole } from '@/hooks/use-role';

interface PermissionGuardProps {
  children: React.ReactNode;
  required: 'write' | 'readAll' | 'committeeOfficer';
  fallback?: React.ReactNode;
}

export function PermissionGuard({
  children,
  required,
  fallback = null,
}: PermissionGuardProps) {
  const role = useRole();

  const allowed =
    (required === 'write' && role.canWrite) ||
    (required === 'readAll' && role.canReadAll) ||
    (required === 'committeeOfficer' && role.isCommitteeOfficer);

  return allowed ? <>{children}</> : <>{fallback}</>;
}
```

---

## 16. PDF Downloads & Reports

### 16.1 Receipt download hook

Create `src/hooks/use-receipt-download.ts`:

```ts
import { useMutation } from '@tanstack/react-query';
import { billingApi } from '@/lib/api/billing';
import { toast } from 'sonner';

function downloadBlob(blob: Blob, filename: string) {
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(url);
}

export function useDownloadReceipt() {
  return useMutation({
    mutationFn: (receiptNo: string) =>
      billingApi.receipts.download(receiptNo).then((r) => r.data),
    onSuccess: (blob, receiptNo) => {
      downloadBlob(blob, `${receiptNo}.pdf`);
      toast.success('Receipt downloaded');
    },
    onError: (error) => toast.error(error.message),
  });
}
```

### 16.2 Report page

Create `src/app/(dashboard)/reports/page.tsx`:

```tsx
'use client';
import { useState } from 'react';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { reportsApi, type ReportType } from '@/lib/api/reports';
import { toast } from 'sonner';

const REPORT_TYPES: { value: ReportType; label: string }[] = [
  { value: 'tree-count', label: 'Tree Count' },
  { value: 'harvest', label: 'Harvest Summary' },
  { value: 'stock-register', label: 'Stock Register' },
  { value: 'sales', label: 'Sales Summary' },
  { value: 'visitor-entries', label: 'Visitor Entries' },
  { value: 'fund-audit', label: 'Fund & Audit' },
  { value: 'governance', label: 'Governance' },
  { value: 'livelihood', label: 'Livelihood' },
  { value: 'offense', label: 'Offense' },
  { value: 'annual-dfo', label: 'Annual DFO' },
];

export default function ReportsPage() {
  const [selected, setSelected] = useState<ReportType>('tree-count');
  const [data, setData] = useState<unknown>(null);

  const handleView = async () => {
    try {
      const response = await reportsApi.get(selected);
      setData(response.data);
    } catch (error) {
      toast.error((error as Error).message);
    }
  };

  const handleDownload = async () => {
    try {
      const blob = await reportsApi.downloadPdf(selected).then((r) => r.data);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${selected}-report.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
      toast.success('Report downloaded');
    } catch (error) {
      toast.error((error as Error).message);
    }
  };

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Reports</h1>
      <div className="flex gap-2">
        <Select value={selected} onValueChange={(v) => setSelected(v as ReportType)}>
          <SelectTrigger className="w-64">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {REPORT_TYPES.map((r) => (
              <SelectItem key={r.value} value={r.value}>
                {r.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Button variant="secondary" onClick={handleView}>
          View JSON
        </Button>
        <Button onClick={handleDownload}>Download PDF</Button>
      </div>
      <pre className="rounded-md bg-stone-100 p-4 text-sm">
        {data ? JSON.stringify(data, null, 2) : 'Click View JSON to load report'}
      </pre>
    </div>
  );
}
```

---

## 17. Notifications & Toast

Use Sonner for all notifications. Install it as part of shadcn/ui.

### Rules

- Show success toasts after successful mutations.
- Show error toasts in `onError` callbacks.
- Never show toasts inside render loops.
- Use `toast.promise()` for long-running operations like PDF downloads.

### Example promise toast

```ts
import { toast } from 'sonner';

toast.promise(downloadReport(), {
  loading: 'Generating report...',
  success: 'Report downloaded',
  error: (err) => err.message || 'Failed to download report',
});
```

---

## 18. Optimistic Updates

Use optimistic updates for actions where the user expects immediate feedback.

### Example: Toggle member active status

```ts
export function useToggleMemberActive() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, active }: { id: string; active: boolean }) =>
      membersApi.update(id, { is_active: active }),

    onMutate: async ({ id, active }) => {
      await queryClient.cancelQueries({ queryKey: ['members', 'detail', id] });
      const previous = queryClient.getQueryData<Member>([
        'members',
        'detail',
        id,
      ]);
      queryClient.setQueryData(['members', 'detail', id], (old: Member) => ({
        ...old,
        is_active: active,
      }));
      return { previous };
    },

    onError: (err, vars, context) => {
      queryClient.setQueryData(
        ['members', 'detail', vars.id],
        context?.previous
      );
      toast.error((err as Error).message);
    },

    onSettled: (_, __, { id }) => {
      queryClient.invalidateQueries({ queryKey: ['members', 'detail', id] });
      queryClient.invalidateQueries({ queryKey: ['members', 'list'] });
    },
  });
}
```

---

## 19. Dashboard Widgets

### 19.1 Stat card

Create `src/components/dashboard/stat-card.tsx`:

```tsx
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { LucideIcon } from 'lucide-react';

interface StatCardProps {
  title: string;
  value: string | number;
  icon: LucideIcon;
  description?: string;
}

export function StatCard({ title, value, icon: Icon, description }: StatCardProps) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        <Icon className="h-4 w-4 text-stone-500" />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        {description && (
          <p className="text-xs text-stone-500">{description}</p>
        )}
      </CardContent>
    </Card>
  );
}
```

### 19.2 Dashboard page

Create `src/app/(dashboard)/page.tsx`:

```tsx
'use client';
import {
  Users,
  Home,
  Axe,
  Package,
  Ticket,
  Wallet,
  ShieldAlert,
} from 'lucide-react';
import { StatCard } from '@/components/dashboard/stat-card';
import { useMembers } from '@/hooks/use-members';
import { useHarvestRequests } from '@/hooks/use-harvest';

export default function DashboardPage() {
  const { data: members } = useMembers({ membership_status: 'active', limit: 1 });
  const { data: harvest } = useHarvestRequests({ status: 'pending', limit: 1 });

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Dashboard</h1>
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Active Members"
          value={members?.count || 0}
          icon={Users}
        />
        <StatCard
          title="Pending Harvests"
          value={harvest?.count || 0}
          icon={Axe}
        />
        <StatCard title="Households" value="—" icon={Home} />
        <StatCard title="Visitor Entries Today" value="—" icon={Ticket} />
      </div>
    </div>
  );
}
```

---

## 20. Responsive Design

### Breakpoints

Use Tailwind defaults:

- `sm`: 640px
- `md`: 768px
- `lg`: 1024px
- `xl`: 1280px

### Rules

- Sidebar hidden on mobile; use a sheet/drawer menu.
- Tables should scroll horizontally on small screens.
- Forms should be single column on mobile, two columns on desktop.
- Use `grid-cols-1 md:grid-cols-2 lg:grid-cols-4` for stat cards.

### Mobile nav

Create `src/components/layout/mobile-nav.tsx`:

```tsx
'use client';
import { Menu } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Sheet,
  SheetContent,
  SheetTrigger,
} from '@/components/ui/sheet';
import { Sidebar } from './sidebar';

export function MobileNav() {
  return (
    <Sheet>
      <SheetTrigger asChild>
        <Button variant="ghost" size="icon" className="md:hidden">
          <Menu className="h-5 w-5" />
        </Button>
      </SheetTrigger>
      <SheetContent side="left" className="p-0">
        <Sidebar />
      </SheetContent>
    </Sheet>
  );
}
```

---

## 21. Testing

### 21.1 Unit tests for hooks

Use Vitest + React Testing Library + MSW.

```ts
// src/hooks/__tests__/use-members.test.ts
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { http, HttpResponse } from 'msw';
import { setupServer } from 'msw/node';
import { useMembers } from '../use-members';

const server = setupServer(
  http.get('/api/v1/members/members/', () =>
    HttpResponse.json({ count: 1, next: null, previous: null, results: [{ id: 1, full_name: 'Ram Bahadur' }] })
  )
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={new QueryClient()}>{children}</QueryClientProvider>
);

test('returns members', async () => {
  const { result } = renderHook(() => useMembers(), { wrapper });
  await waitFor(() => expect(result.current.isSuccess).toBe(true));
  expect(result.current.data?.results).toHaveLength(1);
});
```

### 21.2 Component tests

```ts
// src/components/auth/__tests__/login-form.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { LoginForm } from '../login-form';

test('shows validation errors', async () => {
  render(<LoginForm />);
  fireEvent.click(screen.getByRole('button', { name: /sign in/i }));
  await waitFor(() => {
    expect(screen.getByText(/valid email/i)).toBeInTheDocument();
  });
});
```

---

## 22. Performance

- Use React Query `staleTime` to avoid refetching on every mount.
- Use `placeholderData` for pagination to prevent flicker.
- Lazy load heavy report pages and PDF viewer.
- Memoize table columns with `useMemo`.
- Use `dynamic` imports from Next.js for chart libraries.

---

## 23. Security

- Store tokens in httpOnly cookies in production.
- Use Next.js API routes to proxy backend requests and avoid exposing backend URL.
- Sanitize user inputs; rely on Zod for client-side validation.
- Escape rendered content to prevent XSS.
- Set strict `Content-Security-Policy` headers.
- Validate role on the backend; never trust frontend role checks for security.

---

## 24. Deployment

### Build command

```bash
npm run build
```

### Environment variables for production

```env
NEXT_PUBLIC_API_BASE_URL=/api
API_BASE_URL=https://api.forest.example.com/api
NEXT_PUBLIC_APP_URL=https://forest.example.com
```

### Reverse proxy

Configure nginx or Vercel rewrites so `/api/*` routes hit the Django backend.

### Docker example

```dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/package*.json ./
RUN npm ci --only=production
EXPOSE 3000
CMD ["npm", "start"]
```

---

## Appendix A: Full API Reference

See the backend exploration summary for detailed endpoint listings per app. The frontend should map each backend resource to a route, table, form, and detail view.

### Auth

| Method | Endpoint | Body | Response |
|--------|----------|------|----------|
| POST | `/api/v1/core/auth/login/` | `{ email, password }` | `{ token, user }` |
| POST | `/api/v1/core/auth/logout/` | — | `{ detail }` |
| GET | `/api/v1/core/users/me/` | — | `User` |

### Members

| Method | Endpoint | Notes |
|--------|----------|-------|
| GET/POST | `/api/v1/members/households/` | CRUD |
| GET/PUT/PATCH/DELETE | `/api/v1/members/households/{id}/` | CRUD |
| GET/POST | `/api/v1/members/members/` | CRUD |
| GET/PUT/PATCH/DELETE | `/api/v1/members/members/{id}/` | CRUD |
| GET/POST | `/api/v1/members/membership-renewals/` | Read-only fee fields |

### Harvest

| Method | Endpoint | Notes |
|--------|----------|-------|
| GET/POST | `/api/v1/harvest/requests/` | CRUD |
| POST | `/api/v1/harvest/requests/{id}/approve/` | Officer only |
| POST | `/api/v1/harvest/requests/{id}/reject/` | Body `{ notes }` |

### Inventory

| Method | Endpoint | Notes |
|--------|----------|-------|
| GET/POST | `/api/v1/inventory/ledgers/` | Read `quantity_available` |
| GET/POST | `/api/v1/inventory/transactions/` | CRUD |
| GET/POST | `/api/v1/inventory/price-rates/` | CRUD |
| GET/POST | `/api/v1/inventory/sales/` | CRUD |
| POST | `/api/v1/inventory/sales/record/` | Creates receipt + stock transaction |

### Billing

| Method | Endpoint | Notes |
|--------|----------|-------|
| GET | `/api/v1/billing/receipts/` | Read-only |
| GET | `/api/v1/billing/receipts/{receipt_no}/download/` | PDF blob |
| POST | `/api/v1/billing/receipts/{receipt_no}/regenerate/` | Queue PDF |
| GET/POST | `/api/v1/billing/fee-collections/` | CRUD |

### Reports

| Method | Endpoint | Notes |
|--------|----------|-------|
| GET | `/api/v1/reports/{type}/` | JSON |
| GET | `/api/v1/reports/{type}/?export=pdf` | PDF blob |

---

## Appendix B: TypeScript Types

Extend `src/types/api.ts` with all backend models.  
> **For the full type catalog with request/response shapes and permissions, see `API_DATA_TYPES.md`.**

```ts
export type UserRole =
  | 'committee_officer'
  | 'member'
  | 'sub_committee_member'
  | 'dfo_viewer'
  | 'admin';

export interface User {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  role: UserRole;
  is_active: boolean;
  date_joined: string;
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface SystemConfig {
  id: number;
  new_household_entry_fee: string;
  split_household_entry_fee: string;
  renewal_fee_on_time: string;
  renewal_fee_overdue_3yr: string;
  renewal_fee_overdue_5yr: string;
  renewal_fee_overdue_5yr_plus: string;
  membership_cancellation_years: number;
  current_fiscal_year: string;
  forest_dev_min_percent: string;
  poor_targeted_min_percent: string;
  cash_chair_approval_limit: string;
  cash_treasurer_approval_limit: string;
  audit_external_threshold: string;
  informant_reward_percent: string;
  no_confidence_signature_percent: string;
  handover_deadline_days: number;
  min_female_committee_members: number;
  min_dalit_or_minority_committee_members: number;
}

export interface Household {
  id: number;
  household_head_name: string;
  tole: string;
  wealth_class: 'rich' | 'medium' | 'poor';
  population_male: number;
  population_female: number;
  livestock_cattle: number;
  livestock_buffalo: number;
  livestock_goat: number;
  education_level: 'illiterate' | 'basic' | 'secondary_plus' | '';
  occupation: string;
  caste_ethnicity: string;
  registration_date: string;
  entry_fee_type: 'new_household' | 'split_household';
  entry_fee_due: string;
  status: 'active' | 'inactive';
  created_at: string;
  updated_at: string;
}

export interface Member {
  id: number;
  household: number;
  household_name: string;
  user: number | null;
  user_email: string | null;
  full_name: string;
  citizenship_no: string;
  membership_type: 'general' | 'lifetime' | 'institutional' | 'special' | 'other';
  membership_status: 'active' | 'inactive' | 'cancelled';
  date_joined: string;
  created_at: string;
  updated_at: string;
}

export interface ForestBlock {
  id: number;
  block_name: string;
  area_hectares: string;
  created_at: string;
  updated_at: string;
}

export interface Species {
  id: number;
  species_name: string;
  created_at: string;
  updated_at: string;
}

export interface OperationalPlan {
  id: number;
  valid_from: string;
  valid_to: string;
  approved_harvest_limit: string;
  description: string;
  created_at: string;
  updated_at: string;
}

export interface TreeCountRegister {
  id: number;
  species: number;
  species_name: string;
  block: number | null;
  block_name: string | null;
  total_count: number;
  harvested_count: number;
  remaining_count: number;
  last_updated: string;
  adjustment_reason: string;
  created_at: string;
  updated_at: string;
}

export interface HarvestRequest {
  id: number;
  source_type: 'member_requested' | 'forest_initiated';
  member: number | null;
  member_name: string | null;
  operation_name: string;
  species: number;
  species_name: string;
  quantity: string;
  status: 'pending' | 'approved' | 'rejected';
  requested_date: string;
  approved_by: number | null;
  approved_by_name: string | null;
  notes: string;
  created_at: string;
  updated_at: string;
}

export interface StockLedger {
  id: number;
  species: number;
  species_name: string;
  grade: string;
  quantity_available: string;
  created_at: string;
  updated_at: string;
}

export interface StockTransaction {
  id: number;
  stock: number;
  transaction_type: 'in' | 'out';
  quantity: string;
  reference_type: 'harvest' | 'sale' | 'adjustment';
  reference_id: number;
  note: string;
  created_at: string;
}

export interface PriceRate {
  id: number;
  species: number;
  species_name: string;
  grade: string;
  buyer_type: 'member' | 'outsider';
  rate_per_unit: string;
  effective_from: string;
  created_at: string;
  updated_at: string;
}

export interface Sale {
  id: number;
  buyer_name: string;
  buyer_type: 'member' | 'outsider';
  member: number | null;
  member_name: string | null;
  species: number;
  species_name: string;
  grade: string;
  quantity: string;
  rate_applied: string;
  total_amount: string;
  payment_status: 'paid' | 'due' | 'partial';
  receipt_no: string | null;
  audit_note: string;
  created_at: string;
  updated_at: string;
}

export interface Receipt {
  receipt_no: string;
  reference_type: 'sale' | 'fee_collection' | 'visitor_entry';
  reference_id: number;
  amount: string;
  issued_date: string;
  issued_by: number | null;
  pdf_file: string | null;
  created_at: string;
}

export interface FeeCollection {
  id: number;
  member: number | null;
  member_name: string | null;
  fee_type: 'membership' | 'renewal' | 'royalty' | 'other';
  amount: string;
  amount_paid: string;
  payment_status: 'paid' | 'due' | 'partial';
  receipt_no: string | null;
  description: string;
  created_at: string;
  updated_at: string;
}

export interface CommitteeMember {
  id: number;
  member: number;
  member_name: string;
  position: 'chair' | 'vice_chair' | 'secretary' | 'joint_secretary' | 'treasurer' | 'member';
  gender: string;
  caste_ethnicity: string;
  term_start: string;
  term_end: string;
  status: 'active' | 'vacant' | 'removed';
  subcommittees: number[];
  subcommittee_names: string[];
  created_at: string;
  updated_at: string;
}

export interface CashTransaction {
  id: number;
  type: 'income' | 'expense';
  source_or_purpose: string;
  amount: string;
  requires_committee_approval: boolean;
  approved_by: number | null;
  created_at: string;
  updated_at: string;
}

export interface Audit {
  id: number;
  fiscal_year: string;
  total_income: string;
  audit_tier: 'internal' | 'external';
  auditor_name: string;
  findings: string;
  irregularities_recovered: string;
  created_at: string;
  updated_at: string;
}

export interface OffenseReport {
  id: number;
  reported_by: number | null;
  accused_name: string;
  offense_type: string;
  description: string;
  report_date: string;
  status: 'reported' | 'investigating' | 'resolved' | 'escalated_to_court';
  damage_value: string | null;
  fine_amount: string | null;
  resolution: 'fine_paid' | 'escalated' | 'dismissed' | null;
  informant: number | null;
  evidence_count: number;
  hearings_count: number;
  created_at: string;
  updated_at: string;
}

export interface VisitorEntry {
  id: number;
  entry_date: string;
  visit_purpose: 'general_visit' | 'study_research';
  visitor_count: number;
  days: number;
  fee_waived: boolean;
  total_amount: string;
  receipt_no: string | null;
  created_at: string;
  updated_at: string;
}
```

---

## Appendix C: Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `NEXT_PUBLIC_API_BASE_URL` | Yes | Base URL for client-side API calls |
| `API_BASE_URL` | Yes | Base URL for server-side API calls |
| `NEXT_PUBLIC_APP_URL` | Yes | Public app URL for OAuth redirects |
| `NEXT_PUBLIC_APP_NAME` | No | App name shown in UI |
| `GOOGLE_CLIENT_ID` | No | Reserved for future Google OAuth (not required now) |

---

## Appendix D: Known Backend Gaps

Before production, ensure the backend team addresses:

1. ~~**No login endpoint**~~ — resolved at `POST /api/v1/core/auth/login/`.
2. ~~**No logout endpoint**~~ — resolved at `POST /api/v1/core/auth/logout/`.
4. **No API schema endpoint** — configure `drf-spectacular`.
5. **Media serving in development** — serve `/media/` receipts.
6. **CSRF handling** — document token acquisition for session auth.
7. **Membership renewal workflow** — provide dedicated service endpoint.

---

**End of document.**
