import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { ProtectedRoute } from "./ProtectedRoute";
import { sampleUser } from "@/test/utils";

const state = vi.hoisted(() => ({ user: null as unknown, loading: false }));
vi.mock("@/contexts/AuthContext", () => ({ useAuth: () => state }));

function setup() {
  return render(
    <MemoryRouter initialEntries={["/app"]}>
      <Routes>
        <Route path="/login" element={<p>login page</p>} />
        <Route path="/app" element={<ProtectedRoute />}>
          <Route index element={<p>secret dashboard</p>} />
        </Route>
      </Routes>
    </MemoryRouter>,
  );
}

describe("ProtectedRoute", () => {
  it("redirects anonymous users to login", () => {
    state.user = null;
    setup();
    expect(screen.getByText("login page")).toBeInTheDocument();
    expect(screen.queryByText("secret dashboard")).not.toBeInTheDocument();
  });

  it("renders content for signed-in users", () => {
    state.user = sampleUser;
    setup();
    expect(screen.getByText("secret dashboard")).toBeInTheDocument();
  });
});
