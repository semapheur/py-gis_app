<script lang="ts">
  interface Props {
    checked: boolean;
    label?: string;
    onchange: (checked: boolean) => void;
  }

  let { checked = $bindable(), label, onchange }: Props = $props();

  const uid = $props.id();
  const labelId = $derived(`${uid}-label`)

  function toggle() {
    checked = !checked;
    onchange(checked);
  }

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === " " || e.key === "Enter") {
      e.preventDefault();
      toggle();
    }
  }
</script>

<div class="switch">
  <button
    id={uid}
    class={{ checked }}
    type="button"
    role="switch"
    aria-checked={checked}
    aria-labelledby={label ? labelId : undefined}"
    onclick={toggle}
    onkeydown={handleKeydown}
  />
  {#if label}
    <label id={labelId} for={uid}>
      {label}
    </label>
  {/if}
</div>

<style>
  .switch {
    display: inline-flex;
    align-items: center;
    gap: var(--size-md);
  }

  button {
    --track-w: 2rem;
    --track-h: 1.25rem;
    --pad: 0.175rem;
    --border-w: 1px;
    --thumb-size: calc(var(--track-h) - 2 * var(--pad) - 2 * var(--border-w));

    position: relative;
    width: var(--track-w);
    height: var(--track-h);
    padding: 0;
    border: none;
    cursor: pointer;
    background: oklch(var(--color-primary-accent));
    border: 1px solid oklch(var(--color-secondary));
    border-radius: 99px;

    &::after {
      content: "";
      position: absolute;
      left: var(--pad);
      top: var(--pad);
      width: var(--thumb-size);
      height: var(--thumb-size);
      border-radius: 50%;
      background: oklch(var(--color-text));
      transition: transform 150ms ease;
    }

    &.checked {
      background-color: oklch(var(--color-secondary-accent));
    }

    &.checked::after {
      transform: translateX(
        calc(
          var(--track-w) - var(--thumb-size) - 2 * var(--pad) - 2 *
            var(--border-w)
        )
      );
    }
  }
</style>
