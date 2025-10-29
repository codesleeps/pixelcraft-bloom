import { useAnalytics } from '@/hooks/useAnalytics';

import React from 'react';
import { DashboardLayout } from '@/components/DashboardLayout';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { useAuth } from '@/hooks/useAuth';
import { Users, MessageSquare, TrendingUp, DollarSign } from 'lucide-react';

export default function Dashboard() {
  const { user, role } = useAuth();
  const { data: analyticsData, loading: analyticsLoading, error: analyticsError } = useAnalytics();

  const displayName = user?.user_metadata?.display_name || user?.email;

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <h2 className="text-3xl font-bold tracking-tight">Welcome back, {displayName}!</h2>
        </div>

        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Leads</CardTitle>
              <Users className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{analyticsData?.totalLeads?.value ?? 'N/A'}</div>
              <p className="text-xs text-muted-foreground">{analyticsData?.totalLeads?.change ?? '-'}% from last month</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Active Conversations</CardTitle>
              <MessageSquare className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{analyticsData?.activeConversations?.value ?? 'N/A'}</div>
              <p className="text-xs text-muted-foreground">{analyticsData?.activeConversations?.change ?? '-'}% from last month</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Conversion Rate</CardTitle>
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{analyticsData?.conversionRate?.value ?? 'N/A'}%</div>
              <p className="text-xs text-muted-foreground">{analyticsData?.conversionRate?.change ?? '-'}% from last month</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Revenue</CardTitle>
              <DollarSign className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">${analyticsData?.revenue?.value ?? 'N/A'}</div>
              <p className="text-xs text-muted-foreground">{analyticsData?.revenue?.change ?? '-'}% from last month</p>
            </CardContent>
          </Card>
        </div>

        {role === 'admin' ? (
          <div className="space-y-4">
            <h3 className="text-xl font-semibold">System-wide Metrics</h3>
            <p>Admin view: System-wide metrics and user management options will be displayed here.</p>
            <Card>
              <CardHeader>
                <CardTitle>User Management</CardTitle>
                <CardDescription>Manage users and their roles</CardDescription>
              </CardHeader>
              <CardContent>
                <p>Placeholder for user management interface.</p>
              </CardContent>
            </Card>
          </div>
        ) : (
          <div className="space-y-4">
            <h3 className="text-xl font-semibold">Your Metrics</h3>
            <p>User view: Your personal metrics and activity will be displayed here.</p>
            <Card>
              <CardHeader>
                <CardTitle>Recent Activity</CardTitle>
                <CardDescription>Your latest interactions and updates</CardDescription>
              </CardHeader>
              <CardContent>
                <p>Placeholder for personal activity feed.</p>
              </CardContent>
            </Card>
          </div>
        )}

        <Alert>
          <AlertTitle>Upcoming Features</AlertTitle>
          <AlertDescription>
            Detailed widgets and interactive charts will be added in subsequent phases to provide deeper insights into your data.
          </AlertDescription>
        </Alert>
      </div>
    </DashboardLayout>
  );
}