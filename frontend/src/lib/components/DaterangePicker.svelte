<script lang="ts">
  import Input from "$lib/components/Input.svelte";

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
  }

  let { minDate = null, maxDate = new Date() }: Props = $props();

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

  let view = $state<ViewDate>({
    month: new Date().getMonth(),
    year: new Date().getFullYear(),
  });

  let mode = $state<"calendar" | "choose-month" | "choose-year">("calendar");

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
  }

  function handleSelectPreset(e: Event) {
    const index = Number((e.target as HTMLSelectElement).value);
    if (!isNaN(index)) applyPreset(presets[index]);
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
        open = false;
      } else {
        range = { start: date, end: range.start };
        open = false;
      }
    }
  }

  function isSelectedCell(c: CalendarCell) {
    if (isDisabledCell(c)) return false;

    const d = cellToDate(c);
    if (range.start && !range.end) {
      return d.getTime() === stripTime(range.start).getTime();
    }
    if (range.start && range.end) {
      return d >= stripTime(range.start) && d <= stripTime(range.end);
    }
    return false;
  }

  const calendarWeeks = $derived.by(() => {
    const weeks: Week[] = [];

    const year = view.year;
    const month = view.month;

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
</script>

<div class="datepicker">
  <div class="input-wrapper">
    <Input
      label="Date interval"
      value={range.start && range.end
        ? `${formatDate(range.start)} - ${formatDate(range.end)}`
        : range.start
          ? `${formatDate(range.start)} - `
          : ""}
    />
    <button
      type="button"
      class="calendar-toggle"
      onclick={() => (open = !open)}
    >
      📅
    </button>
  </div>

  {#if open}
    <div class="calendar-wrapper">
      <!-- PRESETS DROPDOWN -->
      <label>
        Presets
        <select onchange={handleSelectPreset}>
          {#each presets as preset, i}
            <option value={i}>{preset.label}</option>
          {/each}
        </select>
      </label>

      <!-- HEADER -->
      <div class="header">
        <button
          class="arrow"
          onclick={() => changeMonth(-1)}
          disabled={!canGoPrevMonth}>◀</button
        >

        <span class="month-year">
          <button
            type="button"
            class="month"
            onclick={() => (mode = "choose-month")}
          >
            {months[view.month]}
          </button>
          &nbsp;
          <button
            type="button"
            class="year"
            onclick={() => (mode = "choose-year")}
          >
            {view.year}
          </button>
        </span>

        <button
          class="arrow"
          onclick={() => changeMonth(1)}
          disabled={!canGoNextMonth}>▶</button
        >
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
        <div class="calendar-grid">
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
                  class:other-month={!day.isCurrentMonth}
                  class:selected={isSelectedCell(day)}
                  onclick={() => clickDayCell(day)}
                  disabled={isDisabledCell(day)}
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
  .datepicker {
    position: relative;
  }

  .input-wrapper {
    position: relative;
    display: flex;
    align-items: center;
    width: calc(21ch + 2.5rem);
  }
  .calendar-toggle {
    position: absolute;
    right: 2rem;
    background: none;
    border: none;
    cursor: pointer;
  }
  .calendar-wrapper {
    position: absolute;
    border: 1px solid #ccc;
    padding: 8px;
    border-radius: 6px;
    margin-top: 4px;
    background: white;
  }
  .header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 6px;
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
  }
  .arrow {
    cursor: pointer;
    background: none;
    border: none;
    font-size: 14px;
    padding: 4px 8px;
  }
  .arrow:disabled {
    opacity: 0.3;
    cursor: not-allowed;
  }

  /* Calendar grid structure */
  .calendar-grid {
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  .calendar-header {
    display: grid;
    grid-template-columns: 40px repeat(7, 1fr);
    gap: 2px;
    margin-bottom: 4px;
  }

  .week-number-header {
    text-align: center;
    font-weight: bold;
    font-size: 12px;
    background: #f0f0f0;
    padding: 4px;
    border-radius: 4px;
  }

  .weekday {
    text-align: center;
    font-weight: 600;
    font-size: 12px;
    padding: 4px;
  }

  .week-row {
    display: grid;
    grid-template-columns: 40px repeat(7, 1fr);
    gap: 2px;
  }

  .week-number {
    text-align: center;
    font-weight: bold;
    font-size: 11px;
    background: #f0f0f0;
    padding: 4px;
    border-radius: 4px;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .day {
    padding: 8px 4px;
    cursor: pointer;
    border-radius: 4px;
    background: #f8f8f8;
    border: 1px solid transparent;
    text-align: center;
    font-size: 13px;
  }

  .day:hover:not(:disabled) {
    background: #e8e8e8;
    border-color: #ccc;
  }

  .day.selected {
    background: #007bff;
    color: white;
  }

  .day:disabled {
    opacity: 0.3;
    cursor: not-allowed;
  }

  .month-grid,
  .year-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 6px;
    padding: 8px 0;
  }

  .month-option,
  .year-option {
    padding: 6px;
    border-radius: 4px;
    background: #efefef;
    cursor: pointer;
    border: 1px solid #ddd;
  }

  .month-option:hover,
  .year-option:hover {
    background: #e0e0e0;
  }
</style>
