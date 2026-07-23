"use client";

import { useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { ArrowUpRight, PenTool, CheckCircle2, Sparkles } from "lucide-react";
import { opsFor } from "@/lib/data";
import { fetchPortfolio, media, ApiSite, fetchSites, Portfolio } from "@/lib/api";
import Reveal from "@/components/Reveal";
import { cn } from "@/lib/utils";

const FILTERS = ["All", "Design", "Completed", "Ongoing"] as const;
type Cat = (typeof FILTERS)[number];

type CardData = {
  id: string;
  title: string;
  location: string;
  year: string;
  category: Exclude<Cat, "All">;
  image: string;
  progress?: number;
  score?: number;
  span?: boolean;
};

const BADGE: Record<CardData["category"], string> = {
  Design: "border-bronze/50 bg-ink/50 text-bronze",
  Completed: "border-bone/20 bg-ink/50 text-bone/80",
  Ongoing: "border-bronze bg-bronze text-ink",
};

function Card({ p, i }: { p: CardData; i: number }) {
  return (
    <motion.article
      layout
      initial={{ opacity: 0, y: 40 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.96 }}
      transition={{ duration: 0.65, delay: i * 0.05, ease: [0.22, 1, 0.36, 1] }}
      className={cn("group relative cursor-pointer", p.span && "sm:col-span-2")}
    >
      <div className={cn("relative overflow-hidden rounded-2xl bg-panel", p.span ? "aspect-[2/1]" : "aspect-[4/3]")}>

        {/* real photo from API / media URL or dummy gradient card if no image */}
        {p.image ? (
          <img src={p.image} alt={p.title} loading="lazy" className="absolute inset-0 h-full w-full object-cover transition-transform duration-[1200ms] ease-[cubic-bezier(0.22,1,0.36,1)] group-hover:scale-[1.06]" />
        ) : (
          <div className="absolute inset-0 flex items-center justify-center bg-gradient-to-br from-ink to-ink/95">
            <span className="text-mute text-xs uppercase tracking-widest">Photo pending</span>
          </div>
        )}
        <div className="absolute inset-0 bg-gradient-to-t from-ink/90 via-ink/10 to-transparent opacity-85 transition-opacity duration-500 group-hover:opacity-100" />

        {/* category badge */}
        <span className={cn("absolute left-4 top-4 flex items-center gap-1.5 rounded-full border px-3 py-1 text-[10px] uppercase tracking-[0.18em] backdrop-blur-md", BADGE[p.category])}>
          {p.category === "Design" && <PenTool className="h-3 w-3" />}
          {p.category === "Completed" && <CheckCircle2 className="h-3 w-3" />}
          {p.category === "Ongoing" && (<span className="relative flex h-2 w-2"><span className="absolute h-full w-full animate-ping rounded-full bg-ink/60" /><span className="relative h-2 w-2 rounded-full bg-ink" /></span>)}
          {p.category}
        </span>

        {/* AI score / progress */}
        {p.score != null && p.category === "Design" && (
          <span className="absolute right-4 top-4 flex items-center gap-1 rounded-full bg-ink/60 px-2.5 py-1 font-display text-[11px] text-bronze backdrop-blur-md">
            <Sparkles className="h-3 w-3" /> {p.score}
          </span>
        )}

        {/* ongoing progress bar */}
        {p.progress != null && (
          <div className="absolute right-4 top-4 flex items-center gap-2 rounded-full bg-ink/60 px-3 py-1.5 backdrop-blur-md">
            <div className="h-1 w-14 overflow-hidden rounded-full bg-bone/20">
              <motion.div initial={{ width: 0 }} whileInView={{ width: `${p.progress}%` }} viewport={{ once: true }} transition={{ duration: 1.2, delay: 0.4 }} className="h-full bg-bronze" />
            </div>
            <span className="text-[10px] font-medium text-bronze">{p.progress}%</span>
          </div>
        )}

        {/* title */}
        <div className="absolute inset-x-5 bottom-5 flex items-end justify-between gap-3">
          <div className="min-w-0">
            <span className="font-display text-sm italic text-bronze">{p.id} — {p.year}</span>
            <h3 className="font-display mt-1 truncate text-xl font-medium leading-tight sm:text-2xl" title={p.title}>{p.title}</h3>
            <p className="mt-1 truncate text-[10px] uppercase tracking-[0.25em] text-mute">{p.location}</p>
          </div>
          <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full border border-bone/25 bg-ink/40 opacity-0 backdrop-blur-md transition-all duration-500 group-hover:rotate-45 group-hover:border-bronze group-hover:bg-bronze group-hover:text-ink group-hover:opacity-100">
            <ArrowUpRight className="h-4 w-4" />
          </span>
        </div>

      </div>
    </motion.article>
  );
}

/** Build portfolio cards from our real API (design + finished + 22 ongoing sites). */
function cardsFromPortfolio(d: Portfolio) {
  const out: CardData[] = [];

  // Design renders
  d.design.forEach((x, i) => out.push({
    id: `D${String(i + 1).padStart(2, "0")}`, title: x.title || "Design Concept",
    location: x.subtitle || "", year: "2025", category: "Design",
    image: media(x.img), score: x.score,
  }));

  // Completed builds
  d.finished.forEach((x, i) => out.push({
    id: `C${String(i + 1).padStart(2, "0")}`, title: x.title || "Completed Build",
    location: x.subtitle ? (x.subtitle.slice(0, 4) || "Zaw G Build") : "Zaw G Build",
    year: x.subtitle ? (x.subtitle.slice(0, 4) || "2024") : "2024",
    category: "Completed", image: media(x.img), score: x.score,
  }));

  // Ongoing sites — now includes ALL 22 active sites from Telegram collector
  d.ongoing.forEach((x, i) => {
    const slug = x.slug || "";
    const ops = slug ? opsFor(slug) : undefined;
    const prog = ((x as any)._auto_progress ?? (typeof ops === "object" && ops !== null && 'progress' in ops ? ((ops as any).progress as number | undefined) : undefined));
    out.push({
      id: `O${String(i + 1).padStart(2, "0")}`, title: x.title || "Loading…", location: x.subtitle || "",
      year: "NOW", category: "Ongoing",
      image: x.img ? media(x.img) : "", score: x.score ?? undefined,
      progress: prog != null ? Math.min(Math.max(prog, 0), 100) : undefined,
    });
  });

  return out;
}

export default function Projects() {
  const [filter, setFilter] = useState<Cat>("All");
  const [cards, setCards] = useState<CardData[]>([]); // show nothing until API responds — avoids flash of dummies.
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    console.log('[Projects] useEffect firing, calling fetchPortfolio...');
    fetchPortfolio()
      .then((d) => {
        console.log('[Projects] fetchPortfolio SUCCESS:', d.design?.length, d.finished?.length, d.ongoing?.length);
        const cards = cardsFromPortfolio(d);
        console.log('[Projects] cardsFromPortfolio returned:', cards.length, 'cards');
        setCards(cards);
        setLoading(false);
      })
      .catch((e) => { console.error('Portfolio fetch failed:', e); setLoading(false); setCards([]); });
  }, []);

  const shown = cards.filter((p) => filter === "All" || p.category === filter);
  const count = (f: Cat) => (f === "All" ? cards.length : cards.filter((p) => p.category === f).length);

  return (
    <section id="works" className="mx-auto max-w-7xl px-6 py-28 lg:px-10 lg:py-36">
      <Reveal>
        <div className="mb-4 flex items-center gap-4">
          <span className="h-px w-12 bg-bronze" />
          <span className="text-[11px] uppercase tracking-[0.35em] text-bronze">Selected Works</span>
        </div>
        <div className="flex flex-wrap items-end justify-between gap-6">
          <h2 className="font-display max-w-2xl text-4xl font-medium leading-[1.05] sm:text-6xl">
            From first sketch
            <em className="text-bronze"> to final key.</em>
          </h2>
          <p className="max-w-xs text-sm leading-relaxed text-mute">
            {loading ? "Loading real data from all 22 active sites…" : `${count("Design")} designs · ${count("Completed")} completed · ${count("Ongoing")} on-site`}
          </p>
        </div>
      </Reveal>

      <Reveal delay={0.15} className="mt-10">
        <div className="flex flex-wrap gap-3">
          {FILTERS.map((f) => (
            <button key={f} onClick={() => setFilter(f)} className={cn("flex items-center gap-2 rounded-full border px-5 py-2 text-[11px] uppercase tracking-[0.2em] transition-all duration-300", filter === f ? "border-bronze bg-bronze text-ink" : "border-line text-mute hover:border-bone/30 hover:text-bone")}>
              {f}
              <span className={cn("rounded-full px-1.5 text-[10px]", filter === f ? "bg-ink/20" : "bg-ink-3")}>{count(f)}</span>
            </button>
          ))}
        </div>
      </Reveal>

      <motion.div layout className="mt-12 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
        <AnimatePresence mode="popLayout">
          {loading ? null : shown.map((p, i) => (
            <Card key={p.id + p.title} p={p} i={i} />
          ))}
          {/* placeholder skeletons during load */}
          {Array.from({ length: 6 }).map((_, i) => (
            <motion.div key={i} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: i * 0.1 }} className="rounded-2xl bg-panel aspect-[4/3] animate-pulse" />
          ))}
        </AnimatePresence>
      </motion.div>
    </section>
  );
}
