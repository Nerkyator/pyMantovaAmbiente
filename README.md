
# Mantova Ambiente integration for Home Assistant

  

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)

  <img  src="https://www.mantovaambiente.it/img/logo_big.png"  alt="Mantova Ambiente Logo"  width="128"  height="64"  align="center">


A custom Home Assistant integration for monitoring waste collection schedules from Mantova Ambiente.

  

## Features

  

-  **Tomorrow's Waste Sensor**: Shows all waste types to be collected tomorrow
-  **Individual Waste Type Sensors**: Boolean sensors for each configured waste type with next collection dates
-  **Configurable Caching**: Customizable cache duration (1-168 hours) to reduce API calls
-  **Zone-based Configuration**: Support for different collection zones
-  **Automatic Data Updates**: Periodic updates with fallback to cached data

  

## Installation

  

### HACS (Recommended)

  

1. Open HACS in your Home Assistant instance
2. Go to "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add `https://github.com/Nerkyator/pyMantovaAmbiente` as repository
6. Select "Integration" as category
7. Click "Add"
8. Install "Mantova Ambiente" from HACS
9. Restart Home Assistant

  

### Manual Installation

  

1. Copy the `custom_components/mantova_ambiente` folder to your Home Assistant `custom_components` directory
2. Restart Home Assistant
3. Go to Configuration > Integrations
4. Click "Add Integration" and search for "Mantova Ambiente"

  

## Configuration

  

### Initial Setup

  

1. Go to Configuration > Integrations
2. Click "Add Integration"
3. Search for "Mantova Ambiente"
4. Enter your configuration:

-  **Zone **:  Select your zone from zones list
-  **Cache Duration**: How long to cache data in hours (default: 24)
-  **Waste Codes**: Select which waste types you want to track

  

## Sensors

  

### Tomorrow Waste Sensor

-  **Entity ID**: `sensor.mantova_ambiente_tomorrow_waste_[zone]`
-  **State**: Comma-separated list of waste types to be collected tomorrow, or "none" if no collections
-  **Attributes**:
-  `count`: Number of waste types to be collected tomorrow
-  `collections`: Detailed information about tomorrow's collections
-  `zone`: Your configured zone code
-  `last_update`: Last data update timestamp

  

### Individual Waste Type Sensors

-  **Entity ID**: `sensor.mantova_ambiente_waste_[code]_[zone]`
-  **State**: `True` if this waste type is collected tomorrow, `False` otherwise
-  **Attributes**:
-  `waste_type`: The waste type code
-  `title`: Human-readable name of the waste type
-  `next_dates`: Array of next collection dates for this waste type
-  `zone`: Your configured zone code
-  `last_update`: Last data update timestamp

  

## Automation Examples

  

### Notification for Tomorrow's Waste Collection

  

```yaml

automation:
  - id: waste_collection_reminder
    alias: "Waste Collection Reminder"
    trigger:
      - platform: time
        at: "20:00:00"
    condition:
      - condition: template
        value_template: "{{ states('sensor.mantova_ambiente_tomorrow_waste_3631') != 'none' }}"
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "🗑️ Waste Collection Tomorrow"
          message: "Remember to put out: {{ states('sensor.mantova_ambiente_tomorrow_waste_3631') }}"
```

  

### Specific Waste Type Automation

  

```yaml

automation:
  - id: organic_waste_reminder
    alias: "Organic Waste Reminder"
    trigger:
      - platform: state
        entity_id: sensor.mantova_ambiente_waste_3707_3631
        to: "true"
    action:
      - service: light.turn_on
        target:
          entity_id: light.kitchen_led_strip
        data:
          color_name: green
          brightness: 255

```

  

## API Information

  

This integration uses the official Mantova Ambiente API:

-  **Base URL**: `https://www.mantovaambiente.it/api/recyclings`
-  **Method**: GET with zone parameter
-  **Update Frequency**: Every hour (configurable via cache duration)
-  **Caching**: Local file-based caching to reduce API calls

  

## Troubleshooting

  

### Integration Not Loading

- Check that your zone code is correct
- Verify internet connectivity
- Check Home Assistant logs for specific error messages

  

### No Data or Sensors

- Ensure your waste type codes are valid for your zone
- Check if the API is accessible from your network
- Verify that collections are scheduled for your zone

  

### Outdated Data

- The integration caches data to reduce API load
- Force refresh by reloading the integration or restarting Home Assistant
- Adjust cache duration in configuration if needed

  

## License

  

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

  

## Disclaimer

This integration is not officially affiliated with Mantova Ambiente. It's a community-developed tool that uses their public API to provide waste collection information to Home Assistant users.