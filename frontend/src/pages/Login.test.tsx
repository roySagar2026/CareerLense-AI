import { beforeEach, describe, expect, it, vi } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderWithProviders } from "@/test/utils";
import Login from "./Login";

const login = vi.fn();
vi.mock("@/contexts/AuthContext", () => ({ useAuth: () => ({ login, user: null, loading: false }) }));

describe("Login page", () => {
  beforeEach(() => login.mockReset());

  it("shows validation errors and does not call the API", async () => {
    renderWithProviders(<Login />);
    await userEvent.click(screen.getByRole("button", { name: /sign in/i }));
    expect(await screen.findByText("Email is required")).toBeInTheDocument();
    expect(login).not.toHaveBeenCalled();
  });

  it("submits valid credentials", async () => {
    login.mockResolvedValue(undefined);
    renderWithProviders(<Login />);
    await userEvent.type(screen.getByLabelText("Email"), "asha@example.com");
    await userEvent.type(screen.getByLabelText("Password"), "CareerLens-Test-9");
    await userEvent.click(screen.getByRole("button", { name: /sign in/i }));
    await waitFor(() => expect(login).toHaveBeenCalledWith("asha@example.com", "CareerLens-Test-9"));
  });

  it("shows the server error message on failure", async () => {
    login.mockRejectedValue(new Error("Invalid email or password."));
    renderWithProviders(<Login />);
    await userEvent.type(screen.getByLabelText("Email"), "asha@example.com");
    await userEvent.type(screen.getByLabelText("Password"), "wrong");
    await userEvent.click(screen.getByRole("button", { name: /sign in/i }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Invalid email or password.");
  });
});
