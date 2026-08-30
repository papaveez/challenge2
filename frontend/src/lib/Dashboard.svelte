<script>
  import { createEventDispatcher, onDestroy, onMount } from 'svelte';
  import { api } from './api.js';
  import Stopwatch from './Stopwatch.svelte';
  import ChallengeCard from './ChallengeCard.svelte';
  import Leaderboard from './Leaderboard.svelte';
  import ProgressGrid from './ProgressGrid.svelte';
  import Admin from './Admin.svelte';

  export let me;
  const dispatch = createEventDispatcher();

  let state = null;
  let error = '';
  let tab = 'challenges';
  let pollTimer;

  const tabs = [
    { id: 'challenges', label: 'Challenges' },
    { id: 'leaderboard', label: 'Leaderboard' },
    { id: 'progress', label: 'Progress' }
  ];

  async function refresh() {
    try {
      state = await api('/api/state');
      error = '';
    } catch (e) {
      error = e.message;
      if (e.status === 401) dispatch('logout');
    }
  }

  onMount(() => {
    refresh();
    pollTimer = setInterval(refresh, 5000);
  });
  onDestroy(() => clearInterval(pollTimer));
</script>

<div class="page">
  <header>
    <div>
      <h1>🏆 The Challenge</h1>
      <p class="muted">
        Signed in as <strong>{me.username}</strong>{me.is_master ? ' (master)' : ''}
        · {state ? state.n_participants : '…'} participants
      </p>
    </div>
    <div class="header-right">
      {#if state}<Stopwatch event={state.event} />{/if}
      <button class="secondary small" on:click={() => dispatch('logout')}>Log out</button>
    </div>
  </header>

  {#if error}<p class="error">{error}</p>{/if}

  <nav>
    {#each tabs as t}
      <button class:active={tab === t.id} class="secondary" on:click={() => (tab = t.id)}>
        {t.label}
      </button>
    {/each}
    {#if me.is_master}
      <button class:active={tab === 'admin'} class="secondary" on:click={() => (tab = 'admin')}>
        Admin
      </button>
    {/if}
  </nav>

  {#if !state}
    <p class="muted">Loading…</p>
  {:else if tab === 'challenges'}
    {#if !state.event.started_at}
      <div class="card notice">
        ⏳ The challenge hasn't started yet.
        {#if me.is_master}Head to the Admin tab to start it.{:else}Waiting for vas to start the clock…{/if}
      </div>
    {:else if state.event.ended_at}
      <div class="card notice">🏁 The challenge is over — final results are in!</div>
    {/if}
    {#if state.challenges.length === 0}
      <p class="muted">No challenges yet.</p>
    {/if}
    <div class="challenge-list">
      {#each state.challenges as challenge (challenge.id)}
        <ChallengeCard {challenge} {me} event={state.event} on:changed={refresh} />
      {/each}
    </div>
  {:else if tab === 'leaderboard'}
    <Leaderboard leaderboard={state.leaderboard} />
  {:else if tab === 'progress'}
    <ProgressGrid {state} />
  {:else if tab === 'admin'}
    <Admin {state} on:changed={refresh} />
  {/if}
</div>

<style>
  .page {
    max-width: 900px;
    margin: 0 auto;
    padding: 1.5rem 1rem 4rem;
    display: flex;
    flex-direction: column;
    gap: 1.25rem;
  }
  header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 1rem;
    flex-wrap: wrap;
  }
  .header-right {
    display: flex;
    align-items: center;
    gap: 1rem;
    flex-wrap: wrap;
  }
  nav { display: flex; gap: 0.5rem; flex-wrap: wrap; }
  nav button.active { background: var(--accent); color: #1a1400; border-color: var(--accent); }
  .challenge-list { display: flex; flex-direction: column; gap: 1rem; }
  .notice { margin-bottom: 1rem; }
</style>
