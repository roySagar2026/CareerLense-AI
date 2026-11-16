import { describe, expect, it, vi } from "vitest";
import { fireEvent, screen, waitFor } from "@testing-library/react";
import { renderWithProviders } from "@/test/utils";
import { ResumeUploader } from "./ResumeUploader";
import { resumesApi } from "@/services/api";

vi.mock("@/services/api", () => ({ resumesApi: { upload: vi.fn() } }));
vi.mock("@/hooks/useQueries", () => ({ useInvalidateAll: () => async () => undefined }));

describe("ResumeUploader", () => {
  it("rejects unsupported files client-side without calling the API", async () => {
    renderWithProviders(<ResumeUploader />);
    const input = screen.getByLabelText("Resume file") as HTMLInputElement;
    fireEvent.change(input, { target: { files: [new File(["x"], "evil.exe")] } });
    expect(await screen.findByRole("alert")).toHaveTextContent("Only PDF and DOCX");
    expect(resumesApi.upload).not.toHaveBeenCalled();
  });

  it("uploads a valid file", async () => {
    vi.mocked(resumesApi.upload).mockResolvedValue({ id: "r1", status: "ready" } as never);
    renderWithProviders(<ResumeUploader />);
    const input = screen.getByLabelText("Resume file") as HTMLInputElement;
    fireEvent.change(input, { target: { files: [new File(["hello"], "cv.pdf", { type: "application/pdf" })] } });
    await waitFor(() => expect(resumesApi.upload).toHaveBeenCalledTimes(1));
  });
});
