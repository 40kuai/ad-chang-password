import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    // 开发环境代理后端 API，避免跨域
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8001",
        changeOrigin: true
      }
    }
  }
});
