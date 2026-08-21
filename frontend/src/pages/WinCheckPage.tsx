import { useEffect, useState } from "react";
import { ApiError, api } from "../api/client";
import type { WinCheckResponse } from "../api/types";

const RANK_LABEL: Record<number, string> = {
  1: "1등",
  2: "2등",
  3: "3등",
  4: "4등",
  5: "5등",
};

export function WinCheckPage() {
  const [data, setData] = useState<WinCheckResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      setLoading(true);
      setError(null);
      try {
        const result = await api.get<WinCheckResponse>("/me/assignments/win-check");
        setData(result);
      } catch (err) {
        setError(err instanceof ApiError ? err.message : "당첨 확인에 실패했습니다.");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  return (
    <div>
      <h1>당첨 확인</h1>
      {loading && <p>불러오는 중...</p>}
      {error && <p className="error">{error}</p>}
      {data && (
        <>
          <p>
            {data.draw_no}회 당첨번호: {data.winning_numbers.join(", ")} + 보너스{" "}
            {data.bonus_no}
          </p>
          <ul className="combo-list">
            {data.results.map((r) => (
              <li key={r.combination_id}>
                {r.numbers.join(", ")} —{" "}
                {r.rank
                  ? `${RANK_LABEL[r.rank]}${r.matched_bonus ? " (보너스 일치)" : ""}`
                  : "낙첨"}{" "}
                ({r.match_count}개 일치)
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  );
}
