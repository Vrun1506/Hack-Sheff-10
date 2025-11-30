'use client';

import { motion } from 'framer-motion';
import { BookOpenCheck, BotMessageSquare, Users, Shield, MessagesSquare, Dumbbell } from 'lucide-react';

const features = [
    {
        title: "Multi Agent Collaboration",
        description: "Each message is refined by multiple specialized AI agents working together.",
        icon: Users,
        colSpan: "md:col-span-2",
        bg: "bg-green-50"
    },
    {
        title: "Professional Tone Transformation",
        description: "Automatically rewrite text into clear, concise, professional language.",
        icon: BookOpenCheck,
        colSpan: "md:col-span-1",
        bg: "bg-blue-50"
    },
    {
        title: "Real-Time Conversation Enhancement",
        description: "The AI assists live while you chat or draft.",
        icon: BotMessageSquare,
        colSpan: "md:col-span-1",
        bg: "bg-red-50"
    },
    {
        title: "Secure & Privacy-Focused",
        description: "Your data stays private and is never stored or shared.",
        icon: Shield,
        colSpan: "md:col-span-2",
        bg: "bg-purple-50"
    },
    {
        title: "Group Tools",
        description: "Designed as a group chat - both for multiple users and agents.",
        icon: MessagesSquare,
        colSpan: "md:col-span-2",
        bg: "bg-orange-50"
    },
    {
        title: "Adaptable to Your Needs",
        description: "A wide range of collboration styles and professional tones.",
        icon: Dumbbell,
        colSpan: "md:col-span-1",
        bg: "bg-yellow-50"
    }
];

export default function FeatureGrid() {
    return (
        <section id = "features" className="px-6 py-24 bg-white">
            <div className="max-w-6xl mx-auto">
                <div className="mb-16 text-center max-w-2xl mx-auto">
                    <h2 className="text-3xl md:text-4xl font-bold mb-4">Everything you need to communicate with confidence.</h2>
                    <p className="text-lg text-gray-600">Powerful features wrapped in a single place.</p>
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
