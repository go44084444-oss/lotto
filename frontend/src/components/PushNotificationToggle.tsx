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
    <div>
      <div className="push-toggle">
        <button
          type="button"
          className="push-toggle__label"
          onClick={handleToggle}
          disabled={busy}
          aria-pressed={subscribed}
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path
              d="M12 4C9.79 4 8 5.79 8 8V11.5L6 14.5V15.5H18V14.5L16 11.5V8C16 5.79 14.21 4 12 4Z"
              stroke="#7c3aed"
              strokeWidth="1.6"
              strokeLinejoin="round"
            />
            <path d="M10 18C10.3 19 11 19.6 12 19.6C13 19.6 13.7 19 14 18" stroke="#7c3aed" strokeWidth="1.6" strokeLinecap="round" />
          </svg>
          당첨 알림 받기
        </button>
        <div className={`toggle-switch${subscribed ? " toggle-switch--on" : ""}`}>
          <div className="toggle-switch__knob" />
        </div>
      </div>
      {error && <p className="error">{error}</p>}
    </div>
  );
}
