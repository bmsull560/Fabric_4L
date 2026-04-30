import * as Dialog from "@radix-ui/react-dialog";
import { Bot, Maximize2, Send, X } from "lucide-react";
import type { AgentChatMode } from "@/types/layout";

interface AgentChatProps {
  mode: AgentChatMode;
  onOpen: () => void;
  onClose: () => void;
  onExpand: () => void;
}

export function AgentChat({
  mode,
  onOpen,
  onClose,
  onExpand,
}: AgentChatProps) {
  const modalOpen = mode === "modal";

  return (
    <>
      {mode === "closed" && (
        <button
          type="button"
          onClick={onOpen}
          className="fixed bottom-5 right-5 z-50 inline-flex h-12 w-12 items-center justify-center rounded-full border bg-primary text-primary-foreground shadow-lg transition-transform hover:scale-105 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
          aria-label="Open agent chat"
        >
          <Bot className="h-5 w-5" />
        </button>
      )}

      <Dialog.Root open={modalOpen} onOpenChange={(open) => !open && onClose()}>
        <Dialog.Portal>
          <Dialog.Overlay className="fixed inset-0 z-40 bg-black/20 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=open]:fade-in-0 data-[state=closed]:fade-out-0" />

          <Dialog.Content className="fixed bottom-4 right-4 z-50 flex h-[480px] w-[min(calc(100vw-2rem),380px)] flex-col overflow-hidden rounded-xl border bg-background shadow-2xl data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=open]:slide-in-from-bottom-4 data-[state=closed]:slide-out-to-bottom-4 max-sm:bottom-0 max-sm:right-0 max-sm:h-[80vh] max-sm:w-full max-sm:rounded-b-none">
            <div className="flex h-12 shrink-0 items-center justify-between border-b px-4">
              <Dialog.Title className="text-sm font-semibold">
                Agent Assistant
              </Dialog.Title>

              <div className="flex items-center gap-1">
                <button
                  type="button"
                  onClick={onExpand}
                  className="inline-flex h-8 w-8 items-center justify-center rounded-md hover:bg-accent"
                  aria-label="Expand agent panel"
                >
                  <Maximize2 className="h-4 w-4" />
                </button>

                <Dialog.Close asChild>
                  <button
                    type="button"
                    className="inline-flex h-8 w-8 items-center justify-center rounded-md hover:bg-accent"
                    aria-label="Close agent chat"
                  >
                    <X className="h-4 w-4" />
                  </button>
                </Dialog.Close>
              </div>
            </div>

            <div className="min-h-0 flex-1 space-y-3 overflow-y-auto p-4">
              <div className="rounded-lg bg-muted p-3 text-sm">
                I can help configure settings, explain RBAC, or guide setup.
              </div>

              <div className="rounded-lg border p-3 text-sm">
                Try asking: Which settings should be admin-only?
              </div>
            </div>

            <form className="flex shrink-0 items-center gap-2 border-t p-3">
              <input
                className="h-9 min-w-0 flex-1 rounded-md border bg-background px-3 text-sm outline-none focus:ring-2 focus:ring-ring"
                placeholder="Ask the agent..."
                aria-label="Agent message"
              />

              <button
                type="submit"
                className="inline-flex h-9 w-9 items-center justify-center rounded-md bg-primary text-primary-foreground hover:opacity-90"
                aria-label="Send message"
              >
                <Send className="h-4 w-4" />
              </button>
            </form>
          </Dialog.Content>
        </Dialog.Portal>
      </Dialog.Root>
    </>
  );
}
