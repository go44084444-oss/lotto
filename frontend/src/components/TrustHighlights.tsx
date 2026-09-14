const ITEMS = ["패턴이 뚜렷한 조합은 미리 제외", "회원마다 겹치지 않게 배정", "매주 자동으로 새로 배정"];

function CheckIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="10" cy="10" r="10" fill="currentColor" opacity="0.15" />
      <path
        d="M6 10.2l2.4 2.4L14 7"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export function TrustHighlights() {
  return (
    <ul className="trust-list">
      {ITEMS.map((item) => (
        <li key={item} className="trust-item">
          <CheckIcon />
          {item}
        </li>
      ))}
    </ul>
  );
}
