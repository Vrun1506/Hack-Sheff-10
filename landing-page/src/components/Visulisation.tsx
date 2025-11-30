'use client';


export default function Visulisation() {
    return (
        <>
            <section id="visulisation" className="bg-white border-t border-gray-100 pt-16 pb-8">
                <div className="max-w-6xl mx-auto px-6 text-center">
                    <h2 className="text-3xl font-bold mb-6">Grafana Dashboard</h2>
                    <p className="text-lg text-gray-600 mb-8">View system metrics and dashboards in Grafana.</p>
                    <a
                        href="https://christopherwilliams0112.grafana.net/public-dashboards/87c77f0e55a94a0f973774ccb8c2d684" // TODO: replace with your Grafana URL
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-block px-6 py-3 bg-foreground text-white rounded-full font-semibold text-lg hover:bg-gray-800 transition-all"
                    >
                        Open Grafana
                    </a>
                </div>
            </section>

        </>
    );
}
