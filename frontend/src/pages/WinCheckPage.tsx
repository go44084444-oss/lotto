import { useEffect, useState } from "react";
import { ApiError, api } from "../api/client";
import type { WinCheckResponse } from "../api/types";
import { NumberBall } from "../components/NumberBall";

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
          <div className="draw-banner">
            <div className="draw-banner__label">{data.draw_no}회차 당첨번호</div>
            <div className="draw-banner__numbers">
              {data.winning_numbers.map((n) => (
                <NumberBall key={n} value={n} variant="winning" />
              ))}
              <span className="draw-banner__plus">+</span>
              <NumberBall value={data.bonus_no} variant="bonus" />
              <span className="draw-banner__bonus-label">보너스</span>
            </div>
          </div>

          <p className="section-label">내 조합 결과</p>
          <ul className="combo-list">
            {data.results.map((r) => {
              const winningSet = new Set(data.winning_numbers);
              const isWin = r.rank !== null;
              return (
                <li key={r.combination_id} className="combo-row combo-row__result">
                  <div className="combo-row__balls">
                    {r.numbers.map((n) => (
                      <NumberBall
                        key={n}
                        value={n}
                        variant={
                          winningSet.has(n) ? (isWin ? "matched-win" : "matched") : "default"
                        }
                      />
                    ))}
                  </div>
                  <div className="combo-row__meta">
                    <span className={`rank-badge${isWin ? " rank-badge--win" : ""}`}>
                      {r.rank
                        ? `${RANK_LABEL[r.rank]}${r.matched_bonus ? " (보너스 일치)" : ""}`
                        : "낙첨"}
                    </span>
                    <span className="match-text">{r.match_count}개 일치</span>
                  </div>
                </li>
              );
            })}
          </ul>
        </>
      )}
    </div>
  );
}
