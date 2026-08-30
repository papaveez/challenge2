<script>
  export let leaderboard;

  const medals = ['🥇', '🥈', '🥉'];
</script>

<div class="card">
  <h2>Leaderboard</h2>
  <p class="muted">
    Points = percentage of each challenge's target you contributed, summed across challenges.
  </p>
  {#if leaderboard.length === 0}
    <p class="muted">No participants yet.</p>
  {:else}
    <ol>
      {#each leaderboard as entry, i (entry.user_id)}
        <li>
          <span class="rank">{medals[i] ?? `${i + 1}.`}</span>
          <span class="name">{entry.username}</span>
          <span class="points">{entry.points} pts</span>
        </li>
      {/each}
    </ol>
  {/if}
</div>

<style>
  ol { list-style: none; margin: 1rem 0 0; padding: 0; }
  li {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.6rem 0.25rem;
    border-bottom: 1px solid var(--border);
    font-size: 1.05rem;
  }
  li:last-child { border-bottom: none; }
  .rank { width: 2.2rem; text-align: center; }
  .name { flex: 1; font-weight: 600; }
  .points { font-variant-numeric: tabular-nums; color: var(--accent); font-weight: 700; }
</style>
