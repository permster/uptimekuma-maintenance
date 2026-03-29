This project creates a simple and **UNPROTECTED** HTTP endpoint to list, pause and resume [Uptime Kuma](https://uptime.kuma.pet)'s maintenances.

I personally use this thing to enable/disable maintenances through [Home Assistant](https://www.home-assistant.io/)'s automations.

## Configuration
Three environment variables are required:
* `UPTIME_KUMA_URL`
* `UPTIME_KUMA_USERNAME`
* `UPTIME_KUMA_PASSWORD`

One environment variable is optional depending on 2FA status:
* `UPTIME_KUMA_2FA_SECRET`

## Usage
A Docker image is provided and is the easiest way to get started: `permster/uptimekuma-maintenance`

    docker run -e UPTIME_KUMA_URL=http://my.uptime.kuma:3001 -e UPTIME_KUMA_USERNAME=admin -e UPTIME_KUMA_PASSWORD=password -p 8000:80 lucatnt/uptimekuma-maintenance

Otherwise, to run directly without Docker:

    pip3 install -r requirements
    fastapi run main.py

## Available URLs
* `/`: Shows available URLs
* `/maintenance`: Lists all maintenances
* `/maintenance/{m_id}`: Shows the details of maintenance with ID `{m_id}`
* `/maintenance/{m_id}/pause`: Pauses maintenance with ID `{m_id}`
* `/maintenance/{m_id}/resume`: Resumes maintenance with ID `{m_id}`


