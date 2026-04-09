<script lang="ts">
  import Input from "$lib/components/Input.svelte";
  import MdiCalendarMonthOutline from "@iconify-svelte/mdi/calendar-month-outline";

  interface DateRange {
    start: Date | null;
    end: Date | null;
  }

  interface ViewDate {
    month: number;
    year: number;
  }

  interface DatePreset {
    label: string;
    value: () => DateRange;
  }

  interface CalendarCell {
    day: number;
    month: number;
    year: number;
    isCurrentMonth: boolean;
  }

  interface Week {
    weekNumber: number;
    days: CalendarCell[];
  }

  interface Props {
    minDate?: Date | null;
    maxDate?: Date | null;
    selectedRange?: DateRange;
  }

  let {
    minDate = null,
    maxDate = new Date(),
    selectedRange = $bindable({ start: null, end: null }),
  }: Props = $props();

  let hoverDate = $state<Date | null>(null);

  const minYear = $derived(minDate ? minDate.getFullYear() : -Infinity);
  const maxYear = $derived(maxDate ? maxDate.getFullYear() : Infinity);

  const presets: DatePreset[] = [
    {
      label: "Last 24h",
      value: () => ({
        start: new Date(Date.now() - 24 * 3600 * 1000),
        end: new Date(),
      }),
    },
    {
      label: "Last Week",
      value: () => ({
        start: new Date(Date.now() - 7 * 24 * 3600 * 1000),
        end: new Date(),
      }),
    },
    {
      label: "Last Month",
      value: () => {
        const d = new Date();
        return {
          start: new Date(d.getFullYear(), d.getMonth() - 1, d.getDate()),
          end: new Date(),
        };
      },
    },
    {
      label: "Last 30 Days",
      value: () => ({
        start: new Date(Date.now() - 30 * 24 * 3600 * 1000),
        end: new Date(),
      }),
    },
  ];

  let open = $state<boolean>(false);
  let range = $state<DateRange>({ start: null, end: null });

  $effect(() => {
    selectedRange = { start: range.start, end: range.end };
  });

  let view = $state<ViewDate>({
    month: new Date().getMonth(),
    year: new Date().getFullYear(),
  });

  let mode = $state<"calendar" | "choose-month" | "choose-year">("calendar");

  $effect(() => {
    if (open) mode = "calendar";
  });

  const months = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
  ];
  const weekdays = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"];

  function daysInMonth(m: number, y: number) {
    return new Date(y, m + 1, 0).getDate();
  }

  function getFirstDayOfMonth(m: number, y: number) {
    const day = new Date(y, m, 1).getDay();
    return (day + 6) % 7;
  }

  function stripTime(d: Date) {
    return new Date(d.getFullYear(), d.getMonth(), d.getDate());
  }

  function applyPreset(p: DatePreset) {
    const tempRange = p.value();

    const clampStart = tempRange.start ? clampToBounds(tempRange.start) : null;
    const clampEnd = tempRange.end ? clampToBounds(tempRange.end) : null;

    range = { start: clampStart, end: clampEnd };

    open = false;
  }

  function handleSelectPreset(e: Event) {
    const value = (e.target as HTMLSelectElement).value;
    if (value === "") return;
    const index = Number(value);
    if (!isNaN(index)) applyPreset(presets[index]);
    (e.target as HTMLSelectElement).value = "";
  }

  function clearRange() {
    range = { start: null, end: null };
  }

  function clampToBounds(d: Date) {
    let date = stripTime(d);

    if (minDate && date < stripTime(minDate)) date = stripTime(minDate);
    if (maxDate && date > stripTime(maxDate)) date = stripTime(maxDate);

    return date;
  }

  const canGoPrevMonth = $derived.by(() => {
    if (!minDate) return true;
    if (view.year > minYear) return true;
    return view.year === minYear && view.month > minDate.getMonth();
  });

  const canGoNextMonth = $derived.by(() => {
    if (!maxDate) return true;
    if (view.year < maxYear) return true;
    return view.year === maxYear && view.month < maxDate.getMonth();
  });

  function changeMonth(delta: number) {
    let newMonth = view.month + delta;
    let newYear = view.year;

    if (newMonth < 0) {
      newMonth = 11;
      newYear--;
    }
    if (newMonth > 11) {
      newMonth = 0;
      newYear++;
    }

    // Clamp to min/max year
    if (newYear < minYear) {
      newYear = minYear;
      newMonth = minDate!.getMonth();
    }
    if (newYear > maxYear) {
      newYear = maxYear;
      newMonth = maxDate!.getMonth();
    }

    // Clamp month in boundary years
    if (newYear === minYear && newMonth < minDate!.getMonth()) {
      newMonth = minDate!.getMonth();
    }
    if (newYear === maxYear && newMonth > maxDate!.getMonth()) {
      newMonth = maxDate!.getMonth();
    }

    view.year = newYear;
    view.month = newMonth;
  }

  function formatDate(date: Date | null) {
    if (!date) return "";
    const y = date.getFullYear();
    const m = String(date.getMonth() + 1).padStart(2, "0");
    const d = String(date.getDate()).padStart(2, "0");
    return `${y}-${m}-${d}`;
  }

  const yearOptions = $derived(
    Array.from({ length: 21 }, (_, i) => view.year - 10 + i).filter(
      (y) => y >= minYear && y <= maxYear,
    ),
  );

  function getISOWeekNumber(date: Date) {
    const d = new Date(date.getFullYear(), date.getMonth(), date.getDate());
    d.setHours(0, 0, 0, 0);
    d.setDate(d.getDate() + 4 - (d.getDay() || 7));
    const yearStart = new Date(d.getFullYear(), 0, 1);
    const weekNo = Math.ceil(
      ((d.getTime() - yearStart.getTime()) / 86400000 + 1) / 7,
    );
    return weekNo;
  }

  function cellToDate(c: CalendarCell): Date {
    return stripTime(new Date(c.year, c.month, c.day));
  }

  function isDisabledCell(c: CalendarCell) {
    if (!c.isCurrentMonth) return true;
    const d = cellToDate(c);
    if (minDate && d < stripTime(minDate)) return true;
    if (maxDate && d > stripTime(maxDate)) return true;
    return false;
  }

  function clickDayCell(c: CalendarCell) {
    if (isDisabledCell(c)) return;

    const date = cellToDate(c);

    if (!range.start || (range.start && range.end)) {
      range = { start: date, end: null };
    } else {
      if (date >= range.start) {
        range.end = date;
      } else {
        range = { start: date, end: range.start };
      }
      open = false;
    }
  }

  const calendarWeeks = $derived.by(() => {
    const weeks: Week[] = [];

    const { year, month } = view;

    const firstDay = getFirstDayOfMonth(month, year);
    const daysThisMonth = daysInMonth(month, year);

    const prevMonth = month === 0 ? 11 : month - 1;
    const prevYear = month === 0 ? year - 1 : year;
    const daysPrevMonth = daysInMonth(prevMonth, prevYear);

    let dayCounter = 1 - firstDay;
    for (let w = 0; w < 6; w++) {
      const days: CalendarCell[] = [];

      for (let i = 0; i < 7; i++) {
        let displayDate: number;
        let cellMonth = month;
        let cellYear = year;

        if (dayCounter < 1) {
          displayDate = daysPrevMonth + dayCounter;
          cellMonth = prevMonth;
          cellYear = prevYear;
        } else if (dayCounter > daysThisMonth) {
          displayDate = dayCounter - daysThisMonth;
          cellMonth = month === 11 ? 0 : month + 1;
          cellYear = month === 11 ? year + 1 : year;
        } else {
          displayDate = dayCounter;
        }

        days.push({
          day: displayDate,
          month: cellMonth,
          year: cellYear,
          isCurrentMonth: cellMonth == month,
        });

        dayCounter++;
      }
      const weekNumber = getISOWeekNumber(
        new Date(days[0].year, days[0].month, days[0].day),
      );

      weeks.push({ weekNumber, days });
    }

    return weeks;
  });

  function isStartCell(c: CalendarCell) {
    if (!range.start) return false;
    const d = cellToDate(c);
    const start = stripTime(range.start);

    if (!range.end && hoverDate && hoverDate < start) {
      return d.getTime() === hoverDate.getTime();
    }
    return d.getTime() === start.getTime();
  }

  function isEndCell(c: CalendarCell) {
    const d = cellToDate(c);
    if (range.end) return d.getTime() === stripTime(range.end).getTime();

    if (range.start && !range.end && hoverDate) {
      const start = stripTime(range.start);
      if (hoverDate > start) return d.getTime() === hoverDate.getTime();
      if (hoverDate < start) return d.getTime() === start.getTime();
    }
    return false;
  }

  function isInRangeCell(c: CalendarCell) {
    if (isDisabledCell(c)) return false;
    const d = cellToDate(c);
    const start = range.start ? stripTime(range.start) : null;
    const end = range.end ? stripTime(range.end) : hoverDate;

    if (!start || !end) return false;
    const from = start < end ? start : end;
    const to = start < end ? end : start;
    return d > from && d < to;
  }

  function repositionCalendar(node: HTMLElement) {
    function recheck() {
      node.style.left = "auto";
      node.style.right = "0";

      const rect = node.getBoundingClientRect();
      const containerRect = container?.getBoundingClientRect();

      if (rect.right > window.innerWidth) {
        node.style.left = "auto";
        node.style.right = "0";
      }

      if (containerRect && rect.left < containerRect.left) {
        node.style.left = "0";
        node.style.right = "auto";
      }
    }

    const container = node.closest(".datepicker")?.parentElement;
    const observer = new ResizeObserver(recheck);

    if (container) observer.observe(container);
    recheck();

    return () => observer.disconnect();
  }
</script>

<div class="datepicker">
  <Input
    placeholder="Date interval"
    value={range.start && range.end
      ? `${formatDate(range.start)} - ${formatDate(range.end)}`
      : range.start
        ? `${formatDate(range.start)} - `
        : ""}
    suffixWidth="1rem"
  >
    {#snippet suffix()}
      <button
        type="button"
        class="calendar-toggle"
        onclick={() => (open = !open)}
      >
        <MdiCalendarMonthOutline width="1rem" />
      </button>
    {/snippet}
  </Input>

  {#if open}
    <div class="calendar-wrapper" {@attach repositionCalendar}>
      <!-- PRESETS DROPDOWN -->
      <label>
        Presets
        <select class="preset-select" onchange={handleSelectPreset}>
          {#each presets as preset, i}
            <option value={i}>{preset.label}</option>
          {/each}
        </select>
      </label>

      <!-- HEADER -->
      <div class="header">
        {#if mode === "calendar"}
          <button
            class="arrow"
            onclick={() => changeMonth(-1)}
            disabled={!canGoPrevMonth}>◀</button
          >
        {/if}

        <span class="month-year">
          <button
            type="button"
            class="month"
            onclick={() => (mode = "choose-month")}
          >
            {months[view.month]}
          </button>
          <button
            type="button"
            class="year"
            onclick={() => (mode = "choose-year")}
          >
            {view.year}
          </button>
        </span>

        {#if mode === "calendar"}
          <button
            class="arrow"
            onclick={() => changeMonth(1)}
            disabled={!canGoNextMonth}>▶</button
          >
        {/if}
      </div>

      <!-- MONTH PICKER -->
      {#if mode === "choose-month"}
        <div class="month-grid">
          {#each months as m, i}
            <button
              class="month-option"
              onclick={() => {
                view.month = i;
                mode = "calendar";
              }}
            >
              {m}
            </button>
          {/each}
        </div>
      {/if}

      <!-- YEAR PICKER -->
      {#if mode === "choose-year"}
        <div class="year-grid">
          {#each yearOptions as y}
            <button
              class="year-option"
              onclick={() => {
                view.year = y;

                // clamp month if necessary
                if (view.year === minYear && view.month < minDate!.getMonth())
                  view.month = minDate!.getMonth();
                if (view.year === maxYear && view.month > maxDate!.getMonth())
                  view.month = maxDate!.getMonth();

                mode = "calendar";
              }}
            >
              {y}
            </button>
          {/each}
        </div>
      {/if}

      <!-- CALENDAR -->
      {#if mode === "calendar"}
        <div
          class="calendar-grid"
          role="presentation"
          onmouseleave={() => (hoverDate = null)}
        >
          <!-- Header row with week number label and weekdays -->
          <div class="calendar-header">
            <div class="week-number-header">Wk</div>
            {#each weekdays as day}
              <div class="weekday">{day}</div>
            {/each}
          </div>

          <!-- Each week row with week number and days -->
          {#each calendarWeeks as week}
            <div class="week-row">
              <div class="week-number">{week.weekNumber}</div>
              {#each week.days as day}
                <button
                  class="day"
                  class:start={isStartCell(day)}
                  class:end={isEndCell(day)}
                  class:in-range={isInRangeCell(day)}
                  class:other-month={!day.isCurrentMonth}
                  disabled={isDisabledCell(day)}
                  onclick={() => clickDayCell(day)}
                  onmouseenter={() => {
                    if (range.start && !range.end && !isDisabledCell(day)) {
                      hoverDate = cellToDate(day);
                    }
                  }}
                  aria-current={day.isCurrentMonth ? "date" : undefined}
                >
                  {day.day}
                </button>
              {/each}
            </div>
          {/each}
        </div>
      {/if}
    </div>
  {/if}
</div>

<style>
  :root {
    --cell-size: 2rem;
  }

  .datepicker {
    position: relative;
  }

  .calendar-toggle {
    display: flex;
    align-items: center;
    background: none;
    border: none;
    cursor: pointer;
    color: inherit;
  }

  .calendar-wrapper {
    position: absolute;
    top: 100%;
    right: 0;
    padding: var(--size-lg);
    margin-top: var(--size-md);
    border: 1px solid #ccc;
    border-radius: var(--size-md);
    background-color: oklch(var(--color-accent));
    z-index: 1;
  }

  .header {
    display: flex;
    justify-content: center;
    align-items: center;
    margin-bottom: 6px;
  }

  .preset-select {
    background-color: oklch(var(--color-secondary));
    color: inherit;
    border-radius: var(--size-sm);
  }

  .month-year {
    cursor: default;
    font-weight: 600;
  }

  .month,
  .year {
    cursor: pointer;
    background: none;
    border: none;
    font: inherit;
    color: inherit;
  }
  .arrow {
    cursor: pointer;
    background: none;
    border: none;
    color: inherit;
  }
  .arrow:disabled {
    opacity: 0.3;
    cursor: not-allowed;
  }

  /* Calendar grid structure */
  .calendar-grid {
    display: flex;
    flex-direction: column;
  }

  .calendar-header {
    display: grid;
    grid-template-columns: repeat(8, auto);
  }

  .week-number-header {
    text-align: center;
    font-weight: bold;
    font-size: var(--text-xs);
    width: var(--text-xl);
    border-right: 1px solid oklch(var(--color-text));
  }

  .weekday {
    text-align: center;
    font-weight: bold;
    font-size: var(--text-xs);
    width: var(--cell-size);
    border-bottom: 1px solid oklch(var(--color-text));
  }

  .week-row {
    display: grid;
    grid-template-columns: repeat(8, auto);
  }

  .week-number {
    display: flex;
    align-items: center;
    justify-content: center;
    width: var(--text-xl);
    text-align: center;
    font-weight: bold;
    font-size: var(--text-2xs);
    border-right: 1px solid oklch(var(--color-text));
  }

  .day {
    all: unset;
    position: relative;
    text-align: center;
    cursor: point;
    width: var(--cell-size);
    height: var(--cell-size);
    margin-top: var(--size-sm);
  }

  .day.in-range::after {
    content: "";
    position: absolute;
    inset: 0;
    z-index: -1;
    background: oklch(var(--color-secondary) / 0.5);
  }

  .day.start,
  .day.end {
    background: oklch(var(--color-secondary));
    border-radius: 50%;
    aspect-ratio: 1;
  }

  .day.start::after {
    content: "";
    position: absolute;
    inset: 0;
    z-index: -1;
    background: oklch(var(--color-secondary) / 0.5);
    border-top-left-radius: 50%;
    border-bottom-left-radius: 50%;
  }

  .day.end::after {
    content: "";
    position: absolute;
    inset: 0;
    z-index: -1;
    background: oklch(var(--color-secondary) / 0.5);
    border-top-right-radius: 50%;
    border-bottom-right-radius: 50%;
  }

  .day:hover:not(:disabled) {
    background: oklch(var(--color-secondary));
    border-radius: 50%;
    aspect-ratio: 1;
  }

  .day:disabled {
    opacity: 0.1;
    cursor: not-allowed;
  }

  .month-grid,
  .year-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: var(--size-md);
  }

  .month-option,
  .year-option {
    border: none;
    background: none;
    color: oklch(var(--color-text));
    cursor: pointer;
  }

  .month-option:hover,
  .year-option:hover {
    background: oklch(var(--color-secondary) / 0.5);
  }
</style>
