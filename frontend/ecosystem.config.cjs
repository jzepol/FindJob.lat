/**
 * PM2 — Findjob.lat Frontend (Next.js)
 *
 * Uso (desde frontend/):
 *   npm run build
 *   pm2 start ecosystem.config.cjs --env production
 *   pm2 save
 *
 * Deploy:
 *   cd /var/www/Findjob/FindJob.lat && bash scripts/deploy/deploy-app.sh
 */
module.exports = {
  apps: [
    {
      name: "findjob-web",
      script: "node_modules/next/dist/bin/next",
      args: "start",
      cwd: __dirname,
      instances: 1,
      exec_mode: "fork",
      autorestart: true,
      watch: false,
      max_memory_restart: "1G",
      time: true,
      merge_logs: true,
      log_date_format: "YYYY-MM-DD HH:mm:ss Z",
      error_file: "logs/pm2-error.log",
      out_file: "logs/pm2-out.log",
      env: {
        NODE_ENV: "development",
        PORT: 3001,
      },
      env_production: {
        NODE_ENV: "production",
        PORT: 3001,
      },
    },
  ],
};