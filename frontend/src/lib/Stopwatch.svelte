<script>
  import { onDestroy } from 'svelte';

  export let event;

  let now = Date.now() / 1000;
  const timer = setInterval(() => (now = Date.now() / 1000), 1000);
  onDestroy(() => clearInterval(timer));

  $: elapsed = event.started_at
    ? Math.max(0, (event.ended_at ?? now) - event.started_at)
    : 0;

  function format(totalSeconds) {
    const s = Math.floor(totalSeconds);
    const days = Math.floor(s / 86400);
    const hours = Math.floor((s % 86400) / 3600);
    const minutes = Math.floor((s % 3600) / 60);
    const seconds = s % 60;
    const pad = (n) => String(n).padStart(2, '0');
    return (days > 0 ? `${days}d ` : '') + `${pad(hours)}:${pad(minutes)}:${pad(seconds)}`;
  }
</script>

<div class="stopwatch" class:running={event.started_at && !event.ended_at}>
  {#if !event.started_at}
    <span class="muted">Not started</span>
  {:else}
    <span class="time">{format(elapsed)}</span>
    {#if event.ended_at}<span class="muted">final</span>{/if}
  {/if}
</div>

<style>
  .stopwatch {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 0.5rem 1rem;
    font-variant-numeric: tabular-nums;
    display: flex;
    align-items: baseline;
    gap: 0.5rem;
  }
  .stopwatch.running { border-color: var(--accent-2); }
  .time { font-size: 1.3rem; font-weight: 700; }
</style>
