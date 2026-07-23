"use client";

import { useRef } from "react";
import Image from "next/image";
import { motion, useScroll, useTransform } from "framer-motion";
import { ArrowDown } from "lucide-react";

const line = {
  hidden: { y: "110%" },
  show: (i: number) => ({
    y: "0%",
    transition: { duration: 1.1, delay: 0.35 + i * 0.14, ease: [0.22, 1, 0.36, 1] as const },
  }),
};

export default function Hero() {
  const ref = useRef<HTMLElement>(null);
  const { scrollYProgress } = useScroll({
    target: ref,
    offset: ["start start", "end start"],
  });
  const imgY = useTransform(scrollYProgress, [0, 1], ["0%", "22%"]);
  const imgScale = useTransform(scrollYProgress, [0, 1], [1.05, 1.22]);
  const fade = useTransform(scrollYProgress, [0, 0.7], [1, 0]);

  return (
    <section ref={ref} className="relative h-[100svh] overflow-hidden">
      <motion.div style={{ y: imgY, scale: imgScale }} className="absolute inset-0">
        <Image
          src="https://images.unsplash.com/photo-1613490493576-7fde63acd811?q=80&w=2400&auto=format&fit=crop"
          alt="Zaw G signature villa at dusk"
          fill
          priority
          className="object-cover"
        />
        <div className="absolute inset-0 bg-gradient-to-b from-ink/60 via-ink/25 to-ink" />
      </motion.div>

      <motion.div
        style={{ opacity: fade }}
        className="relative z-10 mx-auto flex h-full max-w-7xl flex-col justify-end px-6 pb-24 lg:px-10"
      >
        <motion.p
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.25 }}
          className="mb-6 text-[11px] uppercase tracking-[0.4em] text-bronze"
        >
          Mandalay · Design–Build Studio · Est. 2014
        </motion.p>

        <h1 className="font-display text-[13.5vw] leading-[0.95] font-medium tracking-tight sm:text-[11vw] lg:text-[8.5rem]">
          <span className="block overflow-hidden pb-1">
            <motion.span className="block" variants={line} initial="hidden" animate="show" custom={0}>
              We don&rsquo;t build
            </motion.span>
          </span>
          <span className="block overflow-hidden pb-2">
            <motion.span className="block" variants={line} initial="hidden" animate="show" custom={1}>
              houses. <em className="text-bronze not-italic font-semibold">We build</em>
            </motion.span>
          </span>
          <span className="block overflow-hidden pb-2">
            <motion.span className="block" variants={line} initial="hidden" animate="show" custom={2}>
              <span className="text-stroke font-semibold">legacy.</span>
            </motion.span>
          </span>
        </h1>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.9, delay: 1.15 }}
          className="mt-10 flex flex-wrap items-center gap-x-10 gap-y-4 text-xs uppercase tracking-[0.25em] text-mute"
        >
          <span><strong className="mr-2 font-display text-xl normal-case tracking-normal text-bone">50+</strong>Structures</span>
          <span className="h-4 w-px bg-line" />
          <span><strong className="mr-2 font-display text-xl normal-case tracking-normal text-bone">12</strong>Years of Craft</span>
          <span className="h-4 w-px bg-line" />
          <span><strong className="mr-2 font-display text-xl normal-case tracking-normal text-bone">7</strong>Live Sites</span>
          <span className="ml-auto hidden items-center gap-3 sm:flex">
            Scroll <ArrowDown className="h-4 w-4 animate-bounce text-bronze" />
          </span>
        </motion.div>
      </motion.div>
    </section>
  );
}
