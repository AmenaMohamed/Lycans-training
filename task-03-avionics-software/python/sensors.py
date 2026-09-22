import os

def read_sensor_file(filepath):
    """Reads comma-separated sensor telemetry lines from disk."""
    # Read a file line by line
    records = []
    # TODO: Open file, strip whitespace, split lines by comma,
    with open(filepath, mode="r", encoding="utf-8") as file:
        for line in file:
            line = line.strip().split(",")
            #print(line)
            tup = [float(x) if line.index(x)<2 else int(x) for x in line]
            tup=tuple(tup)
            #print(tup)
            records.append(tup)
    # convert types (float, float, int), and append tuple to records
    return records


if __name__ == "__main__" :

    # Get the directory where sensors.py is located
    current_folder = os.path.dirname(__file__)

    # Build the path to telemetry.txt inside the 'data' subfolder
    filepath = os.path.join(current_folder, "data", "telemetry.txt")

    # Call the function with the resolved path
    #read_sensor_file(filepath)
    records = read_sensor_file(filepath)
    print(records)