# Sentry Setup and Configuration Guide

This guide provides comprehensive instructions for integrating Sentry error monitoring and performance tracking into the AgentsFlowAI application. Sentry will help track errors, monitor performance, and provide insights into application health across both backend (FastAPI/Python) and frontend (React/TypeScript) components.

## Prerequisites

- A Sentry account (sign up at [sentry.io](https://sentry.io))
- Access to the Sentry dashboard
- Environment variable management setup (e.g., `.env` files)
- Git repository for release tracking

## Creating Sentry Projects

Sentry organizes monitoring data into projects. For AgentsFlowAI, create separate projects for the backend and frontend to isolate error tracking and performance data.

### Step-by-Step Project Creation

1. Log in to your Sentry account at [sentry.io](https://sentry.io).
2. Click "Projects" in the left sidebar, then "Create Project".
3. For the backend:
   - Select "Python" as the platform.
   - Name the project `agentsflowai-backend` (or similar).
   - Choose a team (create one if needed).
   - Click "Create Project".
4. For the frontend:
   - Select "React" as the platform.
   - Name the project `agentsflowai-frontend` (or similar).
   - Choose the same team as the backend project.
   - Click "Create Project".
5. Note the project slugs (e.g., `agentsflowai-backend`, `agentsflowai-frontend`) for later use.

Each project will have its own DSN (Data Source Name) for configuration.

## Obtaining DSN Keys

The DSN is a unique URL that identifies your project and is used to send data to Sentry.

### Retrieving DSN Keys

1. In the Sentry dashboard, navigate to "Projects" and select the desired project (backend or frontend).
2. Go to Settings > Projects > [project-name] > Client Keys (DSN).
3. Copy the DSN URL (it looks like `https://your-key@sentry.io/project-id`).
4. Store these DSNs securely - they will be used as environment variables.

Keep DSNs separate for each environment (development, staging, production) if you have multiple Sentry projects per environment.

## Configuring Environment Variables

Environment variables control Sentry behavior. Configure them in your `.env` files or deployment environment.

### Backend Environment Variables

Add these to `/backend/.env` (and copy to `.env.example`):

```bash
# Sentry Error Monitoring (Optional)
SENTRY_DSN=https://your-backend-dsn@sentry.io/project-id  # Get from backend project settings
SENTRY_ENVIRONMENT=development  # development | staging | production
SENTRY_TRACES_SAMPLE_RATE=0.1  # 0.0 to 1.0, default 0.1 (10% sampling)
SENTRY_PROFILES_SAMPLE_RATE=0.1  # 0.0 to 1.0, default 0.1 (10% profiling)
SENTRY_RELEASE=agentsflowai-backend@1.0.0  # Release version, e.g., git commit SHA
SENTRY_ENABLE_TRACING=true  # Enable performance tracing
```

### Frontend Environment Variables

Add these to `/.env` (and copy to `.env.example`):

```bash
# Sentry Configuration
VITE_SENTRY_DSN=https://your-frontend-dsn@sentry.io/project-id  # Get from frontend project settings
VITE_SENTRY_ENVIRONMENT=development  # development | staging | production
VITE_SENTRY_TRACES_SAMPLE_RATE=0.1  # 0.0 to 1.0
VITE_SENTRY_RELEASE=agentsflowai-frontend@1.0.0  # Release version
```

### Environment-Specific Configuration

#### Development
- Set `SENTRY_ENVIRONMENT=development`
- Use higher sampling rates for better debugging: `SENTRY_TRACES_SAMPLE_RATE=1.0` (100%)
- Enable detailed logging and profiling

#### Staging
- Set `SENTRY_ENVIRONMENT=staging`
- Use moderate sampling: `SENTRY_TRACES_SAMPLE_RATE=0.5` (50%)
- Test alerting and notification setup

#### Production
- Set `SENTRY_ENVIRONMENT=production`
- Use lower sampling to manage costs: `SENTRY_TRACES_SAMPLE_RATE=0.1` (10%)
- Ensure PII filtering is active
- Set up proper release tracking

### Setting Variables in Different Environments

- **Local Development**: Use `.env` files with `python-dotenv` or similar.
- **Docker**: Pass variables via `docker run -e` or `docker-compose.yml`.
- **Cloud Platforms**:
  - AWS: Use Systems Manager Parameter Store or Secrets Manager.
  - Heroku: Set via dashboard or CLI (`heroku config:set`).
  - Vercel/Netlify: Set in project settings.
- **CI/CD**: Use GitHub Secrets or similar for sensitive values like DSNs.

## Release Tracking Setup

Release tracking associates errors and performance data with specific code versions, enabling better debugging and deployment monitoring.

### Setting Release Versions

1. **Using Git Commit SHAs** (recommended):
   - Set `SENTRY_RELEASE` to the full git commit SHA: `git rev-parse HEAD`
   - Example: `SENTRY_RELEASE=agentsflowai-backend@abc123def456`

2. **Using Version Tags**:
   - Tag releases in git: `git tag v1.2.3`
   - Set `SENTRY_RELEASE` to `agentsflowai-backend@v1.2.3`

3. **Dynamic Release Setting**:
   - In CI/CD pipelines, set the release dynamically:
     ```bash
     export SENTRY_RELEASE="agentsflowai-backend@$(git rev-parse HEAD)"
     ```

### CI/CD Integration

In your deployment workflow (e.g., GitHub Actions), add steps to create and finalize releases:

```yaml
- name: Create Sentry release
  run: |
    sentry-cli releases new "$SENTRY_RELEASE"
    sentry-cli releases set-commits "$SENTRY_RELEASE" --auto
    sentry-cli releases finalize "$SENTRY_RELEASE"
  env:
    SENTRY_AUTH_TOKEN: ${{ secrets.SENTRY_AUTH_TOKEN }}
    SENTRY_ORG: your-org-slug
    SENTRY_PROJECT: agentsflowai-backend
```

For frontend source map uploads:

```yaml
- name: Upload source maps
  run: sentry-cli releases files "$SENTRY_RELEASE" upload-sourcemaps ./dist --rewrite
  env:
    SENTRY_AUTH_TOKEN: ${{ secrets.SENTRY_AUTH_TOKEN }}
    SENTRY_ORG: your-org-slug
    SENTRY_PROJECT: agentsflowai-frontend
```

## Alerting Rules Configuration

Set up alerts to notify your team of critical issues and performance problems.

### Creating Alert Rules

1. In the Sentry dashboard, go to Alerts > Alert Rules.
2. Click "Create Alert Rule".

#### Critical Error Alerts
- **Rule Name**: "Critical Backend Errors"
- **Conditions**:
  - Event Type: Error
  - Environment: production
  - Tags: `http.status_code` = 500
- **Action**: Send notification to #backend-alerts Slack channel

#### Database Connection Failures
- **Rule Name**: "Database Connection Errors"
- **Conditions**:
  - Event Type: Error
  - Message contains: "connection failed" or "timeout"
  - Environment: production
- **Action**: Page on-call engineer via PagerDuty

#### Performance Degradation Alerts
- **Rule Name**: "Slow API Responses"
- **Conditions**:
  - Transaction duration > 2000ms (P95)
  - Transaction name matches: `/api/*`
  - Environment: production
- **Action**: Email dev team

- **Rule Name**: "Long-Running Transactions"
- **Conditions**:
  - Transaction duration > 5000ms
  - Environment: production
- **Action**: Create high-priority issue

### Notification Channels

1. **Email**: Default, sends to team members.
2. **Slack**: Integrate via Settings > Integrations > Slack.
   - Create channels like #backend-alerts, #frontend-alerts.
3. **PagerDuty**: For critical alerts requiring immediate response.
4. **Webhook**: Send to custom endpoints for automation.

### Issue Assignment Rules

1. Go to Settings > Projects > [project] > Issue Owners.
2. Create rules based on file paths or tags:
   - Assign backend errors to backend team: `path:**/backend/**`
   - Assign auth-related issues to security team: `tags.auth_error:*`
   - Assign WebSocket issues to real-time team: `tags.websocket:*`

## Custom Sentry Queries for Monitoring

Use Sentry's Discover feature to create custom queries for monitoring key metrics.

### Error Rate by Endpoint
```
event.type:error AND transaction:* AND environment:production
| count() by transaction
| sort by count DESC
```
- Visualize as a table or time series chart.

### Slow Database Queries
```
event.type:transaction AND op:db.query AND transaction.duration:>1000
| avg(transaction.duration) by db.table
| sort by avg DESC
```
- Set up alerts if avg duration > 2000ms.

### Failed Authentication Attempts
```
event.type:error AND message:"authentication failed" AND environment:production
| count() by user.email
| sort by count DESC
```
- Monitor for brute force attacks.

### WebSocket Connection Failures
```
event.type:error AND tags.websocket:* AND environment:production
| count() by tags.connection_id
| sort by count DESC
```
- Track problematic connections.

### Additional Useful Queries
- **Frontend JS Errors by Browser**: `event.type:error AND browser.name:* | count() by browser.name`
- **API Response Time Trends**: `event.type:transaction AND transaction:/api/* | p95(transaction.duration)`
- **User Impact**: `event.type:error | count_unique(user.id)`

## Best Practices

### Sampling Rates
- **Development**: 100% (1.0) for full visibility during debugging.
- **Staging**: 50% (0.5) for testing without overwhelming data.
- **Production**: 10-20% (0.1-0.2) to balance cost and insights.
- Adjust based on error volume and budget.

### PII Filtering and Data Scrubbing
- Configure data scrubbers in Settings > Projects > [project] > Security & Privacy.
- Add sensitive fields: `password`, `token`, `api_key`, `credit_card`.
- Use `before_send` callbacks in SDK initialization to filter data.
- Example (backend):
  ```python
  def before_send(event, hint):
      # Remove sensitive data
      if 'request' in event:
          if 'data' in event['request']:
              event['request']['data'] = scrub_sensitive_data(event['request']['data'])
      return event
  ```

### Release and Environment Tagging
- Always set `environment` and `release` in SDK config.
- Use consistent naming: `development`, `staging`, `production`.
- Tag releases with version or commit SHA for traceability.

### Custom Context and Breadcrumbs
- Add relevant context to errors: user info, request details, component state.
- Use breadcrumbs for user actions leading to errors.
- Example: Add breadcrumbs for navigation, API calls, form submissions.

### Performance Considerations
- Monitor SDK overhead; sampling helps control data volume.
- Use `before_send` to drop non-critical events.
- Profile in staging before production rollout.

## Troubleshooting

### Sentry Not Capturing Errors
- **Check DSN**: Ensure DSN is correct and matches the project.
- **Environment Variables**: Verify variables are loaded (check logs).
- **Network Issues**: Confirm outbound connections to sentry.io are allowed.
- **SDK Initialization**: Ensure `sentry_sdk.init()` is called early in app startup.
- **Sampling Rate**: In dev, set to 1.0 to capture all events.

### Missing Source Maps for Frontend
- **Build Configuration**: Ensure `sourcemap: true` in Vite config.
- **Upload Process**: Verify source maps are uploaded in CI/CD.
- **Release Matching**: Ensure `release` matches between SDK and uploaded maps.
- **File Paths**: Check that source map paths match the built files.

### Performance Overhead Concerns
- **Sampling**: Reduce `traces_sample_rate` if overhead is too high.
- **Profiling**: Disable profiling in production if not needed.
- **Async Operations**: Use async Sentry methods to avoid blocking.
- **Monitor Metrics**: Track SDK performance with APM tools.

### Rate Limiting and Quota Management
- **Quota Exceeded**: Upgrade plan or reduce sampling rates.
- **Rate Limits**: Implement client-side rate limiting in `before_send`.
- **Data Volume**: Use filters to reduce unnecessary events.
- **Billing Alerts**: Set up billing notifications in Sentry account settings.

### Other Common Issues
- **CORS Errors**: Add sentry.io to allowed origins if needed.
- **WebSocket Monitoring**: Ensure custom instrumentation doesn't break connections.
- **User Context**: Verify user data is set correctly without PII.
- **Release Tracking**: Check that releases are created and finalized in CI/CD.

## Resources

- [Sentry Documentation](https://docs.sentry.io/)
- [Python SDK Docs](https://docs.sentry.io/platforms/python/)
- [React SDK Docs](https://docs.sentry.io/platforms/javascript/guides/react/)
- [Release Tracking Guide](https://docs.sentry.io/product/releases/)
- [Alerting Documentation](https://docs.sentry.io/product/alerts/)
- [Best Practices](https://docs.sentry.io/product/accounts/quotas/best-practices/)
- [Sentry Community Forum](https://forum.sentry.io/)
- [Sentry Support](https://sentry.io/support/)