<script lang="ts" generics="T extends string | number | null = string">
  import type { Snippet } from "svelte";
  import type { HTMLInputAttributes } from "svelte/elements";

  interface Props extends HTMLInputAttributes {
    value?: T;
    invalid?: boolean;
    fieldSizing?: "content" | "fixed";
    suffix?: Snippet;
    suffixWidth?: string;
  }

  let {
    value = $bindable(),
    placeholder,
    required = false,
    invalid = false,
    fieldSizing = "fixed",
    oninput,
    suffix,
    suffixWidth,
    ...rest
  }: Props = $props();
  let minCh = $derived(placeholder ? Math.max(placeholder.length + 2, 6) : 0);

  const uid = $props.id();
</script>

<div class="input">
  <input
    id={uid}
    class:invalid
    bind:value
    {placeholder}
    {required}
    style={`field-sizing: ${fieldSizing}; min-width: ${minCh}ch; ${suffix ? `padding-right: ${suffixWidth};` : ""}`}
    oninput={(e) => {
      if (rest.type === "number") {
        const raw = e.currentTarget.value;
        let v = Number(raw);
        const min = Number(rest.min ?? -Infinity);
        const max = Number(rest.max ?? Infinity);
        if (!isNaN(v) && raw !== "" && !raw.endsWith(".")) {
          const clamped = Math.min(max, Math.max(min, v));
          e.currentTarget.value = String(clamped);
          value = clamped as T;
        } else {
          value = raw as T;
        }
      }
      oninput?.(e);
    }}
    {...rest}
  />
  {#if placeholder}
    <label for={uid}>{placeholder}</label>
  {/if}
  {#if suffix}
    <div class="suffix">
      {@render suffix()}
    </div>
  {/if}
</div>

<style>
  .input {
    position: relative;
    min-width: 0;
  }

  label {
    position: absolute;
    left: var(--size-md);
    font-size: var(--text-2xs);
    top: 0;
    transform: translateY(-50%);
    transition: all 0.15s ease;
    color: oklch(var(--color-text));
    pointer-events: none;
    text-shadow: var(--text-shadow);
  }

  input {
    padding: var(--size-md);
    max-width: 100%;
    font-size: inherit;
    color: oklch(var(--color-text));
    background-color: oklch(var(--color-accent));
    border: 1px solid oklch(var(--color-secondary));
    border-radius: var(--size-sm);

    &.invalid {
      border-color: red;
    }

    &::placeholder {
      color: transparent;
    }

    &:placeholder-shown + label {
      font-size: inherit;
      background-color: transparent;
      transform: translateY(0);
      top: var(--size-sm);
      text-shadow: none;
    }

    &:focus + label {
      font-size: var(--text-2xs);
      top: 0;
      transform: translateY(-50%);
      text-shadow: var(--text-shadow);
    }
  }

  .suffix {
    position: absolute;
    right: 0;
    top: 50%;
    transform: translateY(-50%);
    display: flex;
    align-items: center;
  }
</style>
