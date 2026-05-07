import type { RouteState } from "@/navigation/navigationService";

export interface NextAction {
  id: string;
  label: string;
  target: RouteState;
  params: { accountId: string };
  query?: Record<string, string>;
  disabled?: boolean;
  reason?: string;
}

export function createNextAction(input: Omit<NextAction, "id"> & { id?: string }): NextAction {
  return {
    id: input.id ?? `${input.target}-next-action`,
    ...input,
  };
}
