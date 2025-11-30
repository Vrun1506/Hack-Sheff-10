'use client';

import { motion } from 'framer-motion';
import { useCallback } from 'react';

export default function Navbar() {
  // IDs that should align to the top instead of centered
  const TOP_ALIGN = new Set(['features']);

  const scrollTo = useCallback((id: string, e?: React.MouseEvent) => {
    if (e) e.preventDefault();
    const el = document.getElementById(id);
    if (!el) return;

    // If this id is marked for top alignment, scroll so it appears at the top
    if (TOP_ALIGN.has(id)) {
      el.scrollIntoView({ behavior: 'smooth', block: 'start' });
      return;
    }

    // Otherwise calculate scroll position so the element ends up centered in the viewport
    const rect = el.getBoundingClientRect();
    const elCenterY = window.scrollY + rect.top + rect.height / 2;
    const scrollToY = Math.max(0, elCenterY - window.innerHeight / 2);

    window.scrollTo({ top: scrollToY, behavior: 'smooth' });
  }, []);

  return (
    <motion.nav
      initial={{ y: -100 }}
      animate={{ y: 0 }}
      className="sticky top-0 z-50 flex items-center justify-between px-6 py-4 bg-white/80 backdrop-blur-md border-b border-border"
    >
      <div className="flex items-center gap-2">
        <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center text-white font-bold">
          e
        </div>
        <span className="text-xl font-bold tracking-tight">erm.ai</span>
      </div>

      <div className="hidden md:flex items-center gap-8 text-sm font-medium text-gray-600">
        <a href="#start-slack" onClick={(e) => scrollTo('start-slack', e)} className="hover:text-foreground transition-colors">Start a Slack</a>
        <a href="#our-agents" onClick={(e) => scrollTo('our-agents', e)} className="hover:text-foreground transition-colors">Our Agents</a>
        <a href="#features" onClick={(e) => scrollTo('features', e)} className="hover:text-foreground transition-colors">Features</a>
        <a href="#visulisation" onClick={(e) => scrollTo('visulisation', e)} className="hover:text-foreground transition-colors">Visulisation</a>
        <a href="#example" onClick={(e) => scrollTo('example', e)} className="hover:text-foreground transition-colors">How does it look?</a>
      </div>
    </motion.nav >
  );
}
