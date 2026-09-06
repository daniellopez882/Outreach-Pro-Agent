import type { LucideIcon } from 'lucide-react';
import { useEffect, useState } from 'react';
import {
  Mail,
  CheckCircle,
  Sparkles,
  Shield,
  Building2,
  Brain,
  FileSearch,
  Send,
  Github,
  BookOpen,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { LiveAgentDemo } from '@/components/LiveAgentDemo';
import { Dashboard } from '@/components/Dashboard';

const REPO_URL = 'https://github.com/daniellopez882/Outreach-Pro-Agent';

// Feature Card Component
function FeatureCard({
  icon: Icon,
  title,
  description,
  color,
}: {
  icon: LucideIcon;
  title: string;
  description: string;
  color: string;
}) {
  return (
    <Card className="hover-lift card-shine border-0 shadow-lg">
      <CardContent className="p-6">
        <div className={`w-14 h-14 ${color} rounded-2xl flex items-center justify-center mb-5`}>
          <Icon className="w-7 h-7 text-white" />
        </div>
        <h3 className="text-xl font-semibold text-gray-800 mb-3">{title}</h3>
        <p className="text-gray-600 leading-relaxed">{description}</p>
      </CardContent>
    </Card>
  );
}

// Step Card Component
function StepCard({
  number,
  title,
  description,
  icon: Icon,
}: {
  number: number;
  title: string;
  description: string;
  icon: LucideIcon;
}) {
  return (
    <div className="relative">
      <div className="bg-white rounded-2xl p-6 shadow-lg hover-lift border border-gray-100 h-full">
        <div className="flex items-start gap-4">
          <div className="w-12 h-12 bg-gradient-to-br from-violet-500 to-purple-600 rounded-xl flex items-center justify-center flex-shrink-0">
            <Icon className="w-6 h-6 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="w-6 h-6 bg-violet-100 text-violet-600 rounded-full text-xs font-bold flex items-center justify-center">
                {number}
              </span>
              <h3 className="text-lg font-semibold text-gray-800">{title}</h3>
            </div>
            <p className="text-gray-600 text-sm leading-relaxed">{description}</p>
          </div>
        </div>
      </div>
    </div>
  );
}

// Main App Component
function App() {
  const [scrolled, setScrolled] = useState(false);
  const [view, setView] = useState<'home' | 'dashboard'>('home');

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 50);
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const navText = scrolled || view === 'dashboard' ? 'text-gray-600' : 'text-white/80';

  return (
    <div className="min-h-screen bg-white">
      {/* Navigation */}
      <nav
        className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
          scrolled || view === 'dashboard' ? 'bg-white/90 backdrop-blur-lg shadow-sm' : 'bg-transparent'
        }`}
      >
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <button type="button" className="flex items-center gap-2" onClick={() => setView('home')}>
            <div className="w-10 h-10 bg-gradient-to-br from-violet-500 to-purple-600 rounded-xl flex items-center justify-center">
              <Mail className="w-5 h-5 text-white" />
            </div>
            <span className={`font-bold text-xl ${scrolled || view === 'dashboard' ? 'text-gray-800' : 'text-white'}`}>
              Outreach Architect
            </span>
          </button>
          <div className="hidden md:flex items-center gap-8">
            {view === 'home' ? (
              <>
                <a href="#how-it-works" className={`text-sm font-medium hover:opacity-80 ${navText}`}>
                  How it works
                </a>
                <a href="#demo" className={`text-sm font-medium hover:opacity-80 ${navText}`}>
                  Demo
                </a>
                <a href="#limits" className={`text-sm font-medium hover:opacity-80 ${navText}`}>
                  Limits
                </a>
                <a
                  href={REPO_URL}
                  target="_blank"
                  rel="noreferrer"
                  className={`text-sm font-medium hover:opacity-80 ${navText}`}
                >
                  Source
                </a>
                <Button onClick={() => setView('dashboard')} className="bg-white text-violet-600 hover:bg-gray-100">
                  Dashboard
                </Button>
              </>
            ) : (
              <Button onClick={() => setView('home')} variant="ghost" className={`text-sm font-medium ${navText}`}>
                Back to overview
              </Button>
            )}
          </div>
        </div>
      </nav>

      {view === 'home' ? (
        <>
          {/* Hero Section */}
          <section className="gradient-hero min-h-[70vh] flex items-center relative overflow-hidden">
            <div className="absolute inset-0 overflow-hidden">
              <div className="absolute top-20 left-10 w-72 h-72 bg-white/10 rounded-full blur-3xl animate-float"></div>
              <div
                className="absolute bottom-20 right-10 w-96 h-96 bg-purple-500/20 rounded-full blur-3xl animate-float"
                style={{ animationDelay: '2s' }}
              ></div>
            </div>

            <div className="max-w-7xl mx-auto px-6 py-32 relative z-10">
              <div className="max-w-3xl text-white">
                <div className="inline-flex items-center gap-2 px-4 py-2 bg-white/20 rounded-full text-sm font-medium mb-6 backdrop-blur-sm">
                  <Sparkles className="w-4 h-4" />
                  Works with Kimi, DeepSeek, Anthropic or OpenAI models
                </div>
                <h1 className="text-5xl md:text-6xl font-bold leading-tight mb-6">
                  Research-assisted drafts for cold outreach,
                  <span className="text-yellow-300"> held for review</span>
                </h1>
                <p className="text-xl text-white/90 mb-8 max-w-2xl">
                  Enrich a lead from sources you are licensed to use, ask a model for an analysis and a
                  first draft, score the draft against a quality bar, and keep it as a campaign until a
                  person decides to send it. Sending is off by default.
                </p>
                <div className="flex flex-wrap gap-4">
                  <Button asChild size="lg" className="bg-white text-violet-600 hover:bg-gray-100 px-8">
                    <a href="#demo">
                      <Sparkles className="w-5 h-5 mr-2" />
                      Try the demo
                    </a>
                  </Button>
                  <Button asChild size="lg" variant="outline" className="border-white text-white hover:bg-white/20 px-8">
                    <a href={REPO_URL} target="_blank" rel="noreferrer">
                      <Github className="w-5 h-5 mr-2" />
                      Read the source
                    </a>
                  </Button>
                </div>
                <p className="text-white/70 mt-8 text-sm max-w-2xl">
                  This page makes no response-rate, open-rate or revenue claims. No campaign has been run with
                  this software, so no such number exists; the dashboard shows the counts in your own database
                  and nothing else.
                </p>
              </div>
            </div>
          </section>

          {/* What it does */}
          <section className="py-24 bg-white">
            <div className="max-w-7xl mx-auto px-6">
              <div className="text-center mb-16">
                <Badge className="mb-4 bg-violet-100 text-violet-700 hover:bg-violet-100">What runs</Badge>
                <h2 className="text-4xl font-bold text-gray-800 mb-4">
                  A pipeline with a <span className="gradient-text">quality gate</span>, not a prompt
                </h2>
                <p className="text-gray-600 max-w-2xl mx-auto">
                  Each stage is a module in <code>outreach-architect/</code>, covered by the test suite.
                </p>
              </div>
              <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
                <FeatureCard
                  icon={Building2}
                  title="Enrichment you can defend"
                  description="Operator-supplied fields and the company's own website, fetched with robots.txt honoured, a truthful User-Agent and a size cap. Sites whose terms forbid scraping are refused in code, and a lead-supplied URL cannot reach private or cloud-metadata addresses."
                  color="bg-gradient-to-br from-violet-500 to-purple-600"
                />
                <FeatureCard
                  icon={Brain}
                  title="Model analysis"
                  description="The configured model extracts pain points, interests and trigger events from what enrichment actually found, and says where each came from. Without a key, canned responses stand in and are labelled as such."
                  color="bg-gradient-to-br from-pink-500 to-rose-600"
                />
                <FeatureCard
                  icon={FileSearch}
                  title="Drafts scored before anyone sees them"
                  description="Every draft is scored for personalisation, length, a clear ask and spam phrasing. Below the bar it is regenerated; above it, it becomes a campaign in the ready state."
                  color="bg-gradient-to-br from-orange-500 to-amber-600"
                />
                <FeatureCard
                  icon={Shield}
                  title="Every route authenticated"
                  description="All data and action routes require X-API-Key, compared in constant time. Production refuses to start with the placeholder key, an empty CORS list or SQLite."
                  color="bg-gradient-to-br from-green-500 to-emerald-600"
                />
                <FeatureCard
                  icon={Send}
                  title="Sending is opt-in"
                  description="Delivery goes through SendGrid only when EMAIL_SENDING_ENABLED is true and the sender is configured; otherwise the send route answers 409 and the campaign stays a draft. A campaign is marked sent only after the provider accepts it."
                  color="bg-gradient-to-br from-cyan-500 to-blue-600"
                />
                <FeatureCard
                  icon={CheckCircle}
                  title="Tested and containerised"
                  description="An offline test suite covers the providers and their compliance gate, the SSRF guard, authentication on every protected route, the delivery gate and the readiness checks. CI boots the non-root image and probes it."
                  color="bg-gradient-to-br from-blue-500 to-blue-600"
                />
              </div>
            </div>
          </section>

          {/* How It Works Section */}
          <section id="how-it-works" className="py-24 bg-gray-50">
            <div className="max-w-7xl mx-auto px-6">
              <div className="text-center mb-16">
                <Badge className="mb-4 bg-violet-100 text-violet-700 hover:bg-violet-100">Process</Badge>
                <h2 className="text-4xl font-bold text-gray-800 mb-4">How it works</h2>
                <p className="text-gray-600 max-w-2xl mx-auto">
                  Five stages from a lead record to a draft waiting for a decision
                </p>
              </div>
              <div className="grid md:grid-cols-2 lg:grid-cols-5 gap-6">
                <StepCard
                  number={1}
                  title="Enrich"
                  description="The configured providers add what they can find; each fact carries its source and a confidence."
                  icon={Building2}
                />
                <StepCard
                  number={2}
                  title="Analyse"
                  description="The model summarises pain points, interests and trigger events from the enrichment."
                  icon={Brain}
                />
                <StepCard
                  number={3}
                  title="Draft"
                  description="A first-touch email is generated from the analysis and your context."
                  icon={Mail}
                />
                <StepCard
                  number={4}
                  title="Score"
                  description="Personalisation, length, a clear ask and spam phrasing are checked; below the bar, regenerate."
                  icon={FileSearch}
                />
                <StepCard
                  number={5}
                  title="Hold or send"
                  description="The draft is stored as a ready campaign. Sending is a separate, authenticated, opt-in call."
                  icon={Send}
                />
              </div>
            </div>
          </section>

          {/* Demo Section */}
          <section id="demo" className="py-24 bg-white">
            <div className="max-w-7xl mx-auto px-6">
              <LiveAgentDemo />
            </div>
          </section>

          {/* Limits */}
          <section id="limits" className="py-24 bg-gray-50">
            <div className="max-w-4xl mx-auto px-6">
              <Badge className="mb-4 bg-violet-100 text-violet-700 hover:bg-violet-100">Limits</Badge>
              <h2 className="text-4xl font-bold text-gray-800 mb-6">What this does not do</h2>
              <ul className="space-y-4 text-gray-700 leading-relaxed">
                <li>
                  <strong>No effectiveness data.</strong> No campaign has been run with it, so any response, open
                  or meeting rate would be invented. The dashboard divides replies by sends in your database and
                  shows nothing else.
                </li>
                <li>
                  <strong>No LinkedIn scraping.</strong> The scraper that used to log in with a username and password
                  never worked and breached LinkedIn's terms; it was removed. Person-level data has to come from
                  the person or from a licensed vendor.
                </li>
                <li>
                  <strong>No compliance tooling.</strong> There is no suppression list, unsubscribe handling or
                  consent record. Cold outreach is regulated (CAN-SPAM, GDPR/PECR, CASL); that is why sending is
                  off by default.
                </li>
                <li>
                  <strong>One shared API key.</strong> No per-user accounts, no rate limiting on the HTTP API, no
                  audit log of who sent what. A key built into this page is readable by anyone who can open it.
                </li>
                <li>
                  <strong>The model scores its own draft.</strong> There is no independent evaluation set for draft
                  quality.
                </li>
              </ul>
              <div className="mt-10 flex flex-wrap gap-4">
                <Button asChild variant="outline">
                  <a href={`${REPO_URL}#readme`} target="_blank" rel="noreferrer">
                    <BookOpen className="w-4 h-4 mr-2" />
                    README: what was fixed, and why
                  </a>
                </Button>
                <Button asChild variant="outline">
                  <a
                    href={`${REPO_URL}/blob/main/outreach-architect/docs/threat-model.md`}
                    target="_blank"
                    rel="noreferrer"
                  >
                    <Shield className="w-4 h-4 mr-2" />
                    Threat model
                  </a>
                </Button>
              </div>
            </div>
          </section>

          {/* Footer */}
          <footer className="bg-gray-900 text-white py-12">
            <div className="max-w-7xl mx-auto px-6 flex flex-col md:flex-row items-center justify-between gap-6">
              <div className="flex items-center gap-2">
                <div className="w-10 h-10 bg-gradient-to-br from-violet-500 to-purple-600 rounded-xl flex items-center justify-center">
                  <Mail className="w-5 h-5 text-white" />
                </div>
                <span className="font-bold text-xl">Outreach Architect</span>
              </div>
              <p className="text-gray-400 text-sm">
                MIT licensed. Source, tests, ADRs and the threat model live in the repository.
              </p>
              <a href={REPO_URL} target="_blank" rel="noreferrer" className="text-gray-300 hover:text-white text-sm">
                github.com/daniellopez882/Outreach-Pro-Agent
              </a>
            </div>
          </footer>
        </>
      ) : (
        <div className="pt-20">
          <Dashboard />
        </div>
      )}
    </div>
  );
}

export default App;
