export function portal(target: HTMLElement | string = "body") {
  return (node: HTMLElement) => {
    const targetEl =
      typeof target === "string" ? document.querySelector(target) : target;
    targetEl?.appendChild(node);

    return () => node.remove();
  };
}
