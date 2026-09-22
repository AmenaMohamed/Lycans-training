def check_aircraft_ready(aircraft):
    issues = []

    # TODO: Implement checks and append human-readable error messages to issues list if checks fail

    if aircraft["battery"]< 50 :
        issues.append("the aircraft's battery is low")
    if not aircraft["gps"]:
        issues.append("the aircraft's signal is not locked")
    if aircraft["airspeed"] !=0:
        issues.append("the aircraft is not on the run way")

    is_ready = len(issues) == 0
    return is_ready, issues

#--- Test Fleet Dataset--#
fleet = [
{"name": "LX-A01", "battery": 80, "gps": True, "airspeed": 0},
{"name": "LX-A02", "battery": 40, "gps": True, "airspeed": 0},
{"name": "LX-A03", "battery": 90, "gps": False, "airspeed": 0},
{"name": "LX-A04", "battery": 65, "gps": True, "airspeed": 5}
]
# TODO: Loop over fleet dataset and print execution output report #
for aircraft in fleet :
    is_ready , issues = check_aircraft_ready(aircraft)
    print (is_ready , issues)
    print("pass") if is_ready else print("fail")
        

