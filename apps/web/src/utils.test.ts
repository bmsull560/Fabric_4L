import { describe, it, expect } from "vitest";
import { cn } from "./lib/utils";

describe("cn utility (tailwind-merge)", () => {
  it("should merge tailwind classes correctly", () => {
    const result = cn("px-2 py-1", "px-4");
    // px-4 should override px-2
    expect(result).toBe("py-1 px-4");
  });

  it("should handle conditional classes", () => {
    const isActive = true;
    const result = cn("base-class", isActive && "active-class");
    expect(result).toBe("base-class active-class");
  });

  it("should filter out falsy values", () => {
    const result = cn("class-a", false && "class-b", "class-c", null, undefined);
    expect(result).toBe("class-a class-c");
  });

  it("should handle empty inputs", () => {
    const result = cn();
    expect(result).toBe("");
  });

  it("should merge complex tailwind conflicts", () => {
    const result = cn(
      "bg-blue-500 hover:bg-blue-600",
      "bg-red-500",
      "text-white p-4"
    );
    // bg-red-500 should override bg-blue-500
    expect(result).toContain("bg-red-500");
    expect(result).toContain("hover:bg-blue-600");
    expect(result).toContain("text-white");
    expect(result).toContain("p-4");
  });
});
