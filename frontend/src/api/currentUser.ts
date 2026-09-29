import { useEffect, useState } from "react";
import apiClient from "./client";

export interface CurrentUser {
  id: string;
  full_name: string;
  email: string;
  role: string;
}

let cached: Promise<CurrentUser | null> | null = null;

/** The signed-in user, loaded once from /users/me. */
export function fetchCurrentUser(): Promise<CurrentUser | null> {
  if (!cached) {
    cached = apiClient
      .get<CurrentUser>("/users/me")
      .then((res) => res.data)
      .catch(() => {
        cached = null;
        return null;
      });
  }
  return cached;
}

/** Forget the cached user (call on sign-out). */
export function clearCurrentUser(): void {
  cached = null;
}

export function useCurrentUser(): CurrentUser | null {
  const [user, setUser] = useState<CurrentUser | null>(null);
  useEffect(() => {
    let active = true;
    fetchCurrentUser().then((u) => {
      if (active) setUser(u);
    });
    return () => {
      active = false;
    };
  }, []);
  return user;
}

export function formatRole(role: string | undefined): string {
  if (!role) return "";
  return role.charAt(0) + role.slice(1).toLowerCase();
}
