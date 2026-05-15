<script lang="ts">
  import MdiCircleEditOutline from "@iconify-svelte/mdi/circle-edit-outline";
  import Input from "$lib/components/Input.svelte";
  import { polarAngle, polarToCartesian } from "$lib/utils/math";
  import { type AngleRange } from "$lib/utils/types";

  interface Props {
    selectedRange: AngleRange | null;
    compassRadius?: number;
  }

  const defaultRange = { start: 315, end: 45 };

  let { selectedRange = $bindable(), compassRadius = 75 }: Props = $props();

  let open = $state<boolean>(false);
  let inputValue = $derived(
    selectedRange ? `${selectedRange.start}° - ${selectedRange.end}°` : "",
  );

  let displayRange = $state<AngleRange>(selectedRange ?? defaultRange);

  $effect(() => {
    if (selectedRange) {
      displayRange = selectedRange;
    } else {
      displayRange = defaultRange;
    }
  });

  $effect(() => {
    if (open) {
      selectedRange = displayRange;
    }
  });

  let svgEl = $state<SVGSVGElement | null>(null);
  let dragging = $state<"start" | "end" | null>(null);

  const padding = $derived(compassRadius * 0.4);
  const size = $derived((compassRadius + padding) * 2);
  const center = $derived({ x: size / 2, y: size / 2 });
  let startPoint = $derived(
    polarToCartesian(displayRange.start, compassRadius, center),
  );
  let endPoint = $derived(
    polarToCartesian(displayRange.end, compassRadius, center),
  );
  const HANDLE_R = $derived(compassRadius * 0.1);
  const RING_STROKE_W = $derived(compassRadius * 0.06);
  const TICK_STROKE_W = $derived(compassRadius * 0.03);
  const TICK_LONG = $derived(compassRadius * 0.16);
  const TICK_SHORT = $derived(compassRadius * 0.08);
  const TICK_OUTER = $derived(compassRadius - RING_STROKE_W / 2);
  const LABEL_R = $derived(compassRadius - compassRadius * 0.26);
  const TICKS = Array.from({ length: 72 }, (_, i) => i * 5);
  const CARDINAL = [
    { deg: 0, label: "N" },
    { deg: 90, label: "E" },
    { deg: 180, label: "S" },
    { deg: 270, label: "W" },
  ];

  function tickLine(deg: number, long: boolean) {
    const inner = compassRadius - (long ? TICK_LONG : TICK_SHORT);

    const i = polarToCartesian(deg, inner, center);
    const o = polarToCartesian(deg, TICK_OUTER, center);
    return `M ${o.x} ${o.y} L ${i.x} ${i.y}`;
  }

  function arcPath(startDeg: number, endDeg: number) {
    const startPoint = polarToCartesian(startDeg, compassRadius, center);
    const endPoint = polarToCartesian(endDeg, compassRadius, center);

    let delta = (((endDeg - startDeg) % 360) + 360) % 360;
    const large = delta > 180 ? 1 : 0;
    return `M ${startPoint.x} ${startPoint.y} A ${compassRadius} ${compassRadius} 0 ${large} 1 ${endPoint.x} ${endPoint.y}`;
  }

  function angleFromEvent(e: PointerEvent, svgEl: SVGSVGElement) {
    const rect = svgEl.getBoundingClientRect();
    const clientX = e.touches ? e.touches[0].clientX : e.clientX;
    const clientY = e.touches ? e.touches[0].clientY : e.clientY;
    const scaleX = size / rect.width;
    const scaleY = size / rect.height;
    const lx = (clientX - rect.left) * scaleX - center.x;
    const ly = (clientY - rect.top) * scaleY - center.y;
    return polarAngle(lx, ly);
  }

  function onPointerDown(handle: "start" | "end", e: PointerEvent) {
    e.preventDefault();
    dragging = handle;
    svgEl?.setPointerCapture(e.pointerId);
  }

  function onPointerMove(e: PointerEvent) {
    if (!svgEl || !dragging) return;

    const angle = Math.round(angleFromEvent(e, svgEl));
    if (dragging === "start") {
      displayRange.start = ((angle % 360) + 360) % 360;
    } else {
      displayRange.end = ((angle % 360) + 360) % 360;
    }

    selectedRange = { ...displayRange };
  }

  function onPointerUp() {
    dragging = null;
  }

  function parseInput(value: string) {
    const match = value.match(/^(\d+)\s*-\s*(\d+)$/);
    if (!match) return;
    const start = parseInt(match[1]);
    const end = parseInt(match[2]);
    if (start >= 0 && start <= 359 && end >= 0 && end <= 359) {
      displayRange = { start, end };
      selectedRange = { ...displayRange };
    }
  }
</script>

<div class="azimuth-picker">
  <Input
    placeholder="Azimuth range"
    value={inputValue}
    onchange={(e) => parseInput(e.currentTarget.value)}
  >
    {#snippet suffix()}
      {#if selectedRange}
        <button
          type="button"
          class="clear"
          onclick={() => (selectedRange = null)}>✕</button
        >
      {/if}
      <button
        type="button"
        class="slider-toggle"
        onclick={() => (open = !open)}
      >
        <MdiCircleEditOutline width="1rem" />
      </button>
    {/snippet}
  </Input>

  {#if open}
    <div class="azimuth-slider">
      <svg
        class="slider-svg"
        bind:this={svgEl}
        viewBox="0 0 {size} {size}"
        width={size}
        height={size}
        onpointermove={onPointerMove}
        onpointerup={onPointerUp}
        onpointercancel={onPointerUp}
        role="img"
        aria-label="Azimuth interval selector"
        style="--handle-r: {HANDLE_R}; --handle-r-hover: {HANDLE_R * 1.3}"
      >
        <!-- tick marks -->
        {#each TICKS as deg}
          <path
            d={tickLine(deg, deg % 45 === 0)}
            stroke="var(--tick)"
            stroke-width={deg % 45 === 0 ? TICK_STROKE_W : TICK_STROKE_W * 0.8}
            stroke-linecap="round"
            fill="none"
          />
        {/each}

        <!-- cardinal labels -->
        {#each CARDINAL as { deg, label }}
          {@const lp = polarToCartesian(deg, compassRadius - 26, center)}
          <text
            x={lp.x}
            y={lp.y}
            text-anchor="middle"
            dominant-baseline="central"
            font-size="1rem"
            fill="var(--label)"
            font-weight="600">{label}</text
          >
        {/each}

        <!-- track ring -->
        <circle
          cx={center.x}
          cy={center.y}
          r={compassRadius}
          fill="none"
          stroke="var(--track)"
          stroke-width={RING_STROKE_W}
        />

        <!-- active arc -->
        <path
          d={arcPath(displayRange.start, displayRange.end)}
          fill="none"
          stroke="var(--arc)"
          stroke-width={RING_STROKE_W}
          stroke-linecap="round"
        />

        <!-- start handle -->
        <circle
          class={["handle", { active: dragging === "start" }]}
          cx={startPoint.x}
          cy={startPoint.y}
          r={HANDLE_R}
          fill="var(--handle-start)"
          stroke="var(--handle-stroke)"
          onpointerdown={(e) => onPointerDown("start", e)}
          role="slider"
          aria-label="Start angle"
          aria-valuenow={displayRange.start}
          aria-valuemin="0"
          aria-valuemax="359"
          tabindex="0"
        />
        <!-- end handle -->
        <circle
          class={["handle", { active: dragging === "end" }]}
          cx={endPoint.x}
          cy={endPoint.y}
          r={HANDLE_R}
          fill="var(--handle-end)"
          stroke="var(--handle-stroke)"
          onpointerdown={(e) => onPointerDown("end", e)}
          role="slider"
          aria-label="end angle"
          aria-valuenow={displayRange.end}
          aria-valuemin="0"
          aria-valuemax="359"
          tabindex="0"
        />
      </svg>
    </div>
  {/if}
</div>

<style>
  .azimuth-picker {
    --track: #d1d5db;
    --arc: #3b82f6;
    --handle-start: #f59e0b;
    --handle-end: #3b82f6;
    --handle-stroke: #fff;
    --tick: #9ca3af;
    --label: #6b7280;
    --readout-label: #9ca3af;
    --readout-value: #1f2937;

    position: relative;
  }

  .slider-toggle {
    display: flex;
    align-items: center;
    background: none;
    border: none;
    cursor: pointer;
    color: inherit;
  }

  .azimuth-slider {
    position: absolute;
    top: 100%;
    right: 0;
    background-color: oklch(var(--color-accent));
    z-index: 1;
  }

  .slider-svg {
    display: block;
    max-width: 100%;
    touch-action: none;
    cursor: default;
  }

  .handle {
    cursor: grab;
    transition: r 0.1s ease;
    r: calc(var(--handle-r) * 1px);
  }

  .handle:hover,
  .handle.active {
    r: calc(var(--handle-r-hover) * 1px);
  }

  .handle.active {
    cursor: grabbing;
  }

  .clear {
    background: none;
    border: none;
    color: oklch(var(--color-text));
  }

  .clear:hover {
    color: red;
  }
</style>
