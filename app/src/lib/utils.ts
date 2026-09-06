import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Merge Tailwind class names, resolving conflicts so the last value wins.
 *
 * This file was missing from the repository entirely, while all 50 vendored
 * shadcn/ui components import it as `@/lib/utils`. Every one of them failed
 * with `TS2307: Cannot find module '@/lib/utils'`, so the frontend could not
 * be built. `clsx` and `tailwind-merge` were already declared in package.json;
 * only the helper that uses them was absent.
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
