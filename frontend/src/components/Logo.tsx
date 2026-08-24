export function LogoMark({ size = 22 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M24 3L15 17L33 17Z" fill="#e0242c" />
      <path d="M24 11L8 33L40 33Z" fill="#e0242c" />
      <rect x="19" y="33" width="10" height="11" fill="#7c3aed" />
    </svg>
  );
}
