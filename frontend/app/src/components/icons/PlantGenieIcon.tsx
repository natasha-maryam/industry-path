type PlantGenieIconProps = {
  size?: number;
};

export default function PlantGenieIcon({ size = 30 }: PlantGenieIconProps) {
  const innerSize = Math.round(size * 0.7);

  return (
    <span
      aria-hidden="true"
      className="inline-flex items-center justify-center rounded-full bg-white text-[#EF4444]"
      style={{
        width: size,
        height: size,
        border: "1px solid rgba(239, 68, 68, 0.16)",
        boxShadow: "0 2px 6px rgba(0,0,0,0.08)",
      }}
    >
      <svg width={innerSize} height={innerSize} viewBox="0 0 24 24" fill="none">
        <path
          d="M8.35 7.45a3.2 3.2 0 0 1 5.32-1.98 3.2 3.2 0 0 1 2.15 5.63 3.5 3.5 0 0 1-.47 4.72 3.2 3.2 0 0 1-5.27 2.13 3.2 3.2 0 0 1-2.56-5.28 3.42 3.42 0 0 1 .83-5.22Z"
          stroke="currentColor"
          strokeWidth="1.55"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        <path d="M9.2 9.15h1.7M13.1 8.55h1.7M9.05 12h5.9M10.1 14.95h1.9M13.2 14.35h1.7" stroke="currentColor" strokeWidth="1.45" strokeLinecap="round" />
        <circle cx="8.35" cy="7.45" r="1.15" fill="currentColor" />
        <circle cx="16.1" cy="7.15" r="1.15" fill="currentColor" />
        <circle cx="16.25" cy="15.85" r="1.15" fill="currentColor" />
        <circle cx="8.55" cy="16.25" r="1.15" fill="currentColor" />
      </svg>
    </span>
  );
}