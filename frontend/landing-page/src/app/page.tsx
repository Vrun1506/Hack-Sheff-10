import Navbar from "@/components/Navbar";
import Hero from "@/components/Hero";
import FeatureGrid from "@/components/FeatureGrid";
import Visulisation from "@/components/Visulisation";
import Link from "next/link";

export default function Home() {
  return (
    <main className="min-h-screen bg-background">
      <Navbar />
      <Hero />
      <FeatureGrid />
       <Visulisation />
      <section id="example" className="py-24 bg-primary text-white text-center px-6">
        <div className="max-w-3xl mx-auto">
          <h2 className="text-3xl md:text-5xl font-bold mb-8">Ready to get started?</h2>
          <p className="text-xl mb-10 opacity-90">Achieve professional clarity, powered by many minds.</p>
          {/* Placeholder example output button */}
          <a
            href="https://youtu.be/owogrzfarmU" // TODO: replace with real example output link
            className="inline-block px-6 py-3 bg-white text-primary rounded-full font-semibold text-lg hover:opacity-90 transition-all mb-6"
          >
            View example output
          </a>

          {/* Quick value row */}
          <div className="mt-4 text-sm opacity-90">
            Fast &bull; Accurate &bull; Multi-Agent Smart
          </div>
        </div>
      </section>
       <footer className="bg-white">
                <div className="max-w-6xl mx-auto px-6">
                    <div className="flex flex-col md:flex-row justify-between items-center pt-8 border-t border-gray-100 text-sm text-gray-500">
                        <p>© 2025 erm.ai Inc. All rights reserved. (not actually tho)</p>
                        <div className="flex gap-6 mt-4 md:mt-0">
                            <Link
                                href="https://github.com/Vrun1506/Hack-Sheff-10"
                                target="_blank"
                                rel="noopener noreferrer"
                                className="hover:text-foreground"
                            >
                                GitHub
                            </Link>
                        </div>
                    </div>
                </div>
          </footer>
    </main>
  );
}
