"use client";

import { useEffect, useRef, useState } from "react";
import { animate, useInView } from "framer-motion";
import Reveal from "@/components/Reveal";
import { fetchStats } from "@/lib/api";

const FALLBACK = [
  { value: 50, suffix: "+", label: "Structures Delivered" },
  { value: 22, suffix: "", label: "Sites Tracked Live" },
  { value: 574, suffix: "", label: "Engineer Reports" },
  { value: 300, suffix: "+", label: "Site Photos" },
];

function Counter({ value, suffix }: { value: number; suffix: string }) {
  const ref = useRef<HTMLSpanElement>(null);
  const inView = useInView(ref, { once: true, margin: "-60px" });

  useEffect(() => {
    if (!inView || !ref.current) return;
    const controls = animate(0, value, {
      duration: 2,
      ease: [0.22, 1, 0.36, 1],
      onUpdate: (v) => {
        if (ref.current) ref.current.textContent = Math.round(v).toString();
      },
    });
    return () => controls.stop();
  }, [inView, value]);

  return (
    <span className="font-display text-6xl font-medium text-bone sm:text-7xl">
      <span ref={ref}>0</span>
      <span className="text-bronze">{suffix}</span>
    </span>
  );
}

export default function Stats() {
  const [stats, setStats] = useState(FALLBACK);

  useEffect(() => {
    fetchStats()
      .then((s) =>
        setStats([
          { value: 50, suffix: "+", label: "Structures Delivered" },
          { value: s.sites_total, suffix: "", label: "Sites Tracked Live" },
          { value: s.reports, suffix: "", label: "Engineer Reports" },
          { value: s.photos, suffix: "+", label: "Site Photos" },
        ])
      )
      .catch(() => {});
  }, []);

  return (
    <section className="border-y border-line bg-ink-2">
      <div className="mx-auto grid max-w-7xl grid-cols-2 gap-y-14 px-6 py-20 lg:grid-cols-4 lg:px-10">
        {stats.map((s, i) => (
          <Reveal key={s.label} delay={i * 0.1} className="text-center">
            <Counter value={s.value} suffix={s.suffix} />
            <p className="mt-3 text-[11px] uppercase tracking-[0.3em] text-mute">{s.label}</p>
          </Reveal>
        ))}
      </div>
    </section>
  );
}
