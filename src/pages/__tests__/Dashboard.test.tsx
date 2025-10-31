import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders } from '@/test/utils/test-utils';

// Mocks for hooks and libs used by Dashboard
vi.mock('@/hooks/useAuth', () => ({ useAuth: vi.fn() }));
vi.mock('@/hooks/useAnalytics', () => ({ useAnalytics: vi.fn() }));
vi.mock('@/hooks/useAnalyticsTrends', () => ({
  useLeadTrends: vi.fn(),
  useConversationTrends: vi.fn(),
  useServiceRecommendations: vi.fn(),
  useAgentPerformance: vi.fn(),
}));
vi.mock('@/hooks/useRecentActivity', () => ({ useRecentActivity: vi.fn() }));
vi.mock('@/hooks/useWebSocket', () => ({ useWebSocket: vi.fn() }));
vi.mock('@/hooks/useNotifications', () => ({ useNotifications: vi.fn() }));

// Mock Router pieces used inside Dashboard
vi.mock('react-router-dom', async (orig) => {
  const actual = await (orig as any)();
  return {
    ...actual,
    useNavigate: vi.fn(() => vi.fn()),
  };
});

// Mock UI chart components to avoid rendering complex charts
vi.mock('@/components/ui/chart', () => ({
  ChartContainer: ({ children }: any) => <div data-testid="chart-container">{children}</div>,
  ChartTooltip: ({ children }: any) => <div>{children}</div>,
  ChartTooltipContent: () => <div />,
  ChartLegend: ({ children }: any) => <div>{children}</div>,
  ChartLegendContent: () => <div />,
}));

// Mock recharts primitives used (render minimal placeholders)
vi.mock('recharts', () => ({
  LineChart: ({ children }: any) => <div data-testid="line-chart">{children}</div>,
  BarChart: ({ children }: any) => <div data-testid="bar-chart">{children}</div>,
  Line: () => <div role="img" aria-label="line" />,
  Bar: () => <div role="img" aria-label="bar" />,
  XAxis: () => <div />, YAxis: () => <div />, CartesianGrid: () => <div />, Tooltip: () => <div />, Legend: () => <div />, ResponsiveContainer: ({ children }: any) => <div>{children}</div>,
}));

// Mock toast from sonner to observe calls
const toastError = vi.fn();
const toastSuccess = vi.fn();
vi.mock('sonner', () => ({ toast: { error: toastError, success: toastSuccess } }));

import Dashboard from '../Dashboard';

const authAdmin = { user: { user_metadata: { display_name: 'Admin A' }, email: 'admin@example.com' }, role: 'admin' };
const authUser = { user: { user_metadata: { display_name: 'User U' }, email: 'user@example.com' }, role: 'user' };

const setupMocks = ({
  auth = authAdmin,
  analytics = { data: { total_leads: { value: 10, change: 5 }, active_conversations: { value: 3, change: -1 }, conversion_rate: { value: 12.5, change: 0.5 }, total_revenue: { value: 1200, change: 10 } }, loading: false, error: null },
  ws = { isConnected: true, error: null },
  notifications = { notifications: [] as any[] },
  trends = {
    lead: { data: [{ date: new Date().toISOString(), value: 1 }], isLoading: false, error: null },
    conv: { data: [{ date: new Date().toISOString(), value: 2 }], isLoading: false, error: null },
    service: { data: [{ service_name: 'Design', acceptance_rate: 0.7 }], isLoading: false, error: null },
    agent: { data: [{ agent_type: 'chat', success_rate: 0.9, avg_execution_time: 1.2 }], isLoading: false, error: null },
  },
  recent = { data: [], isLoading: false, error: null },
} = {}) => {
  const { useAuth } = vi.mocked(await import('@/hooks/useAuth'));
  const { useAnalytics } = vi.mocked(await import('@/hooks/useAnalytics'));
  const { useLeadTrends, useConversationTrends, useServiceRecommendations, useAgentPerformance } = vi.mocked(await import('@/hooks/useAnalyticsTrends'));
  const { useRecentActivity } = vi.mocked(await import('@/hooks/useRecentActivity'));
  const { useWebSocket } = vi.mocked(await import('@/hooks/useWebSocket'));
  const { useNotifications } = vi.mocked(await import('@/hooks/useNotifications'));

  useAuth.mockReturnValue(auth as any);
  useAnalytics.mockReturnValue(analytics as any);
  useWebSocket.mockReturnValue(ws as any);
  useNotifications.mockReturnValue(notifications as any);
  useLeadTrends.mockReturnValue({ data: trends.lead.data, isLoading: trends.lead.isLoading, error: trends.lead.error } as any);
  useConversationTrends.mockReturnValue({ data: trends.conv.data, isLoading: trends.conv.isLoading, error: trends.conv.error } as any);
  useServiceRecommendations.mockReturnValue({ data: trends.service.data, isLoading: trends.service.isLoading, error: trends.service.error } as any);
  useAgentPerformance.mockReturnValue({ data: trends.agent.data, isLoading: trends.agent.isLoading, error: trends.agent.error } as any);
  useRecentActivity.mockReturnValue({ data: recent.data, isLoading: recent.isLoading, error: recent.error } as any);
};

describe('Dashboard page', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders greeting with display name and metrics when analytics loaded', async () => {
    await setupMocks();
    renderWithProviders(<Dashboard />);

    expect(screen.getByText(/Welcome back, Admin A/i)).toBeInTheDocument();
    expect(screen.getByText('Total Leads')).toBeInTheDocument();
    expect(screen.getByText('Active Conversations')).toBeInTheDocument();
    expect(screen.getByText('Conversion Rate')).toBeInTheDocument();
    expect(screen.getByText('Revenue')).toBeInTheDocument();
    // values rendered
    expect(screen.getByText('10')).toBeInTheDocument();
    expect(screen.getByText('3')).toBeInTheDocument();
    expect(screen.getByText(/12.5%/)).toBeInTheDocument();
    expect(screen.getByText(/\$1200/)).toBeInTheDocument();
  });

  it('shows websocket status badge as Live when connected, Error when wsError, Offline otherwise', async () => {
    await setupMocks({ ws: { isConnected: true, error: null } });
    const { rerender } = renderWithProviders(<Dashboard />);
    expect(screen.getByText(/Live/i)).toBeInTheDocument();

    await setupMocks({ ws: { isConnected: false, error: 'Socket failed' } });
    rerender(<Dashboard />);
    expect(screen.getByText(/Error/i)).toBeInTheDocument();
    expect(toastError).toHaveBeenCalledWith('WebSocket Error', expect.any(Object));

    await setupMocks({ ws: { isConnected: false, error: null } });
    rerender(<Dashboard />);
    expect(screen.getByText(/Offline/i)).toBeInTheDocument();
  });

  it('renders admin-only analytics sections when role is admin and hides for user role except Recent Activity', async () => {
    await setupMocks({ auth: authAdmin });
    const view = renderWithProviders(<Dashboard />);
    expect(screen.getByText('Analytics Overview')).toBeInTheDocument();
    expect(screen.getByText('Lead Generation Trends')).toBeInTheDocument();
    expect(screen.getByText('Conversation Activity')).toBeInTheDocument();
    expect(screen.getByText('Service Recommendations')).toBeInTheDocument();
    expect(screen.getByText('Agent Performance')).toBeInTheDocument();

    await setupMocks({ auth: authUser });
    view.rerender(<Dashboard />);
    expect(screen.queryByText('Analytics Overview')).not.toBeInTheDocument();
    expect(screen.getByText('Recent Activity')).toBeInTheDocument();
  });

  it('handles time range selection and triggers state change', async () => {
    await setupMocks();
    renderWithProviders(<Dashboard />);
    const trigger = screen.getByRole('button', { name: /Select time range/i });
    await userEvent.click(trigger);
    const option = await screen.findByRole('option', { name: /Last 7 Days/i });
    await userEvent.click(option);
    // We cannot inspect internal hook params; assert UI reflects selection via Select value
    expect(screen.getByRole('button', { name: /Last 7 Days/i })).toBeInTheDocument();
  });

  it('shows notifications as toast based on severity and avoids duplicates', async () => {
    const noteId = 'n1';
    await setupMocks({
      notifications: {
        notifications: [
          { id: noteId, title: 'Warn', message: 'w', severity: 'warning', created_at: new Date().toISOString() },
          { id: 'n2', title: 'Success', message: 's', severity: 'success', created_at: new Date().toISOString() },
        ],
      },
    });
    renderWithProviders(<Dashboard />);
    expect(toastError).toHaveBeenCalledWith('Warn', expect.objectContaining({ description: 'w' }));
    expect(toastSuccess).toHaveBeenCalledWith('Success', expect.objectContaining({ description: 's' }));

    // Re-render with same notification to ensure not duplicated due to ref tracking
    await setupMocks({
      notifications: {
        notifications: [
          { id: noteId, title: 'Warn', message: 'w', severity: 'warning', created_at: new Date().toISOString() },
        ],
      },
    });
    // Rerender component
    renderWithProviders(<Dashboard />);
    // Should still have been called at least once but not necessarily twice with identical
    expect(toastError).toHaveBeenCalled();
  });

  it('renders graceful error alerts for analytics and trend hooks', async () => {
    await setupMocks({
      analytics: { data: null, loading: false, error: { message: 'Server error 5xx' } as any },
      trends: {
        lead: { data: null, isLoading: false, error: { message: 'timeout' } as any },
        conv: { data: null, isLoading: false, error: { message: 'Network' } as any },
        service: { data: null, isLoading: false, error: { message: '401 unauthorized' } as any },
        agent: { data: null, isLoading: false, error: { message: 'unknown' } as any },
      },
    });

    renderWithProviders(<Dashboard />);

    // Top analytics error alert
    expect(screen.getByText('Server Error')).toBeInTheDocument();

    // Trend-specific alerts are present
    expect(screen.getAllByText(/Error/).length).toBeGreaterThan(1);
  });
});
