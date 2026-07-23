"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { ArrowUpRight, Globe, PlayCircle, Rss } from "lucide-react";
import { fetchFeed, type FeedPost } from "@/lib/api";
import Reveal from "@/components/Reveal";
import { cn } from "@/lib/utils";

function relDate(iso: string): string {
  const d = new Date(iso + "T00:00:00");
  const days = Math.floor((Date.now() - d.getTime()) / 86400000);
  if (days <= 0) return "Today";
  if (days === 1) return "Yesterday";
  if (days < 7) return `${days} days ago`;
  return d.toLocaleDateString("en-GB", { day: "numeric", month: "short" });
}

function Card({ p, i, hero = false }: { p: FeedPost; i: number; hero?: boolean }) {
  return (
    <motion.a
      href={p.link}
      target="_blank"
      rel="noreferrer"
      initial={{ opacity: 0, y: 36 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-60px" }}
      transition={{ duration: 0.65, delay: i * 0.06, ease: [0.22, 1, 0.36, 1] }}
      className={cn("group relative cursor-pointer", hero && "sm:col-span-2")}
    >
      <div className={cn(
        "relative overflow-hidden rounded-2xl bg-panel",
        hero ? "aspect-[16/9] sm:aspect-[2/1]" : "aspect-[4/3]"
      )}>
        {p.image ? (
          <img
            src={p.image}
            alt=""
            loading="lazy"
            className="absolute inset-0 h-full w-full object-cover transition-transform duration-[1200ms] ease-[cubic-bezier(0.22,1,0.36,1)] group-hover:scale-[1.06]"
          />
        ) : (
          <div className="absolute inset-0 flex items-center justify-center bg-gradient-to-br from-ink-3 to-panel">
            <Globe className="h-10 w-10 text-bronze/40" />
          </div>
        )}
        <div className="absolute inset-0 bg-gradient-to-t from-ink/90 via-ink/15 to-transparent opacity-90 transition-opacity duration-500 group-hover:opacity-100" />

        {/* date badge */}
        <span className="absolute left-4 top-4 rounded-full border border-bone/20 bg-ink/55 px-3 py-1 text-[10px] uppercase tracking-[0.18em] text-bone/90 backdrop-blur-md">
          {relDate(p.date)}
        </span>

        {/* media chip */}
        {p.media === "video" && (
          <span className="absolute right-4 top-4 flex items-center gap-1.5 rounded-full bg-ink/55 px-3 py-1 text-[10px] uppercase tracking-[0.18em] text-bronze backdrop-blur-md">
            <PlayCircle className="h-3.5 w-3.5" /> Video
          </span>
        )}

        {/* caption */}
        <div className="absolute inset-x-5 bottom-5 flex items-end justify-between gap-3">
          <p className={cn(
            "min-w-0 font-medium leading-snug text-bone",
            hero ? "line-clamp-3 text-base sm:text-lg" : "line-clamp-2 text-sm"
          )}>
            {p.text || "(photo / video post)"}
          </p>
          <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full border border-bone/25 bg-ink/40 opacity-0 backdrop-blur-md transition-all duration-500 group-hover:rotate-45 group-hover:border-bronze group-hover:bg-bronze group-hover:text-ink group-hover:opacity-100">
            <ArrowUpRight className="h-4 w-4" />
          </span>
        </div>
      </div>
    </motion.a>
  );
}

export default function Updates() {
  const [posts, setPosts] = useState<FeedPost[]>([]);

  useEffect(() => {
    fetchFeed().then((d) => setPosts(Array.isArray(d) ? d.slice(0, 10) : [])).catch(() => {});
  }, []);

  if (posts.length === 0) return null;

  // photo posts first for a visual grid; hero = latest with an image
  const visual = [...posts].sort((a, b) => Number(!!b.image) - Number(!!a.image));
  const [hero, ...rest] = visual;

  return (
    <section id="updates" className="mx-auto max-w-7xl px-6 py-24 lg:px-10">
      <Reveal>
        <div className="mb-4 flex items-center gap-4">
          <span className="h-px w-12 bg-bronze" />
          <span className="flex items-center gap-2 text-[11px] uppercase tracking-[0.35em] text-bronze">
            <Rss className="h-3.5 w-3.5" /> Latest Updates
          </span>
        </div>
        <div className="flex flex-wrap items-end justify-between gap-6">
          <h2 className="font-display max-w-xl text-4xl font-medium leading-[1.05] sm:text-5xl">
            Daily activity,
            <em className="text-bronze"> straight from the page.</em>
          </h2>
          <a
            href="https://www.facebook.com/310908306475419"
            target="_blank"
            rel="noreferrer"
            className={cn(
              "group flex items-center gap-2 rounded-full border border-line px-5 py-2.5",
              "text-[11px] uppercase tracking-[0.2em] text-mute transition-all duration-300",
              "hover:border-bronze hover:bg-bronze hover:text-ink"
            )}
          >
            <Globe className="h-4 w-4" />
            Follow on Facebook
          </a>
        </div>
      </Reveal>

      <div className="mt-12 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
        <Card p={hero} i={0} hero />
        {rest.map((p, i) => (
          <Card key={p.id} p={p} i={i + 1} />
        ))}
      </div>
    </section>
  );
}
