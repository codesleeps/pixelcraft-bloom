import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Filter, Plus, Download, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { DashboardLayout } from '@/components/DashboardLayout';
import { useToast } from '@/hooks/use-toast';
import { authenticatedFetch } from '@/lib/api';

interface Lead {
  id: string;
  name: string;
  email: string;
  company: string;
  phone?: string;
  status: string;
  lead_score?: number;
  services_interested?: string[];
  budget_range?: string;
  timeline?: string;
  created_at: string;
  assigned_to?: string;
}

const statusColors: Record<string, string> = {
  received: 'bg-blue-100 text-blue-800',
  contacted: 'bg-yellow-100 text-yellow-800',
  qualified: 'bg-purple-100 text-purple-800',
  converted: 'bg-green-100 text-green-800',
  lost: 'bg-red-100 text-red-800',
};

const LeadsList: React.FC = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [leads, setLeads] = useState<Lead[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const limit = 50;

  useEffect(() => {
    fetchLeads();
  }, [page, statusFilter, searchQuery]);

  const fetchLeads = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        limit: limit.toString(),
        offset: ((page - 1) * limit).toString(),
      });

      if (statusFilter && statusFilter !== 'all') {
        params.append('status', statusFilter);
      }

      if (searchQuery) {
        params.append('search', searchQuery);
      }

      const response = await authenticatedFetch(
        `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/leads?${params}`
      );

      if (!response.ok) {
        throw new Error('Failed to fetch leads');
      }

      const data = await response.json();
      setLeads(data.items || []);
      setTotal(data.total || 0);
    } catch (error) {
      console.error('Error fetching leads:', error);
      toast({
        title: 'Error',
        description: 'Failed to fetch leads. Please try again.',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (value: string) => {
    setSearchQuery(value);
    setPage(1); // Reset to first page on new search
  };

  const handleStatusFilter = (value: string) => {
    setStatusFilter(value);
    setPage(1); // Reset to first page on filter change
  };

  const getScoreBadge = (score?: number) => {
    if (!score) return null;

    let variant: 'default' | 'secondary' | 'destructive' | 'outline' = 'outline';
    if (score >= 75) variant = 'default';
    else if (score >= 50) variant = 'secondary';
    else if (score < 50) variant = 'destructive';

    return (
      <Badge variant={variant} className="font-mono">
        {score}
      </Badge>
    );
  };

  const exportLeads = () => {
    // Simple CSV export
    const headers = ['ID', 'Name', 'Email', 'Company', 'Status', 'Score', 'Created'];
    const rows = leads.map(lead => [
      lead.id,
      lead.name,
      lead.email,
      lead.company || '',
      lead.status,
      lead.lead_score?.toString() || '',
      new Date(lead.created_at).toLocaleDateString(),
    ]);

    const csv = [headers, ...rows].map(row => row.join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `leads-${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <DashboardLayout>
      <div className="container mx-auto py-8">
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-3xl">Leads Management</CardTitle>
                <CardDescription>
                  View and manage all your leads in one place
                </CardDescription>
              </div>
              <Button onClick={() => navigate('/dashboard/leads/new')}>
                <Plus className="mr-2 h-4 w-4" />
                New Lead
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {/* Filters and Search */}
            <div className="flex flex-col md:flex-row gap-4 mb-6">
              <div className="flex-1">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
                  <Input
                    placeholder="Search by name, email, or company..."
                    value={searchQuery}
                    onChange={(e) => handleSearch(e.target.value)}
                    className="pl-10"
                  />
                </div>
              </div>
              <Select value={statusFilter} onValueChange={handleStatusFilter}>
                <SelectTrigger className="w-[200px]">
                  <Filter className="mr-2 h-4 w-4" />
                  <SelectValue placeholder="Filter by status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Statuses</SelectItem>
                  <SelectItem value="received">Received</SelectItem>
                  <SelectItem value="contacted">Contacted</SelectItem>
                  <SelectItem value="qualified">Qualified</SelectItem>
                  <SelectItem value="converted">Converted</SelectItem>
                  <SelectItem value="lost">Lost</SelectItem>
                </SelectContent>
              </Select>
              <Button variant="outline" onClick={fetchLeads}>
                <RefreshCw className="mr-2 h-4 w-4" />
                Refresh
              </Button>
              <Button variant="outline" onClick={exportLeads}>
                <Download className="mr-2 h-4 w-4" />
                Export
              </Button>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
              <Card>
                <CardContent className="pt-6">
                  <div className="text-2xl font-bold">{total}</div>
                  <p className="text-xs text-muted-foreground">Total Leads</p>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="pt-6">
                  <div className="text-2xl font-bold">
                    {leads.filter(l => l.status === 'received').length}
                  </div>
                  <p className="text-xs text-muted-foreground">New Leads</p>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="pt-6">
                  <div className="text-2xl font-bold">
                    {leads.filter(l => l.status === 'qualified').length}
                  </div>
                  <p className="text-xs text-muted-foreground">Qualified</p>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="pt-6">
                  <div className="text-2xl font-bold">
                    {leads.filter(l => l.status === 'converted').length}
                  </div>
                  <p className="text-xs text-muted-foreground">Converted</p>
                </CardContent>
              </Card>
            </div>

            {/* Table */}
            {loading ? (
              <div className="flex justify-center items-center py-12">
                <RefreshCw className="h-8 w-8 animate-spin text-primary" />
              </div>
            ) : leads.length === 0 ? (
              <div className="text-center py-12">
                <p className="text-muted-foreground">No leads found</p>
              </div>
            ) : (
              <div className="rounded-md border">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Name</TableHead>
                      <TableHead>Company</TableHead>
                      <TableHead>Email</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Score</TableHead>
                      <TableHead>Services</TableHead>
                      <TableHead>Created</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {leads.map((lead) => (
                      <TableRow
                        key={lead.id}
                        className="cursor-pointer hover:bg-muted/50"
                        onClick={() => navigate(`/dashboard/leads/${lead.id}`)}
                      >
                        <TableCell className="font-medium">{lead.name}</TableCell>
                        <TableCell>{lead.company || '-'}</TableCell>
                        <TableCell>{lead.email}</TableCell>
                        <TableCell>
                          <Badge className={statusColors[lead.status] || 'bg-gray-100'}>
                            {lead.status}
                          </Badge>
                        </TableCell>
                        <TableCell>{getScoreBadge(lead.lead_score)}</TableCell>
                        <TableCell>
                          <div className="flex gap-1 flex-wrap">
                            {lead.services_interested?.slice(0, 2).map((service) => (
                              <Badge key={service} variant="outline" className="text-xs">
                                {service}
                              </Badge>
                            ))}
                            {(lead.services_interested?.length || 0) > 2 && (
                              <Badge variant="outline" className="text-xs">
                                +{(lead.services_interested?.length || 0) - 2}
                              </Badge>
                            )}
                          </div>
                        </TableCell>
                        <TableCell>
                          {new Date(lead.created_at).toLocaleDateString()}
                        </TableCell>
                        <TableCell className="text-right">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={(e) => {
                              e.stopPropagation();
                              navigate(`/dashboard/leads/${lead.id}`);
                            }}
                          >
                            View
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}

            {/* Pagination */}
            {total > limit && (
              <div className="flex items-center justify-between mt-4">
                <p className="text-sm text-muted-foreground">
                  Showing {(page - 1) * limit + 1} to {Math.min(page * limit, total)} of {total} leads
                </p>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setPage(p => Math.max(1, p - 1))}
                    disabled={page === 1}
                  >
                    Previous
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setPage(p => p + 1)}
                    disabled={page * limit >= total}
                  >
                    Next
                  </Button>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
};

export default LeadsList;
