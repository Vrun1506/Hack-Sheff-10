export default function TrustedBy() {
    return (
        <section className="py-12 border-y border-gray-100 bg-white/50">
            <div className="max-w-6xl mx-auto px-6 text-center">
                <p className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-8">Trusted by innovative teams at</p>
                <div className="flex flex-wrap justify-center items-center gap-12 opacity-50 grayscale hover:grayscale-0 transition-all duration-500">
                    {/* Placeholder logos using text for now, in a real app these would be SVGs */}
                    <span className="text-xl font-bold">ACME Corp</span>
                    <span className="text-xl font-bold">GlobalBank</span>
                    <span className="text-xl font-bold">Nebula</span>
                    <span className="text-xl font-bold">FoxRun</span>
                    <span className="text-xl font-bold">Circle</span>
                </div>
            </div>
        </section>
    );
}
