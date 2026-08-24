import { useCallback, useEffect, useState } from "react";
import { ApiError, api } from "../api/client";
import type { AssignmentBatchOut } from "../api/types";
import { PushNotificationToggle } from "../components/PushNotificationToggle";

export function DashboardPage() {
  const [batch, setBatch] = useState<AssignmentBatchOut | null>(null);
  const [loading, setLoading] = useState(true);
  const [requesting, setRequesting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadCurrent = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.get<AssignmentBatchOut>("/me/assignments/current");
      setBatch(data);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "조회에 실패했습니다.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadCurrent();
  }, [loadCurrent]);

  async function handleRequest() {
    setRequesting(true);
    setError(null);
    try {
      const data = await api.post<AssignmentBatchOut>("/me/assignments");
      setBatch(data);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "배정 요청에 실패했습니다.");
    } finally {
      setRequesting(false);
    }
  }

  const hasAssignment = batch !== null && batch.combinations.length > 0;

  return (
    <div>
      <h1>이번 주 배정</h1>
      <PushNotificationToggle />
      {loading && <p>불러오는 중...</p>}
      {error && <p className="error">{error}</p>}

      {!loading && !hasAssignment && (
        <button onClick={handleRequest} disabled={requesting}>
          {requesting ? "받는 중..." : "이번 주 조합 받기"}
        </button>
      )}

      {hasAssignment && batch && (
        <>
          <p>
            {batch.cycle_key} 주차 · {batch.combinations.length}/{batch.quota}개
          </p>
          <ul className="combo-list">
            {batch.combinations.map((c) => (
              <li key={c.id}>{c.numbers.join(", ")}</li>
            ))}
          </ul>
        </>
      )}

      <p className="disclaimer">
        이 조합은 패턴이 뚜렷한 조합을 제외한 풀에서 무작위로 고른 것으로, 당첨 확률을 높이지
        않습니다.
      </p>
    </div>
  );
}
