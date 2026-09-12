import { useCallback, useEffect, useState } from "react";
import { ApiError, api } from "../api/client";
import type { DrawOut } from "../api/types";
import { NumberBall } from "../components/NumberBall";

const PAGE_SIZE = 20;

export function DrawHistoryPage() {
  const [draws, setDraws] = useState<DrawOut[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [hasMore, setHasMore] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadPage = useCallback(async (offset: number) => {
    const page = await api.get<DrawOut[]>(`/draws?limit=${PAGE_SIZE}&offset=${offset}`);
    setDraws((prev) => (offset === 0 ? page : [...prev, ...page]));
    setHasMore(page.length === PAGE_SIZE);
  }, []);

  useEffect(() => {
    (async () => {
      setLoading(true);
      setError(null);
      try {
        await loadPage(0);
      } catch (err) {
        setError(err instanceof ApiError ? err.message : "지난 회차를 불러오지 못했습니다.");
      } finally {
        setLoading(false);
      }
    })();
  }, [loadPage]);

  async function handleLoadMore() {
    setLoadingMore(true);
    setError(null);
    try {
      await loadPage(draws.length);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "지난 회차를 불러오지 못했습니다.");
    } finally {
      setLoadingMore(false);
    }
  }

  return (
    <div>
      <h1>지난 회차</h1>
      {loading && <p>불러오는 중...</p>}
      {error && <p className="error">{error}</p>}

      {!loading && (
        <ul className="draw-history-list">
          {draws.map((d) => (
            <li key={d.draw_no} className="draw-history-row">
              <div className="draw-history-row__meta">
                <span className="draw-history-row__no">{d.draw_no}회</span>
                <span className="draw-history-row__date">{d.draw_date}</span>
              </div>
              <div className="draw-history-row__balls">
                {d.numbers.map((n) => (
                  <NumberBall key={n} value={n} />
                ))}
                <span className="draw-banner__plus">+</span>
                <NumberBall value={d.bonus_no} variant="bonus" />
              </div>
            </li>
          ))}
        </ul>
      )}

      {!loading && hasMore && (
        <button onClick={handleLoadMore} disabled={loadingMore} className="draw-history-more">
          {loadingMore ? "불러오는 중..." : "더 보기"}
        </button>
      )}
    </div>
  );
}
