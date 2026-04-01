type UserAvatarProps = {
  size?: number;
};

export default function UserAvatar({ size = 30 }: UserAvatarProps) {
  return (
    <span
      aria-hidden="true"
      className="inline-flex items-center justify-center rounded-full bg-[#E5E7EB] text-[#6B7280]"
      style={{ width: size, height: size }}
    >
      <svg width={Math.round(size * 0.68)} height={Math.round(size * 0.68)} viewBox="0 0 24 24" fill="none">
        <circle cx="12" cy="8" r="4.1" fill="currentColor" />
        <path
          d="M5.2 19.4c0-3.22 3.03-5.84 6.8-5.84 3.76 0 6.8 2.62 6.8 5.84"
          fill="currentColor"
        />
      </svg>
    </span>
  );
}