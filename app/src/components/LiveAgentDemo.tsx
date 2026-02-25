import { useState } from 'react';
import {
    Send, Sparkles, Loader2, CheckCircle, AlertCircle,
    Brain, Mail, Building2, User
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';

interface AnalysisResult {
    pain_points: string[];
    interests: string[];
    trigger_events: Array<{ description: string; type: string }>;
    relevance_score: number;
}

interface EmailResult {
    subject_line: string;
    email_body: string;
    personalization_elements: string[];
}

interface CampaignResult {
    status: string;
    stages: {
        analysis?: AnalysisResult;
        email_generation?: EmailResult;
        quality_check?: {
            quality_score: number;
            passes_qa: boolean;
        };
    };
}

export function LiveAgentDemo() {
    const [loading, setLoading] = useState(false);
    const [stage, setStage] = useState<'idle' | 'enriching' | 'analyzing' | 'drafting' | 'complete'>('idle');
    const [result, setResult] = useState<CampaignResult | null>(null);
    const [error, setError] = useState<string | null>(null);

    const [formData, setFormData] = useState({
        name: "John Doe",
        email: "john.doe@example.com",
        company: "Acme Corp",
        job_title: "CTO",
        linkedin_url: "",
    });

    const handleGenerate = async () => {
        setLoading(true);
        setError(null);
        setResult(null);
        setStage('enriching');

        try {
            // 1. Create Lead
            const leadRes = await fetch('http://localhost:8000/leads', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    ...formData,
                    source: 'live_demo'
                })
            });

            if (!leadRes.ok) throw new Error('Failed to create lead');
            const lead = await leadRes.json();

            setStage('analyzing');

            // 2. Generate Campaign
            const campaignRes = await fetch('http://localhost:8000/campaigns', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    lead_ids: [lead.id],
                    company_context: "We provide AI-driven sales enablement tools.",
                    value_proposition: "Increase response rates by 10x with hyper-personalization.",
                    auto_send: false
                })
            });

            if (!campaignRes.ok) throw new Error('Failed to generate campaign');

            setStage('drafting');

            const campaignData = await campaignRes.json();

            // In a real app we might poll, but here we assume sync response for demo
            if (campaignData.results && campaignData.results[0]) {
                setResult(campaignData.results[0]);
                setStage('complete');
            } else {
                throw new Error('No campaign generated');
            }

        } catch (err: any) {
            setError(err.message);
            setStage('idle');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="grid lg:grid-cols-2 gap-12 items-start">
            {/* Input Section */}
            <div>
                <Badge className="mb-4 bg-violet-100 text-violet-700 hover:bg-violet-100">Live Agent Demo</Badge>
                <h2 className="text-4xl font-bold text-gray-800 mb-6">
                    Try the Agent <span className="gradient-text">Yourself</span>
                </h2>
                <p className="text-gray-600 mb-8 leading-relaxed">
                    Enter a lead's details (or use the defaults) to see the agent research, analyze, and draft an email in real-time.
                </p>

                <Card className="border-0 shadow-lg bg-white">
                    <CardContent className="p-6 space-y-4">
                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label htmlFor="name">Lead Name</Label>
                                <div className="relative">
                                    <User className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                                    <Input
                                        id="name"
                                        value={formData.name}
                                        onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                        className="pl-9"
                                        placeholder="Jane Smith"
                                    />
                                </div>
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="email">Email</Label>
                                <div className="relative">
                                    <Mail className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                                    <Input
                                        id="email"
                                        value={formData.email}
                                        onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                                        className="pl-9"
                                        placeholder="jane@company.com"
                                    />
                                </div>
                            </div>
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label htmlFor="company">Company</Label>
                                <div className="relative">
                                    <Building2 className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                                    <Input
                                        id="company"
                                        value={formData.company}
                                        onChange={(e) => setFormData({ ...formData, company: e.target.value })}
                                        className="pl-9"
                                        placeholder="Acme Inc"
                                    />
                                </div>
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="job">Job Title</Label>
                                <Input
                                    id="job"
                                    value={formData.job_title}
                                    onChange={(e) => setFormData({ ...formData, job_title: e.target.value })}
                                    placeholder="VP of Engineering"
                                />
                            </div>
                        </div>

                        <Button
                            onClick={handleGenerate}
                            disabled={loading}
                            className="w-full bg-gradient-to-r from-violet-600 to-purple-600 hover:from-violet-700 hover:to-purple-700 text-white h-12 text-lg"
                        >
                            {loading ? (
                                <>
                                    <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                                    {stage === 'enriching' && 'Enriching Data...'}
                                    {stage === 'analyzing' && 'Analyzing Profile...'}
                                    {stage === 'drafting' && 'Drafting Email...'}
                                </>
                            ) : (
                                <>
                                    <Sparkles className="mr-2 h-5 w-5" /> Generate Campaign
                                </>
                            )}
                        </Button>

                        {error && (
                            <div className="flex items-center gap-2 text-red-600 bg-red-50 p-3 rounded-lg text-sm">
                                <AlertCircle className="h-4 w-4" /> {error}
                            </div>
                        )}
                    </CardContent>
                </Card>
            </div>

            {/* Output Section */}
            <div>
                <Tabs defaultValue="email" className="w-full">
                    <TabsList className="grid w-full grid-cols-2 mb-6">
                        <TabsTrigger value="email">Generated Email</TabsTrigger>
                        <TabsTrigger value="analysis">AI Analysis</TabsTrigger>
                    </TabsList>

                    <TabsContent value="email">
                        <div className={`terminal shadow-2xl transition-all duration-500 ${loading ? 'opacity-50' : 'opacity-100'}`}>
                            <div className="terminal-header">
                                <div className="terminal-dot bg-red-500"></div>
                                <div className="terminal-dot bg-yellow-500"></div>
                                <div className="terminal-dot bg-green-500"></div>
                                <span className="ml-4 text-gray-400 text-sm">Email Preview</span>
                            </div>
                            <div className="terminal-body min-h-[300px]">
                                {result?.stages?.email_generation ? (
                                    <>
                                        <div className="mb-4 pb-4 border-b border-gray-700">
                                            <span className="text-gray-400">Subject: </span>
                                            <span className="text-white">{result.stages.email_generation.subject_line}</span>
                                        </div>
                                        <pre className="text-green-400 whitespace-pre-wrap font-mono text-sm leading-relaxed">
                                            {result.stages.email_generation.email_body}
                                        </pre>
                                    </>
                                ) : (
                                    <div className="flex flex-col items-center justify-center h-full text-gray-500">
                                        <Mail className="w-12 h-12 mb-4 opacity-50" />
                                        <p>Enter lead details to generate an email</p>
                                    </div>
                                )}
                            </div>
                        </div>
                    </TabsContent>

                    <TabsContent value="analysis">
                        <div className={`terminal shadow-2xl transition-all duration-500 ${loading ? 'opacity-50' : 'opacity-100'}`}>
                            <div className="terminal-header">
                                <div className="terminal-dot bg-red-500"></div>
                                <div className="terminal-dot bg-yellow-500"></div>
                                <div className="terminal-dot bg-green-500"></div>
                                <span className="ml-4 text-gray-400 text-sm">Analysis Results</span>
                            </div>
                            <div className="terminal-body min-h-[300px] text-sm">
                                {result?.stages?.analysis ? (
                                    <>
                                        <div className="text-yellow-400 mb-2">Pain Points:</div>
                                        {result.stages.analysis.pain_points.map((p, i) => (
                                            <div key={i} className="text-green-400 mb-1">• {p}</div>
                                        ))}

                                        <div className="text-yellow-400 mt-4 mb-2">Trigger Events:</div>
                                        {result.stages.analysis.trigger_events.map((t, i) => (
                                            <div key={i} className="text-green-400 mb-1">
                                                • {t.description} <span className="text-gray-500 text-xs">({t.type})</span>
                                            </div>
                                        ))}

                                        <div className="mt-4 pt-4 border-t border-gray-700">
                                            <div className="flex justify-between items-center">
                                                <span className="text-gray-400">Relevance Score:</span>
                                                <span className="text-green-400 font-bold">{result.stages.analysis.relevance_score || 'N/A'}</span>
                                            </div>
                                        </div>
                                    </>
                                ) : (
                                    <div className="flex flex-col items-center justify-center h-full text-gray-500">
                                        <Brain className="w-12 h-12 mb-4 opacity-50" />
                                        <p>Analysis data will appear here</p>
                                    </div>
                                )}
                            </div>
                        </div>
                    </TabsContent>
                </Tabs>
            </div>
        </div>
    );
}
