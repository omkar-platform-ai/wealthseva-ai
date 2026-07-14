import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

/**
 * Merge Tailwind class strings safely: clsx handles conditionals/objects,
 * twMerge resolves conflicts so later classes win (e.g. focus:outline-none
 * is stripped when a focus-ring is composed in).
 */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

/** Keyboard focus ring — apply to any focusable element via cn(FOCUS_RING, ...).
 *  Mirrors the `.focus-ring` component class in globals.css. */
export const FOCUS_RING =
  'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-idbi-green focus-visible:ring-offset-2 focus-visible:ring-offset-idbi-bg';
