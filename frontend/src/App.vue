<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { createBijiangSite } from './bijiang/site.js'

const siteRoot = ref(null)
const toastRoot = ref(null)
let destroySite

onMounted(() => {
  destroySite = createBijiangSite(siteRoot.value, toastRoot.value)
})

onBeforeUnmount(() => destroySite?.())
</script>

<template>
  <svg class="svg-sprite" aria-hidden="true">
    <symbol id="i-home" viewBox="0 0 24 24"><path d="m3 10 9-7 9 7v10a1 1 0 0 1-1 1h-5v-7H9v7H4a1 1 0 0 1-1-1Z" /></symbol>
    <symbol id="i-compass" viewBox="0 0 24 24"><circle cx="12" cy="12" r="9" /><path d="m15.5 8.5-2.1 4.9-4.9 2.1 2.1-4.9Z" /></symbol>
    <symbol id="i-book" viewBox="0 0 24 24"><path d="M3 5.5A3.5 3.5 0 0 1 6.5 2H11a1 1 0 0 1 1 1v18a4 4 0 0 0-4-4H3Z" /><path d="M21 5.5A3.5 3.5 0 0 0 17.5 2H13a1 1 0 0 0-1 1v18a4 4 0 0 1 4-4h5Z" /></symbol>
    <symbol id="i-user" viewBox="0 0 24 24"><circle cx="12" cy="8" r="4" /><path d="M4 22c.5-5 3-7 8-7s7.5 2 8 7" /></symbol>
    <symbol id="i-map" viewBox="0 0 24 24"><path d="m3 5 6-3 6 3 6-3v17l-6 3-6-3-6 3Z" /><path d="M9 2v17M15 5v17" /></symbol>
    <symbol id="i-stamp" viewBox="0 0 24 24"><path d="M8 13h8l3 4v3H5v-3Z" /><path d="M9 13c.4-2 0-3-.7-4.3A4.5 4.5 0 1 1 17 7c0 .7-.2 1.3-.6 2-.7 1.2-.8 2-.4 4Z" /></symbol>
    <symbol id="i-arrow" viewBox="0 0 24 24"><path d="m9 5 7 7-7 7" /></symbol>
    <symbol id="i-back" viewBox="0 0 24 24"><path d="m15 5-7 7 7 7" /></symbol>
    <symbol id="i-clock" viewBox="0 0 24 24"><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></symbol>
    <symbol id="i-pin" viewBox="0 0 24 24"><path d="M20 10c0 5-8 12-8 12S4 15 4 10a8 8 0 1 1 16 0Z" /><circle cx="12" cy="10" r="2.5" /></symbol>
    <symbol id="i-walk" viewBox="0 0 24 24"><circle cx="13" cy="4" r="2" /><path d="m11 8-2 5 3 2 2 7M11 8l4 3 3 1M9 13l-3 7" /></symbol>
    <symbol id="i-star" viewBox="0 0 24 24"><path d="m12 3 2.7 5.5 6.1.9-4.4 4.3 1 6.1-5.4-2.9-5.4 2.9 1-6.1-4.4-4.3 6.1-.9Z" /></symbol>
    <symbol id="i-play" viewBox="0 0 24 24"><path d="m9 6 9 6-9 6Z" /></symbol>
    <symbol id="i-pause" viewBox="0 0 24 24"><path d="M8 6v12M16 6v12" /></symbol>
    <symbol id="i-check" viewBox="0 0 24 24"><path d="m5 12 4 4L19 6" /></symbol>
    <symbol id="i-lock" viewBox="0 0 24 24"><rect x="5" y="10" width="14" height="11" rx="2" /><path d="M8 10V7a4 4 0 0 1 8 0v3" /></symbol>
    <symbol id="i-building" viewBox="0 0 24 24"><path d="M3 21h18M5 21V10h14v11M3 10l9-6 9 6M9 21v-6h6v6" /></symbol>
    <symbol id="i-leaf" viewBox="0 0 24 24"><path d="M20 4C11 4 5 8 5 15c0 3 2 5 5 5 7 0 10-7 10-16Z" /><path d="M4 21c3-5 7-8 12-11" /></symbol>
    <symbol id="i-volume" viewBox="0 0 24 24"><path d="M4 10v4h4l5 4V6l-5 4Z" /><path d="M16 9c1.5 1.5 1.5 4.5 0 6M19 6c3.3 3.3 3.3 8.7 0 12" /></symbol>
    <symbol id="i-route" viewBox="0 0 24 24"><circle cx="6" cy="18" r="2" /><circle cx="18" cy="6" r="2" /><path d="M8 18c7 0 2-10 8-10" /></symbol>
  </svg>
  <div ref="siteRoot" />
  <div ref="toastRoot" class="toast" role="status" aria-live="polite" />
</template>
