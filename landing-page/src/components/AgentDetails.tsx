'use client';

import React, { useState } from 'react';

const AGENTS = [
  {
    name: 'Kyle',
    role: 'Legal Advisor',
    summary: 'Routes tasks and coordinates agents.',
    details:
      'Placeholder: Schedules jobs, prioritizes tasks, and monitors agent health. Exposes status metrics and retry logic.',
  },
  {
    name: 'Bill',
    role: 'Business Guide',
    summary: 'Processes inputs and extracts insights.',
    details:
      'Placeholder: Runs data parsing, NLP pipelines, feature extraction, and provides analysis summaries for other agents.',
  },
  {
    name: 'Jeremy',
    role: 'Other thing..',
    summary: 'Performs external actions (APIs, DB).',
    details:
      'Placeholder: Executes API calls, updates databases, and returns execution results with success/failure metadata.',
  },
  {
    name: 'Sarah',
    role: 'Other thing',
    summary: 'Monitors for safety, compliance and policy violations.',
    details:
      'Placeholder: Enforces content filters, checks for PII, and vetoes or flags potentially unsafe outputs.',
  },
];

export default function AgentsDetails() {
  const [openIndex, setOpenIndex] = useState<number | null>(null);

  function toggle(i: number) {
    setOpenIndex(prev => (prev === i ? null : i));
  }

  return (
    <section id="our-agents" className="py-12 border-y border-gray-100 bg-white/50">
      <div className="max-w-6xl mx-auto px-6">
        <p className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-8">
          Multi-agent model — click an agent for details
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {AGENTS.map((agent, i) => (
            <div
              key={agent.name}
              className="rounded-2xl border border-gray-100 bg-white p-4 shadow-sm hover:shadow-md transition-shadow"
            >
              <button
                onClick={() => toggle(i)}
                className="w-full flex items-center justify-between text-left"
                aria-expanded={openIndex === i}
                aria-controls={`agent-panel-${i}`}
              >
                <div>
                  <div className="text-lg font-semibold text-foreground">{agent.name}</div>
                  <div className="text-sm text-gray-500">{agent.role}</div>
                  <div className="text-sm text-gray-600 mt-2">{agent.summary}</div>
                </div>

                <div
                  className={`ml-4 transform transition-transform ${
                    openIndex === i ? 'rotate-180' : 'rotate-0'
                  }`}
                  aria-hidden
                >
                  <svg
                    className="w-5 h-5 text-gray-400"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
                  </svg>
                </div>
              </button>

              <div
                id={`agent-panel-${i}`}
                className={`mt-4 text-sm text-gray-600 overflow-hidden transition-all ${
                  openIndex === i ? 'max-h-96' : 'max-h-0'
                }`}
              >
                <div className="space-y-2">
                  <p>{agent.details}</p>
                  <ul className="text-xs text-gray-500 list-disc list-inside">
                    <li>Capabilities: Placeholder capabilities</li>
                    <li>Inputs: Placeholder inputs</li>
                    <li>Outputs: Placeholder outputs</li>
                  </ul>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
