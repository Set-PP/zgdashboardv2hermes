// ─── SiteOps types for CEO Command Center overlay ───
export type SiteOps = {
  progress: number; delta: number; stage: string; workers: number; weather: string;
  manpower: number[]; major: { label: string; done: boolean }[]; minor: { label: string; pct: number }[];
  materials: string[]; issues: string[];
};

export type SiteOpsReal = {
  stage?: string; progress?: number | null; workers?: number; manpower?: any[]; milestones?: any[];
};

// ─── Portfolio / Project types ───
export type WorkCategory = "Design" | "Completed" | "Ongoing";

export type Project = {
  id: string; title: string; location: string; category: WorkCategory; year: string;
  image: string; span?: boolean; progress?: number;
};

export type SiteReport = { id: string; engineer: string; time: string; text: string; photos: number; shots: string[]; };
export type SiteStatus = "on-track" | "watch" | "delayed";

const STAGE_PROG: Record<string, number> = { Substructure: 22, Structure: 45, Masonry: 62, Plaster: 78, Painting: 91, Finishing: 97 };

export const OPS_DEFAULT: SiteOps = {
  progress: 30, delta: 2, stage: "Substructure", workers: 8, weather: "Mandalay · 35°C · Clear",
  manpower: [6, 7, 8, 8, 9, 8, 8], major: [{ label: "Foundation", done: false }], minor: [], materials: [], issues: [],
};

// Manual ops overlay — parsed from engineer Telegram reports (kept in DB site_ops table)
export const SITE_OPS: Record<string, Partial<SiteOps>> = {
  "r02-26-rain-fashion":    { progress: 94, delta: 5, stage: "Painting & sealer", workers: 14, manpower: [8,10,12,14,14,13,14] },
  "p02-25-lha":             { progress: 92, delta: 4, stage: "Interior finishing", workers: 1, manpower: [12,14,16,18,18,17,1] },
  "p22-26-kume":            { progress: 65, delta: 3, stage: "L1 brickwork", workers: 0, manpower: [14,15,16,16,17,15,16] },
  "p21-25-shwe-nagar":      { progress: 63, delta: 3, stage: "L1 lintel → L2 slab", workers: 25, manpower: [18,20,22,25,25,24,25] },
  "p06-26-mdy-car-showroom":{ progress: 75, delta: 6, stage: "Steel frame → roof", workers: 7, manpower: [14,17,20,21,22,19,20] },
  "p05-26-pol-03":          { progress: 48, delta: 3, stage: "L1 columns → slab prep", workers: 4, manpower: [12,13,14,14,13,12,14] },
  "p22-25-pol-02":          { progress: 58, delta: 4, stage: "L1 columns / L2 lintel", workers: 32, manpower: [26,28,30,32,31,30,32] },
  "p10-25-62a":             { progress: 97, delta: 2, stage: "Cleaning & handover", workers: 10, manpower: [8,8,9,10,10,10,10] },
};

const AUTO_SITE_OPS: Record<string, { stage: string; workers: number }> = {
  "p01-25-59-market":   { stage: "Substructure", workers: 4 },
  "p03-26-aap":         { stage: "Structure", workers: 4 },
  "p04-25-lyc":         { stage: "Substructure", workers: 2 },
  "p05-25-atg":         { stage: "Substructure", workers: 6 },
  "p06-25-atg":         { stage: "Substructure", workers: 4 },
  "p13-26-68b":         { stage: "Substructure", workers: 2 },
  "p14-24-47cls":       { stage: "Substructure", workers: 0 },
  "p16-24-59a":         { stage: "Substructure", workers: 6 },
  "p18-25-sww":         { stage: "Substructure", workers: 4 },
  "p19-25-ht":          { stage: "Substructure", workers: 2 },
};

export const opsFor = (site: string): SiteOps => {
  const manual = SITE_OPS[site];
  if (manual) return ({ ...OPS_DEFAULT, ...manual } as unknown) as SiteOps;
  const info = AUTO_SITE_OPS[site];
  if (info) return (({ ...OPS_DEFAULT, stage: info.stage, workers: info.workers, progress: STAGE_PROG[info.stage] ?? 30 }) as unknown) as SiteOps;
  return (({ ...OPS_DEFAULT } as unknown) as SiteOps);
};

// Portfolio grid data — real projects come from /api/portfolio endpoint (FastAPI on :8600)
export const PROJECTS: Project[] = [];

// Live sites overlay — real data is served by /api/sites and rendered server-side via API
export type LIVE_SITES_DATA = {
  id: string; name: string; client: string; location: string; engineer: string; stage: string;
  progress: number; delta: number; status: SiteStatus; workers: number; week: number[]; weather: string;
  image: string; major: { label: string; done: boolean }[]; minor: { label: string; pct: number }[];
  materials: string[]; issues: string[]; reports: SiteReport[];
};
export const LIVE_SITES: LIVE_SITES_DATA[] = [];

// Client portal data — served via /api/portal/auth with access code
export type PortalDay = { date: string; stage: string; note: string; photos: string[] };
export const SITE_DAYS: PortalDay[] = [];
