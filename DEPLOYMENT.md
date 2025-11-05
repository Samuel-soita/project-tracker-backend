# Deployment Guide - Render

This guide explains how to deploy the Project Tracker Backend to Render.

## Prerequisites

- A [Render account](https://render.com)
- Your code pushed to a Git repository (GitHub, GitLab, or Bitbucket)
- Environment variables ready (SendGrid API key, Cloudinary credentials, etc.)

## Quick Deploy

### Option 1: Using render.yaml (Recommended)

1. Push your code to your Git repository
2. Go to [Render Dashboard](https://dashboard.render.com)
3. Click "New" → "Blueprint"
4. Connect your repository
5. Render will automatically detect `render.yaml` and set up:
   - Web Service (Flask backend)
   - PostgreSQL Database

### Option 2: Manual Setup

#### Step 1: Create PostgreSQL Database

1. In Render Dashboard, click "New" → "PostgreSQL"
2. Configure:
   - Name: `project-tracker-db`
   - Database: `project_tracker`
   - User: `project_tracker_user`
   - Plan: Choose based on your needs (Free tier available)
3. Click "Create Database"
4. Copy the "Internal Database URL" for next step

#### Step 2: Create Web Service

1. Click "New" → "Web Service"
2. Connect your repository
3. Configure:
   - Name: `project-tracker-backend`
   - Runtime: `Python 3`
   - Build Command: `./build.sh`
   - Start Command: `gunicorn -w 4 -b 0.0.0.0:$PORT run:app`

#### Step 3: Set Environment Variables

Add the following environment variables in your web service settings:

**Required:**
- `DATABASE_URL` - Use the Internal Database URL from your PostgreSQL instance
- `SECRET_KEY` - Generate a secure random key

**Optional (based on your features):**
- `CLOUDINARY_CLOUD_NAME` - Your Cloudinary cloud name
- `CLOUDINARY_API_KEY` - Your Cloudinary API key
- `CLOUDINARY_API_SECRET` - Your Cloudinary API secret
- `SENDGRID_API_KEY` - Your SendGrid API key for emails
- `FRONTEND_URL` - Your frontend URL for CORS (e.g., https://your-app.netlify.app)

#### Step 4: Deploy

1. Click "Create Web Service"
2. Render will automatically:
   - Install dependencies from `requirements.txt` (build phase)
   - Run database migrations via `preDeployCommand` (pre-deploy phase, when DB is available)
   - Start your application with gunicorn

## Post-Deployment

### Access Your API

Your API will be available at:
```
https://project-tracker-backend.onrender.com
```

### Health Check

Test your deployment:
```bash
curl https://project-tracker-backend.onrender.com/health
```

Expected response:
```json
{"status": "ok"}
```

### API Documentation

Swagger documentation is available at:
```
https://project-tracker-backend.onrender.com/apidocs
```

## Environment Variables Reference

| Variable | Required | Description |
|----------|----------|-------------|
| DATABASE_URL | Yes | PostgreSQL connection string (auto-set by Render) |
| SECRET_KEY | Yes | Flask secret key for sessions |
| CLOUDINARY_CLOUD_NAME | No | Cloudinary cloud name for image uploads |
| CLOUDINARY_API_KEY | No | Cloudinary API key |
| CLOUDINARY_API_SECRET | No | Cloudinary API secret |
| SENDGRID_API_KEY | No | SendGrid API key for email service |
| FRONTEND_URL | No | Frontend URL for CORS configuration |

## Connecting Frontend

Update your frontend application to use the Render backend URL:

```javascript
const API_BASE_URL = 'https://project-tracker-backend.onrender.com';
```

Make sure to add your frontend URL to the `FRONTEND_URL` environment variable in Render.

## Database Migrations

Migrations run automatically during deployment via the `preDeployCommand` in `render.yaml`. This ensures the database connection is available when migrations run. To run migrations manually:

1. Go to your web service in Render
2. Click "Shell" tab
3. Run:
```bash
flask db upgrade
```

### Important Note for Fresh Deployments

If you're deploying to a fresh database, Render will automatically run the initial migration (`bb670e29e77b_initial_migration.py`) which creates all tables with the current schema. This migration is self-contained and includes all necessary columns.

### Migration Conflicts

If you encounter "column already exists" errors during deployment:
1. The database may have been partially migrated
2. Check the `alembic_version` table in your database to see which migrations have run
3. You may need to manually fix the migration state or recreate the database

## Troubleshooting

### Build Fails

- Check build logs in Render dashboard
- Ensure all dependencies in `requirements.txt` are correct
- Verify `build.sh` has execute permissions

### Database Connection Issues

- Verify `DATABASE_URL` environment variable is set correctly
- Check database is running in Render dashboard
- Ensure database migrations completed successfully

### CORS Errors

- Add your frontend URL to `FRONTEND_URL` environment variable
- Include the protocol (http:// or https://)
- Restart the web service after adding environment variables

### Application Crashes

- Check logs in Render dashboard under "Logs" tab
- Verify all required environment variables are set
- Check for any missing dependencies

## Scaling

Render Free Tier spins down after 15 minutes of inactivity. For production:

1. Upgrade to a paid plan for:
   - Zero downtime
   - Better performance
   - More resources

2. Consider these optimizations:
   - Increase gunicorn workers (currently set to 4)
   - Use Redis for caching
   - Implement connection pooling for database

## Support

For Render-specific issues, visit:
- [Render Documentation](https://render.com/docs)
- [Render Community](https://community.render.com)

For application issues, check the application logs and refer to the project README.
