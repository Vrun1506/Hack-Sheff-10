'use client';

import { motion } from 'framer-motion';
import { Zap, Layout, Share2, Shield, Smartphone, Globe } from 'lucide-react';

const features = [
    {
        title: "Instant Automations",
        description: "Connect over 5,000 apps with a single click.",
        icon: Zap,
        colSpan: "md:col-span-2",
        bg: "bg-orange-50"
    },
    {
        title: "Flexible Layouts",
        description: "Drag and drop to create your perfect workspace.",
        icon: Layout,
        colSpan: "md:col-span-1",
        bg: "bg-blue-50"
    },
    {
        title: "Team Collaboration",
        description: "Work together in real-time, anywhere.",
        icon: Share2,
        colSpan: "md:col-span-1",
        bg: "bg-green-50"
    },
    {
        title: "Enterprise Security",
        description: "Bank-grade encryption for your data.",
        icon: Shield,
        colSpan: "md:col-span-2",
        bg: "bg-purple-50"
    },
    {
        title: "Mobile Ready",
        description: "Access your work from any device.",
        icon: Smartphone,
        colSpan: "md:col-span-1",
        bg: "bg-pink-50"
    },
    {
        title: "Global CDN",
        description: "Lightning fast performance worldwide.",
        icon: Globe,
        colSpan: "md:col-span-2",
        bg: "bg-yellow-50"
    }
];

export default function FeatureGrid() {
    return (
        <section className="px-6 py-24 bg-white">
            <div className="max-w-6xl mx-auto">
                <div className="mb-16 text-center max-w-2xl mx-auto">
                    <h2 className="text-3xl md:text-4xl font-bold mb-4">Everything you need to run your business</h2>
                    <p className="text-lg text-gray-600">Powerful features wrapped in a simple interface.</p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {features.map((feature, index) => (
                        <motion.div
                            key={index}
                            initial={{ opacity: 0, y: 20 }}
                            whileInView={{ opacity: 1, y: 0 }}
                            viewport={{ once: true }}
                            transition={{ delay: index * 0.1 }}
                            className={`${feature.colSpan} p-8 rounded-3xl border border-gray-100 hover:shadow-lg transition-shadow ${feature.bg}`}
                        >
                            <div className="w-12 h-12 bg-white rounded-xl flex items-center justify-center mb-6 shadow-sm">
                                <feature.icon className="w-6 h-6 text-foreground" />
                            </div>
                            <h3 className="text-xl font-bold mb-2">{feature.title}</h3>
                            <p className="text-gray-600 leading-relaxed">{feature.description}</p>
                        </motion.div>
                    ))}
                </div>
            </div>
        </section>
    );
}
