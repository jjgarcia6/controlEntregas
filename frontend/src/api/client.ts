import axios, { AxiosRequestConfig } from "axios";

import { authStore } from "../store/authStore";

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL as string,
});

// Attach JWT to every request
apiClient.interceptors.request.use((config) => {
  const token = authStore.getState().token;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Refresh queue: hold 401 requests while a refresh is in-flight
let isRefreshing = false;
let failedQueue: Array<{ resolve: (token: string) => void; reject: (err: unknown) => void }> = [];

function processQueue(error: unknown, token: string | null) {
  failedQueue.forEach(({ resolve, reject }) => {
    if (error) reject(error);
    else resolve(token as string);
  });
  failedQueue = [];
}

interface RetryableRequest extends AxiosRequestConfig {
  _retry?: boolean;
}

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest: RetryableRequest = error.config;

    if (error.response?.status !== 401) {
      return Promise.reject(error);
    }

    // Already retried — give up
    if (originalRequest._retry) {
      return Promise.reject(error);
    }

    if (isRefreshing) {
      // Queue this request until refresh completes
      return new Promise<string>((resolve, reject) => {
        failedQueue.push({ resolve, reject });
      }).then((newToken) => {
        originalRequest.headers = {
          ...originalRequest.headers,
          Authorization: `Bearer ${newToken}`,
        };
        return apiClient(originalRequest);
      });
    }

    originalRequest._retry = true;
    isRefreshing = true;

    try {
      const currentToken = authStore.getState().token;
      const { data } = await axios.post<{ token: string }>(
        `${import.meta.env.VITE_API_URL as string}/auth/refresh`,
        null,
        { headers: { Authorization: `Bearer ${currentToken}` } }
      );

      authStore.getState().setToken(data.token);
      processQueue(null, data.token);

      originalRequest.headers = {
        ...originalRequest.headers,
        Authorization: `Bearer ${data.token}`,
      };
      return apiClient(originalRequest);
    } catch (refreshError) {
      processQueue(refreshError, null);
      authStore.getState().logout();
      window.location.href = "/login";
      return Promise.reject(refreshError);
    } finally {
      isRefreshing = false;
    }
  }
);

export default apiClient;
