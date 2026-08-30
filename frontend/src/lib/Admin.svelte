<script>
  import { createEventDispatcher } from 'svelte';
  import { api } from './api.js';

  export let state;
  const dispatch = createEventDispatcher();

  let name = '';
  let unit = '';
  let baseAmount = '';
  let perPerson = true;
  let error = '';
  let busy = false;

  function fmt(n) {
    return Number.isInteger(n) ? n : Number(n.toFixed(2));
  }

  async function run(fn) {
    error = '';
    busy = true;
    try {
      await fn();
      dispatch('changed');
    } catch (e) {
      error = e.message;
    } finally {
      busy = false;
    }
  }

  const createChallenge = () =>
    run(async () => {
      await api('/api/challenges', {
        method: 'POST',
        body: { name, unit, base_amount: Number(baseAmount), per_person: perPerson }
      });
      name = unit = baseAmount = '';
      perPerson = true;
    });

  const deleteChallenge = (challenge) =>
    confirm(`Delete "${challenge.name}" and all its contributions?`) &&
    run(() => api(`/api/challenges/${challenge.id}`, { method: 'DELETE' }));

  const startEvent = () =>
    confirm('Start the challenge? The stopwatch begins now.') &&
    run(() => api('/api/event/start', { method: 'POST' }));

  const stopEvent = () =>
    confirm('Stop the challenge? The stopwatch freezes and contributions close.') &&
    run(() => api('/api/event/stop', { method: 'POST' }));

  const resetEvent = () =>
    confirm('Reset EVERYTHING? This deletes all contributions and the timer.') &&
    run(() => api('/api/event/reset', { method: 'POST' }));
</script>

<div class="stack">
  <div class="card">
    <h2>Event</h2>
    <div class="row">
      {#if !state.event.started_at}
        <button on:click={startEvent} disabled={busy}>▶ Start challenge</button>
      {:else if !state.event.ended_at}
        <button class="danger" on:click={stopEvent} disabled={busy}>⏹ Stop challenge</button>
      {/if}
      <button class="secondary" on:click={resetEvent} disabled={busy}>Reset everything</button>
    </div>
  </div>

  <div class="card">
    <h2>New challenge</h2>
    <form on:submit|preventDefault={createChallenge}>
      <input placeholder="Name (e.g. Bananas)" bind:value={name} required />
      <input placeholder="Unit (e.g. bananas, wins)" bind:value={unit} required />
      <input type="number" step="any" min="0" placeholder="Amount" bind:value={baseAmount} required />
      <label class="checkbox">
        <input type="checkbox" bind:checked={perPerson} />
        per person (target = amount × participants)
      </label>
      <button type="submit" disabled={busy || !name || !unit || !baseAmount}>Create</button>
    </form>
    <p class="muted">
      With {state.n_participants} participants, "10 per person" means a target of
      {10 * state.n_participants}. Untick for a fixed total (e.g. 1 minecraft finish).
    </p>
  </div>

  <div class="card">
    <h2>Challenges</h2>
    {#if state.challenges.length === 0}
      <p class="muted">None yet.</p>
    {:else}
      <ul>
        {#each state.challenges as ch (ch.id)}
          <li>
            <span>
              <strong>{ch.name}</strong> — {fmt(ch.base_amount)} {ch.unit}
              {ch.per_person ? `per person (target ${fmt(ch.target)})` : '(fixed total)'}
            </span>
            <button class="danger small" on:click={() => deleteChallenge(ch)} disabled={busy}>Delete</button>
          </li>
        {/each}
      </ul>
    {/if}
  </div>

  {#if error}<p class="error">{error}</p>{/if}
</div>

<style>
  .stack { display: flex; flex-direction: column; gap: 1rem; }
  .row { display: flex; gap: 0.75rem; flex-wrap: wrap; }
  form { display: flex; flex-direction: column; gap: 0.75rem; max-width: 420px; margin-bottom: 0.75rem; }
  .checkbox { display: flex; align-items: center; gap: 0.5rem; color: var(--muted); }
  .checkbox input { width: auto; }
  ul { list-style: none; margin: 0; padding: 0; }
  li {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 1rem;
    padding: 0.5rem 0;
    border-bottom: 1px solid var(--border);
  }
  li:last-child { border-bottom: none; }
</style>
