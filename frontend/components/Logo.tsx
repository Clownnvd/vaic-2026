/** Logo PolicyRadar — motif radar quét (vòng cung + tia quét + chấm mục tiêu).
 *  Render thuần SVG, nét theo brand xanh thể chế. Dùng cho sidebar + header. */
export function Logo({ size = 32 }: { size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 40 40"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-label="PolicyRadar"
    >
      <defs>
        <linearGradient id="pr-bg" x1="0" y1="0" x2="40" y2="40" gradientUnits="userSpaceOnUse">
          <stop stopColor="#3364f5" />
          <stop offset="1" stopColor="#1a37b5" />
        </linearGradient>
        <linearGradient id="pr-sweep" x1="20" y1="20" x2="33" y2="9" gradientUnits="userSpaceOnUse">
          <stop stopColor="#bcd3ff" stopOpacity="0.9" />
          <stop offset="1" stopColor="#bcd3ff" stopOpacity="0" />
        </linearGradient>
      </defs>

      {/* nền bo tròn */}
      <rect width="40" height="40" rx="10" fill="url(#pr-bg)" />

      {/* các vòng radar */}
      <circle cx="20" cy="20" r="12.5" stroke="#8eb5ff" strokeOpacity="0.55" strokeWidth="1.3" />
      <circle cx="20" cy="20" r="8" stroke="#8eb5ff" strokeOpacity="0.7" strokeWidth="1.3" />
      <circle cx="20" cy="20" r="3.5" stroke="#dae6ff" strokeWidth="1.3" />

      {/* quạt quét */}
      <path d="M20 20 L20 6.5 A13.5 13.5 0 0 1 32 12.7 Z" fill="url(#pr-sweep)" />

      {/* tia quét */}
      <line x1="20" y1="20" x2="31.5" y2="11.5" stroke="#eaf1ff" strokeWidth="1.6" strokeLinecap="round" />

      {/* chấm mục tiêu (chính sách trúng) */}
      <circle cx="27.5" cy="24.5" r="2.4" fill="#6ee7a8" />
      <circle cx="27.5" cy="24.5" r="4.4" stroke="#6ee7a8" strokeOpacity="0.5" strokeWidth="1.1" />
    </svg>
  );
}
