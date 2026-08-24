export interface TokenOut {
  access_token: string;
  token_type: string;
}

export interface MemberOut {
  id: number;
  email: string;
  status: "active" | "withdrawn";
  tier: string;
  created_at: string;
}

export interface CombinationOut {
  id: number;
  numbers: number[];
}

export interface AssignmentBatchOut {
  weekly_cycle_id: number;
  cycle_key: string;
  quota: number;
  combinations: CombinationOut[];
}

export interface WinCheckResultItem {
  combination_id: number;
  numbers: number[];
  match_count: number;
  matched_bonus: boolean;
  rank: number | null;
}

export interface WinCheckResponse {
  cycle_key: string;
  draw_no: number;
  winning_numbers: number[];
  bonus_no: number;
  results: WinCheckResultItem[];
}

export interface VapidPublicKeyOut {
  vapid_public_key: string;
}
