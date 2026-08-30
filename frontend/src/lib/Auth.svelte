<script>
  import { createEventDispatcher } from 'svelte';
  import { api } from './api.js';

  const dispatch = createEventDispatcher();

  let username = '';
  let password = '';
  let error = '';
  let busy = false;

  async function submit(path) {
    error = '';
    busy = true;
    try {
      const data = await api(path, { method: 'POST', body: { username, password } });
      dispatch('login', data);
    } catch (e) {
      error = e.message;
    } finally {
      busy = false;
    }
  }
</script>

<main>
  <div class="card auth">
    <h1>🏆 The Challenge</h1>
    <p class="muted">Sign in or create an account to join.</p>
    <form on:submit|preventDefault={() => submit('/api/login')}>
      <input placeholder="Username" bind:value={username} autocomplete="username" />
      <input type="password" placeholder="Password" bind:value={password} autocomplete="current-password" />
      {#if error}<p class="error">{error}</p>{/if}
      <div class="row">
        <button type="submit" disabled={busy || !username || !password}>Log in</button>
        <button type="button" class="secondary" disabled={busy || !username || !password}
          on:click={() => submit('/api/signup')}>Sign up</button>
      </div>
    </form>
  </div>
</main>

<style>
  main {
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 100vh;
    padding: 1rem;
  }
  .auth { width: 100%; max-width: 380px; }
  form { display: flex; flex-direction: column; gap: 0.75rem; margin-top: 1rem; }
  .row { display: flex; gap: 0.75rem; }
  .row button { flex: 1; }
</style>
