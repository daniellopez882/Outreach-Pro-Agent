import { useEffect, useState } from 'react';
import {
    Users, Mail, BarChart3, TrendingUp, MoreHorizontal,
    Search, RefreshCw, Eye
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

interface Lead {
    id: number;
    name: string;
    email: string;
    company: string;
    job_title: string;
    source: string;
    created_at: string;
}

interface Campaign {
    id: number;
    lead_id: number;
    subject_line: string;
    status: string;
    personalization_elements: string[];
    created_at: string;
}

export function Dashboard() {
    const [leads, setLeads] = useState<Lead[]>([]);
    const [campaigns, setCampaigns] = useState<Campaign[]>([]);
    const [loading, setLoading] = useState(true);
    const [stats, setStats] = useState({ total_leads: 0, total_campaigns: 0, response_rate: 0 });

    const fetchData = async () => {
        setLoading(true);
        try {
            // Parallel fetch for speed
            const [leadsRes, campaignsRes, statsRes] = await Promise.all([
                fetch('http://localhost:8000/leads'),
                fetch('http://localhost:8000/campaigns'),
                fetch('http://localhost:8000/analytics/stats')
            ]);

            if (leadsRes.ok) setLeads(await leadsRes.json());
            if (campaignsRes.ok) setCampaigns(await campaignsRes.json());
            if (statsRes.ok) setStats(await statsRes.json());

        } catch (error) {
            console.error("Failed to fetch dashboard data:", error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
        // Auto-refresh every 30s to keep dashboard alive
        const interval = setInterval(fetchData, 30000);
        return () => clearInterval(interval);
    }, []);

    return (
        <div className="space-y-8 p-8 bg-gray-50 min-h-screen">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold text-gray-900">Agent Dashboard</h1>
                    <p className="text-gray-500 mt-1">Monitor real-time outreach performance</p>
                </div>
                <div className="flex gap-3">
                    <Button variant="outline" onClick={fetchData} disabled={loading}>
                        <RefreshCw className={`mr-2 h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
                        Refresh
                    </Button>
                    <Button className="bg-violet-600 hover:bg-violet-700">
                        <TrendingUp className="mr-2 h-4 w-4" /> Generate Report
                    </Button>
                </div>
            </div>

            {/* Stats Grid */}
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Total Leads</CardTitle>
                        <Users className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{stats.total_leads}</div>
                        <p className="text-xs text-muted-foreground">+2 since last hour</p>
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Active Campaigns</CardTitle>
                        <Mail className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{stats.total_campaigns}</div>
                        <p className="text-xs text-muted-foreground">Mocked data active</p>
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Response Rate</CardTitle>
                        <BarChart3 className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{stats.response_rate}%</div>
                        <p className="text-xs text-muted-foreground">Target: 15-20%</p>
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Agent Status</CardTitle>
                        <RefreshCw className="h-4 w-4 text-green-500" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-green-600">Active</div>
                        <p className="text-xs text-muted-foreground">Kimi 2.5 Logic Running</p>
                    </CardContent>
                </Card>
            </div>

            {/* Main Content */}
            <Tabs defaultValue="leads" className="space-y-4">
                <TabsList>
                    <TabsTrigger value="leads">Metrics & Leads</TabsTrigger>
                    <TabsTrigger value="campaigns">Generated Campaigns</TabsTrigger>
                </TabsList>

                <TabsContent value="leads" className="space-y-4">
                    <Card>
                        <CardHeader className="flex flex-row items-center justify-between">
                            <div>
                                <CardTitle>Recent Leads</CardTitle>
                                <div className="text-sm text-gray-500 mt-1">
                                    Manage your prospect list before outreach
                                </div>
                            </div>
                            <div className="relative w-64">
                                <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                                <Input placeholder="Search leads..." className="pl-8" />
                            </div>
                        </CardHeader>
                        <CardContent>
                            <Table>
                                <TableHeader>
                                    <TableRow>
                                        <TableHead>Name</TableHead>
                                        <TableHead>Company</TableHead>
                                        <TableHead>Role</TableHead>
                                        <TableHead>Source</TableHead>
                                        <TableHead className="text-right">Actions</TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {leads.length === 0 ? (
                                        <TableRow>
                                            <TableCell colSpan={5} className="text-center h-24 text-gray-500">
                                                No leads found. Use the demo form to add some!
                                            </TableCell>
                                        </TableRow>
                                    ) : (
                                        leads.map((lead) => (
                                            <TableRow key={lead.id}>
                                                <TableCell className="font-medium">{lead.name}</TableCell>
                                                <TableCell>{lead.company}</TableCell>
                                                <TableCell>{lead.job_title}</TableCell>
                                                <TableCell>
                                                    <Badge variant="secondary">{lead.source}</Badge>
                                                </TableCell>
                                                <TableCell className="text-right">
                                                    <Button variant="ghost" size="sm">
                                                        <MoreHorizontal className="h-4 w-4" />
                                                    </Button>
                                                </TableCell>
                                            </TableRow>
                                        ))
                                    )}
                                </TableBody>
                            </Table>
                        </CardContent>
                    </Card>
                </TabsContent>

                <TabsContent value="campaigns">
                    <Card>
                        <CardHeader>
                            <CardTitle>Campaign Performance</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <Table>
                                <TableHeader>
                                    <TableRow>
                                        <TableHead>ID</TableHead>
                                        <TableHead>Subject Line</TableHead>
                                        <TableHead>Status</TableHead>
                                        <TableHead>Personalization</TableHead>
                                        <TableHead className="text-right">View</TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {campaigns.length === 0 ? (
                                        <TableRow>
                                            <TableCell colSpan={5} className="text-center h-24 text-gray-500">
                                                No campaigns generated yet.
                                            </TableCell>
                                        </TableRow>
                                    ) : (
                                        campaigns.map((camp) => (
                                            <TableRow key={camp.id}>
                                                <TableCell>#{camp.id}</TableCell>
                                                <TableCell className="max-w-md truncate" title={camp.subject_line}>
                                                    {camp.subject_line}
                                                </TableCell>
                                                <TableCell>
                                                    <Badge className={
                                                        camp.status === 'draft' ? 'bg-yellow-100 text-yellow-800' :
                                                            camp.status === 'sent' ? 'bg-green-100 text-green-800' : 'bg-gray-100'
                                                    }>
                                                        {camp.status}
                                                    </Badge>
                                                </TableCell>
                                                <TableCell>
                                                    <div className="flex gap-1">
                                                        {camp.personalization_elements?.length || 0} elements
                                                    </div>
                                                </TableCell>
                                                <TableCell className="text-right">
                                                    <Button variant="ghost" size="sm">
                                                        <Eye className="h-4 w-4" />
                                                    </Button>
                                                </TableCell>
                                            </TableRow>
                                        ))
                                    )}
                                </TableBody>
                            </Table>
                        </CardContent>
                    </Card>
                </TabsContent>
            </Tabs>
        </div>
    );
}
