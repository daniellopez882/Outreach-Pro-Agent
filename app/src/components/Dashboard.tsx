import { useCallback, useEffect, useState } from 'react';
import { Users, Mail, BarChart3, Send, Search, RefreshCw, KeyRound } from 'lucide-react';
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
} from '@/components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ApiError, apiFetch, fetchReady, getApiKey, setApiKey } from '@/lib/api';

interface Lead {
    id: number;
    name: string;
    email: string;
    company: string | null;
    job_title: string | null;
    source?: string | null;
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

/** Exactly what GET /analytics/stats returns: counts from the database, nothing projected. */
interface Stats {
    total_leads: number;
    total_campaigns: number;
    sent_campaigns: number;
    replied_campaigns: number;
    response_rate: number;
}

const EMPTY_STATS: Stats = {
    total_leads: 0,
    total_campaigns: 0,
    sent_campaigns: 0,
    replied_campaigns: 0,
    response_rate: 0,
};

// Values of the backend's OutreachStatus enum.
const STATUS_STYLES: Record<string, string> = {
    ready: 'bg-yellow-100 text-yellow-800',
    sent: 'bg-green-100 text-green-800',
    replied: 'bg-emerald-100 text-emerald-800',
    failed: 'bg-red-100 text-red-800',
};

export function Dashboard() {
    const [leads, setLeads] = useState<Lead[]>([]);
    const [campaigns, setCampaigns] = useState<Campaign[]>([]);
    const [stats, setStats] = useState<Stats>(EMPTY_STATS);
    const [sendingEnabled, setSendingEnabled] = useState<boolean | null>(null);
    const [loading, setLoading] = useState(true);
    const [problem, setProblem] = useState<string | null>(null);
    const [needsKey, setNeedsKey] = useState(false);
    const [keyInput, setKeyInput] = useState('');
    const [query, setQuery] = useState('');

    const fetchData = useCallback(async () => {
        setLoading(true);
        try {
            const [leadsData, campaignsData, statsData, ready] = await Promise.all([
                apiFetch<Lead[]>('/leads'),
                apiFetch<Campaign[]>('/campaigns'),
                apiFetch<Stats>('/analytics/stats'),
                fetchReady(),
            ]);
            setLeads(leadsData);
            setCampaigns(campaignsData);
            setStats(statsData);
            setSendingEnabled(ready?.checks.email_sending?.enabled ?? null);
            setProblem(null);
            setNeedsKey(false);
        } catch (error) {
            if (error instanceof ApiError && error.status === 401) {
                setNeedsKey(true);
                setProblem(
                    getApiKey()
                        ? 'The API rejected the configured key.'
                        : 'No API key is configured, and every route except the probes needs one.',
                );
            } else {
                setNeedsKey(false);
                setProblem(
                    error instanceof Error
                        ? `Could not reach the API: ${error.message}`
                        : 'Could not reach the API.',
                );
            }
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        void fetchData();
        // Auto-refresh every 30s to keep dashboard alive
        const interval = setInterval(() => void fetchData(), 30000);
        return () => clearInterval(interval);
    }, [fetchData]);

    const applyKey = () => {
        setApiKey(keyInput.trim());
        setKeyInput('');
        void fetchData();
    };

    const needle = query.trim().toLowerCase();
    const visibleLeads = needle
        ? leads.filter((lead) =>
              [lead.name, lead.email, lead.company ?? '', lead.job_title ?? '']
                  .join(' ')
                  .toLowerCase()
                  .includes(needle),
          )
        : leads;

    return (
        <div className="space-y-8 p-8 bg-gray-50 min-h-screen">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
                    <p className="text-gray-500 mt-1">
                        Leads, drafted campaigns and counts, read from the database every 30 seconds.
                    </p>
                </div>
                <Button variant="outline" onClick={() => void fetchData()} disabled={loading}>
                    <RefreshCw className={`mr-2 h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
                    Refresh
                </Button>
            </div>

            {problem && (
                <Card className="border-amber-200 bg-amber-50">
                    <CardContent className="p-4 flex flex-wrap items-center gap-3 text-sm text-amber-900">
                        <KeyRound className="h-4 w-4 shrink-0" />
                        <span>{problem}</span>
                        {needsKey && (
                            <form
                                className="flex items-center gap-2"
                                onSubmit={(event) => {
                                    event.preventDefault();
                                    applyKey();
                                }}
                            >
                                <Input
                                    type="password"
                                    autoComplete="off"
                                    placeholder="X-API-Key"
                                    value={keyInput}
                                    onChange={(event) => setKeyInput(event.target.value)}
                                    className="w-64 bg-white"
                                />
                                <Button type="submit" variant="outline" disabled={!keyInput.trim()}>
                                    Use key
                                </Button>
                            </form>
                        )}
                    </CardContent>
                </Card>
            )}

            {/* Stats Grid */}
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Leads</CardTitle>
                        <Users className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{stats.total_leads}</div>
                        <p className="text-xs text-muted-foreground">rows in the leads table</p>
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Campaigns</CardTitle>
                        <Mail className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{stats.total_campaigns}</div>
                        <p className="text-xs text-muted-foreground">{stats.sent_campaigns} sent</p>
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Response rate</CardTitle>
                        <BarChart3 className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{stats.response_rate}%</div>
                        <p className="text-xs text-muted-foreground">
                            {stats.replied_campaigns} replied ÷ {stats.sent_campaigns} sent
                        </p>
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Delivery</CardTitle>
                        <Send className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div
                            className={`text-2xl font-bold ${
                                sendingEnabled ? 'text-green-600' : 'text-gray-700'
                            }`}
                        >
                            {sendingEnabled === null ? '—' : sendingEnabled ? 'On' : 'Off'}
                        </div>
                        <p className="text-xs text-muted-foreground">EMAIL_SENDING_ENABLED, from /ready</p>
                    </CardContent>
                </Card>
            </div>

            {/* Main Content */}
            <Tabs defaultValue="leads" className="space-y-4">
                <TabsList>
                    <TabsTrigger value="leads">Leads</TabsTrigger>
                    <TabsTrigger value="campaigns">Campaigns</TabsTrigger>
                </TabsList>

                <TabsContent value="leads" className="space-y-4">
                    <Card>
                        <CardHeader className="flex flex-row items-center justify-between">
                            <div>
                                <CardTitle>Leads</CardTitle>
                                <div className="text-sm text-gray-500 mt-1">
                                    Everything in the leads table, newest last
                                </div>
                            </div>
                            <div className="relative w-64">
                                <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                                <Input
                                    placeholder="Filter by name, email, company…"
                                    className="pl-8"
                                    value={query}
                                    onChange={(event) => setQuery(event.target.value)}
                                />
                            </div>
                        </CardHeader>
                        <CardContent>
                            <Table>
                                <TableHeader>
                                    <TableRow>
                                        <TableHead>Name</TableHead>
                                        <TableHead>Email</TableHead>
                                        <TableHead>Company</TableHead>
                                        <TableHead>Role</TableHead>
                                        <TableHead>Source</TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {visibleLeads.length === 0 ? (
                                        <TableRow>
                                            <TableCell colSpan={5} className="text-center h-24 text-gray-500">
                                                {leads.length === 0
                                                    ? 'No leads yet. The demo form above adds one.'
                                                    : 'No leads match the filter.'}
                                            </TableCell>
                                        </TableRow>
                                    ) : (
                                        visibleLeads.map((lead) => (
                                            <TableRow key={lead.id}>
                                                <TableCell className="font-medium">{lead.name}</TableCell>
                                                <TableCell>{lead.email}</TableCell>
                                                <TableCell>{lead.company ?? '—'}</TableCell>
                                                <TableCell>{lead.job_title ?? '—'}</TableCell>
                                                <TableCell>
                                                    <Badge variant="secondary">{lead.source ?? 'manual'}</Badge>
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
                            <CardTitle>Campaigns</CardTitle>
                            <div className="text-sm text-gray-500 mt-1">
                                Drafts are held as <code>ready</code> until someone sends them
                            </div>
                        </CardHeader>
                        <CardContent>
                            <Table>
                                <TableHeader>
                                    <TableRow>
                                        <TableHead>ID</TableHead>
                                        <TableHead>Subject line</TableHead>
                                        <TableHead>Status</TableHead>
                                        <TableHead>Personalisation</TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {campaigns.length === 0 ? (
                                        <TableRow>
                                            <TableCell colSpan={4} className="text-center h-24 text-gray-500">
                                                No campaigns drafted yet.
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
                                                    <Badge className={STATUS_STYLES[camp.status] ?? 'bg-gray-100 text-gray-800'}>
                                                        {camp.status}
                                                    </Badge>
                                                </TableCell>
                                                <TableCell>
                                                    {camp.personalization_elements?.length ?? 0} elements
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
