<script>
  export let state;

  function fmt(n) {
    return Number.isInteger(n) ? n : Number(n.toFixed(2));
  }

  function amountFor(entry, challengeId) {
    return entry.per_challenge[String(challengeId)] ?? 0;
  }
</script>

<div class="card">
  <h2>Progress by person</h2>
  <p class="muted">How much of each challenge everyone has done.</p>
  {#if state.challenges.length === 0}
    <p class="muted">No challenges yet.</p>
  {:else}
    <div class="overflow-x">
      <table>
        <thead>
          <tr>
            <th>Person</th>
            {#each state.challenges as ch (ch.id)}
              <th>{ch.name}<br /><span class="muted">/ {fmt(ch.target)} {ch.unit}</span></th>
            {/each}
          </tr>
        </thead>
        <tbody>
          {#each state.leaderboard as entry (entry.user_id)}
            <tr>
              <td><strong>{entry.username}</strong></td>
              {#each state.challenges as ch (ch.id)}
                {@const amount = amountFor(entry, ch.id)}
                <td class:zero={amount === 0}>
                  {fmt(amount)}
                  {#if ch.target > 0}
                    <span class="muted pct">({Math.round((amount / ch.target) * 100)}%)</span>
                  {/if}
                </td>
              {/each}
            </tr>
          {/each}
          <tr class="total">
            <td>Total</td>
            {#each state.challenges as ch (ch.id)}
              <td>{fmt(ch.done)} <span class="muted pct">({Math.round(ch.target > 0 ? (ch.done / ch.target) * 100 : 0)}%)</span></td>
            {/each}
          </tr>
        </tbody>
      </table>
    </div>
  {/if}
</div>

<style>
  .zero { color: var(--muted); }
  .pct { font-size: 0.8rem; }
  .total td { font-weight: 700; border-top: 2px solid var(--border); }
</style>
