/**
 * SkipLink — Keyboard-only skip-to-content link for accessibility.
 *
 * Renders as the first focusable element in the page layout.
 * Follows WCAG 2.1 AA 2.4.1 Bypass Blocks.
 */

import { useSkipLink } from "@/hooks/useAccessibility";

interface SkipLinkProps {
  targetId: string;
  children?: React.ReactNode;
}

export function SkipLink({ targetId, children = "Skip to content" }: SkipLinkProps) {
  const { skipLinkProps } = useSkipLink(targetId);

  return (
    <a {...skipLinkProps} className={skipLinkProps.className}>
      {children}
    </a>
  );
}
