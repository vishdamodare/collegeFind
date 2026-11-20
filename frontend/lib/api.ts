export const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(public status: number) { super(`API ${status}`); }
}

export async function get<T>(path: string): Promise<T> {
  const r = await fetch(`${API}${path}`, { cache: "no-store" });
  if (!r.ok) throw new ApiError(r.status);
  return r.json();
}

export type Cutoff = {
  college: string; college_slug: string; institute_code: string; branch: string; choice_code: string;
  category: string; seat_type: string; seat_type_code: string; year: string; round: number; stage: number; stage_label: string;
  closing_percentile: string | null; closing_rank: number | null; original_text: string;
  source_url: string | null; source_page: number | null; verification_status: string;
  status?: string; gap?: string | null; reason?: string | null;
};
export type Meta = {
  years: string[]; rounds: number[]; seat_types: { code: string; name: string }[];
  categories: { code: string; seat_type_code: string }[]; records: Record<string, number>; serving_unverified: boolean; preview_rounds: string[];
};
export const pct = (v: string | null) => (v == null ? "Data not available" : Number(v).toFixed(4));

export type PredictRecord = {
  year: string; round: number; stage_label: string; closing_percentile: string | null; closing_rank: number | null;
  status: string; gap: string | null; source_page: number | null; original_text: string;
};
export type PredictItem = {
  college: string; college_slug: string; branch: string; choice_code: string; category: string;
  seat_type_code: string; status: string; headline_idx: number; records: PredictRecord[];
};
export type PredictResponse = {
  summary: Record<string, number>; total: number; offset: number; items: PredictItem[];
  sources: Record<string, string | null>; basis: string; disclaimer: string;
};

/** Decode CET Cell category codes (e.g. LOBCH → "OBC", group "Ladies"). Last letter = seat level, already implied by seat type. */
const CASTE: Record<string, string> = { OPEN: "Open", OBC: "OBC", SEBC: "SEBC", SC: "SC", ST: "ST", VJ: "VJ / DT-A", NT1: "NT-B", NT2: "NT-C", NT3: "NT-D" };
const SPECIAL: Record<string, string> = { EWS: "EWS", TFWS: "Tuition Fee Waiver", MI: "Minority", ORPHAN: "Orphan" };
const GROUP: Record<string, string> = { G: "General", L: "Ladies", DEF: "Defence", DEFR: "Defence", PWD: "PwD", PWDR: "PwD" };
export const CAT_GROUPS = ["General", "Ladies", "Other", "Defence", "PwD"];
export function catInfo(code: string): { group: string; label: string } {
  if (SPECIAL[code]) return { group: "Other", label: SPECIAL[code] };
  const m = code.match(/^(DEFR|DEF|PWDR|PWD|G|L)(OPEN|OBC|SEBC|SC|ST|VJ|NT1|NT2|NT3)[SHO]$/);
  return m ? { group: GROUP[m[1]], label: CASTE[m[2]] } : { group: "Other", label: code };
}
export const catLabel = (code: string) => { const c = catInfo(code); return c.group === "Other" ? c.label : `${c.label} · ${c.group}`; };

/** Short, readable seat-type labels (the official names are very long). */
export const SEAT_SHORT: Record<string, string> = {
  STATE_LEVEL: "State Level",
  HU_TO_HU: "Home Univ. seat · Home Univ. candidate",
  HU_TO_OHU: "Home Univ. seat · Other-Univ. candidate",
  OHU_TO_OHU: "Other-Univ. seat · Other-Univ. candidate",
  OHU_TO_HU: "Other-Univ. seat · Home Univ. candidate",
  MIN_TO_MH: "Minority seat · Maharashtra candidate",
  MH_TO_AI: "Maharashtra seat · All India candidate",
  ALL_INDIA: "All India",
};
