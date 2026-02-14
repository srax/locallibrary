# Deploying to DigitalOcean App Platform

This guide explains how to deploy the LocalLibrary application to DigitalOcean App Platform.

## Prerequisites

- A DigitalOcean account
- This repository pushed to GitHub
- DigitalOcean CLI (optional, for command-line deployment)

## Quick Deploy

### Option 1: Using the DigitalOcean Console (Recommended)

1. **Log in to DigitalOcean**
   - Go to [DigitalOcean App Platform](https://cloud.digitalocean.com/apps)
   - Click "Create App"

2. **Connect Your Repository**
   - Select GitHub as your source
   - Authorize DigitalOcean to access your GitHub account
   - Select the `krutisbs/locallibrary` repository
   - Choose the `main` branch

3. **Configure Your App**
   - DigitalOcean will auto-detect your app settings from `.do/app.yaml`
   - Review the detected settings:
     - **Web Service**: Python application running Daphne
     - **Database**: PostgreSQL 16
     - **Pre-Deploy Job**: Database migrations

4. **Set Environment Variables**
   - Click on the web service and go to "Environment Variables"
   - Add the following required variables:
     ```
     SECRET_KEY=<generate-a-secure-random-string>
     DEBUG=False
     DJANGO_ENV=production
     ```
   - The `DATABASE_URL` will be automatically set by DigitalOcean

5. **Review and Launch**
   - Review your app configuration
   - Click "Create Resources"
   - Wait for the deployment to complete (usually 5-10 minutes)

### Option 2: Using DigitalOcean CLI

1. **Install the DigitalOcean CLI**
   ```bash
   # macOS
   brew install doctl
   
   # Windows (using Chocolatey)
   choco install doctl
   
   # Linux
   snap install doctl
   ```

2. **Authenticate**
   ```bash
   doctl auth init
   ```

3. **Create the App**
   ```bash
   doctl apps create --spec .do/app.yaml
   ```

4. **Set Environment Variables**
   ```bash
   # Get your app ID
   doctl apps list
   
   # Update environment variables
   doctl apps update <app-id> --spec .do/app.yaml
   ```

## Configuration Files

### `.do/app.yaml`
The main App Platform specification file that defines:
- Web service configuration (Daphne ASGI server)
- Database configuration (PostgreSQL)
- Build and run commands
- Environment variables
- Pre-deploy migration job
- Health checks

### `runtime.txt`
Specifies the Python version (3.11.7) for the deployment.

### `build.sh`
Build script that:
- Upgrades pip
- Installs dependencies from `requirements.txt`
- Collects static files

### `requirements.txt`
Python dependencies including:
- Django 5.2.7
- Daphne (ASGI server)
- Channels (WebSocket support)
- PostgreSQL adapter (psycopg2-binary)
- WhiteNoise (static file serving)

## Environment Variables

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `SECRET_KEY` | Django secret key | `your-secret-key-here` |
| `DEBUG` | Debug mode (always False in production) | `False` |
| `DJANGO_ENV` | Environment setting | `production` |

### Auto-Generated Variables

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string (auto-generated) |
| `PORT` | Application port (auto-set by DigitalOcean) |
| `APP_DOMAIN` | Your app's domain (auto-set) |

## Post-Deployment Steps

1. **Create a superuser**
   - Go to the DigitalOcean console
   - Navigate to your app → Console
   - Run: `python manage.py createsuperuser`
   - Follow the prompts

2. **Access your application**
   - Your app will be available at: `https://<your-app-name>.ondigitalocean.app`

3. **Set up custom domain (optional)**
   - In the DigitalOcean console, go to Settings → Domains
   - Add your custom domain
   - Update DNS records as instructed

## Monitoring and Logs

- **View Logs**: Go to your app in the DigitalOcean console → Runtime Logs
- **Metrics**: Check CPU, Memory, and Request metrics in the console
- **Alerts**: Set up alerts for deployment failures or performance issues

## Database Management

### Accessing the Database

```bash
# Using doctl
doctl databases db get <database-id>

# Get connection details
doctl apps list
doctl databases connection <database-id>
```

### Running Migrations

Migrations run automatically before each deployment via the pre-deploy job. To run manually:

```bash
# Via console
python manage.py migrate

# Via doctl
doctl apps logs <app-id> --type run
```

## Scaling

### Vertical Scaling (Instance Size)
- Go to your app → Settings → Scale
- Choose from: basic-xxs, basic-xs, basic-s, basic-m, professional-xs, etc.

### Horizontal Scaling (Instance Count)
- Update `instance_count` in `.do/app.yaml`
- Redeploy your app

## Troubleshooting

### Build Failures
- Check build logs in the DigitalOcean console
- Verify `requirements.txt` has all dependencies
- Ensure `runtime.txt` specifies a supported Python version

### Runtime Errors
- Check runtime logs for error messages
- Verify environment variables are set correctly
- Ensure `DATABASE_URL` is properly configured

### Static Files Not Loading
- Verify `python manage.py collectstatic` runs in the build command
- Check that `STATIC_ROOT` and `STATIC_URL` are correctly set in `settings.py`
- Ensure WhiteNoise is in the middleware stack

### Database Connection Issues
- Verify the database component is running
- Check that `DATABASE_URL` environment variable is set
- Ensure migrations have run successfully

## Cost Optimization

- **Development**: Use `basic-xxs` instance ($5/month) with development database
- **Production**: Upgrade to `basic-xs` or higher with production database
- **Database**: Start with development tier, upgrade as needed

## Security Best Practices

1. **Always use strong SECRET_KEY**: Generate using `python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'`
2. **Keep DEBUG=False** in production
3. **Use environment variables** for sensitive data
4. **Enable HTTPS** (automatically enabled on DigitalOcean)
5. **Regular updates**: Keep dependencies updated

## Support

- [DigitalOcean App Platform Documentation](https://docs.digitalocean.com/products/app-platform/)
- [DigitalOcean Community](https://www.digitalocean.com/community)
- [Django Deployment Checklist](https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/)
