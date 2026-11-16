import { describe, expect, it } from "vitest";
import { formatBytes, formatScore, scoreTone, titleCase } from "./format";

describe("format helpers", () => {
  it("formats scores and handles n/a", () => {
    expect(formatScore(47.6)).toBe("48");
    expect(formatScore(null)).toBe("—");
  });
  it("maps scores to tones", () => {
    expect(scoreTone(80)).toBe("success");
    expect(scoreTone(50)).toBe("warning");
    expect(scoreTone(10)).toBe("danger");
    expect(scoreTone(null)).toBe("muted");
  });
  it("formats bytes and titles", () => {
    expect(formatBytes(512)).toBe("512 B");
    expect(formatBytes(2048)).toBe("2.0 KB");
    expect(titleCase("missing_mandatory")).toBe("Missing Mandatory");
  });
});
