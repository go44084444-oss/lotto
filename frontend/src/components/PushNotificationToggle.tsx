import { useEffect, useState } from "react";
import {
  getCurrentSubscription,
  isPushSupported,
  subscribeToPush,
  unsubscribeFromPush,
} from "../push/subscribe";

export function PushNotificationToggle() {
  const [subscribed, setSubscribed] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isPushSupported()) return;
    getCurrentSubscription().then((sub) => setSubscribed(sub !== null));
  }, []);

  if (!isPushSupported()) return null;

  async function handleToggle() {
    setBusy(true);
    setError(null);
    try {
      if (subscribed) {
        await unsubscribeFromPush();
        setSubscribed(false);
      } else {
        await subscribeToPush();
        setSubscribed(true);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "알림 설정에 실패했습니다.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="push-toggle">
      <button onClick={handleToggle} disabled={busy}>
        {subscribed ? "당첨 알림 끄기" : "당첨 알림 받기"}
      </button>
      {error && <p className="error">{error}</p>}
    </div>
  );
}
