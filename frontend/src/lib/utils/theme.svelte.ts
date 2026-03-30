import { browser } from "$app/environment";

function getUserPreference() {
  if (window.localStorage.getItem("theme")) {
    return window.localStorage.getItem("theme") as string;
  }

  return window.matchMedia("(prefers-color-scheme: dark").matches
    ? "dark"
    : "light";
}

class Theme {
  current = $state(browser ? getUserPreference() : "light");

  constructor() {
    $effect.root(() => {
      $effect(() => {
        document.body.dataset.theme = this.current;
        //document.documentElement.classList.toggle("dark", this.current === "dark")
        localStorage.setItem("theme", this.current);
      });
    });
  }

  toggle() {
    this.current = this.current === "dark" ? "light" : "dark";
  }

  set(value: string) {
    this.current = value;
  }
}

export const theme = new Theme();
