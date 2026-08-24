type Variant = "default" | "winning" | "bonus" | "matched" | "matched-win";

export function NumberBall({ value, variant = "default" }: { value: number; variant?: Variant }) {
  const modifier = variant === "default" ? "" : ` number-ball--${variant}`;
  return <span className={`number-ball${modifier}`}>{value}</span>;
}
