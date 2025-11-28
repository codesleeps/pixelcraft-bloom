import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  Mail,
  Phone,
  Building,
  Calendar,
  DollarSign,
  Target,
  TrendingUp,
  MessageSquare,
  Save,
  RefreshCw,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { DashboardLayout } from '@/components/DashboardLayout';
import { useToast } from '@/hooks/use-toast';
import { Label } from '@/components/ui/label';

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
  notes?: string;
  created_at: string;
  assigned_to?: string;
  metadata?: {
    notes?: Array<{
      content: string;
      created_at: string;
      created_by?: string;
    }>;
    last_analysis?: {
      lead_score: {
        score: number;
        confidence: number;
        priority: string;
      };
      recommended_services: string[];
      key_insights: string[];
      suggested_actions: string[];
      estimated_value?: number;
    };
  };
}

const statusColors: Record<string, string> = {
  received: 'bg-blue-100 text-blue-800',
  contacted: 'bg-yellow-100 text-yellow-800',
  qualified: 'bg-purple-100 text-purple-800',
  converted: 'bg-green-100 text-green-800',
  lost: 'bg-red-100 text-red-800',
};

const LeadDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();
  const [lead, setLead] = useState<Lead | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [newNote, setNewNote] = useState('');
  const [editedLead, setEditedLead] = useState<Partial<Lead>>({});

  useEffect(() => {
    if (id) {
      fetchLead();
    }
  }, [id]);

  const fetchLead = async () => {
    setLoading(true);
    try {
      const response = await fetch(
        `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/leads/${id}`
      );

      if (!response.ok) {
        throw new Error('Failed to fetch lead');
      }

      const data = await response.json();
      setLead(data);
      setEditedLead({
        status: data.status,
        assigned_to: data.assigned_to,
      });
    } catch (error) {
      console.error('Error fetching lead:', error);
      toast({
        title: 'Error',
        description: 'Failed to fetch lead details. Please try again.',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const updateLead = async () => {
    if (!id) return;

    setSaving(true);
    try {
      const response = await fetch(
        `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/leads/${id}`,
        {
          method: 'PATCH',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(editedLead),
        }
      );

      if (!response.ok) {
        throw new Error('Failed to update lead');
      }

      toast({
        title: 'Success',
        description: 'Lead updated successfully.',
      });

      fetchLead();
    } catch (error) {
      console.error('Error updating lead:', error);
      toast({
        title: 'Error',
        description: 'Failed to update lead. Please try again.',
        variant: 'destructive',
      });
    } finally {
      setSaving(false);
    }
  };

  const addNote = async () => {
    if (!id || !newNote.trim()) return;

    setSaving(true);
    try {
      const response = await fetch(
        `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/leads/${id}`,
        {
          method: 'PATCH',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ notes: newNote }),
        }
      );

      if (!response.ok) {
        throw new Error('Failed to add note');
      }

      setNewNote('');
      toast({
        title: 'Success',
        description: 'Note added successfully.',
      });

      fetchLead();
    } catch (error) {
      console.error('Error adding note:', error);
      toast({
        title: 'Error',
        description: 'Failed to add note. Please try again.',
        variant: 'destructive',
      });
    } finally {
      setSaving(false);
    }
  };

  const analyzeLeadAI = async () => {
    if (!id) return;

    setAnalyzing(true);
    try {
      const response = await fetch(
        `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/leads/${id}/analyze`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) {
        throw new Error('Failed to analyze lead');
      }

      toast({
        title: 'Success',
        description: 'AI analysis completed successfully.',
      });

      fetchLead();
    } catch (error) {
      console.error('Error analyzing lead:', error);
      toast({
        title: 'Error',
        description: 'Failed to analyze lead. Please try again.',
        variant: 'destructive',
      });
    } finally {
      setAnalyzing(false);
    }
  };

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex justify-center items-center h-screen">
          <RefreshCw className="h-8 w-8 animate-spin text-primary" />
        </div>
      </DashboardLayout>
    );
  }

  if (!lead) {
    return (
      <DashboardLayout>
        <div className="container mx-auto py-8">
          <p>Lead not found</p>
        </div>
      </DashboardLayout>
    );
  }

  const analysis = lead.metadata?.last_analysis;

  return (
    <DashboardLayout>
      <div className="container mx-auto py-8">
        <div className="mb-6">
          <Button variant="ghost" onClick={() => navigate('/dashboard/leads')} className="mb-4">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Leads
          </Button>

          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold">{lead.name}</h1>
              <p className="text-muted-foreground">{lead.email}</p>
            </div>
            <div className="flex gap-2">
              <Button onClick={analyzeLeadAI} disabled={analyzing} variant="outline">
                <TrendingUp className="mr-2 h-4 w-4" />
                {analyzing ? 'Analyzing...' : 'Run AI Analysis'}
              </Button>
              <Button onClick={updateLead} disabled={saving}>
                <Save className="mr-2 h-4 w-4" />
                {saving ? 'Saving...' : 'Save Changes'}
              </Button>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            <Tabs defaultValue="details" className="w-full">
              <TabsList>
                <TabsTrigger value="details">Details</TabsTrigger>
                <TabsTrigger value="analysis">AI Analysis</TabsTrigger>
                <TabsTrigger value="activity">Activity</TabsTrigger>
              </TabsList>

              <TabsContent value="details" className="space-y-6">
                <Card>
                  <CardHeader>
                    <CardTitle>Contact Information</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label>Name</Label>
                        <div className="flex items-center gap-2 p-2 border rounded">
                          <span>{lead.name}</span>
                        </div>
                      </div>
                      <div className="space-y-2">
                        <Label>Email</Label>
                        <div className="flex items-center gap-2 p-2 border rounded">
                          <Mail className="h-4 w-4 text-muted-foreground" />
                          <span>{lead.email}</span>
                        </div>
                      </div>
                      <div className="space-y-2">
                        <Label>Company</Label>
                        <div className="flex items-center gap-2 p-2 border rounded">
                          <Building className="h-4 w-4 text-muted-foreground" />
                          <span>{lead.company || '-'}</span>
                        </div>
                      </div>
                      <div className="space-y-2">
                        <Label>Phone</Label>
                        <div className="flex items-center gap-2 p-2 border rounded">
                          <Phone className="h-4 w-4 text-muted-foreground" />
                          <span>{lead.phone || '-'}</span>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>Lead Information</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label>Budget Range</Label>
                        <div className="flex items-center gap-2 p-2 border rounded">
                          <DollarSign className="h-4 w-4 text-muted-foreground" />
                          <span>{lead.budget_range || '-'}</span>
                        </div>
                      </div>
                      <div className="space-y-2">
                        <Label>Timeline</Label>
                        <div className="flex items-center gap-2 p-2 border rounded">
                          <Calendar className="h-4 w-4 text-muted-foreground" />
                          <span>{lead.timeline || '-'}</span>
                        </div>
                      </div>
                    </div>
                    <div className="space-y-2">
                      <Label>Services Interested</Label>
                      <div className="flex gap-2 flex-wrap">
                        {lead.services_interested?.map((service) => (
                          <Badge key={service} variant="outline">
                            {service}
                          </Badge>
                        ))}
                      </div>
                    </div>
                    <div className="space-y-2">
                      <Label>Initial Notes</Label>
                      <p className="p-2 border rounded text-sm">{lead.notes || 'No notes provided'}</p>
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="analysis">
                <Card>
                  <CardHeader>
                    <CardTitle>AI Analysis Results</CardTitle>
                    <CardDescription>
                      AI-powered insights and recommendations for this lead
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-6">
                    {analysis ? (
                      <>
                        <div className="grid grid-cols-3 gap-4">
                          <div className="space-y-2">
                            <Label>Lead Score</Label>
                            <div className="text-3xl font-bold">{analysis.lead_score.score}</div>
                            <p className="text-sm text-muted-foreground">
                              {analysis.lead_score.confidence}% confidence
                            </p>
                          </div>
                          <div className="space-y-2">
                            <Label>Priority</Label>
                            <Badge className="text-lg uppercase">{analysis.lead_score.priority}</Badge>
                          </div>
                          <div className="space-y-2">
                            <Label>Estimated Value</Label>
                            <div className="text-2xl font-bold">
                              ${analysis.estimated_value?.toLocaleString() || 'TBD'}
                            </div>
                          </div>
                        </div>

                        <div className="space-y-2">
                          <Label>Recommended Services</Label>
                          <div className="flex gap-2 flex-wrap">
                            {analysis.recommended_services.map((service) => (
                              <Badge key={service} variant="secondary">
                                {service}
                              </Badge>
                            ))}
                          </div>
                        </div>

                        <div className="space-y-2">
                          <Label>Key Insights</Label>
                          <ul className="list-disc list-inside space-y-1">
                            {analysis.key_insights.map((insight, idx) => (
                              <li key={idx} className="text-sm">
                                {insight}
                              </li>
                            ))}
                          </ul>
                        </div>

                        <div className="space-y-2">
                          <Label>Suggested Actions</Label>
                          <ul className="list-disc list-inside space-y-1">
                            {analysis.suggested_actions.map((action, idx) => (
                              <li key={idx} className="text-sm">
                                {action}
                              </li>
                            ))}
                          </ul>
                        </div>
                      </>
                    ) : (
                      <div className="text-center py-12">
                        <p className="text-muted-foreground mb-4">
                          No AI analysis available yet
                        </p>
                        <Button onClick={analyzeLeadAI} disabled={analyzing}>
                          <TrendingUp className="mr-2 h-4 w-4" />
                          Run Analysis Now
                        </Button>
                      </div>
                    )}
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="activity">
                <Card>
                  <CardHeader>
                    <CardTitle>Notes & Activity</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="space-y-2">
                      <Label>Add Note</Label>
                      <Textarea
                        value={newNote}
                        onChange={(e) => setNewNote(e.target.value)}
                        placeholder="Add a note about this lead..."
                        rows={3}
                      />
                      <Button onClick={addNote} disabled={!newNote.trim() || saving}>
                        <MessageSquare className="mr-2 h-4 w-4" />
                        Add Note
                      </Button>
                    </div>

                    <div className="space-y-2">
                      <Label>Activity History</Label>
                      <div className="space-y-3">
                        {lead.metadata?.notes?.map((note, idx) => (
                          <div key={idx} className="border-l-2 border-primary pl-4 py-2">
                            <p className="text-sm">{note.content}</p>
                            <p className="text-xs text-muted-foreground mt-1">
                              {new Date(note.created_at).toLocaleString()}
                            </p>
                          </div>
                        ))}
                        {(!lead.metadata?.notes || lead.metadata.notes.length === 0) && (
                          <p className="text-sm text-muted-foreground">No activity yet</p>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>
            </Tabs>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Lead Status</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label>Current Status</Label>
                  <Select
                    value={editedLead.status || lead.status}
                    onValueChange={(value) => setEditedLead({ ...editedLead, status: value })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="received">Received</SelectItem>
                      <SelectItem value="contacted">Contacted</SelectItem>
                      <SelectItem value="qualified">Qualified</SelectItem>
                      <SelectItem value="converted">Converted</SelectItem>
                      <SelectItem value="lost">Lost</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label>Lead Score</Label>
                  <div className="text-2xl font-bold">{lead.lead_score || 'N/A'}</div>
                </div>

                <div className="space-y-2">
                  <Label>Created</Label>
                  <p className="text-sm">{new Date(lead.created_at).toLocaleString()}</p>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Quick Actions</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <Button variant="outline" className="w-full" onClick={() => window.location.href = `mailto:${lead.email}`}>
                  <Mail className="mr-2 h-4 w-4" />
                  Send Email
                </Button>
                <Button variant="outline" className="w-full" onClick={() => window.location.href = `tel:${lead.phone}`}>
                  <Phone className="mr-2 h-4 w-4" />
                  Call Lead
                </Button>
                <Button variant="outline" className="w-full" onClick={() => navigate('/dashboard/strategy-session')}>
                  <Calendar className="mr-2 h-4 w-4" />
                  Schedule Meeting
                </Button>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
};

export default LeadDetail;
