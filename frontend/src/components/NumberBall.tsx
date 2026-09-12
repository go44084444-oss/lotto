type Variant = "default" | "winning" | "bonus" | "matched" | "matched-win";

function rangeModifier(value: number): string {
  if (value <= 10) return " number-ball--range-1";
  if (value <= 20) return " number-ball--range-2";
  if (value <= 30) return " number-ball--range-3";
  if (value <= 40) return " number-ball--range-4";
  return " number-ball--range-5";
}

export function NumberBall({ value, variant = "default" }: { value: number; variant?: Variant }) {
  if (variant === "matched" || variant === "matched-win") {
    return <span className={`number-ball number-ball--${variant}`}>{value}</span>;
  }
  const modifier = rangeModifier(value) + (variant === "bonus" ? " number-ball--bonus" : "");
  return <span className={`number-ball${modifier}`}>{value}</span>;
}
