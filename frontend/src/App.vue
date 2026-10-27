<script setup lang="ts">
import { onMounted, ref } from 'vue'

interface Ticket {
  id: number
  description: string
  category: string | null
  priority: string | null
  summary: string | null
}

const ticketsUrl = 'http://127.0.0.1:8000/tickets'
const description = ref('')
const tickets = ref<Ticket[]>([])
const loading = ref(true)
const submitting = ref(false)
const loadError = ref('')
const submitError = ref('')

async function loadTickets() {
  try {
    const response = await fetch(ticketsUrl)
    if (!response.ok) throw new Error('Error al consultar las solicitudes')
    tickets.value = await response.json()
  } catch {
    loadError.value = 'No se pudieron cargar las solicitudes. Comprobá que el backend esté en ejecución y recargá la página.'
  } finally {
    loading.value = false
  }
}

async function createTicket() {
  const text = description.value.trim()
  if (!text || loading.value || loadError.value || submitting.value) return

  submitting.value = true
  submitError.value = ''
  try {
    const response = await fetch(ticketsUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ description: text }),
    })
    if (!response.ok) throw new Error('Error al crear la solicitud')
    const ticket: Ticket = await response.json()
    tickets.value.push(ticket)
    description.value = ''
  } catch {
    submitError.value = 'No se pudo confirmar la creación. Comprobá la conexión y recargá la lista antes de reintentar.'
  } finally {
    submitting.value = false
  }
}

onMounted(loadTickets)
</script>

<template>
  <main>
    <header>
      <h1>MiniDesk AI</h1>
      <p>Escribí una solicitud y consultá las que ya guardaste.</p>
    </header>

    <section aria-labelledby="new-ticket-title">
      <h2 id="new-ticket-title">Nueva solicitud</h2>
      <form @submit.prevent="createTicket">
        <label for="description">Descripción</label>
        <textarea
          id="description"
          v-model="description"
          rows="5"
          required
          maxlength="5000"
          :disabled="submitting"
          placeholder="Por ejemplo: no puedo acceder al correo."
        ></textarea>
        <button
          type="submit"
          :disabled="loading || !!loadError || submitting || !description.trim()"
        >
          {{ submitting ? 'Guardando…' : 'Crear solicitud' }}
        </button>
        <p v-if="submitError" role="alert" class="error">{{ submitError }}</p>
      </form>
    </section>

    <section aria-labelledby="tickets-title" :aria-busy="loading">
      <h2 id="tickets-title">Solicitudes guardadas</h2>
      <p v-if="loading" role="status">Cargando solicitudes…</p>
      <p v-else-if="loadError" role="alert" class="error">{{ loadError }}</p>
      <p v-else-if="tickets.length === 0">Todavía no hay solicitudes. Creá la primera con el formulario.</p>
      <ul v-else>
        <li v-for="ticket in tickets" :key="ticket.id">
          <span class="ticket-id">Solicitud #{{ ticket.id }}</span>
          <p class="description">{{ ticket.description }}</p>
        </li>
      </ul>
    </section>
  </main>
</template>

<style scoped>
:global(body) {
  margin: 0;
  background: #f3f6fa;
  color: #172c44;
  font-family: 'Segoe UI', sans-serif;
  line-height: 1.5;
}

main {
  max-width: 720px;
  margin: 0 auto;
  padding: 32px 20px;
}

h1 { margin: 0; font-size: 2rem; letter-spacing: -0.04em; }
h2 { margin: 0 0 16px; font-size: 1.2rem; }
header { margin-bottom: 28px; }
header p { margin: 8px 0 0; }
section { margin-top: 24px; padding: 24px; background: #fff; border: 1px solid #d4deea; border-radius: 8px; }
label { display: block; margin-bottom: 8px; font-weight: 600; }
textarea { box-sizing: border-box; width: 100%; padding: 12px; border: 1px solid #70829a; border-radius: 4px; resize: vertical; font: inherit; }
button { margin-top: 12px; padding: 10px 18px; border: 0; border-radius: 4px; background: #245da8; color: #fff; font: inherit; font-weight: 600; cursor: pointer; }
button:hover:not(:disabled) { background: #19477f; }
button:disabled { opacity: 0.55; cursor: not-allowed; }
textarea:focus-visible, button:focus-visible { outline: 3px solid #245da8; outline-offset: 3px; }
ul { margin: 0; padding: 0; list-style: none; }
li + li { margin-top: 16px; padding-top: 16px; border-top: 1px solid #d4deea; }
.ticket-id { color: #52657d; font-family: Consolas, monospace; font-size: 0.85rem; }
.description { margin: 6px 0 0; white-space: pre-wrap; overflow-wrap: anywhere; }
.error { color: #a12c2c; }
</style>
