<script>
  import { createEventDispatcher } from 'svelte';
  import { api } from './api.js';

  export let challenge;
  export let me;
  export let event;

  const dispatch = createEventDispatcher();

  let amount = '';
  let photoInput;
  let error = '';
  let busy = false;
  let showAll = false;

  $: active = event.started_at && !event.ended_at;
  $: pct = challenge.target > 0 ? Math.min(100, (challenge.done / challenge.target) * 100) : 0;
  $: complete = challenge.done >= challenge.target && challenge.target > 0;
  $: visibleContributions = showAll ? challenge.contributions : challenge.contributions.slice(0, 5);

  function fmt(n) {
    return Number.isInteger(n) ? n : Number(n.toFixed(2));
  }

  async function contribute() {
    error = '';
    busy = true;
    try {
      const form = new FormData();
      form.append('challenge_id', challenge.id);
      form.append('amount', amount);
      const file = photoInput?.files?.[0];
      if (file) form.append('photo', file);
      await api('/api/contributions', { method: 'POST', body: form });
      amount = '';
      if (photoInput) photoInput.value = '';
      dispatch('changed');
    } catch (e) {
      error = e.message;
    } finally {
      busy = false;
    }
  }

  async function removeContribution(id) {
    if (!confirm('Delete this contribution?')) return;
    try {
      await api(`/api/contributions/${id}`, { method: 'DELETE' });
      dispatch('changed');
    } catch (e) {
      error = e.message;
    }
  }
</script>

<div class="card" class:complete>
  <div class="top">
    <div>
      <h3>{challenge.name} {complete ? '✅' : ''}</h3>
      <p class="muted">
        Target: {fmt(challenge.target)} {challenge.unit}
        {#if challenge.per_person}({fmt(challenge.base_amount)} per person){/if}
      </p>
    </div>
    <div class="count">{fmt(challenge.done)} / {fmt(challenge.target)}</div>
  </div>

  <div class="bar"><div class="fill" style="width: {pct}%"></div></div>

  {#if active}
    <form on:submit|preventDefault={contribute}>
      <input type="number" step="any" min="0" placeholder="Amount" bind:value={amount} required />
      <input type="file" accept="image/*" bind:this={photoInput} />
      <button type="submit" disabled={busy || !amount}>Add</button>
    </form>
    {#if error}<p class="error">{error}</p>{/if}
  {/if}

  {#if challenge.contributions.length > 0}
    <ul class="contributions">
      {#each visibleContributions as c (c.id)}
        <li>
          <span><strong>{c.username}</strong> +{fmt(c.amount)} {challenge.unit}</span>
          <span class="right">
            {#if c.photo}
              <a href={c.photo} target="_blank" rel="noreferrer">
                <img src={c.photo} alt="proof from {c.username}" />
              </a>
            {/if}
            <span class="muted when">{new Date(c.created_at * 1000).toLocaleString()}</span>
            {#if c.user_id === me.id || me.is_master}
              <button class="danger small" on:click={() => removeContribution(c.id)}>✕</button>
            {/if}
          </span>
        </li>
      {/each}
    </ul>
    {#if challenge.contributions.length > 5}
      <button class="secondary small" on:click={() => (showAll = !showAll)}>
        {showAll ? 'Show less' : `Show all ${challenge.contributions.length}`}
      </button>
    {/if}
  {/if}
</div>

<style>
  .card.complete { border-color: var(--accent-2); }
  .top { display: flex; justify-content: space-between; gap: 1rem; align-items: flex-start; }
  .count { font-size: 1.2rem; font-weight: 700; white-space: nowrap; }
  .bar {
    height: 10px;
    background: var(--panel-2);
    border-radius: 5px;
    overflow: hidden;
    margin: 0.75rem 0;
  }
  .fill { height: 100%; background: var(--accent); transition: width 0.4s; }
  .complete .fill { background: var(--accent-2); }
  form { display: flex; gap: 0.5rem; flex-wrap: wrap; margin: 0.5rem 0; }
  form input[type='number'] { width: 110px; }
  form input[type='file'] { flex: 1; min-width: 180px; }
  .contributions { list-style: none; margin: 0.75rem 0 0.5rem; padding: 0; }
  .contributions li {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 0.5rem;
    padding: 0.4rem 0;
    border-bottom: 1px solid var(--border);
    flex-wrap: wrap;
  }
  .contributions li:last-child { border-bottom: none; }
  .right { display: flex; align-items: center; gap: 0.6rem; }
  .right img {
    height: 36px;
    width: 36px;
    object-fit: cover;
    border-radius: 6px;
    display: block;
  }
  .when { font-size: 0.8rem; }
</style>
