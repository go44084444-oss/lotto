export function LogoMark({ size = 21 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 26 26" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="13" cy="5" r="3" stroke="#7c3aed" strokeWidth="2" />
      <circle cx="5" cy="20" r="3" stroke="#7c3aed" strokeWidth="2" />
      <circle cx="21" cy="20" r="3" stroke="#7c3aed" strokeWidth="2" />
      <path d="M13 8L6 17M13 8L20 17" stroke="#7c3aed" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}
