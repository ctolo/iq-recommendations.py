# Usage
`python3 iq-recommendations.py -u IQ_URL:8070 -a user:password -i APP_PUBLIC_ID -s STAGE -l LIMIT_ON_NUMBER_OF_COMPONENTS`

Example:
`python3 iq-recommendations.py -u http://localhost:8070 -a admin:admin123 -i App_Public_Name -s build -l 0`

By default the URL is `http://localhost:8070`, username and password are `admin:admin123`, stage is `build` and component limiter is set to `10`. Selecting a limit of zero (`0`) will remove any limits and provide all the components in the app (this might take long!). On average the script takes 1.5 seconds per component to run.
