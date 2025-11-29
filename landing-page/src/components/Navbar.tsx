'use client';

import Link from 'next/link';
import { motion } from 'framer-motion';

export default function Navbar() {
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
        <Link href="#" className="hover:text-foreground transition-colors">Product</Link>
        <Link href="#" className="hover:text-foreground transition-colors">Solutions</Link>
        <Link href="#" className="hover:text-foreground transition-colors">Resources</Link>
        <Link href="#" className="hover:text-foreground transition-colors">Pricing</Link>
      </div>

      <div className="flex items-center gap-4">
        <Link href="#" className="hidden md:block text-sm font-medium hover:text-primary transition-colors">
          Log in
        </Link>
        <button className="bg-foreground text-white px-4 py-2 rounded-full text-sm font-medium hover:bg-gray-800 transition-colors">
          Get Started
        </button>
      </div>
    </motion.nav >
  );
}
