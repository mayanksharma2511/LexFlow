import apiClient from "./client";

export interface Case {
  id: string;
  title: string;
  case_number?: string | null;
  client_name?: string | null;
  opposing_party?: string | null;
  court?: string | null;
  description?: string | null;
  status?: string | null;
  priority?: string | null;
  created_at?: string;
  updated_at?: string;
}

export async function getCases(): Promise<Case[]> {
  const response = await apiClient.get<Case[]>("/cases");
  return response.data;
}