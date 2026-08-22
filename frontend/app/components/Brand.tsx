import Image from "next/image";

type BrandProps = {
  compact?: boolean;
  className?: string;
};

export default function Brand({ compact = false, className = "" }: BrandProps) {
  return (
    <span className={`inline-flex items-center ${compact ? "gap-2.5" : "gap-3"} ${className}`}>
      <Image
        src="/icon.svg"
        alt=""
        width={compact ? 38 : 48}
        height={compact ? 38 : 48}
        priority
        aria-hidden="true"
        className="shrink-0"
      />
      <span className="min-w-0">
        <span className={`block whitespace-nowrap font-serif leading-none text-cloud ${compact ? "text-lg" : "text-2xl"}`}>
          微蓝日报
        </span>
        <span className={`mt-1 block whitespace-nowrap font-mono uppercase text-cyan ${compact ? "text-[8px] tracking-[0.22em]" : "text-[9px] tracking-[0.28em]"}`}>
          Blue Hour Daily
        </span>
      </span>
    </span>
  );
}
