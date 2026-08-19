/**
 * EKIP v1.0.0 — World-Class Production Landing Page
 */

import React from 'react';

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-[#0B0F19] text-[#F9FAFB] font-sans selection:bg-[#6366F1] selection:text-white">
      {/* Navigation Bar */}
      <nav className="border-b border-[#1F2937] bg-[#0B0F19]/80 backdrop-blur-md sticky top-0 z-50 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <span className="text-2xl">🧠</span>
          <span className="text-xl font-bold bg-gradient-to-r from-[#818CF8] to-[#10B981] bg-clip-text text-transparent">
            EKIP
          </span>
          <span className="text-xs bg-[#1F2937] text-[#9CA3AF] px-2 py-0.5 rounded-full font-mono">
            v1.0.0 Public Release
          </span>
        </div>
        <div className="hidden md:flex items-center space-x-6 text-sm font-medium text-[#9CA3AF]">
          <a href="#features" className="hover:text-white transition">Features</a>
          <a href="#pipeline" className="hover:text-white transition">Orchestration</a>
          <a href="#benchmarks" className="hover:text-white transition">Benchmarks</a>
          <a href="#docs" className="hover:text-white transition">Docs</a>
        </div>
        <div className="flex items-center space-x-4">
          <a href="/login" className="text-sm font-medium text-[#9CA3AF] hover:text-white transition">Sign In</a>
          <a href="/dashboard" className="bg-[#6366F1] hover:bg-[#4F46E5] text-white text-sm font-medium px-4 py-2 rounded-lg transition shadow-lg shadow-indigo-500/20">
            Launch Platform 🚀
          </a>
        </div>
      </nav>

      {/* Hero Section */}
      <header className="max-w-6xl mx-auto px-6 pt-20 pb-16 text-center">
        <div className="inline-flex items-center space-x-2 bg-indigo-500/10 border border-indigo-500/20 text-[#818CF8] text-xs font-semibold px-3 py-1 rounded-full mb-6">
          <span>✨ AI Learning Operating System</span>
        </div>
        <h1 className="text-5xl md:text-6xl font-extrabold tracking-tight leading-tight mb-6">
          Learn Smarter with <br />
          <span className="bg-gradient-to-r from-[#818CF8] via-[#10B981] to-[#6366F1] bg-clip-text text-transparent">
            Verified Multimodal AI Knowledge
          </span>
        </h1>
        <p className="text-lg md:text-xl text-[#9CA3AF] max-w-3xl mx-auto mb-10 leading-relaxed">
          EKIP transforms fragmented search into an intelligent, evidence-verified learning operating system. Powered by multi-agent LangGraph orchestration, 14 domain knowledge providers, and adaptive study modules.
        </p>
        <div className="flex flex-wrap justify-center gap-4">
          <a href="/dashboard" className="bg-[#6366F1] hover:bg-[#4F46E5] text-white text-base font-semibold px-8 py-3.5 rounded-xl transition shadow-xl shadow-indigo-500/25">
            Try Demo Platform
          </a>
          <a href="https://github.com" target="_blank" rel="noreferrer" className="bg-[#1F2937] hover:bg-[#374151] text-white text-base font-semibold px-8 py-3.5 rounded-xl border border-gray-700 transition">
            Star on GitHub ⭐️
          </a>
        </div>
      </header>

      {/* Orchestration Pipeline */}
      <section id="pipeline" className="max-w-6xl mx-auto px-6 py-16 border-t border-[#1F2937]">
        <h2 className="text-3xl font-bold text-center mb-4">12-Node LangGraph Orchestration Pipeline</h2>
        <p className="text-center text-[#9CA3AF] mb-12">From natural student prompt to verified educational lesson and practice artifacts.</p>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
          {[
            { step: '01', title: 'Student Question', desc: 'Natural query input' },
            { step: '02', title: 'Knowledge Planner', desc: 'Intent & difficulty' },
            { step: '03', title: 'Multi-Agent Collection', desc: '14 Parallel sources' },
            { step: '04', title: 'Evidence Verification', desc: 'CRAG & Agreement matrix' },
            { step: '05', title: 'Educational Synthesis', desc: 'Multimodal lessons' },
            { step: '06', title: 'Guided Learning', desc: 'Skill tree generation' },
            { step: '07', title: 'Learning Modules', desc: 'Quizzes & flashcards' },
            { step: '08', title: 'Workspace Persistence', desc: 'Long-term sessions' },
          ].map((item, idx) => (
            <div key={idx} className="bg-[#111827] border border-[#1F2937] p-5 rounded-xl hover:border-[#6366F1]/50 transition">
              <span className="text-[#10B981] font-mono text-xs font-bold uppercase tracking-widest mb-2 block">
                Step {item.step}
              </span>
              <h3 className="text-base font-semibold mb-1">{item.title}</h3>
              <p className="text-xs text-[#9CA3AF]">{item.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-[#1F2937] py-8 text-center text-xs text-[#9CA3AF]">
        <p>© 2026 Educational Knowledge Intelligence Platform (EKIP). Released under MIT License.</p>
      </footer>
    </div>
  );
}
