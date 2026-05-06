/**
 * OptimizedImage — Reusable image primitive with performance defaults.
 *
 * Enforces lazy loading, async decoding, and responsive sizing.
 * Prefer WebP/AVIF sources at build time or via CDN transforms.
 */

import { cn } from "@/lib/utils";

interface OptimizedImageProps extends React.ComponentProps<"img"> {
  src: string;
  alt: string;
}

export function OptimizedImage({
  src,
  alt,
  className,
  loading = "lazy",
  decoding = "async",
  ...props
}: OptimizedImageProps) {
  return (
    <img
      src={src}
      alt={alt}
      loading={loading}
      decoding={decoding}
      className={cn("h-auto max-w-full", className)}
      {...props}
    />
  );
}
