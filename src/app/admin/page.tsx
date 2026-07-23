"use client";

import { useCallback, useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Check, Eye, EyeOff, ImageIcon, KeyRound, Loader2, Lock, Save, ShieldCheck, Users } from "lucide-react";
import {
  adminCovers, adminCuration, adminOverview, adminSavePortal, adminSetHidden, adminSetProgress,
  type AdminSite, type CurationItem,
} from "@/lib/api";

const API = "http://127.0.0.1:8600";

/* ---------------- key gate ---------------- */

function Gate({ onKey }: { onKey: (k: string) => void }) {
  const [key, setKey] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  const submit = async () => {
    if (!key.trim() || busy) return;
    setBusy(true); setErr("");
    try { await adminOverview(key.trim()); onKey(key.trim()); }
    catch { setErr("Invalid admin key."); }
    finally { setBusy(false); }
  };

  return (
    <main className="flex min-h-screen items-center justify-center bg-[#0b0908] px-5 text-[#f4efe8]">
      <motion.div initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} className="w-full max-w-md">
        <p className="text-[11px] uppercase tracking-[0.35em] text-[#c8963e]">Zaw G · Internal</p>
        <h1 className="mt-3 font-[Fraunces] text-4xl font-light">Admin Panel</h1>
        <div className="mt-8 flex items-center gap-3 rounded-full border border-white/15 bg-white/5 px-5 py-4 focus-within:border-[#c8963e]/60">
          <Lock className="h-5 w-5 shrink-0 text-[#c8963e]" />
          <input type="password" value={key} onChange={(e) => setKey(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && submit()} placeholder="Admin key"
            className="w-full bg-transparent text-lg tracking-widest outline-none placeholder:text-[#f4efe8]/25" />
        </div>
        {err && <p className="mt-3 text-sm text-red-400">{err}</p>}
        <button onClick={submit} disabled={busy}
          className="mt-6 flex w-full items-center justify-center gap-2 rounded-full bg-[#c8963e] py-4 text-sm font-semibold uppercase tracking-[0.2em] text-[#0b0908] transition hover:bg-[#d9a84f] disabled:opacity-50">
          {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <ShieldCheck className="h-4 w-4" />} Unlock
        </button>
      </motion.div>
    </main>
  );
}

/* ---------------- portal manager ---------------- */

function PortalRow({ k, site, onSaved }: { k: string; site: AdminSite; onSaved: () => void }) {
  const [client, setClient] = useState(site.client_name);
  const [code, setCode] = useState(site.access_code);
  const [note, setNote] = useState(site.note);
  const [cover, setCover] = useState(site.cover_rel);
  const [cands, setCands] = useState<{ site: string[]; design: string[] } | null>(null);
  const [busy, setBusy] = useState(false);
  const [saved, setSaved] = useState(false);
  const [err, setErr] = useState("");
  const [prog, setProg] = useState(site.progress_override != null ? String(site.progress_override) : "");
  const [progBusy, setProgBusy] = useState(false);
  const [progMsg, setProgMsg] = useState("");
  const saveProgress = async () => {
    const v = parseInt(prog, 10);
    if (isNaN(v) || v < 0 || v > 100) { setProgMsg("0-100 only"); return; }
    setProgBusy(true); setProgMsg("");
    try { await adminSetProgress(k, site.site_id, v); setProgMsg("progress set"); onSaved(); }
    catch { setProgMsg("failed"); }
    finally { setProgBusy(false); }
  };
  const resetProgress = async () => {
    setProgBusy(true);
    try { await adminSetProgress(k, site.site_id, null); setProg(""); setProgMsg("back to auto"); onSaved(); }
    finally { setProgBusy(false); }
  };

  const loadCovers = () => { if (!cands) adminCovers(k, site.site_id).then(setCands).catch(() => {}); };
  const save = async () => {
    setBusy(true); setErr(""); setSaved(false);
    try {
      await adminSavePortal(k, site.site_id, { client_name: client, access_code: code, cover_rel: cover, note });
      setSaved(true); onSaved();
    } catch (e) { setErr(String(e).includes("409") ? "Access code already used by another site." : "Save failed."); }
    finally { setBusy(false); }
  };
  const shownCover = cover || site.best_photo;

  return (
    <div className="rounded-3xl border border-white/10 bg-white/[0.04] p-6">
      <div className="flex flex-wrap items-start gap-5">
        <div className="relative h-28 w-40 shrink-0 overflow-hidden rounded-2xl border border-white/10 bg-white/5">
          {shownCover
            ? <img src={`${API}${shownCover}`} alt="" className="h-full w-full object-cover" />
            : <ImageIcon className="absolute inset-0 m-auto h-8 w-8 text-white/20" />}
          <span className="absolute bottom-1 left-2 rounded bg-black/60 px-2 py-0.5 text-[9px] uppercase tracking-widest text-white/80">cover</span>
        </div>
        <div className="min-w-[220px] flex-1">
          <div className="flex items-center gap-3">
            <h3 className="font-[Fraunces] text-2xl">{site.name}</h3>
            <span className={`rounded-full px-2.5 py-0.5 text-[10px] uppercase tracking-wider ${site.active ? "bg-emerald-400/15 text-emerald-300" : "bg-white/10 text-white/40"}`}>
              {site.active ? "active" : "done"}
            </span>
            <span className="text-xs text-white/35">{site.photos} photos · {site.reports} reports</span>
          </div>
          <div className="mt-4 grid gap-3 sm:grid-cols-2">
            <input value={client} onChange={(e) => setClient(e.target.value)} placeholder="Client name (e.g. Daw Aye)"
              className="rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm outline-none focus:border-[#c8963e]/60" />
            <input value={code} onChange={(e) => setCode(e.target.value)} placeholder="Access code (e.g. ZG54B-2026)"
              className="rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm tracking-wider outline-none focus:border-[#c8963e]/60" />
          </div>
          <textarea value={note} onChange={(e) => setNote(e.target.value)} rows={2}
            placeholder="Note to client (shown on their portal)"
            className="mt-3 w-full rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm outline-none focus:border-[#c8963e]/60" />
        </div>
      </div>

      {/* real parsed ops + progress override */}
      <div className="mt-4 flex flex-wrap items-center gap-3 rounded-2xl border border-white/10 bg-white/[0.03] px-4 py-3 text-xs">
        <span className="uppercase tracking-[0.2em] text-white/40">Parsed from reports:</span>
        <span className="rounded-full bg-[#c8963e]/15 px-3 py-1 text-[#c8963e]">{site.stage ?? "no data yet"}</span>
        <span className="text-white/60">progress {site.progress ?? "—"}%{site.progress_override != null && " (manual)"}</span>
        <input
          type="number" min={0} max={100} placeholder="Set %"
          value={prog}
          onChange={(e) => setProg(e.target.value)}
          className="w-20 rounded-lg border border-white/10 bg-white/5 px-2 py-1 text-center outline-none focus:border-[#c8963e]/60"
        />
        <button onClick={saveProgress} disabled={progBusy}
          className="rounded-full border border-[#c8963e]/50 px-4 py-1 uppercase tracking-widest text-[#c8963e] transition hover:bg-[#c8963e] hover:text-black disabled:opacity-40">
          {progBusy ? "…" : "Set"}
        </button>
        {site.progress_override != null && (
          <button onClick={resetProgress} className="text-white/40 underline hover:text-white">reset to auto</button>
        )}
        {progMsg && <span className="text-emerald-300">{progMsg}</span>}
      </div>

      {/* cover picker */}
      <div className="mt-4">
        <button onClick={loadCovers} className="text-xs uppercase tracking-[0.2em] text-[#c8963e] hover:underline">
          {cands ? "Choose cover photo" : "Load cover candidates (site photos + design renders)"}
        </button>
        {cands && (
          <div className="mt-3 flex gap-2 overflow-x-auto pb-2">
            {[...cands.site, ...cands.design].map((c) => (
              <button key={c} onClick={() => setCover(c)}
                className={`relative h-20 w-28 shrink-0 overflow-hidden rounded-xl border-2 transition ${cover === c ? "border-[#c8963e]" : "border-transparent opacity-60 hover:opacity-100"}`}>
                <img src={`${API}${c}`} alt="" className="h-full w-full object-cover" loading="lazy" />
                {cover === c && <Check className="absolute right-1 top-1 h-4 w-4 rounded-full bg-[#c8963e] p-0.5 text-black" />}
              </button>
            ))}
          </div>
        )}
      </div>

      <div className="mt-4 flex items-center gap-4">
        <button onClick={save} disabled={busy}
          className="flex items-center gap-2 rounded-full bg-[#c8963e] px-6 py-2.5 text-xs font-semibold uppercase tracking-[0.2em] text-black transition hover:bg-[#d9a84f] disabled:opacity-50">
          {busy ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Save className="h-3.5 w-3.5" />} Save portal
        </button>
        {saved && <span className="flex items-center gap-1 text-xs text-emerald-300"><Check className="h-4 w-4" /> Saved — portal live at /portal</span>}
        {err && <span className="text-xs text-red-400">{err}</span>}
      </div>
    </div>
  );
}

/* ---------------- homepage curation ---------------- */

function Curation({ k }: { k: string }) {
  const [items, setItems] = useState<CurationItem[] | null>(null);
  const load = useCallback(() => adminCuration(k).then(setItems).catch(() => setItems([])), [k]);
  useEffect(() => { load(); }, [load]);

  const toggle = async (img: string, hidden: boolean) => {
    setItems((xs) => xs?.map((x) => x.img === img ? { ...x, hidden } : x) ?? xs);
    await adminSetHidden(k, img, hidden).catch(() => {});
  };

  if (!items) return <Loader2 className="mx-auto mt-20 h-8 w-8 animate-spin text-[#c8963e]" />;
  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
      {items.map((it) => (
        <div key={it.img} className={`group relative aspect-[4/3] overflow-hidden rounded-2xl border transition ${it.hidden ? "border-red-400/40 opacity-40" : "border-white/10"}`}>
          <img src={`${API}${it.img}`} alt="" loading="lazy" className="h-full w-full object-cover" />
          <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/80 to-transparent p-3">
            <p className="truncate text-xs text-white/85">{it.title}</p>
            <p className="text-[10px] uppercase tracking-widest text-[#c8963e]">{it.category} · ★{it.score}</p>
          </div>
          <button onClick={() => toggle(it.img, !it.hidden)}
            className={`absolute right-2 top-2 rounded-full p-2 backdrop-blur transition ${it.hidden ? "bg-red-500/80 text-white" : "bg-black/50 text-white/70 hover:text-white"}`}>
            {it.hidden ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
          </button>
        </div>
      ))}
    </div>
  );
}

/* ---------------- panel ---------------- */

function Panel({ k }: { k: string }) {
  const [tab, setTab] = useState<"portals" | "homepage">("portals");
  const [sites, setSites] = useState<AdminSite[] | null>(null);
  const load = useCallback(() => adminOverview(k).then(setSites).catch(() => setSites([])), [k]);
  useEffect(() => { load(); }, [load]);

  return (
    <main className="min-h-screen bg-[#0b0908] px-6 py-10 text-[#f4efe8]">
      <div className="mx-auto max-w-6xl">
        <p className="text-[11px] uppercase tracking-[0.35em] text-[#c8963e]">Zaw G · Internal</p>
        <h1 className="mt-2 font-[Fraunces] text-4xl font-light">Admin Panel</h1>

        <div className="mt-8 flex gap-2">
          {([["portals", Users, "Client Portals"], ["homepage", ImageIcon, "Homepage Curation"]] as const).map(([id, Icon, label]) => (
            <button key={id} onClick={() => setTab(id)}
              className={`flex items-center gap-2 rounded-full px-5 py-2.5 text-xs font-semibold uppercase tracking-[0.15em] transition ${tab === id ? "bg-[#c8963e] text-black" : "border border-white/15 text-white/60 hover:text-white"}`}>
              <Icon className="h-4 w-4" /> {label}
            </button>
          ))}
        </div>

        <div className="mt-8 space-y-6">
          {tab === "portals" && (
            !sites ? <Loader2 className="mx-auto mt-20 h-8 w-8 animate-spin text-[#c8963e]" />
            : sites.map((s) => <PortalRow key={s.site_id} k={k} site={s} onSaved={load} />)
          )}
          {tab === "homepage" && <Curation k={k} />}
        </div>

        <p className="mt-12 flex items-center gap-2 text-xs text-white/25">
          <KeyRound className="h-3.5 w-3.5" /> New [ZG] Telegram groups appear here automatically after the next 3-hour sync.
        </p>
      </div>
    </main>
  );
}

export default function AdminPage() {
  const [key, setKey] = useState<string | null>(null);
  return key ? <Panel k={key} /> : <Gate onKey={setKey} />;
}
