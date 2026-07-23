"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { AnimatePresence, motion } from "framer-motion";
import {
  ArrowLeft, AlertTriangle, Camera, CheckCircle2, Circle, CloudSun, Loader2,
  MapPin, MessageSquareText, Package, Radio, Sparkles, TrendingUp, User, Users, X,
} from "lucide-react";
import {
  ApiSite, ApiReport, SiteDay, fetchDays, fetchReports, fetchSites,
  fmtDay, fmtWhen, media,
} from "@/lib/api";
import { opsFor, SiteOps, OPS_DEFAULT } from "@/lib/data";
import { cn } from "@/lib/utils";

const active = (s: ApiSite) =>
  s.last_photo ? Date.now() - new Date(s.last_photo).getTime() < 3 * 864e5 : false;

/* ── lightbox ─────────────────────────────────────────────── */
function Lightbox({ src, onClose }: { src: string | null; onClose: () => void }) {
  return (
    <AnimatePresence>
      {src && (
        <motion.div
          initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
          className="fixed inset-0 z-[80] flex items-center justify-center bg-ink/90 p-6 backdrop-blur-sm"
          onClick={onClose}
        >
          <motion.img
            initial={{ scale: 0.92 }} animate={{ scale: 1 }} src={src} alt=""
            className="max-h-[88vh] max-w-full rounded-xl border border-bone/20 object-contain shadow-2xl"
          />
          <button className="absolute right-6 top-6 rounded-full border border-bone/30 bg-ink/60 p-2 text-bone">
            <X className="h-5 w-5" />
          </button>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

/* ── site detail ──────────────────────────────────────────── */
function SiteDetail({ site, onZoom }: { site: ApiSite; onZoom: (s: string) => void }) {
  const [reports, setReports] = useState<ApiReport[]>([]);
  const [days, setDays] = useState<SiteDay[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAll, setShowAll] = useState(false);
  const ops = { ...OPS_DEFAULT, ...opsFor(site.id || "") } as SiteOps;

  useEffect(() => {
    let dead = false;
    setLoading(true);
    setShowAll(false);
    Promise.all([fetchReports(site.id, 12), fetchDays(site.id)])
      .then(([r, d]) => { if (!dead) { setReports(r); setDays(d); } })
      .finally(() => !dead && setLoading(false));
    return () => { dead = true; };
  }, [site.id]);

  const toggleFilter = (all: boolean) => {
    setShowAll(all);
    fetchDays(site.id, all).then(setDays);
  };

  const keptPhotos = days.reduce((n, d) => n + d.photos.length, 0);
  const maxMan = Math.max(...ops.manpower);

  return (
    <motion.div
      key={site.id}
      initial={{ opacity: 0, y: 24 }} animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45, ease: [0.16, 1, 0.3, 1] }}
      className="space-y-6"
    >
      {/* banner */}
      <div className="relative h-52 overflow-hidden rounded-2xl border border-bone/10 bg-panel">
        {site.cover_url && (
          <img src={media(site.cover_url)} alt={site.name} className="h-full w-full object-cover" />
        )}
        <div className="absolute inset-0 bg-gradient-to-t from-ink via-ink/40 to-transparent" />
        <div className="absolute inset-x-6 bottom-5 flex flex-wrap items-end justify-between gap-3">
          <div>
            <p className="text-[11px] uppercase tracking-[0.25em] text-bronze">{site.code || "ZG Project"}</p>
            <h2 className="mt-1 font-display text-3xl">{site.name}</h2>
            <p className="mt-1 flex items-center gap-1.5 text-xs text-bone/70">
              <MapPin className="h-3.5 w-3.5" /> {site.title}
            </p>
          </div>
          <span className={cn(
            "flex items-center gap-2 rounded-full border px-4 py-2 text-xs",
            active(site) ? "border-emerald-400/40 bg-emerald-400/10 text-emerald-300" : "border-bone/20 bg-panel text-mute"
          )}>
            <span className={cn("h-2 w-2 rounded-full", active(site) ? "bg-emerald-400" : "bg-mute")} />
            {active(site) ? "Reporting active" : "Quiet"}
          </span>
        </div>
      </div>

      {/* real stats */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {[
          { label: "Reports (7d)", value: site.report_count, icon: MessageSquareText },
          { label: "Photos in", value: site.photo_count, icon: Camera },
          { label: "AI-curated", value: keptPhotos, icon: Sparkles, gold: true },
          { label: "Last photo", value: site.last_photo ? fmtWhen(site.last_photo).date : "—", icon: Radio },
        ].map((s) => (
          <div key={s.label} className="rounded-xl border border-bone/10 bg-panel p-4">
            <s.icon className={cn("h-4 w-4", s.gold ? "text-bronze" : "text-mute")} />
            <p className="mt-2 font-display text-2xl text-bone">{s.value}</p>
            <p className="text-[10px] uppercase tracking-wider text-mute">{s.label}</p>
          </div>
        ))}
      </div>

      {/* overall progress + manpower */}
      <div className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-xl border border-bone/10 bg-panel p-6">
          <div className="flex items-center justify-between">
            <p className="text-[11px] uppercase tracking-[0.25em] text-mute">Overall Progress</p>
            <span className="flex items-center gap-1.5 rounded-full bg-emerald-400/10 px-3 py-1 text-[11px] text-emerald-300">
              <TrendingUp className="h-3.5 w-3.5" /> +{ops.delta}% this week
            </span>
          </div>
          <div className="mt-4 flex items-end gap-3">
            <p className="font-display text-5xl text-bone">{ops.progress}<span className="text-2xl text-bronze">%</span></p>
            <p className="pb-1.5 text-sm text-mute">{ops.stage}</p>
          </div>
          <div className="mt-4 h-2.5 overflow-hidden rounded-full bg-ink">
            <motion.div
              initial={{ width: 0 }} animate={{ width: `${ops.progress}%` }}
              transition={{ duration: 1, ease: [0.22, 1, 0.36, 1], delay: 0.2 }}
              className="h-full rounded-full bg-gradient-to-r from-bronze to-bronze-2"
            />
          </div>
          <div className="mt-4 flex flex-wrap gap-x-5 gap-y-1.5 text-xs text-mute">
            <span className="flex items-center gap-1.5"><Users className="h-3.5 w-3.5 text-bronze" /> {ops.workers} workers today</span>
            <span className="flex items-center gap-1.5"><CloudSun className="h-3.5 w-3.5 text-bronze" /> {ops.weather}</span>
          </div>
        </div>

        <div className="rounded-xl border border-bone/10 bg-panel p-6">
          <p className="text-[11px] uppercase tracking-[0.25em] text-mute">Manpower · Last 7 Days</p>
          <div className="mt-5 flex h-28 items-end gap-2">
            {ops.manpower.map((n, i) => (
              <div key={i} className="flex flex-1 flex-col items-center gap-1.5">
                <span className="text-[10px] text-mute">{n}</span>
                <motion.div
                  initial={{ height: 0 }} animate={{ height: `${(n / maxMan) * 100}%` }}
                  transition={{ duration: 0.6, delay: 0.3 + i * 0.07 }}
                  className={cn("w-full rounded-t-md", i === ops.manpower.length - 1 ? "bg-bronze" : "bg-bronze/30")}
                />
                <span className="text-[9px] uppercase text-mute/60">
                  {["M", "T", "W", "T", "F", "S", "S"][i]}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* major + minor progress */}
      <div className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-xl border border-bone/10 bg-panel p-6">
          <p className="text-[11px] uppercase tracking-[0.25em] text-mute">Major Milestones</p>
          <div className="mt-4 space-y-2.5">
            {ops.major.map((m, i) => (
              <motion.div
                key={m.label}
                initial={{ opacity: 0, x: -12 }} animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.3 + i * 0.07 }}
                className="flex items-center gap-3 text-sm"
              >
                {m.done
                  ? <CheckCircle2 className="h-4.5 w-4.5 shrink-0 text-bronze" />
                  : <Circle className="h-4.5 w-4.5 shrink-0 text-mute/40" />}
                <span className={m.done ? "text-bone/85" : "text-mute"}>{m.label}</span>
                {m.done && <span className="ml-auto text-[10px] uppercase tracking-wider text-bronze">Done</span>}
              </motion.div>
            ))}
          </div>
        </div>

        <div className="rounded-xl border border-bone/10 bg-panel p-6">
          <p className="text-[11px] uppercase tracking-[0.25em] text-mute">Minor Works</p>
          <div className="mt-4 space-y-4">
            {ops.minor.map((m, i) => (
              <div key={m.label}>
                <div className="mb-1.5 flex items-center justify-between text-xs">
                  <span className="text-bone/85">{m.label}</span>
                  <span className="font-display text-bronze">{m.pct}%</span>
                </div>
                <div className="h-1.5 overflow-hidden rounded-full bg-ink">
                  <motion.div
                    initial={{ width: 0 }} animate={{ width: `${m.pct}%` }}
                    transition={{ duration: 0.8, delay: 0.4 + i * 0.1 }}
                    className="h-full rounded-full bg-bronze/70"
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* materials + issues */}
      {(ops.materials.length > 0 || ops.issues.length > 0) && (
        <div className="grid gap-6 lg:grid-cols-2">
          {ops.materials.length > 0 && (
            <div className="rounded-xl border border-bone/10 bg-panel p-6">
              <p className="flex items-center gap-2 text-[11px] uppercase tracking-[0.25em] text-mute">
                <Package className="h-4 w-4 text-bronze" /> Materials on Site
              </p>
              <div className="mt-3.5 flex flex-wrap gap-2">
                {ops.materials.map((m) => (
                  <span key={m} className="rounded-full border border-bone/15 bg-panel2 px-3 py-1.5 text-xs text-bone/80">{m}</span>
                ))}
              </div>
            </div>
          )}
          {ops.issues.length > 0 && (
            <div className="rounded-xl border border-amber-400/25 bg-amber-400/5 p-6">
              <p className="flex items-center gap-2 text-[11px] uppercase tracking-[0.25em] text-amber-300">
                <AlertTriangle className="h-4 w-4" /> Issues & Risks
              </p>
              <ul className="mt-3.5 space-y-2 text-sm text-bone/85">
                {ops.issues.map((i) => <li key={i} className="flex gap-2"><span className="text-amber-300">•</span>{i}</li>)}
              </ul>
            </div>
          )}
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center gap-3 rounded-xl border border-bone/10 bg-panel p-10 text-mute">
          <Loader2 className="h-5 w-5 animate-spin text-bronze" /> Pulling Telegram data…
        </div>
      ) : (
        <>
          {/* curated photo journal */}
          <div className="rounded-xl border border-bone/10 bg-panel p-6">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <p className="flex items-center gap-2 text-[11px] uppercase tracking-[0.25em] text-mute">
                <Sparkles className="h-4 w-4 text-bronze" /> Site Photos
              </p>
              <div className="flex rounded-full border border-bone/15 p-0.5 text-[10px] uppercase tracking-wider">
                {([["Curated ✦", false], ["All photos", true]] as const).map(([label, all]) => (
                  <button
                    key={label}
                    onClick={() => toggleFilter(all)}
                    className={cn(
                      "rounded-full px-3.5 py-1.5 transition-all",
                      showAll === all ? "bg-bronze text-ink" : "text-mute hover:text-bone"
                    )}
                  >
                    {label}
                  </button>
                ))}
              </div>
            </div>
            {days.length === 0 ? (
              <p className="mt-6 text-sm text-mute">No photos passed the quality gate yet.</p>
            ) : (
              <div className="mt-5 space-y-6">
                {days.map((d) => (
                  <div key={d.date}>
                    <p className="mb-2.5 text-xs font-semibold text-bone/80">{fmtDay(d.date)}</p>
                    <div className="grid grid-cols-3 gap-2 sm:grid-cols-4 lg:grid-cols-5">
                      {d.photos.map((p, i) => (
                        <button
                          key={p.url + i}
                          onClick={() => onZoom(media(p.url))}
                          className="group relative aspect-[4/3] overflow-hidden rounded-lg border border-bone/10"
                        >
                          <img
                            src={media(p.url)} alt="" loading="lazy"
                            className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-110"
                          />
                          <span className="absolute bottom-1 right-1 rounded bg-ink/80 px-1.5 py-0.5 font-display text-[10px] text-bronze">
                            {p.score}
                          </span>
                        </button>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* engineer reports */}
          <div className="rounded-xl border border-bone/10 bg-panel p-6">
            <p className="flex items-center gap-2 text-[11px] uppercase tracking-[0.25em] text-mute">
              <MessageSquareText className="h-4 w-4 text-bronze" /> Engineer Reports · Telegram
            </p>
            <div className="mt-5 space-y-3">
              {reports.filter((r) => r.text.trim()).slice(0, 8).map((r) => (
                <div key={r.id} className="rounded-xl border border-bone/10 bg-panel2 p-4">
                  <div className="flex items-center gap-2 text-[11px] text-mute">
                    <span className="flex h-6 w-6 items-center justify-center rounded-full bg-bronze/15 text-bronze">
                      <User className="h-3.5 w-3.5" />
                    </span>
                    <span className="font-semibold text-bone/80">{r.sender}</span>
                    <span className="ml-auto">{fmtWhen(r.date).full}</span>
                  </div>
                  <p className="mt-2 text-sm leading-relaxed text-bone/90">{r.text}</p>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </motion.div>
  );
}

/* ── page ─────────────────────────────────────────────────── */
export default function LiveSiteDashboard() {
  const [sites, setSites] = useState<ApiSite[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [zoom, setZoom] = useState<string | null>(null);

  useEffect(() => {
    fetchSites()
      .then((all) => {
        const live = all.filter((s) => s.photo_count > 0);
        setSites(live);
        setActiveId(live[0]?.id ?? null);
      })
      .catch((e) => setError(String(e)));
  }, []);

  const kpis = useMemo(() => {
    if (!sites) return null;
    return {
      sites: sites.length,
      active: sites.filter(active).length,
      reports: sites.reduce((n, s) => n + s.report_count, 0),
      photos: sites.reduce((n, s) => n + s.photo_count, 0),
      kept: sites.reduce((n, s) => n + s.keep_count, 0),
    };
  }, [sites]);

  const site = sites?.find((s) => s.id === activeId) ?? null;

  return (
    <div className="min-h-screen bg-ink text-bone">
      <Lightbox src={zoom} onClose={() => setZoom(null)} />

      <header className="sticky top-0 z-40 border-b border-bone/10 bg-ink/80 backdrop-blur-md">
        <div className="mx-auto flex max-w-[1600px] items-center gap-4 px-6 py-4">
          <Link href="/" className="flex items-center gap-2 text-mute transition-colors hover:text-bronze">
            <ArrowLeft className="h-4 w-4" /> <span className="text-sm">Portfolio</span>
          </Link>
          <div className="h-5 w-px bg-bone/15" />
          <p className="font-display text-lg">Zaw G <span className="text-bronze">Command Center</span></p>
          <div className="ml-auto flex items-center gap-2 text-[11px] uppercase tracking-wider text-mute">
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-bronze opacity-60" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-bronze" />
            </span>
            Telegram · Live
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-[1600px] space-y-6 px-6 py-8">
        {error && (
          <div className="rounded-xl border border-red-400/30 bg-red-400/10 p-6 text-sm text-red-300">
            Pipeline API unreachable ({error}). Start it: <code>python -m uvicorn api:app --port 8600</code>
          </div>
        )}
        {!sites && !error && (
          <div className="flex items-center justify-center gap-3 p-20 text-mute">
            <Loader2 className="h-6 w-6 animate-spin text-bronze" /> Connecting to pipeline…
          </div>
        )}

        {kpis && (
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-5">
            {[
              { l: "Live Sites", v: kpis.sites },
              { l: "Active (3d)", v: kpis.active },
              { l: "Reports (7d)", v: kpis.reports },
              { l: "Photos In", v: kpis.photos },
              { l: "AI-Curated", v: kpis.kept, gold: true },
            ].map((k) => (
              <div key={k.l} className="rounded-xl border border-bone/10 bg-panel p-5">
                <p className={cn("font-display text-3xl", k.gold && "text-bronze")}>{k.v}</p>
                <p className="mt-1 text-[10px] uppercase tracking-wider text-mute">{k.l}</p>
              </div>
            ))}
          </div>
        )}

        {sites && (
          <div className="grid gap-6 lg:grid-cols-[340px_1fr]">
            <div className="space-y-2">
              <p className="px-1 text-[11px] uppercase tracking-[0.25em] text-mute">All Sites · {sites.length}</p>
              <div className="space-y-2 lg:max-h-[calc(100vh-220px)] lg:overflow-y-auto lg:pr-1">
                {sites.map((s) => {
                  const isActive = s.id === activeId;
                  return (
                    <button
                      key={s.id}
                      onClick={() => setActiveId(s.id)}
                      className={cn(
                        "w-full rounded-xl border p-3 text-left transition-all",
                        isActive ? "border-bronze/50 bg-bronze/10" : "border-bone/10 bg-panel hover:border-bone/25"
                      )}
                    >
                      <div className="flex items-center gap-3">
                        <span className="relative h-11 w-11 shrink-0 overflow-hidden rounded-lg bg-panel2">
                          {s.cover_url && (
                            <img src={media(s.cover_url)} alt="" className="h-full w-full object-cover" />
                          )}
                        </span>
                        <div className="min-w-0 flex-1">
                          <div className="flex items-center gap-2">
                            <span className={cn("h-1.5 w-1.5 rounded-full", active(s) ? "bg-emerald-400" : "bg-mute/50")} />
                            <span className={cn("truncate text-sm", isActive ? "text-bone" : "text-bone/80")}>{s.name}</span>
                          </div>
                          <p className="mt-0.5 flex items-center gap-2 text-[10px] text-mute">
                            <span>{s.code}</span>
                            <span className="flex items-center gap-1"><Camera className="h-3 w-3" />{s.photo_count}</span>
                            <span className="flex items-center gap-1 text-bronze"><Sparkles className="h-3 w-3" />{s.keep_count}</span>
                          </p>
                        </div>
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>

            <div>
              {site && <SiteDetail site={site} onZoom={setZoom} />}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
