import axios from "axios";
import { toast } from "./toast";

const apiClient = axios.create({
  baseURL: "http://127.0.0.1:8000/api/v1",
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 30000,
});

apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("access_token");

    if (token) {
      config.headers.set("Authorization", `Bearer ${token}`);
    }

    return config;
  },
  (error) => Promise.reject(error),
);

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response?.status;
    const message = error.response?.data?.detail || error.message || "An unexpected error occurred.";

    if (status === 429) {
      console.warn("API Rate Limit / Quota Exceeded:", message);
      toast.warning(
        "API Rate Limit / Quota Exceeded",
        "Third-party AI service limit reached. Processing paused gracefully.",
      );
    } else if (status === 500) {
      console.error("Internal Server Error:", message);
      toast.error(
        "Server Error (500)",
        "The server encountered an error processing your request.",
      );
    } else if (error.code === "ECONNABORTED" || error.message?.includes("timeout")) {
      console.warn("Network Timeout:", message);
      toast.warning(
        "Request Timeout",
        "Network connection timed out. Please retry your operation.",
      );
    } else if (!error.response && error.request) {
      console.warn("Network Error / Connection Failed");
      toast.error(
        "Network Error",
        "Unable to connect to LexFlow API service. Please check network state.",
      );
    } else if (status === 401) {
      console.warn("API authentication failed.");
    }

    return Promise.reject(error);
  },
);

export default apiClient;