export interface ToastMessage {
  id: string;
  type: "error" | "warning" | "success" | "info";
  title: string;
  message: string;
}

type ToastListener = (toasts: ToastMessage[]) => void;

let toasts: ToastMessage[] = [];
const listeners: Set<ToastListener> = new Set();

export const toastStore = {
  subscribe(listener: ToastListener) {
    listeners.add(listener);
    listener([...toasts]);
    return () => {
      listeners.delete(listener);
    };
  },

  show(type: ToastMessage["type"], title: string, message: string) {
    const id = Math.random().toString(36).substring(2, 9);
    const newToast: ToastMessage = { id, type, title, message };
    toasts = [...toasts, newToast];
    listeners.forEach((listener) => listener([...toasts]));

    setTimeout(() => {
      toastStore.dismiss(id);
    }, 6000);
  },

  dismiss(id: string) {
    toasts = toasts.filter((t) => t.id !== id);
    listeners.forEach((listener) => listener([...toasts]));
  },
};

export const toast = {
  error: (title: string, message: string) => toastStore.show("error", title, message),
  warning: (title: string, message: string) => toastStore.show("warning", title, message),
  success: (title: string, message: string) => toastStore.show("success", title, message),
  info: (title: string, message: string) => toastStore.show("info", title, message),
};
