import { useEffect, useState, useRef } from 'react';
import {
  Mail, Linkedin, TrendingUp, Zap, CheckCircle,
  BarChart3, Users, Clock, ArrowRight, Sparkles,
  Target, MessageSquare, Shield, Play, ChevronDown,
  Star, Quote, Building2, Rocket, Brain, LineChart
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { LiveAgentDemo } from '@/components/LiveAgentDemo';
import { Dashboard } from '@/components/Dashboard';

import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

// Animated counter hook
function useCountUp(end: number, duration: number = 2000) {
  const [count, setCount] = useState(0);
  const countRef = useRef(0);
  const [isVisible, setIsVisible] = useState(false);
  const elementRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting && !isVisible) {
          setIsVisible(true);
        }
      },
      { threshold: 0.3 }
    );

    if (elementRef.current) {
      observer.observe(elementRef.current);
    }

    return () => observer.disconnect();
  }, [isVisible]);

  useEffect(() => {
    if (!isVisible) return;

    const startTime = Date.now();
    const animate = () => {
      const elapsed = Date.now() - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const easeOut = 1 - Math.pow(1 - progress, 3);
      countRef.current = Math.floor(easeOut * end);
      setCount(countRef.current);

      if (progress < 1) {
        requestAnimationFrame(animate);
      }
    };

    requestAnimationFrame(animate);
  }, [isVisible, end, duration]);

  return { count, elementRef };
}

// Stat Card Component
function StatCard({ value, suffix, label, icon: Icon, delay }: {
  value: number;
  suffix: string;
  label: string;
  icon: any;
  delay: number;
}) {
  const { count, elementRef } = useCountUp(value);

  return (
    <div
      ref={elementRef}
      className="bg-white rounded-2xl p-6 shadow-lg hover-lift animate-slide-up"
      style={{ animationDelay: `${delay}ms` }}
    >
      <div className="flex items-center gap-4 mb-4">
        <div className="w-12 h-12 bg-gradient-to-br from-violet-500 to-purple-600 rounded-xl flex items-center justify-center">
          <Icon className="w-6 h-6 text-white" />
        </div>
      </div>
      <div className="text-4xl font-bold gradient-text stat-number mb-1">
        {count}{suffix}
      </div>
      <div className="text-gray-500 text-sm">{label}</div>
    </div>
  );
}

// Feature Card Component
function FeatureCard({ icon: Icon, title, description, color }: {
  icon: any;
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
function StepCard({ number, title, description, icon: Icon }: {
  number: number;
  title: string;
  description: string;
  icon: any;
}) {
  return (
    <div className="relative">
      <div className="bg-white rounded-2xl p-6 shadow-lg hover-lift border border-gray-100">
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

// Email Preview Component
function EmailPreview() {
  const [isTyping, setIsTyping] = useState(false);
  const [displayedText, setDisplayedText] = useState('');
  const fullText = `Hi Rahul,

Saw your LinkedIn post this week about deployment bottlenecks as TechCorp scales. With your Series B and 15+ engineering openings, this timing feels familiar.

We helped Razorpay tackle similar challenges during their hypergrowth phase - they went from 45-minute deploys to 12 minutes, letting their teams ship 3x more features.

Worth a 15-minute chat about their approach?

Best,
[Your Name]`;

  useEffect(() => {
    const timer = setTimeout(() => setIsTyping(true), 1000);
    return () => clearTimeout(timer);
  }, []);

  useEffect(() => {
    if (!isTyping) return;

    let index = 0;
    const interval = setInterval(() => {
      if (index < fullText.length) {
        setDisplayedText(fullText.slice(0, index + 1));
        index++;
      } else {
        clearInterval(interval);
      }
    }, 30);

    return () => clearInterval(interval);
  }, [isTyping]);

  return (
    <div className="terminal shadow-2xl">
      <div className="terminal-header">
        <div className="terminal-dot bg-red-500"></div>
        <div className="terminal-dot bg-yellow-500"></div>
        <div className="terminal-dot bg-green-500"></div>
        <span className="ml-4 text-gray-400 text-sm">Generated Email Preview</span>
      </div>
      <div className="terminal-body">
        <div className="mb-4 pb-4 border-b border-gray-700">
          <span className="text-gray-400">Subject: </span>
          <span className="text-white">Your post about deployment bottlenecks</span>
        </div>
        <pre className="text-green-400 whitespace-pre-wrap font-mono text-sm leading-relaxed">
          {displayedText}
          <span className="animate-pulse">|</span>
        </pre>
      </div>
      <div className="px-5 pb-5">
        <div className="flex flex-wrap gap-2">
          <Badge className="bg-green-500/20 text-green-400 border-green-500/30">
            <CheckCircle className="w-3 h-3 mr-1" /> Personalization Score: 92%
          </Badge>
          <Badge className="bg-blue-500/20 text-blue-400 border-blue-500/30">
            <Target className="w-3 h-3 mr-1" /> Relevance: High
          </Badge>
          <Badge className="bg-purple-500/20 text-purple-400 border-purple-500/30">
            <Sparkles className="w-3 h-3 mr-1" /> 4 Hooks Detected
          </Badge>
        </div>
      </div>
    </div>
  );
}

// ROI Calculator Component
function ROICalculator() {
  const [leadsPerMonth, setLeadsPerMonth] = useState(1000);
  const [avgDealSize, setAvgDealSize] = useState(5000);
  const [currentResponseRate, setCurrentResponseRate] = useState(1);

  const newResponseRate = 18;
  const currentMeetings = Math.floor(leadsPerMonth * (currentResponseRate / 100) * 0.3);
  const newMeetings = Math.floor(leadsPerMonth * (newResponseRate / 100) * 0.3);
  const additionalMeetings = newMeetings - currentMeetings;
  const additionalRevenue = additionalMeetings * avgDealSize * 0.2;
  const monthlyCost = 189 + (leadsPerMonth * 0.009);
  const roi = ((additionalRevenue - monthlyCost) / monthlyCost * 100).toFixed(0);

  return (
    <Card className="border-0 shadow-2xl bg-white">
      <CardHeader className="bg-gradient-to-r from-violet-600 to-purple-600 text-white rounded-t-lg">
        <CardTitle className="text-2xl flex items-center gap-2">
          <BarChart3 className="w-6 h-6" />
          ROI Calculator
        </CardTitle>
      </CardHeader>
      <CardContent className="p-6 space-y-6">
        <div className="space-y-4">
          <div>
            <label className="text-sm font-medium text-gray-700 mb-2 block">
              Leads per month: <span className="text-violet-600 font-bold">{leadsPerMonth}</span>
            </label>
            <input
              type="range"
              min="100"
              max="10000"
              step="100"
              value={leadsPerMonth}
              onChange={(e) => setLeadsPerMonth(Number(e.target.value))}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-violet-600"
            />
          </div>
          <div>
            <label className="text-sm font-medium text-gray-700 mb-2 block">
              Average deal size: <span className="text-violet-600 font-bold">${avgDealSize.toLocaleString()}</span>
            </label>
            <input
              type="range"
              min="1000"
              max="50000"
              step="1000"
              value={avgDealSize}
              onChange={(e) => setAvgDealSize(Number(e.target.value))}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-violet-600"
            />
          </div>
          <div>
            <label className="text-sm font-medium text-gray-700 mb-2 block">
              Current response rate: <span className="text-violet-600 font-bold">{currentResponseRate}%</span>
            </label>
            <input
              type="range"
              min="0.5"
              max="5"
              step="0.5"
              value={currentResponseRate}
              onChange={(e) => setCurrentResponseRate(Number(e.target.value))}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-violet-600"
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4 pt-4 border-t">
          <div className="text-center p-4 bg-gray-50 rounded-xl">
            <div className="text-sm text-gray-500 mb-1">Current Meetings</div>
            <div className="text-2xl font-bold text-gray-700">{currentMeetings}</div>
          </div>
          <div className="text-center p-4 bg-violet-50 rounded-xl">
            <div className="text-sm text-violet-600 mb-1">With Our System</div>
            <div className="text-2xl font-bold text-violet-700">{newMeetings}</div>
          </div>
        </div>

        <div className="bg-gradient-to-r from-green-500 to-emerald-500 rounded-xl p-5 text-white">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm opacity-90">Additional Monthly Revenue</div>
              <div className="text-3xl font-bold">${additionalRevenue.toLocaleString()}</div>
            </div>
            <div className="text-right">
              <div className="text-sm opacity-90">ROI</div>
              <div className="text-3xl font-bold">{roi}%</div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// Testimonial Card
function TestimonialCard({ name, role, company, quote, rating }: {
  name: string;
  role: string;
  company: string;
  quote: string;
  rating: number;
}) {
  return (
    <Card className="border-0 shadow-lg hover-lift">
      <CardContent className="p-6">
        <div className="flex gap-1 mb-4">
          {[...Array(rating)].map((_, i) => (
            <Star key={i} className="w-5 h-5 fill-yellow-400 text-yellow-400" />
          ))}
        </div>
        <Quote className="w-8 h-8 text-violet-200 mb-3" />
        <p className="text-gray-700 mb-6 leading-relaxed">{quote}</p>
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 bg-gradient-to-br from-violet-500 to-purple-600 rounded-full flex items-center justify-center text-white font-bold">
            {name.split(' ').map(n => n[0]).join('')}
          </div>
          <div>
            <div className="font-semibold text-gray-800">{name}</div>
            <div className="text-sm text-gray-500">{role} at {company}</div>
          </div>
        </div>
      </CardContent>
    </Card>
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

  return (
    <div className="min-h-screen bg-white">
      {/* Navigation */}
      <nav className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${scrolled ? 'bg-white/90 backdrop-blur-lg shadow-sm' : 'bg-transparent'
        }`}>
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2 cursor-pointer" onClick={() => setView('home')}>
            <div className="w-10 h-10 bg-gradient-to-br from-violet-500 to-purple-600 rounded-xl flex items-center justify-center">
              <Mail className="w-5 h-5 text-white" />
            </div>
            <span className={`font-bold text-xl ${scrolled ? 'text-gray-800' : 'text-white'}`}>
              Outreach Architect
            </span>
          </div>
          <div className="hidden md:flex items-center gap-8">
            {view === 'home' ? (
              <>
                <a href="#features" className={`text-sm font-medium hover:opacity-80 ${scrolled ? 'text-gray-600' : 'text-white/80'}`}>Features</a>
                <a href="#how-it-works" className={`text-sm font-medium hover:opacity-80 ${scrolled ? 'text-gray-600' : 'text-white/80'}`}>How It Works</a>
                <a href="#demo" className={`text-sm font-medium hover:opacity-80 ${scrolled ? 'text-gray-600' : 'text-white/80'}`}>Demo</a>
                <a href="#roi" className={`text-sm font-medium hover:opacity-80 ${scrolled ? 'text-gray-600' : 'text-white/80'}`}>ROI</a>
                <Button
                  onClick={() => setView('dashboard')}
                  className="bg-white text-violet-600 hover:bg-gray-100"
                >
                  Go to Dashboard
                </Button>
              </>
            ) : (
              <Button
                onClick={() => setView('home')}
                variant="ghost"
                className={`text-sm font-medium hover:opacity-80 ${scrolled ? 'text-gray-600' : 'text-white/80'}`}
              >
                Back to Home
              </Button>
            )}
          </div>
        </div>
      </nav>

      {view === 'home' ? (
        <>
          {/* Hero Section */}
          <section className="gradient-hero min-h-screen flex items-center relative overflow-hidden">
            {/* Background decorations */}
            <div className="absolute inset-0 overflow-hidden">
              <div className="absolute top-20 left-10 w-72 h-72 bg-white/10 rounded-full blur-3xl animate-float"></div>
              <div className="absolute bottom-20 right-10 w-96 h-96 bg-purple-500/20 rounded-full blur-3xl animate-float" style={{ animationDelay: '2s' }}></div>
              <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-violet-500/10 rounded-full blur-3xl"></div>
            </div>

            <div className="max-w-7xl mx-auto px-6 py-32 relative z-10">
              <div className="grid lg:grid-cols-2 gap-12 items-center">
                <div className="text-white">
                  <div className="inline-flex items-center gap-2 px-4 py-2 bg-white/20 rounded-full text-sm font-medium mb-6 backdrop-blur-sm">
                    <Sparkles className="w-4 h-4" />
                    Powered by Kimi 2.5 AI
                  </div>
                  <h1 className="text-5xl md:text-6xl lg:text-7xl font-bold leading-tight mb-6">
                    Turn Cold Outreach Into
                    <span className="text-yellow-300"> Warm Conversations</span>
                  </h1>
                  <p className="text-xl text-white/90 mb-8 max-w-xl">
                    Generic emails get 1% response rates. Our AI-powered system achieves
                    <span className="font-bold text-yellow-300"> 15-20%</span> through hyper-personalization.
                  </p>
                  <div className="flex flex-wrap gap-4">
                    <Button size="lg" className="bg-white text-violet-600 hover:bg-gray-100 px-8">
                      <Play className="w-5 h-5 mr-2" />
                      Watch Demo
                    </Button>
                    <Button size="lg" variant="outline" className="border-white text-white hover:bg-white/20 px-8">
                      Schedule Call
                    </Button>
                  </div>
                  <div className="flex items-center gap-6 mt-10">
                    <div className="flex -space-x-3">
                      {[1, 2, 3, 4].map((i) => (
                        <div key={i} className="w-10 h-10 rounded-full bg-gradient-to-br from-violet-400 to-purple-500 border-2 border-white flex items-center justify-center text-white text-xs font-bold">
                          {String.fromCharCode(64 + i)}
                        </div>
                      ))}
                    </div>
                    <div className="text-white/80 text-sm">
                      <span className="font-bold text-white">500+</span> companies trust us
                    </div>
                  </div>
                </div>
                <div className="relative">
                  <EmailPreview />
                </div>
              </div>
            </div>

            <div className="absolute bottom-8 left-1/2 -translate-x-1/2 text-white/60 animate-bounce">
              <ChevronDown className="w-6 h-6" />
            </div>
          </section>

          {/* Stats Section */}
          <section className="py-20 bg-gray-50">
            <div className="max-w-7xl mx-auto px-6">
              <div className="text-center mb-12">
                <h2 className="text-3xl font-bold text-gray-800 mb-4">Proven Results</h2>
                <p className="text-gray-600">Real numbers from real campaigns</p>
              </div>
              <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
                <StatCard value={18} suffix="%" label="Average Response Rate" icon={TrendingUp} delay={0} />
                <StatCard value={42} suffix="%" label="Open Rate" icon={Mail} delay={100} />
                <StatCard value={10000} suffix="+" label="Leads Processed/Day" icon={Users} delay={200} />
                <StatCard value={30} suffix="s" label="Per Email Generated" icon={Clock} delay={300} />
              </div>
            </div>
          </section>

          {/* Features Section */}
          <section id="features" className="py-24 bg-white">
            <div className="max-w-7xl mx-auto px-6">
              <div className="text-center mb-16">
                <Badge className="mb-4 bg-violet-100 text-violet-700 hover:bg-violet-100">Features</Badge>
                <h2 className="text-4xl font-bold text-gray-800 mb-4">
                  Everything You Need for <span className="gradient-text">High-Converting</span> Outreach
                </h2>
                <p className="text-gray-600 max-w-2xl mx-auto">
                  Our AI-powered platform handles the entire outreach workflow from research to sending
                </p>
              </div>
              <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
                <FeatureCard
                  icon={Linkedin}
                  title="LinkedIn Profile Analysis"
                  description="Deep scan of LinkedIn profiles, recent posts, and professional activity to understand each lead."
                  color="bg-gradient-to-br from-blue-500 to-blue-600"
                />
                <FeatureCard
                  icon={Building2}
                  title="Company Intelligence"
                  description="Aggregates company news, funding signals, hiring trends, and trigger events for perfect timing."
                  color="bg-gradient-to-br from-violet-500 to-purple-600"
                />
                <FeatureCard
                  icon={Brain}
                  title="AI-Powered Analysis"
                  description="Kimi 2.5 analyzes pain points, interests, and identifies the best personalization hooks."
                  color="bg-gradient-to-br from-pink-500 to-rose-600"
                />
                <FeatureCard
                  icon={MessageSquare}
                  title="Hyper-Personalized Emails"
                  description="Not templates - actual personalized writing based on real data and recent activity."
                  color="bg-gradient-to-br from-green-500 to-emerald-600"
                />
                <FeatureCard
                  icon={Shield}
                  title="Quality Control"
                  description="Automated quality scoring ensures every email meets personalization standards."
                  color="bg-gradient-to-br from-orange-500 to-amber-600"
                />
                <FeatureCard
                  icon={LineChart}
                  title="A/B Testing"
                  description="Generate multiple variants with different approaches to optimize response rates."
                  color="bg-gradient-to-br from-cyan-500 to-blue-600"
                />
              </div>
            </div>
          </section>

          {/* How It Works Section */}
          <section id="how-it-works" className="py-24 bg-gray-50">
            <div className="max-w-7xl mx-auto px-6">
              <div className="text-center mb-16">
                <Badge className="mb-4 bg-violet-100 text-violet-700 hover:bg-violet-100">Process</Badge>
                <h2 className="text-4xl font-bold text-gray-800 mb-4">How It Works</h2>
                <p className="text-gray-600 max-w-2xl mx-auto">
                  Four simple stages from lead to personalized email
                </p>
              </div>
              <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
                <StepCard
                  number={1}
                  title="Data Enrichment"
                  description="Scrape LinkedIn profiles, fetch company news, detect trigger events"
                  icon={Zap}
                />
                <StepCard
                  number={2}
                  title="AI Analysis"
                  description="Kimi analyzes pain points, interests, and personalization opportunities"
                  icon={Brain}
                />
                <StepCard
                  number={3}
                  title="Email Generation"
                  description="Generate hyper-personalized emails with specific hooks"
                  icon={Mail}
                />
                <StepCard
                  number={4}
                  title="Quality Control"
                  description="Score emails, check personalization, auto-send or queue for review"
                  icon={CheckCircle}
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

          {/* ROI Calculator Section */}
          <section id="roi" className="py-24 bg-gray-50">
            <div className="max-w-7xl mx-auto px-6">
              <div className="grid lg:grid-cols-2 gap-12 items-center">
                <div>
                  <Badge className="mb-4 bg-violet-100 text-violet-700 hover:bg-violet-100">ROI Calculator</Badge>
                  <h2 className="text-4xl font-bold text-gray-800 mb-6">
                    Calculate Your <span className="gradient-text">Potential ROI</span>
                  </h2>
                  <p className="text-gray-600 mb-8 leading-relaxed">
                    See how much additional revenue you could generate by switching from generic
                    cold emails to hyper-personalized outreach. Adjust the sliders to match your business.
                  </p>
                  <div className="space-y-6">
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center">
                        <TrendingUp className="w-6 h-6 text-green-600" />
                      </div>
                      <div>
                        <div className="font-semibold text-gray-800">18x More Meetings</div>
                        <div className="text-gray-600 text-sm">Average improvement in meetings booked</div>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center">
                        <Clock className="w-6 h-6 text-blue-600" />
                      </div>
                      <div>
                        <div className="font-semibold text-gray-800">Save 500+ Hours/Month</div>
                        <div className="text-gray-600 text-sm">No more manual personalization</div>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-12 bg-purple-100 rounded-xl flex items-center justify-center">
                        <Rocket className="w-6 h-6 text-purple-600" />
                      </div>
                      <div>
                        <div className="font-semibold text-gray-800">13,100% ROI</div>
                        <div className="text-gray-600 text-sm">Average return on investment</div>
                      </div>
                    </div>
                  </div>
                </div>
                <div>
                  <ROICalculator />
                </div>
              </div>
            </div>
          </section>

          {/* Testimonials Section */}
          <section className="py-24 bg-white">
            <div className="max-w-7xl mx-auto px-6">
              <div className="text-center mb-16">
                <Badge className="mb-4 bg-violet-100 text-violet-700 hover:bg-violet-100">Testimonials</Badge>
                <h2 className="text-4xl font-bold text-gray-800 mb-4">Loved by Sales Teams</h2>
                <p className="text-gray-600 max-w-2xl mx-auto">
                  See what our customers have to say about their results
                </p>
              </div>
              <div className="grid md:grid-cols-3 gap-8">
                <TestimonialCard
                  name="Sarah Chen"
                  role="VP of Sales"
                  company="TechFlow"
                  quote="We went from 0.8% response rate to 16.5% in just one month. The AI understands our prospects better than our SDRs did."
                  rating={5}
                />
                <TestimonialCard
                  name="Michael Roberts"
                  role="Sales Director"
                  company="CloudScale"
                  quote="The personalization is incredible. Our prospects actually think we researched them for hours. Best investment we've made."
                  rating={5}
                />
                <TestimonialCard
                  name="Priya Sharma"
                  role="Head of Growth"
                  company="DataSync"
                  quote="Saved our team 40 hours per week while tripling our meeting bookings. The ROI was visible within the first week."
                  rating={5}
                />
              </div>
            </div>
          </section>

          {/* Pricing Section */}
          <section className="py-24 bg-gray-50">
            <div className="max-w-7xl mx-auto px-6">
              <div className="text-center mb-16">
                <Badge className="mb-4 bg-violet-100 text-violet-700 hover:bg-violet-100">Pricing</Badge>
                <h2 className="text-4xl font-bold text-gray-800 mb-4">Simple, Transparent Pricing</h2>
                <p className="text-gray-600 max-w-2xl mx-auto">
                  Start free, scale as you grow. No hidden fees.
                </p>
              </div>
              <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
                <Card className="border-0 shadow-lg">
                  <CardHeader className="pb-4">
                    <CardTitle className="text-xl">Starter</CardTitle>
                    <div className="text-3xl font-bold text-gray-800 mt-2">$99<span className="text-lg text-gray-500">/mo</span></div>
                  </CardHeader>
                  <CardContent>
                    <ul className="space-y-3 mb-6">
                      <li className="flex items-center gap-2 text-sm text-gray-600">
                        <CheckCircle className="w-4 h-4 text-green-500" /> 500 leads/month
                      </li>
                      <li className="flex items-center gap-2 text-sm text-gray-600">
                        <CheckCircle className="w-4 h-4 text-green-500" /> Basic personalization
                      </li>
                      <li className="flex items-center gap-2 text-sm text-gray-600">
                        <CheckCircle className="w-4 h-4 text-green-500" /> Email generation
                      </li>
                      <li className="flex items-center gap-2 text-sm text-gray-600">
                        <CheckCircle className="w-4 h-4 text-green-500" /> Analytics dashboard
                      </li>
                    </ul>
                    <Button variant="outline" className="w-full">Get Started</Button>
                  </CardContent>
                </Card>
                <Card className="border-2 border-violet-500 shadow-xl relative">
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-4 py-1 bg-violet-500 text-white text-sm font-medium rounded-full">
                    Most Popular
                  </div>
                  <CardHeader className="pb-4">
                    <CardTitle className="text-xl">Professional</CardTitle>
                    <div className="text-3xl font-bold text-violet-600 mt-2">$299<span className="text-lg text-gray-500">/mo</span></div>
                  </CardHeader>
                  <CardContent>
                    <ul className="space-y-3 mb-6">
                      <li className="flex items-center gap-2 text-sm text-gray-600">
                        <CheckCircle className="w-4 h-4 text-green-500" /> 2,500 leads/month
                      </li>
                      <li className="flex items-center gap-2 text-sm text-gray-600">
                        <CheckCircle className="w-4 h-4 text-green-500" /> Advanced personalization
                      </li>
                      <li className="flex items-center gap-2 text-sm text-gray-600">
                        <CheckCircle className="w-4 h-4 text-green-500" /> A/B testing
                      </li>
                      <li className="flex items-center gap-2 text-sm text-gray-600">
                        <CheckCircle className="w-4 h-4 text-green-500" /> LinkedIn integration
                      </li>
                      <li className="flex items-center gap-2 text-sm text-gray-600">
                        <CheckCircle className="w-4 h-4 text-green-500" /> Priority support
                      </li>
                    </ul>
                    <Button className="w-full bg-violet-600 hover:bg-violet-700">Get Started</Button>
                  </CardContent>
                </Card>
                <Card className="border-0 shadow-lg">
                  <CardHeader className="pb-4">
                    <CardTitle className="text-xl">Enterprise</CardTitle>
                    <div className="text-3xl font-bold text-gray-800 mt-2">Custom</div>
                  </CardHeader>
                  <CardContent>
                    <ul className="space-y-3 mb-6">
                      <li className="flex items-center gap-2 text-sm text-gray-600">
                        <CheckCircle className="w-4 h-4 text-green-500" /> Unlimited leads
                      </li>
                      <li className="flex items-center gap-2 text-sm text-gray-600">
                        <CheckCircle className="w-4 h-4 text-green-500" /> Custom AI training
                      </li>
                      <li className="flex items-center gap-2 text-sm text-gray-600">
                        <CheckCircle className="w-4 h-4 text-green-500" /> Dedicated support
                      </li>
                      <li className="flex items-center gap-2 text-sm text-gray-600">
                        <CheckCircle className="w-4 h-4 text-green-500" /> SLA guarantee
                      </li>
                      <li className="flex items-center gap-2 text-sm text-gray-600">
                        <CheckCircle className="w-4 h-4 text-green-500" /> On-premise option
                      </li>
                    </ul>
                    <Button variant="outline" className="w-full">Contact Sales</Button>
                  </CardContent>
                </Card>
              </div>
            </div>
          </section>

          {/* CTA Section */}
          <section className="py-24 gradient-hero relative overflow-hidden">
            <div className="absolute inset-0 overflow-hidden">
              <div className="absolute top-0 left-0 w-full h-full bg-[url('data:image/svg+xml,%3Csvg%20width%3D%2260%22%20height%3D%2260%22%20viewBox%3D%220%200%2060%2060%22%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%3E%3Cg%20fill%3D%22none%22%20fill-rule%3D%22evenodd%22%3E%3Cg%20fill%3D%22%23ffffff%22%20fill-opacity%3D%220.05%22%3E%3Cpath%20d%3D%22M36%2034v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6%2034v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6%204V0H4v4H0v2h4v4h2V6h4V4H6z%22%2F%3E%3C%2Fg%3E%3C%2Fg%3E%3C%2Fsvg%3E')] opacity-20"></div>
            </div>
            <div className="max-w-4xl mx-auto px-6 text-center relative z-10">
              <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">
                Ready to 18x Your Response Rates?
              </h2>
              <p className="text-xl text-white/90 mb-10 max-w-2xl mx-auto">
                Join 500+ companies using Outreach Architect to transform their cold outreach into warm conversations.
              </p>
              <div className="flex flex-wrap justify-center gap-4">
                <Button size="lg" className="bg-white text-violet-600 hover:bg-gray-100 px-8 text-lg">
                  Start Free Trial
                  <ArrowRight className="w-5 h-5 ml-2" />
                </Button>
                <Button size="lg" variant="outline" className="border-white text-white hover:bg-white/20 px-8 text-lg">
                  Schedule Demo
                </Button>
              </div>
              <p className="text-white/70 mt-6 text-sm">No credit card required. 14-day free trial.</p>
            </div>
          </section>

          {/* Footer */}
          <footer className="bg-gray-900 text-white py-16">
            <div className="max-w-7xl mx-auto px-6">
              <div className="grid md:grid-cols-4 gap-12 mb-12">
                <div>
                  <div className="flex items-center gap-2 mb-4">
                    <div className="w-10 h-10 bg-gradient-to-br from-violet-500 to-purple-600 rounded-xl flex items-center justify-center">
                      <Mail className="w-5 h-5 text-white" />
                    </div>
                    <span className="font-bold text-xl">Outreach Architect</span>
                  </div>
                  <p className="text-gray-400 text-sm leading-relaxed">
                    Hyper-personalized cold outreach powered by AI.
                    Transform your sales process today.
                  </p>
                </div>
                <div>
                  <h4 className="font-semibold mb-4">Product</h4>
                  <ul className="space-y-2 text-gray-400 text-sm">
                    <li><a href="#" className="hover:text-white transition">Features</a></li>
                    <li><a href="#" className="hover:text-white transition">Pricing</a></li>
                    <li><a href="#" className="hover:text-white transition">Integrations</a></li>
                    <li><a href="#" className="hover:text-white transition">API</a></li>
                  </ul>
                </div>
                <div>
                  <h4 className="font-semibold mb-4">Company</h4>
                  <ul className="space-y-2 text-gray-400 text-sm">
                    <li><a href="#" className="hover:text-white transition">About</a></li>
                    <li><a href="#" className="hover:text-white transition">Blog</a></li>
                    <li><a href="#" className="hover:text-white transition">Careers</a></li>
                    <li><a href="#" className="hover:text-white transition">Contact</a></li>
                  </ul>
                </div>
                <div>
                  <h4 className="font-semibold mb-4">Legal</h4>
                  <ul className="space-y-2 text-gray-400 text-sm">
                    <li><a href="#" className="hover:text-white transition">Privacy</a></li>
                    <li><a href="#" className="hover:text-white transition">Terms</a></li>
                    <li><a href="#" className="hover:text-white transition">Security</a></li>
                  </ul>
                </div>
              </div>
              <div className="pt-8 border-t border-gray-800 text-center text-gray-500 text-sm">
                <p>© 2024 Outreach Architect. All rights reserved.</p>
              </div>
            </div>
          </footer>
        </>
      ) : (
        <Dashboard />
      )}
    </div>
  );
}

export default App;
