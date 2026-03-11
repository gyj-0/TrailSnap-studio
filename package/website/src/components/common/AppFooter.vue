<template>
  <el-footer class="app-footer" height="40px">
    <div class="footer-content">
      <span class="copyright">
        &copy; {{ currentYear }} TrailSnap. All rights reserved.
      </span>
      <span class="version">
        v{{ version }}
      </span>
    </div>
  </el-footer>
</template>

<script setup lang="ts">
const currentYear = new Date().getFullYear()
const version = import.meta.env.VITE_APP_VERSION || '1.0.0'
</script>

<style scoped>
.app-footer {
  background: var(--bg-base);
  border-top: 1px solid var(--border-lighter);
  padding: 0 20px;
}

.footer-content {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 12px;
  color: var(--text-secondary);
}

.copyright {
  opacity: 0.8;
}

.version {
  font-family: monospace;
}
</style>
