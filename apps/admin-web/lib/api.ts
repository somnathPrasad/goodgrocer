import type { components } from "./api.generated";
export type Product = components["schemas"]["ProductOut"];
export type Brand = components["schemas"]["BrandOut"];
export type Category = components["schemas"]["CategoryOut"];
export type Variant = components["schemas"]["VariantOut"];
export type Order = components["schemas"]["OrderOut"];
export type ProductPage = components["schemas"]["ProductPage"];
export type ProductInput = components["schemas"]["ProductInput"];
export type VariantInput = components["schemas"]["VariantInput"];
export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message);
  }
}
export async function api<T>(
  path: string,
  method = "GET",
  data?: unknown,
  signal?: AbortSignal,
): Promise<T> {
  const body =
    data instanceof FormData
      ? data
      : data === undefined
        ? undefined
        : JSON.stringify(data);
  const response = await fetch("/api/v1/admin" + path, {
    method,
    signal,
    body,
    credentials: "same-origin",
    headers:
      data instanceof FormData
        ? undefined
        : { "Content-Type": "application/json" },
  });
  if (!response.ok) {
    const error = await response.json().catch(() => null);
    throw new ApiError(
      error?.error?.message || "Request failed. Please try again.",
      response.status,
    );
  }
  return response.status === 204 ? (undefined as T) : response.json();
}
export function money(value: string | number) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
  }).format(Number(value));
}
