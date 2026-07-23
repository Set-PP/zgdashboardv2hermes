"use client";

import { useRef } from "react";
import Image from "next/image";
import { motion, useScroll, useTransform } from "framer-motion";
import { DraftingCompass, HardHat, KeyRound } from "lucide-react";
import Reveal from "@/components/Reveal";

const PILLARS = [
  { icon: DraftingCompass, title: "Design-First", text: "Every structure begins as architecture — in-house architects and engineers under one roof." },
  { icon: HardHat, title: "Engineering-Grade", text: "Earthquake-aware structural design, total-station QC, cube-tested concrete. No shortcuts, ever." },
  { icon: KeyRound, title: "True Turnkey", text: "From empty plot to keys in hand. One contract, one team, one accountable partner." },
];

export default function Studio() {
  const ref = useRef<HTMLElement>(null);
  const { scrollYProgress } = useScroll({ target: ref, offset: ["start end", "end start"] });
  const y = useTransform(scrollYProgress, [0, 1], ["-8%", "8%"]);

  return (
    <section id="studio" ref={ref} className="relative overflow-hidden border-y border-line bg-ink-2">
      <div className="mx-auto grid max-w-7xl grid-cols-1 gap-14 px-6 py-28 lg:grid-cols-2 lg:px-10 lg:py-36">
        <div className="relative order-2 lg:order-1">
          <motion.div style={{ y }} className="relative aspect-[4/5] overflow-hidden rounded-2xl">
            <Image
              src="https://images.unsplash.com/photo-1600607687920-4e2a09cf159d?q=80&w=1400&auto=format&fit=crop"
              alt="Zaw G interior craftsmanship"
              fill
              sizes="(max-width:1024px) 100vw, 50vw"
              className="object-cover"
            />
          </motion.div>
          <Reveal delay={0.25} className="absolute -bottom-8 -right-4 sm:right-8">
            <div className="rounded-2xl border border-line bg-ink/90 px-7 py-6 backdrop-blur-xl">
              <span className="font-display text-5xl font-medium text-bronze">50+</span>
              <p className="mt-1 text-[10px] uppercase tracking-[0.3em] text-mute">Structures &amp; counting</p>
            </div>
          </Reveal>
        </div>

        <div className="order-1 lg:order-2">
          <Reveal>
            <div className="mb-4 flex items-center gap-4">
              <span className="h-px w-12 bg-bronze" />
              <span className="text-[11px] uppercase tracking-[0.35em] text-bronze">The Studio</span>
            </div>
            <h2 className="font-display text-4xl font-medium leading-[1.08] sm:text-5xl">
              A construction company with an
              <em className="text-bronze"> architect&rsquo;s soul.</em>
            </h2>
            <p className="mt-6 max-w-lg text-sm leading-relaxed text-mute">
              Founded by a civil engineer who designs, Zaw G treats every plot like a
              legacy project — whether a family villa in Mandalay or a steel factory
              in Myitnge. Design, structure, and craft are never separated.
            </p>
          </Reveal>

          <div className="mt-12 space-y-8">
            {PILLARS.map((p, i) => (
              <Reveal key={p.title} delay={0.15 + i * 0.12}>
                <div className="group flex gap-5">
                  <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl border border-line bg-ink-3 text-bronze transition-all duration-300 group-hover:border-bronze group-hover:bg-bronze group-hover:text-ink">
                    <p.icon className="h-5 w-5" />
                  </span>
                  <div>
                    <h3 className="font-display text-xl font-medium">{p.title}</h3>
                    <p className="mt-1.5 max-w-md text-sm leading-relaxed text-mute">{p.text}</p>
                  </div>
                </div>
              </Reveal>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
