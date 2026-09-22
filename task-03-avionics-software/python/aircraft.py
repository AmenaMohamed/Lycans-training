class Aircraft:
    def __init__(self, name, battery=100 ):
    # TODO: Initialize instance attributes
        self.name=name
        self.battery=battery
        self.altitude=0.0
        self.airspeed=0.0
        self.gps_ready=False
        self.position_history=[]
        
    def update_telemetry(self, altitude, airspeed, battery):
    # TODO: Update telemetry parameters
        self.altitude=altitude
        self.airspeed=airspeed
        self.battery=battery
        
    def update_position(self, lat, lon):
    # TODO: Append tuple to position_history
        self.position_history.append((lat,lon))
        
    def is_safe(self):
    # TODO: Evaluate battery threshold and altitude ceiling
        if self.battery>=20 and self.altitude <=120.0:
            return True
        
    def print_telemetry(self):
    # TODO: Print status readout
        # 1. Determine status strings cleanly
        # I found out that I have to use self.method if I was calling a method inside the same class
        safety_status = "within safe margin" if self.is_safe() else "OUTSIDE safe margin"
        gps_status = "ready" if self.gps_ready else "not ready"
        
        # 2. Print everything using a single multi-line f-string
        print(
            f"flight number : {self.name}\n"
            f"battery: {self.battery}%\n"
            f"altitude: {self.altitude} above ground\n"
            f"flight is {safety_status} with battery: {self.battery} and altitude: {self.altitude}\n"
            f"airspeed : {self.airspeed}\n"
            f"gps is {gps_status}"
        )


    #--- Verification Execution--

if __name__ == "__main__":

    plane = Aircraft("LX-A02", battery=85)
    plane.gps_ready = True
    plane.update_telemetry(altitude=45.5, airspeed=18.2, battery=78)
    plane.update_position(31.2001, 29.9182)
    plane.update_position(31.2005, 29.9190)
    plane.print_telemetry()
    print("Flight Path History:", plane.position_history)
