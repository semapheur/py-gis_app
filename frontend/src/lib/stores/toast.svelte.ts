type ToastType = "success" | "error" | "info" | "warning";

interface Toast {
  id: number;
  message: string;
  type: ToastType;
  duration: number;
}

class ToastStore {
  items = $state<Toast[]>([]);
  #counter = 0;

  #add(message: string, type: ToastType, duration = 3000) {
    const id = this.#counter++;
    this.items.push({ id, message, type, duration });
    setTimeout(() => this.remove(id), duration);
  }

  remove(id: number) {
    const index = this.items.findIndex((t) => t.id === id);
    if (index !== -1) this.items.splice(index, 1);
  }

  success(message: string, duration = 3000) {
    this.#add(message, "success", duration);
  }
  error(message: string, duration = 3000) {
    this.#add(message, "error", duration);
  }
  info(message: string, duration = 3000) {
    this.#add(message, "info", duration);
  }
  warning(message: string, duration = 3000) {
    this.#add(message, "warning", duration);
  }
}

export const toast = new ToastStore();
