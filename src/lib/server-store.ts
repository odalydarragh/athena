import { MemoryStore } from "./store/memory";
import { seedDemo } from "./store/seed";

const globalStore = globalThis as typeof globalThis & { __documdr?: MemoryStore };

export function getStore(): MemoryStore {
  if (!globalStore.__documdr) {
    const store = new MemoryStore();
    seedDemo(store);
    globalStore.__documdr = store;
  }
  return globalStore.__documdr;
}
