"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ArrowUpRight, Building2, Camera, FileText, KeyRound, Loader2, MapPin, ShieldCheck } from "lucide-react";
import { portalAuth, type PortalData } from "@/lib/api";
import { opsFor } from "@/lib/data";

/* ---------------- Access gate ---------------- */

function Gate({ onAuth }: { onAuth: (d: PortalData) => void }) {
  const [code, setCode] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  const submit = async () => {
    if (!code.trim() || busy) return;
    setBusy(true); setErr("");
    try { onAuth(await portalAuth(code.trim())); }
    catch { setErr("Invalid access code. Please check with Zaw G Design Studio."); }
    finally { setBusy(false); }
  };

  return (
    <main className="flex min-h-screen items-center justify-center bg-[#0b0908] px-5 text-[#f4efe8]">
      <motion.div initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.8 }}
        className="w-full max-w-md">
        <p className="text-[11px] uppercase tracking-[0.35em] text-[#c8963e]">Zaw G Design & Construction</p>
        <h1 className="mt-3 font-[Fraunces] text-4xl font-light">Client Portal</h1>
        <p className="mt-3 text-sm text-[#f4efe8]/50">
          Enter the private access code we sent you to follow your project's progress.
        </p>
        <div className="mt-8 flex items-center gap-3 rounded-full border border-white/15 bg-white/5 px-5 py-4 backdrop-blur focus-within:border-[#c8963e]/60">
          <KeyRound className="h-5 w-5 shrink-0 text-[#c8963e]" />
          <input
            value={code}
            onChange={(e) => setCode(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && submit()}
            placeholder="Your access code"
            className="w-full bg-transparent text-lg tracking-widest outline-none placeholder:text-[#f4efe8]/25"
          />
        </div>
        {err && <p className="mt-3 text-sm text-red-400">{err}</p>}
        <button onClick={submit} disabled={busy}
          className="mt-6 flex w-full items-center justify-center gap-2 rounded-full bg-[#c8963e] py-4 text-sm font-semibold uppercase tracking-[0.2em] text-[#0b0908] transition hover:bg-[#d9a84f] disabled:opacity-50">
          {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <ShieldCheck className="h-4 w-4" />}
          Enter my portal
        </button>
      </motion.div>
    </main>
  );
}

/* ---------------- Portal view ---------------- */

function Portal({ d }: { d: PortalData }) {
  const ops = opsFor(d.slug);
  const fmt = (iso?: string | null) =>
    iso ? new Date(iso).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" }) : "—";

  return (
    <main className="min-h-screen bg-[#0b0908] text-[#f4efe8]">
      {/* hero cover */}
      <section className="relative h-[62vh] min-h-[420px] w-full overflow-hidden">
        {d.cover && (
          <motion.img initial={{ scale: 1.12 }} animate={{ scale: 1 }} transition={{ duration: 2, ease: [0.16, 1, 0.3, 1] }}
            src={`http://127.0.0.1:8600${d.cover}`} alt={d.name}
            className="absolute inset-0 h-full w-full object-cover" />
        )}
        <div className="absolute inset-0 bg-gradient-to-t from-[#0b0908] via-[#0b0908]/30 to-transparent" />
        <div className="absolute inset-x-0 bottom-0 mx-auto max-w-6xl px-6 pb-12">
          <motion.div initial={{ opacity: 0, y: 40 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3, duration: 0.9 }}>
            <p className="text-[11px] uppercase tracking-[0.35em] text-[#c8963e]">
              {d.client_name ? `Prepared for ${d.client_name}` : "Client Progress Portal"}
            </p>
            <h1 className="mt-2 font-[Fraunces] text-5xl font-light md:text-6xl">{d.name}</h1>
            <p className="mt-2 flex items-center gap-2 text-sm text-[#f4efe8]/60">
              <MapPin className="h-4 w-4 text-[#c8963e]" /> {d.code}
              <span className={`ml-3 rounded-full px-3 py-1 text-[10px] uppercase tracking-widest ${d.active ? "bg-emerald-400/15 text-emerald-300" : "bg-white/10 text-white/50"}`}>
                {d.active ? "In progress" : "Completed"}
              </span>
            </p>
          </motion.div>
        </div>
      </section>

      {/* stats strip */}
      <section className="border-y border-white/10 bg-white/[0.03]">
        <div className="mx-auto grid max-w-6xl grid-cols-2 gap-6 px-6 py-8 sm:grid-cols-4">
          {[
            { icon: Camera, label: "Site photos", val: String(d.photo_count) },
            { icon: FileText, label: "Site reports", val: String(d.report_count) },
            { icon: Building2, label: "Work started", val: fmt(d.first_report) },
            { icon: ArrowUpRight, label: "Latest update", val: fmt(d.last_report) },
          ].map((s) => (
            <div key={s.label}>
              <s.icon className="h-5 w-5 text-[#c8963e]" />
              <p className="mt-2 font-[Fraunces] text-2xl">{s.val}</p>
              <p className="mt-1 text-[10px] uppercase tracking-[0.25em] text-[#f4efe8]/40">{s.label}</p>
            </div>
          ))}
        </div>
      </section>

      <div className="mx-auto max-w-6xl px-6 py-14">
        {/* note from the studio */}
        {d.note && (
          <motion.blockquote initial={{ opacity: 0 }} whileInView={{ opacity: 1 }}
            className="mb-14 rounded-3xl border border-[#c8963e]/25 bg-[#c8963e]/[0.06] p-8 font-[Fraunces] text-xl font-light italic leading-relaxed text-[#f4efe8]/85">
            "{d.note}"
            <footer className="mt-4 text-xs not-italic uppercase tracking-[0.3em] text-[#c8963e]">— Zaw G Design Studio</footer>
          </motion.blockquote>
        )}

        {/* progress + milestones (ops overlay) */}
        {ops && (
          <section className="mb-14 grid gap-8 md:grid-cols-2">
            <div className="rounded-3xl border border-white/10 bg-white/[0.04] p-8">
              <p className="text-[10px] uppercase tracking-[0.3em] text-[#f4efe8]/40">Overall progress</p>
              <p className="mt-3 font-[Fraunces] text-6xl font-light text-[#c8963e]">{ops.progress}%</p>
              <div className="mt-5 h-2 overflow-hidden rounded-full bg-white/10">
                <motion.div initial={{ width: 0 }} whileInView={{ width: `${ops.progress}%` }}
                  transition={{ duration: 1.4, ease: "easeOut" }}
                  className="h-full rounded-full bg-gradient-to-r from-[#c8963e] to-[#e8c06a]" />
              </div>
              {ops.delta > 0 && (
                <p className="mt-3 text-xs text-emerald-300">+{ops.delta}% this week</p>
              )}
            </div>
            <div className="rounded-3xl border border-white/10 bg-white/[0.04] p-8">
              <p className="text-[10px] uppercase tracking-[0.3em] text-[#f4efe8]/40">Milestones</p>
              <ul className="mt-4 space-y-3">
                {ops.major.map((m) => (
                  <li key={m.label} className="flex items-center justify-between gap-4 text-sm">
                    <span className={m.done ? "text-[#f4efe8]/45 line-through" : ""}>{m.label}</span>
                    <span className={`rounded-full px-2.5 py-0.5 text-[10px] uppercase tracking-wider ${m.done ? "bg-emerald-400/15 text-emerald-300" : "bg-[#c8963e]/15 text-[#c8963e]"}`}>
                      {m.done ? "Done" : "Next"}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          </section>
        )}

        {/* photo journal */}
        <section>
          <div className="mb-8 flex items-end justify-between">
            <div>
              <p className="text-[11px] uppercase tracking-[0.35em] text-[#c8963e]">Photo journal</p>
              <h2 className="mt-2 font-[Fraunces] text-3xl font-light">Latest from your site</h2>
            </div>
            <p className="text-xs text-[#f4efe8]/35">AI-curated · best shots only</p>
          </div>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
            {d.photos.map((p, i) => (
              <motion.div key={p.img} initial={{ opacity: 0, y: 24 }} whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }} transition={{ delay: (i % 8) * 0.05, duration: 0.6 }}
                className="group relative aspect-[4/3] overflow-hidden rounded-2xl border border-white/10">
                <img src={`http://127.0.0.1:8600${p.img}`} alt="" loading="lazy"
                  className="h-full w-full object-cover transition duration-700 group-hover:scale-105" />
                <div className="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent opacity-0 transition group-hover:opacity-100" />
                <p className="absolute bottom-2 left-3 text-[10px] uppercase tracking-widest text-white/70 opacity-0 transition group-hover:opacity-100">
                  {fmt(p.date)}
                </p>
              </motion.div>
            ))}
          </div>
        </section>

        <footer className="mt-20 border-t border-white/10 pt-8 text-center text-xs text-[#f4efe8]/30">
          Zaw G Design & Construction · Private client portal · Questions? Message us anytime on Facebook.
        </footer>
      </div>
    </main>
  );
}

export default function PortalPage() {
  const [data, setData] = useState<PortalData | null>(null);
  return (
    <AnimatePresence mode="wait">
      {data ? <Portal key="p" d={data} /> : <Gate key="g" onAuth={setData} />}
    </AnimatePresence>
  );
}
