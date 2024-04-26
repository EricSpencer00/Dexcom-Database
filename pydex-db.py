import datetime
import pydexcom
import mysql.connector
import os

# Connect to MySQL database
db_connection = mysql.connector.connect(
    host = os.getenv("sql_host"),
    user = os.getenv("sql_user"),
    password = os.getenv("sql_password"),
    database = os.getenv("sql_database")
)
cursor = db_connection.cursor()

# Initialize Dexcom client
dx_username = os.getenv("DEXCOM_USERNAME")
dx_password = os.getenv("DEXCOM_PASSWORD")
dexcom = pydexcom.Dexcom(dx_username, dx_password)

# Get the last 288 glucose readings from Dexcom
glucose_readings = dexcom.get_glucose_readings(minutes=1440, max_count=288)

# Keep track of already inserted timestamps
existing_timestamps = set()

# Insert data into MySQL database
for index, reading in enumerate(glucose_readings):
    # Create timestamp
    timestamp = datetime.datetime.now() - datetime.timedelta(minutes=index * 5)  # Decrease minutes by 5 for each reading
    timestamp = timestamp.replace(second=0, microsecond=0)  # Set seconds and microseconds to 0 for consistency

    # Round timestamp to nearest 5 minutes
    minutes = timestamp.minute
    if minutes % 5 != 0:
        # Calculate rounded timestamp
        rounded_minutes = 5 * round(minutes / 5)
        if rounded_minutes == 60:  # If rounded to 60, reset to 0 and increment hour
            timestamp = timestamp.replace(hour=(timestamp.hour + 1) % 24)
        else:
            timestamp = timestamp.replace(minute=rounded_minutes)

    # Ensure the timestamp is unique and not already inserted
    if timestamp not in existing_timestamps:
        # Get current glucose reading
        mgdl_reading = reading.value  # Use the value attribute to get the glucose reading

        # Insert the reading into the database
        cursor.execute("INSERT INTO dexcom_data (timestamp, mgdl_reading) VALUES (%s, %s)", (timestamp, mgdl_reading))
        existing_timestamps.add(timestamp)

# Commit changes and close connections
db_connection.commit()
cursor.close()
db_connection.close()

print("Success")
