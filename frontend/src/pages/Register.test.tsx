import { describe, expect, it, vi } from "vitest";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderWithProviders } from "@/test/utils";
import Register from "./Register";

const register = vi.fn();
vi.mock("@/contexts/AuthContext", () => ({ useAuth: () => ({ register, user: null, loading: false }) }));

describe("Register page", () => {
  it("blocks weak or mismatched passwords", async () => {
    renderWithProviders(<Register />);
    await userEvent.type(screen.getByLabelText("Email"), "asha@example.com");
    await userEvent.type(screen.getByLabelText("Password"), "short");
    await userEvent.type(screen.getByLabelText("Confirm password"), "other");
    await userEvent.click(screen.getByRole("button", { name: /create account/i }));
    expect(await screen.findByText("Use at least 10 characters")).toBeInTheDocument();
    expect(register).not.toHaveBeenCalled();
  });
});
