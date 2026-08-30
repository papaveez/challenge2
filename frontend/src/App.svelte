<script>
  import { onMount } from 'svelte';
  import { api, getToken, setToken } from './lib/api.js';
  import Auth from './lib/Auth.svelte';
  import Dashboard from './lib/Dashboard.svelte';

  let me = null;
  let checking = !!getToken();

  onMount(async () => {
    if (!getToken()) return;
    try {
      me = await api('/api/me');
    } catch {
      setToken(null);
    } finally {
      checking = false;
    }
  });

  function handleLogin(event) {
    setToken(event.detail.token);
    me = event.detail.user;
  }

  function handleLogout() {
    setToken(null);
    me = null;
  }
</script>

{#if checking}
  <main class="center"><p class="muted">Loading…</p></main>
{:else if !me}
  <Auth on:login={handleLogin} />
{:else}
  <Dashboard {me} on:logout={handleLogout} />
{/if}

<style>
  .center {
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 100vh;
  }
</style>
