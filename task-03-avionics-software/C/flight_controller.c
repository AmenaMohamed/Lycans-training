#include <stdio.h> 
#include <stdbool.h>

// Return codes: 
// 0 = DISARMED / CRITICAL 
// 1 = HOLD
// 2 = CLIMB 
// 3 = DESCEND
int calculate_flight_command(float current_alt, float target_alt, float battery_pct, bool armed)
{

    // TODO : Step 1-Check arming status
    if (armed == false ) return 0;
    // TODO : Step 2-Check low battery threshold
    if (battery_pct < 15.0f) return 0;
    // TODO : Step 3-Compare current_alt against target_alt (+/-2.0 m deadband )
    if (current_alt < target_alt - 2.0f) return 2;
    else if (current_alt > target_alt + 2.0f ) return 3;
    else if (target_alt - 2.0 < current_alt < target_alt + 2.0) return 1;

}
int main()
{
    // Execution Test Bench
    printf("Test 1 (Climb): %d (Target Expected: 2)\n", calculate_flight_command(50.0f, 100.0f, 80.0f, true));
    printf("Test 2 (Disarmed): %d (Target Expected: 0)\n", calculate_flight_command(50.0f, 100.0f, 80.0f, false));
    printf("Test 3 (Low Battery): %d (Target Expected: 0)\n", calculate_flight_command(50.0f, 100.0f, 12.0f, true));
    printf("Test 4 (Hold): %d (Target Expected: 1)\n", calculate_flight_command(99.0f, 100.0f, 80.0f, true));
    printf("Test 5 (Descend): %d (Target Expected: 3)\n", calculate_flight_command(110.0f, 100.0f, 80.0f, true));

    return 0;
}