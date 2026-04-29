declare module "zustand" {
  export type StateCreator<T> = (set: (partial: Partial<T>) => void) => T;
  export type UseBoundStore<T> = { getState: () => T };
  export function create<T>(): (initializer: StateCreator<T>) => UseBoundStore<T>;
}

declare module "zustand/middleware" {
  import type { StateCreator } from "zustand";
  export type PersistOptions<T> = {
    name: string;
    partialize?: (state: T) => unknown;
  };
  export function persist<T>(initializer: StateCreator<T>, options: PersistOptions<T>): StateCreator<T>;
}
