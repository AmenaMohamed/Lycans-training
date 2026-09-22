import os
from aircraft import Aircraft
from sensors import read_sensor_file

def main () :
    plane = Aircraft ( " LX-A02 " )
    # Get the directory where sensors.py is located
    current_folder = os.path.dirname(__file__)
    data_path = os . path . join ( current_folder,"data" , "telemetry.txt" )
    log_path = os . path . join ( current_folder, "data" , "flight.log" )

    try:
        # TODO: 1. Read telemetry data using sensors module
        records= read_sensor_file(data_path)
        # # TODO: 2. Open log_path in append mode (’a’)
        # Append to a File
        with open(log_path, mode="a", encoding="utf-8") as file:
            for flight in records:
                # TODO: 3. Update aircraft parameters per record line
                plane.update_telemetry(flight[0],flight[1],flight[2])
                safety_status = "within safe margin" if plane.is_safe() else "OUTSIDE safe margin"
                gps_status = "ready" if plane.gps_ready else "not ready"
                log_entry= (f"flight number : {plane.name}, battery: {plane.battery}% , altitude: {plane.altitude} above ground, flight is {safety_status} with battery: {plane.battery} and altitude: {plane.altitude}, airspeed : {plane.airspeed}, gps is {gps_status}\n")
            
                file.write(log_entry)       
                # TODO: 4. Write string log status entry to file
                print("Logged: ", log_entry.strip())
        
    except FileNotFoundError:
        print(f"[ERROR] Telemetry file not found at: {data_path}")


if __name__ == "__main__" :
    main ()
    
