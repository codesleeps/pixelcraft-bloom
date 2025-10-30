import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQueryClient } from '@tanstack/react-query';
import { DashboardLayout } from '@/components/DashboardLayout';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { useAuth } from '@/hooks/useAuth';
import { useAnalytics } from '@/hooks/useAnalytics';
import { useLeadTrends, useConversationTrends, useServiceRecommendations, useAgentPerformance } from '@/hooks/useAnalyticsTrends';
import { useRecentActivity } from '@/hooks/useRecentActivity';
import { useWebSocket } from '@/hooks/useWebSocket';
import { useNotifications } from '@/hooks/useNotifications';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { ChartContainer, ChartTooltip, ChartTooltipContent, ChartLegend, ChartLegendContent } from '@/components/ui/chart';
import { format } from 'date-fns';
import { Users, MessageSquare, TrendingUp, DollarSign, MessageSquare as MessageSquareIcon, Calendar, Wifi, WifiOff, AlertTriangle } from 'lucide-react';
import { toast } from 'sonner';

const getErrorMessage = (error: any, context: string) => {
  const message = error?.message || '';
  let title = 'Error Loading Data';
  let description = `Unable to load ${context}. Please try again.`;
  const actions: Array<{ label: string; onClick: () => void }> = [];

  if (message.includes('401') || message.includes('Authentication')) {
    title = 'Session Expired';
    description = 'Please sign in again.';
    actions.push({ label: 'Sign In', onClick: () => window.location.href = '/login' });
  } else if (message.includes('5xx') || message.includes('Server error')) {
    title = 'Server Error';
    description = 'Our servers are experiencing issues. Please try again in a few minutes.';
    actions.push({ label: 'Retry', onClick: () => window.location.reload() });
  } else if (message.includes('Network') || message.includes('fetch failed')) {
    title = 'Connection Error';
    description = 'Please check your internet connection and try again.';
    actions.push({ label: 'Retry', onClick: () => window.location.reload() });
  } else if (message.includes('timeout')) {
    title = 'Request Timeout';
    description = 'The request took too long. Please try again.';
    actions.push({ label: 'Retry', onClick: () => window.location.reload() });
  } else {
    actions.push({ label: 'Retry', onClick: () => window.location.reload() });
  }

  return { title, description, actions };
};

export default function Dashboard() {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const { user, role } = useAuth();
  const { data: analyticsData, loading: analyticsLoading, error: analyticsError } = useAnalytics();
  const { isConnected: wsConnected, error: wsError } = useWebSocket();
  const { notifications } = useNotifications({ unread_only: true, limit: 5 });
  useEffect(() => {
    if (wsError) {
      toast.error('WebSocket Error', {
        description: `${wsError}. Real-time updates unavailable. Data will refresh periodically.`,
      });
    }
  }, [wsError]);
  useEffect(() => {
    if (!notifications) return;
    
    const now = new Date();
    const recentNotifications = notifications.filter(n => {
      const createdAt = new Date(n.created_at);
      const ageInSeconds = (now.getTime() - createdAt.getTime()) / 1000;
      return ageInSeconds < 10 && !shownNotificationsRef.current.has(n.id);
    });
    
    recentNotifications.forEach(notification => {
      if (notification.severity === 'error' || notification.severity === 'warning') {
        toast.error(notification.title, { 
          description: notification.message, 
          action: notification.action_url ? { 
            label: 'View', 
            onClick: () => navigate(notification.action_url) 
          } : undefined 
        });
      } else if (notification.severity === 'success') {
        toast.success(notification.title, { description: notification.message });
      }
      shownNotificationsRef.current.add(notification.id);
    });
  }, [notifications, navigate]);
  const [timeRange, setTimeRange] = useState('30d');
  const navigate = useNavigate();
  const shownNotificationsRef = useRef<Set<string>>(new Set());

  const getTimeRangeParams = (range: string) => {
    const now = new Date();
    let startDate = new Date();
    switch (range) {
      case '24h':
        startDate.setHours(startDate.getHours() - 24);
        break;
      case '7d':
        startDate.setDate(startDate.getDate() - 7);
        break;
      case '30d':
        startDate.setDate(startDate.getDate() - 30);
        break;
    }
    return {
      start_date: startDate.toISOString(),
      end_date: now.toISOString(),
    };
  };

  const timeRangeParams = getTimeRangeParams(timeRange);

  const { data: leadTrendsData, isLoading: leadTrendsLoading, error: leadTrendsError } = useLeadTrends({ timeRange: timeRangeParams, aggregation: 'daily' });
  const { data: conversationTrendsData, isLoading: conversationTrendsLoading, error: conversationTrendsError } = useConversationTrends({ timeRange: timeRangeParams, aggregation: 'daily' });
  const { data: serviceRecommendationsData, isLoading: serviceRecommendationsLoading, error: serviceRecommendationsError } = useServiceRecommendations();
  const { data: agentPerformanceData, isLoading: agentPerformanceLoading, error: agentPerformanceError } = useAgentPerformance({ timeRange: timeRangeParams });

  const { data: recentActivityData, isLoading: recentActivityLoading, error: recentActivityError } = useRecentActivity({ limit: 10 });

  const displayName = user?.user_metadata?.display_name || user?.email;

  const leadChartConfig = {
    leads: {
      label: 'Leads',
      color: 'hsl(var(--chart-1))',
    },
  };

  const conversationChartConfig = {
    conversations: {
      label: 'Conversations',
      color: 'hsl(var(--chart-2))',
    },
  };

  const serviceChartConfig = {
    acceptance_rate: {
      label: 'Acceptance Rate',
      color: 'hsl(var(--chart-3))',
    },
  };

  const agentChartConfig = {
    success_rate: {
      label: 'Success Rate',
      color: 'hsl(var(--chart-4))',
    },
    avg_execution_time: {
      label: 'Avg Execution Time',
      color: 'hsl(var(--chart-5))',
    },
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {analyticsError && (
          <Alert variant="destructive">
            <AlertTriangle className="h-4 w-4" />
            <AlertTitle>{getErrorMessage(analyticsError, 'analytics data').title}</AlertTitle>
            <AlertDescription>
              {getErrorMessage(analyticsError, 'analytics data').description}
              <div className="mt-2 flex gap-2">
                {getErrorMessage(analyticsError, 'analytics data').actions.map(action => (
                  <Button key={action.label} size="sm" onClick={action.onClick}>
                    {action.label}
                  </Button>
                ))}
                <Button size="sm" onClick={() => window.open('mailto:support@example.com', '_blank')}>
                  Contact Support
                </Button>
              </div>
            </AlertDescription>
          </Alert>
        )}
        <div className="flex justify-between items-center">
          <h2 className="text-3xl font-bold tracking-tight">Welcome back, {displayName}!</h2>
          <Select value={timeRange} onValueChange={setTimeRange}>
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="Select time range" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="24h">Last 24 Hours</SelectItem>
              <SelectItem value="7d">Last 7 Days</SelectItem>
              <SelectItem value="30d">Last 30 Days</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="flex items-center gap-2">
          <Badge variant={wsConnected ? "default" : wsError ? "destructive" : "secondary"}>
            {wsConnected ? <Wifi className="h-3 w-3" /> : <WifiOff className="h-3 w-3" />} {wsConnected ? "Live" : wsError ? "Error" : "Offline"}
          </Badge>
        </div>

        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Leads</CardTitle>
              <Users className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              {analyticsLoading ? (
                <div className="space-y-2">
                  <Skeleton className="h-8 w-16" />
                  <Skeleton className="h-4 w-24" />
                </div>
              ) : (
                <>
                  <div className="text-2xl font-bold">{analyticsData?.total_leads?.value ?? 'N/A'}</div>
                  <p className="text-xs text-muted-foreground">{analyticsData?.total_leads?.change ?? '-'}% from last month</p>
                </>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Active Conversations</CardTitle>
              <MessageSquare className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              {analyticsLoading ? (
                <div className="space-y-2">
                  <Skeleton className="h-8 w-16" />
                  <Skeleton className="h-4 w-24" />
                </div>
              ) : (
                <>
                  <div className="text-2xl font-bold">{analyticsData?.active_conversations?.value ?? 'N/A'}</div>
                  <p className="text-xs text-muted-foreground">{analyticsData?.active_conversations?.change ?? '-'}% from last month</p>
                </>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Conversion Rate</CardTitle>
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              {analyticsLoading ? (
                <div className="space-y-2">
                  <Skeleton className="h-8 w-16" />
                  <Skeleton className="h-4 w-24" />
                </div>
              ) : (
                <>
                  <div className="text-2xl font-bold">{analyticsData?.conversion_rate?.value ?? 'N/A'}%</div>
                  <p className="text-xs text-muted-foreground">{analyticsData?.conversion_rate?.change ?? '-'}% from last month</p>
                </>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Revenue</CardTitle>
              <DollarSign className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              {analyticsLoading ? (
                <div className="space-y-2">
                  <Skeleton className="h-8 w-16" />
                  <Skeleton className="h-4 w-24" />
                </div>
              ) : (
                <>
                  <div className="text-2xl font-bold">${analyticsData?.total_revenue?.value ?? 'N/A'}</div>
                  <p className="text-xs text-muted-foreground">{analyticsData?.total_revenue?.change ?? '-'}% from last month</p>
                </>
              )}
            </CardContent>
          </Card>
        </div>

        {role === 'admin' && (
          <div className="space-y-4">
            <h3 className="text-xl font-semibold">Analytics Overview</h3>
            <div className="grid gap-4 md:grid-cols-2">
              <Card>
                <CardHeader>
                  <CardTitle>Lead Generation Trends</CardTitle>
                  <CardDescription>New leads over time</CardDescription>
                </CardHeader>
                <CardContent>
                  {leadTrendsLoading ? (
                    <div className="space-y-2">
                      <Skeleton className="h-[300px] w-full" />
                      <p className="text-sm text-muted-foreground text-center">Loading chart data...</p>
                    </div>
                  ) : leadTrendsError ? (
                    (() => {
                      const leadError = getErrorMessage(leadTrendsError, 'lead trends data');
                      return (
                        <Alert variant="destructive">
                          <AlertTriangle className="h-4 w-4" />
                          <AlertTitle>{leadError.title}</AlertTitle>
                          <AlertDescription>
                            {leadError.description}
                            <div className="mt-2 flex gap-2">
                              {leadError.actions.map(action => (
                                <Button key={action.label} size="sm" onClick={action.onClick}>
                                  {action.label}
                                </Button>
                              ))}
                            </div>
                          </AlertDescription>
                        </Alert>
                      );
                    })()
                  ) : (
                    <ChartContainer config={leadChartConfig} className="h-[300px]">
                      <LineChart data={leadTrendsData}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="date" tickFormatter={(date) => format(new Date(date), 'MMM dd')} />
                        <YAxis />
                        <ChartTooltip content={<ChartTooltipContent />} />
                        <Line type="monotone" dataKey="value" stroke="var(--color-leads)" strokeWidth={2} />
                      </LineChart>
                    </ChartContainer>
                  )}
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Conversation Activity</CardTitle>
                  <CardDescription>Conversations over time</CardDescription>
                </CardHeader>
                <CardContent>
                  {conversationTrendsLoading ? (
                    <div className="space-y-2">
                      <Skeleton className="h-[300px] w-full" />
                      <p className="text-sm text-muted-foreground text-center">Loading chart data...</p>
                    </div>
                  ) : conversationTrendsError ? (
                    (() => {
                      const convError = getErrorMessage(conversationTrendsError, 'conversation trends data');
                      return (
                        <Alert variant="destructive">
                          <AlertTriangle className="h-4 w-4" />
                          <AlertTitle>{convError.title}</AlertTitle>
                          <AlertDescription>
                            {convError.description}
                            <div className="mt-2 flex gap-2">
                              {convError.actions.map(action => (
                                <Button key={action.label} size="sm" onClick={action.onClick}>
                                  {action.label}
                                </Button>
                              ))}
                            </div>
                          </AlertDescription>
                        </Alert>
                      );
                    })()
                  ) : (
                    <ChartContainer config={conversationChartConfig} className="h-[300px]">
                      <LineChart data={conversationTrendsData}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="date" tickFormatter={(date) => format(new Date(date), 'MMM dd')} />
                        <YAxis />
                        <ChartTooltip content={<ChartTooltipContent />} />
                        <Line type="monotone" dataKey="value" stroke="var(--color-conversations)" strokeWidth={2} />
                      </LineChart>
                    </ChartContainer>
                  )}
                </CardContent>
              </Card>

              <Card className="md:col-span-2">
                <CardHeader>
                  <CardTitle>Service Recommendations</CardTitle>
                  <CardDescription>Acceptance rates by service</CardDescription>
                </CardHeader>
                <CardContent>
                  {serviceRecommendationsLoading ? (
                    <div className="space-y-2">
                      <Skeleton className="h-[300px] w-full" />
                      <p className="text-sm text-muted-foreground text-center">Loading chart data...</p>
                    </div>
                  ) : serviceRecommendationsError ? (
                    (() => {
                      const servError = getErrorMessage(serviceRecommendationsError, 'service recommendations data');
                      return (
                        <Alert variant="destructive">
                          <AlertTriangle className="h-4 w-4" />
                          <AlertTitle>{servError.title}</AlertTitle>
                          <AlertDescription>
                            {servError.description}
                            <div className="mt-2 flex gap-2">
                              {servError.actions.map(action => (
                                <Button key={action.label} size="sm" onClick={action.onClick}>
                                  {action.label}
                                </Button>
                              ))}
                            </div>
                          </AlertDescription>
                        </Alert>
                      );
                    })()
                  ) : (
                    <ChartContainer config={serviceChartConfig} className="h-[300px]">
                      <BarChart data={serviceRecommendationsData}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="service_name" />
                        <YAxis />
                        <ChartTooltip content={<ChartTooltipContent />} />
                        <Bar dataKey="acceptance_rate" fill="var(--color-acceptance_rate)" />
                      </BarChart>
                    </ChartContainer>
                  )}
                </CardContent>
              </Card>

              {role === 'admin' && (
                <Card className="md:col-span-2">
                  <CardHeader>
                    <CardTitle>Agent Performance</CardTitle>
                    <CardDescription>Success rates by agent type</CardDescription>
                  </CardHeader>
                  <CardContent>
                    {agentPerformanceLoading ? (
                      <div className="space-y-2">
                        <Skeleton className="h-[300px] w-full" />
                        <p className="text-sm text-muted-foreground text-center">Loading chart data...</p>
                      </div>
                    ) : agentPerformanceError ? (
                      (() => {
                        const agentError = getErrorMessage(agentPerformanceError, 'agent performance data');
                        return (
                          <Alert variant="destructive">
                            <AlertTriangle className="h-4 w-4" />
                            <AlertTitle>{agentError.title}</AlertTitle>
                            <AlertDescription>
                              {agentError.description}
                              <div className="mt-2 flex gap-2">
                                {agentError.actions.map(action => (
                                  <Button key={action.label} size="sm" onClick={action.onClick}>
                                    {action.label}
                                  </Button>
                                ))}
                              </div>
                            </AlertDescription>
                          </Alert>
                        );
                      })()
                    ) : (
                      <ChartContainer config={agentChartConfig} className="h-[300px]">
                        <BarChart data={agentPerformanceData}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="agent_type" />
                          <YAxis />
                          <ChartTooltip content={<ChartTooltipContent />} />
                          <ChartLegend content={<ChartLegendContent />} />
                          <Bar dataKey="success_rate" fill="var(--color-success_rate)" />
                          <Bar dataKey="avg_execution_time" fill="var(--color-avg_execution_time)" />
                        </BarChart>
                      </ChartContainer>
                    )}
                  </CardContent>
                </Card>
              )}
            </div>
          </div>
        )}

        {role === 'user' && (
          <div className="space-y-4">
            <h3 className="text-xl font-semibold">Recent Activity</h3>
            <Card>
              <CardHeader>
                <CardTitle>Your Recent Activity</CardTitle>
                <CardDescription>Latest conversations and appointments</CardDescription>
              </CardHeader>
              <CardContent className="max-h-96 overflow-y-auto">
                {recentActivityLoading ? (
                  <div className="space-y-2">
                    {Array.from({ length: 5 }).map((_, i) => (
                      <Skeleton key={i} className="h-12 w-full" />
                    ))}
                  </div>
                ) : recentActivityError ? (
                  (() => {
                    const activityError = getErrorMessage(recentActivityError, 'recent activity data');
                    return (
                      <Alert variant="destructive">
                        <AlertTriangle className="h-4 w-4" />
                        <AlertTitle>{activityError.title}</AlertTitle>
                        <AlertDescription>
                          {activityError.description}
                          <div className="mt-2 flex gap-2">
                            {activityError.actions.map(action => (
                              <Button key={action.label} size="sm" onClick={action.onClick}>
                                {action.label}
                              </Button>
                            ))}
                          </div>
                        </AlertDescription>
                      </Alert>
                    );
                  })()
                ) : recentActivityData && recentActivityData.length > 0 ? (
                  recentActivityData.map((item, index) => (
                    <div key={index} className="flex items-center justify-between py-2 border-b last:border-0">
                      <div className="flex items-center space-x-2">
                        {item.type === 'conversation' ? (
                          <MessageSquareIcon className="h-4 w-4 text-muted-foreground" />
                        ) : (
                          <Calendar className="h-4 w-4 text-muted-foreground" />
                        )}
                        <span className="text-sm font-medium">
                          {item.type === 'conversation' ? 'Conversation' : 'Appointment'}
                        </span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Badge variant={item.data.status === 'completed' ? 'default' : 'secondary'}>
                          {item.data.status}
                        </Badge>
                        <span className="text-sm text-muted-foreground">
                          {format(new Date(item.created_at), 'MMM dd, yyyy HH:mm')}
                        </span>
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="text-sm text-muted-foreground">No recent activity.</p>
                )}
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
