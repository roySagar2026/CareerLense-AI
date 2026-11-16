import { AxiosError, type AxiosResponse } from "axios";
import { describe, expect, it } from "vitest";
import { errorCode, errorMessage, getAccessToken, setAccessToken } from "./http";

function apiError(status: number, code: string, message: string) {
  const err = new AxiosError("fail", "ERR_BAD_REQUEST");
  err.response = { status, data: { error: { code, message } } } as AxiosResponse;
  return err;
}

describe("http helpers", () => {
  it("keeps the access token in memory only", () => {
    setAccessToken("abc");
    expect(getAccessToken()).toBe("abc");
    expect(window.localStorage.length).toBe(0);
    setAccessToken(null);
    expect(getAccessToken()).toBeNull();
  });

  it("extracts API error messages and codes", () => {
    const err = apiError(422, "no_requirements", "Nothing to analyze.");
    expect(errorMessage(err)).toBe("Nothing to analyze.");
    expect(errorCode(err)).toBe("no_requirements");
  });

  it("explains network failures", () => {
    expect(errorMessage(new AxiosError("Network Error"))).toMatch(/Cannot reach the server/);
  });
});
