import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { 
  X, Briefcase, BookOpen, Building2, TrendingUp, Code, Share2, 
  CreditCard, Award, ShieldAlert, Package, Truck, RotateCcw, 
  FileText, ShieldCheck, HeartHandshake, ExternalLink 
} from 'lucide-react';

const INFO_CONTENT = {
  careers: {
    title: 'Careers at Apex',
    icon: Briefcase,
    subtitle: 'Build the future of multi-tenant enterprise e-commerce',
    content: (
      <div className="space-y-4">
        <p className="text-gray-300 text-sm">
          At Apex, we are building next-generation distributed microservice platforms that empower thousands of merchants worldwide. Join our engineering, design, and operations teams to solve complex systems challenges.
        </p>
        <div className="bg-[#1f293d] p-4 rounded-lg border border-gray-700 space-y-2">
          <h5 className="font-semibold text-white text-sm">Open Positions</h5>
          <ul className="text-xs text-gray-300 space-y-1.5 list-disc list-inside">
            <li>Senior Full-Stack Engineer (React, Django, Go)</li>
            <li>Distributed Systems & Cloud Architect (Kubernetes, GCP)</li>
            <li>Product Designer — Enterprise UI/UX Systems</li>
            <li>Senior Security & Compliance Engineer</li>
          </ul>
        </div>
      </div>
    )
  },
  blog: {
    title: 'Apex Tech & Engineering Blog',
    icon: BookOpen,
    subtitle: 'Insights on microservice architecture, performance, and scaling',
    content: (
      <div className="space-y-4 text-sm text-gray-300">
        <p>Explore our engineering deep dives, system design write-ups, and product release updates.</p>
        <div className="space-y-3">
          <div className="p-3 bg-[#1f293d] rounded-lg border border-gray-700">
            <h5 className="font-semibold text-white">Scaling Microservices to 10M Requests/Sec</h5>
            <p className="text-xs text-gray-400 mt-1">How we optimized Kafka event streams and PostgreSQL connection pools across tenant clusters.</p>
          </div>
          <div className="p-3 bg-[#1f293d] rounded-lg border border-gray-700">
            <h5 className="font-semibold text-white">Designing Enterprise Admin UI Systems</h5>
            <p className="text-xs text-gray-400 mt-1">Best practices for building ultra-responsive, accessible admin interfaces in React.</p>
          </div>
        </div>
      </div>
    )
  },
  about: {
    title: 'About Apex Ecosystem',
    icon: Building2,
    subtitle: 'Modern cloud-native commerce infrastructure',
    content: (
      <div className="space-y-4 text-sm text-gray-300">
        <p>
          Apex is a high-performance multi-tenant e-commerce platform designed with isolated microservices for Catalog, Orders, Inventory, Identity, Payments, and Real-time Chat.
        </p>
        <div className="grid grid-cols-2 gap-3 text-xs">
          <div className="p-3 bg-[#1f293d] rounded-lg border border-gray-700">
            <span className="font-bold text-white block text-sm mb-1">99.99% Uptime</span>
            <span>Redundant multi-region deployment across container engines.</span>
          </div>
          <div className="p-3 bg-[#1f293d] rounded-lg border border-gray-700">
            <span className="font-bold text-white block text-sm mb-1">Sub-50ms Latency</span>
            <span>Global edge caching for product catalogs and dynamic storefronts.</span>
          </div>
        </div>
      </div>
    )
  },
  investors: {
    title: 'Investor Relations',
    icon: TrendingUp,
    subtitle: 'Financial news, quarterly reports, and corporate governance',
    content: (
      <div className="space-y-4 text-sm text-gray-300">
        <p>Apex delivers sustained annual revenue growth driven by multi-tenant SaaS adoption and platform commerce volume.</p>
        <div className="bg-[#1f293d] p-4 rounded-lg border border-gray-700 text-xs space-y-2">
          <div className="flex justify-between border-b border-gray-700 pb-2">
            <span className="text-gray-400">Quarterly GMV Growth:</span>
            <span className="font-bold text-emerald-400">+42% YoY</span>
          </div>
          <div className="flex justify-between border-b border-gray-700 pb-2">
            <span className="text-gray-400">Active Merchant Tenants:</span>
            <span className="font-bold text-white">12,400+</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">Annual Recurring Revenue (ARR):</span>
            <span className="font-bold text-purple-400">$85M+</span>
          </div>
        </div>
      </div>
    )
  },
  apps: {
    title: 'Sell Apps on Apex Developer Portal',
    icon: Code,
    subtitle: 'Extend Apex platform capabilities with custom microservice apps',
    content: (
      <div className="space-y-4 text-sm text-gray-300">
        <p>Publish custom integrations, storefront themes, and automated workflow apps on the Apex App Marketplace.</p>
        <ul className="list-disc list-inside text-xs space-y-1.5 bg-[#1f293d] p-3 rounded-lg border border-gray-700">
          <li>REST & GraphQL APIs with 100% endpoint coverage</li>
          <li>Real-time Webhook subscriptions for Order & Payment events</li>
          <li>80% developer revenue share on app subscriptions</li>
        </ul>
      </div>
    )
  },
  affiliate: {
    title: 'Apex Affiliate Program',
    icon: Share2,
    subtitle: 'Earn up to 10% commission on referred sales & merchant subscriptions',
    content: (
      <div className="space-y-4 text-sm text-gray-300">
        <p>Join thousands of creators, publishers, and agencies earning passive income by recommending Apex products and store plans.</p>
        <div className="p-3 bg-[#1f293d] rounded-lg border border-gray-700 text-xs space-y-2">
          <div className="flex items-center gap-2">
            <Award className="w-4 h-4 text-amber-400" />
            <span>Competitive commission payouts paid directly via ACH/Stripe</span>
          </div>
          <div className="flex items-center gap-2">
            <FileText className="w-4 h-4 text-purple-400" />
            <span>Dedicated affiliate tracking dashboard with real-time analytics</span>
          </div>
        </div>
      </div>
    )
  },
  card: {
    title: 'Apex Business Card',
    icon: CreditCard,
    subtitle: '5% Cash Back on all Apex Purchases & No Annual Fees',
    content: (
      <div className="space-y-4 text-sm text-gray-300">
        <p>Accelerate your business savings with zero foreign transaction fees, flexible payment terms, and instant virtual cards.</p>
        <div className="bg-gradient-to-r from-purple-900/60 to-indigo-900/60 p-4 rounded-xl border border-purple-500/40 text-xs space-y-2">
          <p className="font-bold text-white text-sm">Cardholder Benefits:</p>
          <ul className="space-y-1 list-disc list-inside text-gray-200">
            <li>5% Cash Back on Apex.com & merchant purchases</li>
            <li>2% Cash Back on gas stations & shipping services</li>
            <li>1% Cash Back on all other eligible business purchases</li>
          </ul>
        </div>
      </div>
    )
  },
  points: {
    title: 'Shop with Points',
    icon: Award,
    subtitle: 'Redeem accumulated rewards directly at checkout',
    content: (
      <div className="space-y-4 text-sm text-gray-300">
        <p>Every purchase earns Apex Rewards Points that can be converted directly into checkout discounts or store gift balances.</p>
        <div className="p-3 bg-[#1f293d] rounded-lg border border-gray-700 text-xs flex justify-between items-center">
          <span>Current Conversion Rate:</span>
          <span className="font-bold text-amber-400">100 Points = $1.00 Credit</span>
        </div>
      </div>
    )
  },
  covid: {
    title: 'Apex & COVID-19 Health Safety Protocols',
    icon: ShieldAlert,
    subtitle: 'Our commitment to customer safety and supply chain continuity',
    content: (
      <div className="space-y-4 text-sm text-gray-300">
        <p>We maintain strict hygiene and safety standards across all fulfillment centers and delivery networks.</p>
        <ul className="list-disc list-inside text-xs space-y-1.5 bg-[#1f293d] p-3 rounded-lg border border-gray-700">
          <li>100% Contact-Free doorstep delivery options available</li>
          <li>Regular sanitization of warehouse sorting machinery</li>
          <li>Temperature screening and personal protective equipment for staff</li>
        </ul>
      </div>
    )
  },
  shipping: {
    title: 'Shipping Rates & Delivery Policies',
    icon: Truck,
    subtitle: 'Fast, reliable fulfillment options for every order',
    content: (
      <div className="space-y-4 text-sm text-gray-300">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
          <div className="p-3 bg-[#1f293d] rounded-lg border border-gray-700 text-center">
            <span className="font-bold text-white block text-sm">Standard</span>
            <span className="text-gray-400">2 - 4 Business Days</span>
            <span className="text-emerald-400 font-semibold block mt-1">FREE over $35</span>
          </div>
          <div className="p-3 bg-[#1f293d] rounded-lg border border-gray-700 text-center">
            <span className="font-bold text-white block text-sm">Express</span>
            <span className="text-gray-400">1 - 2 Business Days</span>
            <span className="text-gray-200 block mt-1">$9.99 Flat Rate</span>
          </div>
          <div className="p-3 bg-[#1f293d] rounded-lg border border-gray-700 text-center">
            <span className="font-bold text-white block text-sm">Same-Day</span>
            <span className="text-gray-400">Select Zip Codes</span>
            <span className="text-purple-400 block mt-1">$14.99 Flat Rate</span>
          </div>
        </div>
      </div>
    )
  },
  returns: {
    title: 'Returns & Replacements Policy',
    icon: RotateCcw,
    subtitle: 'Hassle-free 30-day return window with instant refunds',
    content: (
      <div className="space-y-4 text-sm text-gray-300">
        <p>If you are not 100% satisfied with your order, return eligible items within 30 days of receipt for a full refund or replacement.</p>
        <div className="p-3 bg-[#1f293d] rounded-lg border border-gray-700 text-xs space-y-2">
          <div className="flex items-center gap-2">
            <RotateCcw className="w-4 h-4 text-emerald-400" />
            <span>Print pre-paid shipping labels directly from your Order History</span>
          </div>
          <div className="flex items-center gap-2">
            <Package className="w-4 h-4 text-purple-400" />
            <span>Drop off packages at any authorized logistics counter or carrier hub</span>
          </div>
        </div>
      </div>
    )
  },
  terms: {
    title: 'Conditions of Use & Terms of Service',
    icon: FileText,
    subtitle: 'Legal guidelines governing platform use and transactions',
    content: (
      <div className="space-y-4 text-sm text-gray-300 max-h-60 overflow-y-auto custom-scrollbar pr-2">
        <p>By accessing or using the Apex storefront or services, you agree to comply with our standard terms of use, privacy rules, and seller guidelines.</p>
        <h5 className="font-semibold text-white text-xs">Key Provisions:</h5>
        <ul className="list-disc list-inside text-xs space-y-1 text-gray-400">
          <li>Account security and credential confidentiality responsibilities</li>
          <li>Prohibition of unauthorized automated scraping or system abuse</li>
          <li>Intellectual property ownership of platform marks and catalog data</li>
          <li>Dispute resolution and binding arbitration procedures</li>
        </ul>
      </div>
    )
  },
  privacy: {
    title: 'Privacy Notice',
    icon: ShieldCheck,
    subtitle: 'How we collect, protect, and handle your data',
    content: (
      <div className="space-y-4 text-sm text-gray-300">
        <p>Apex strictly respects customer data privacy and complies with GDPR, CCPA, and global data defense standards.</p>
        <div className="p-3 bg-[#1f293d] rounded-lg border border-gray-700 text-xs space-y-1.5">
          <p className="font-semibold text-white">Our Privacy Guarantees:</p>
          <p>• We NEVER sell personal customer data to third-party advertisers.</p>
          <p>• End-to-end TLS encryption for all payment transactions and token storage.</p>
          <p>• You can export or request complete deletion of your account data anytime.</p>
        </div>
      </div>
    )
  },
  healthPrivacy: {
    title: 'Consumer Health Data Privacy Disclosure',
    icon: HeartHandshake,
    subtitle: 'Specific health data protections and state privacy compliance',
    content: (
      <div className="space-y-4 text-sm text-gray-300">
        <p>This disclosure describes how Apex processes consumer health data collected in connection with personal care or health-related product categories.</p>
        <p className="text-xs text-gray-400">We process health category preferences solely to fulfill consumer orders and provide customer support, never for unauthorized profiling.</p>
      </div>
    )
  }
};

export const Footer = () => {
  const [activeModalKey, setActiveModalKey] = useState(null);

  const activeModalData = activeModalKey ? INFO_CONTENT[activeModalKey] : null;

  return (
    <footer className="bg-[#131921] text-white mt-12 relative z-10 border-t border-slate-800 font-sans">
      {/* Back To Top Bar */}
      <div 
        className="bg-[#37475A] py-3.5 text-center hover:bg-[#485769] cursor-pointer transition-colors select-none" 
        onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
      >
        <span className="text-xs font-semibold tracking-wide text-gray-100">Back to top</span>
      </div>
      
      {/* Main Footer Links Columns */}
      <div className="max-w-6xl mx-auto py-8 sm:py-12 px-4 sm:px-6 md:px-8 grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-6 sm:gap-8">
        {/* Column 1: Get to Know Us */}
        <div>
          <h4 className="font-extrabold text-sm mb-3.5 text-white tracking-wide">Get to Know Us</h4>
          <ul className="space-y-2 text-xs text-gray-300 font-normal">
            <li>
              <button onClick={() => setActiveModalKey('careers')} className="hover:underline hover:text-white text-left transition-colors">
                Careers
              </button>
            </li>
            <li>
              <button onClick={() => setActiveModalKey('blog')} className="hover:underline hover:text-white text-left transition-colors">
                Blog
              </button>
            </li>
            <li>
              <button onClick={() => setActiveModalKey('about')} className="hover:underline hover:text-white text-left transition-colors">
                About Apex
              </button>
            </li>
            <li>
              <button onClick={() => setActiveModalKey('investors')} className="hover:underline hover:text-white text-left transition-colors">
                Investor Relations
              </button>
            </li>
          </ul>
        </div>

        {/* Column 2: Make Money with Us */}
        <div>
          <h4 className="font-extrabold text-sm mb-3.5 text-white tracking-wide">Make Money with Us</h4>
          <ul className="space-y-2 text-xs text-gray-300 font-normal">
            <li>
              <a 
                href="http://localhost:3002/register" 
                target="_blank" 
                rel="noopener noreferrer" 
                className="hover:underline hover:text-amber-400 transition-colors inline-flex items-center gap-1 font-semibold text-white"
              >
                <span>Sell products on Apex</span>
                <ExternalLink className="w-3 h-3 text-amber-400" />
              </a>
            </li>
            <li>
              <a 
                href="http://localhost:3002/login" 
                target="_blank" 
                rel="noopener noreferrer" 
                className="hover:underline hover:text-amber-400 transition-colors inline-flex items-center gap-1"
              >
                <span>Sell on Apex Business</span>
                <ExternalLink className="w-3 h-3 text-gray-400" />
              </a>
            </li>
            <li>
              <button onClick={() => setActiveModalKey('apps')} className="hover:underline hover:text-white text-left transition-colors">
                Sell apps on Apex
              </button>
            </li>
            <li>
              <button onClick={() => setActiveModalKey('affiliate')} className="hover:underline hover:text-white text-left transition-colors">
                Become an Affiliate
              </button>
            </li>
            <li>
              <Link to="/item-requests" className="hover:underline hover:text-purple-300 transition-colors font-medium text-purple-400 block pt-1">
                + Submit Item Sourcing Request
              </Link>
            </li>
          </ul>
        </div>

        {/* Column 3: Apex Payment Products */}
        <div>
          <h4 className="font-extrabold text-sm mb-3.5 text-white tracking-wide">Apex Payment Products</h4>
          <ul className="space-y-2 text-xs text-gray-300 font-normal">
            <li>
              <button onClick={() => setActiveModalKey('card')} className="hover:underline hover:text-white text-left transition-colors">
                Apex Business Card
              </button>
            </li>
            <li>
              <button onClick={() => setActiveModalKey('points')} className="hover:underline hover:text-white text-left transition-colors">
                Shop with Points
              </button>
            </li>
            <li>
              <Link to="/payments" className="hover:underline hover:text-white text-left transition-colors block">
                Reload Your Balance
              </Link>
            </li>
            <li>
              <Link to="/invoices" className="hover:underline hover:text-white text-left transition-colors block">
                Invoices & Statements
              </Link>
            </li>
          </ul>
        </div>

        {/* Column 4: Let Us Help You */}
        <div>
          <h4 className="font-extrabold text-sm mb-3.5 text-white tracking-wide">Let Us Help You</h4>
          <ul className="space-y-2 text-xs text-gray-300 font-normal">
            <li>
              <button onClick={() => setActiveModalKey('covid')} className="hover:underline hover:text-white text-left transition-colors">
                Apex and COVID-19
              </button>
            </li>
            <li>
              <Link to="/profile" className="hover:underline hover:text-white text-left transition-colors block">
                Your Account
              </Link>
            </li>
            <li>
              <Link to="/orders" className="hover:underline hover:text-white text-left transition-colors block">
                Your Orders
              </Link>
            </li>
            <li>
              <button onClick={() => setActiveModalKey('shipping')} className="hover:underline hover:text-white text-left transition-colors">
                Shipping Rates & Policies
              </button>
            </li>
            <li>
              <button onClick={() => setActiveModalKey('returns')} className="hover:underline hover:text-white text-left transition-colors">
                Returns & Replacements
              </button>
            </li>
            <li>
              <Link to="/chat" className="hover:underline hover:text-emerald-400 transition-colors block font-medium text-emerald-300 pt-1">
                Live Support Chat
              </Link>
            </li>
          </ul>
        </div>
      </div>

      {/* Footer Bottom Bar */}
      <div className="border-t border-[#232F3E] py-8 text-center text-xs text-gray-400 flex flex-col items-center bg-[#0F1117] px-4 space-y-3">
        <div className="flex flex-wrap justify-center gap-4 sm:gap-6 text-xs font-medium">
          <button onClick={() => setActiveModalKey('terms')} className="hover:underline hover:text-white transition-colors">
            Conditions of Use
          </button>
          <button onClick={() => setActiveModalKey('privacy')} className="hover:underline hover:text-white transition-colors">
            Privacy Notice
          </button>
          <button onClick={() => setActiveModalKey('healthPrivacy')} className="hover:underline hover:text-white transition-colors">
            Consumer Health Data Privacy Disclosure
          </button>
        </div>
        <div className="text-[11px] text-gray-500 font-mono">
          © 2024-{new Date().getFullYear()}, Apex Commerce Inc. or its microservice affiliates. All rights reserved.
        </div>
      </div>

      {/* Informational Policy & Content Modal */}
      {activeModalData && (
        <div 
          className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-3 sm:p-4 animate-in fade-in duration-200"
          onClick={() => setActiveModalKey(null)}
        >
          <div 
            className="bg-[#171e2e] border border-gray-700 rounded-2xl max-w-lg w-full p-4 sm:p-6 shadow-2xl flex flex-col max-h-[90vh] sm:max-h-[85vh] relative text-left text-white animate-in zoom-in-95 duration-200 my-auto overflow-hidden"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div className="flex items-start justify-between gap-3 border-b border-gray-700/80 pb-3 shrink-0">
              <div className="flex items-center gap-3">
                {activeModalData.icon && (
                  <div className="w-10 h-10 rounded-xl bg-purple-600/20 border border-purple-500/40 flex items-center justify-center text-purple-400 shrink-0">
                    <activeModalData.icon className="w-5 h-5" />
                  </div>
                )}
                <div>
                  <h3 className="font-extrabold text-base text-white tracking-wide leading-snug">
                    {activeModalData.title}
                  </h3>
                  <p className="text-xs text-gray-400 mt-0.5">
                    {activeModalData.subtitle}
                  </p>
                </div>
              </div>

              <button 
                onClick={() => setActiveModalKey(null)}
                className="p-1.5 rounded-lg bg-gray-800 hover:bg-gray-700 text-gray-400 hover:text-white transition-colors shrink-0"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Body Content */}
            <div className="flex-1 overflow-y-auto custom-scrollbar py-3 pr-1">
              {activeModalData.content}
            </div>

            {/* Modal Footer */}
            <div className="flex justify-end pt-3 border-t border-gray-700/80 shrink-0">
              <button 
                onClick={() => setActiveModalKey(null)}
                className="px-5 py-2 rounded-lg bg-purple-600 hover:bg-purple-500 text-white font-semibold text-xs transition-all shadow-md active:scale-95"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </footer>
  );
};
