// API client for the Zaw G pipeline (FastAPI on :8600)
const API = process.env.NEXT_PUBLIC_PIPELINE_API ?? "http://127.0.0.1:8600";

export type SiteOpsReal = {
  stage: string; progress: number; workers: number;
  manpower: { date: string; workers: number }[];
  milestones: { label: string; done: boolean }[];
  updated: string | null;
};

export type ApiSite = {
  id: string;
  group_id: number;
  title: string;
  name: string;
  code: string;
  report_count: number;
  photo_count: number;
  keep_count: number;
  last_photo: string | null;
  cover_url: string | null;
  active?: number;
  ops?: SiteOpsReal | null;
};

export type DayPhoto = { url: string; score: number; reason: string };
export type SiteDay = { date: string; photos: DayPhoto[] };

export type ApiReport = {
  id: number;
  site_id: string;
  msg_id: number;
  date: string;
  sender: string;
  text: string;
};

async function get<T>(path: string): Promise<T> {
  const r = await fetch(`${API}${path}`, { cache: "no-store" });
  if (!r.ok) throw new Error(`${path} → ${r.status}`);
  return r.json();
}

export type PortfolioItem = {
  title: string;
  subtitle: string;
  score: number | null;
  img: string | null;
  slug?: string;
};
export type Portfolio = { design: PortfolioItem[]; finished: PortfolioItem[]; ongoing: PortfolioItem[] };
export const fetchPortfolio = () => get<Portfolio>("/api/portfolio");

export type FeedPost = {
  id: string;
  date: string;
  text: string;
  image: string | null;
  link: string;
  media: string;
};
export const fetchFeed = () => get<FeedPost[]>("/api/feed");

export const fetchSites = () => get<ApiSite[]>("/api/sites");
export const fetchDays = (id: string, all = false) =>
  get<SiteDay[]>(`/api/sites/${id}/days${all ? "?only_keep=false" : ""}`);
export const fetchReports = (id: string, limit = 30) =>
  get<ApiReport[]>(`/api/sites/${id}/reports?limit=${limit}`);
export const media = (url: string | null | undefined): string => {
  if (!url) return "";
  return url.startsWith("http") ? url : `${API}${url}`;
};

// "2026-07-18T14:25:00+00:00" → "Jul 18 · 2:25 PM"
export function fmtWhen(iso: string) {
  const d = new Date(iso);
  const date = d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
  const time = d.toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" });
  return { date, time, full: `${date} · ${time}` };
}

export const fmtDay = (ymd: string) =>
  new Date(ymd + "T00:00:00").toLocaleDateString("en-US", {
    weekday: "short", month: "short", day: "numeric",
  });

// ---------------- Client portal + Admin ----------------
const post = <T>(p: string, body: unknown, key?: string) =>
  fetch(`${API}${p}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...(key ? { "X-Admin-Key": key } : {}) },
    body: JSON.stringify(body),
  }).then(async (r) => { if (!r.ok) throw new Error(`${r.status}`); return r.json() as Promise<T>; });

const getAdmin = <T>(p: string, key: string) =>
  fetch(`${API}${p}`, { headers: { "X-Admin-Key": key } })
    .then(async (r) => { if (!r.ok) throw new Error(`${r.status}`); return r.json() as Promise<T>; });

export type PortalData = {
  slug: string; name: string; code: string; client_name: string; note: string;
  active: boolean; cover: string | null;
  ops?: SiteOpsReal | null;
  photos: { img: string; score: number; date: string }[];
  photo_count: number; report_count: number;
  first_report: string | null; last_report: string | null;
};
export const portalAuth = (code: string) => post<PortalData>("/api/portal/auth", { code });

export type AdminSite = {
  site_id: string; name: string; code: string; title: string; active: boolean;
  photos: number; reports: number;
  client_name: string; access_code: string; cover_rel: string; note: string;
  best_photo: string | null;
  stage: string | null; progress: number | null; progress_override: number | null; workers: number | null;
};
export const adminOverview = (key: string) => getAdmin<AdminSite[]>("/api/admin/overview", key);
export const adminCovers = (key: string, siteId: string) =>
  getAdmin<{ site: string[]; design: string[] }>(`/api/admin/covers/${siteId}`, key);
export const adminSavePortal = (key: string, siteId: string, cfg: { client_name: string; access_code: string; cover_rel: string; note: string }) =>
  post<{ ok: boolean }>(`/api/admin/portal/${siteId}`, cfg, key);

export type CurationItem = { category: string; title: string; score: number; img: string; hidden: boolean };
export const adminCuration = (key: string) => getAdmin<CurationItem[]>("/api/admin/curation", key);
export const adminSetHidden = (key: string, img: string, hidden: boolean) =>
  post<{ ok: boolean }>("/api/admin/curation", { img, hidden }, key);

export type Stats = {
  sites_total: number; sites_active: number; reports: number;
  photos: number; photos_kept: number; design_renders: number; finished_projects: number;
};
export const fetchStats = () => get<Stats>("/api/stats");
export const adminSetProgress = (key: string, siteId: string, progress: number | null) =>
  post<{ ok: boolean }>(`/api/admin/ops/${siteId}`, { progress }, key);
