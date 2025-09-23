#!/usr/bin/env python3
"""
Test script to verify the CSV parsing fix for flight data.
"""

# Test data with the problematic line break from the debug file
test_data = """[START_FLIGHT_DATA]
HEADER,F_399282,231114,true,68,10,60,165
GPS,990,4,MOTOR_RUN,39.246693,-77.196678
GPS,2003,4,MOTOR_RUN,39.246674,-77.196716
GPS,99001,7,POST_DT_DESCENT,39.246685,-
77.196556
GPS,101002,7,POST_DT_DESCENT,39.246685,-77.196571
[END_FLIGHT_DATA]"""

def process_test_data(raw_data):
    """Process flight data using the same logic as the GUI."""
    # Remove carriage returns and normalize line endings
    raw_data = raw_data.replace('\r\n', '\n').replace('\r', '\n')

    # Reassemble any records that were split across lines
    lines = raw_data.split('\n')
    processed_lines = []
    i = 0

    while i < len(lines):
        line = lines[i].strip()
        print(f"Processing line {i}: '{line}'")

        # Skip empty lines and control markers
        if not line or line.startswith('[') or line.startswith('DEBUG'):
            print(f"  Skipping control/empty line")
            i += 1
            continue

        # Check if this is an incomplete GPS record
        if line.startswith('GPS,'):
            parts = line.split(',')
            print(f"  GPS line has {len(parts)} parts: {parts}")

            # GPS records need 6 parts: GPS,timestamp,state,state_name,lat,lon
            # Also check if lat/lon fields look incomplete (contain only minus sign)
            is_incomplete = False

            if len(parts) < 6:
                is_incomplete = True
                print(f"  Incomplete GPS record (not enough parts)")
            elif len(parts) >= 6:
                # Check if latitude or longitude fields are incomplete
                lat_field = parts[4] if len(parts) > 4 else ""
                lon_field = parts[5] if len(parts) > 5 else ""

                # Check for incomplete coordinate values (just a minus sign or empty)
                if lat_field in ["-", ""] or lon_field in ["-", ""]:
                    is_incomplete = True
                    print(f"  Incomplete GPS record (bad coordinates: lat='{lat_field}', lon='{lon_field}')")

            if is_incomplete:
                # This GPS record is incomplete, try to merge with next line
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    # Merge the lines
                    merged_line = line + next_line
                    print(f"  Merged: '{line}' + '{next_line}' = '{merged_line}'")
                    processed_lines.append(merged_line)
                    i += 2  # Skip both current and next line
                else:
                    # Last line, can't merge
                    print(f"  Last line, cannot merge")
                    processed_lines.append(line)
                    i += 1
            else:
                # Complete GPS record
                print(f"  Complete GPS record")
                processed_lines.append(line)
                i += 1
        else:
            # Non-GPS line (HEADER, etc.)
            print(f"  Non-GPS line")
            processed_lines.append(line)
            i += 1

    flight_header = None
    gps_records = []

    for line in processed_lines:
        if line.startswith('HEADER,'):
            # Parse header
            parts = line.split(',')
            if len(parts) >= 8:
                flight_header = {
                    'flight_id': parts[1],
                    'duration_ms': int(parts[2]),
                    'gps_available': parts[3] == 'true',
                    'position_count': int(parts[4]),
                    'parameters': {
                        'motor_run_time': int(parts[5]),
                        'total_flight_time': int(parts[6]),
                        'motor_speed': int(parts[7])
                    }
                }
                print(f"Parsed header: {flight_header}")
        elif line.startswith('GPS,'):
            # Parse GPS record
            parts = line.split(',')
            if len(parts) >= 6:
                try:
                    gps_record = {
                        'timestamp_ms': int(parts[1]),
                        'flight_state': int(parts[2]),
                        'state_name': parts[3],
                        'latitude': float(parts[4]),
                        'longitude': float(parts[5])
                    }
                    gps_records.append(gps_record)
                    print(f"Parsed GPS: {gps_record}")
                except ValueError as ve:
                    print(f"ERROR - Skipping malformed GPS record: {line} - Error: {ve}")
                    continue

    print(f"\nSUCCESS: Parsed {len(gps_records)} GPS records without errors")
    return flight_header, gps_records

if __name__ == "__main__":
    print("Testing CSV parsing fix...")
    print("=" * 50)

    try:
        header, records = process_test_data(test_data)
        print(f"\nFinal result: {len(records)} GPS records successfully parsed")

        # Verify the problematic record was parsed correctly
        problem_record = None
        for record in records:
            if record['timestamp_ms'] == 99001:
                problem_record = record
                break

        if problem_record:
            print(f"\nProblem record successfully parsed:")
            print(f"  Latitude: {problem_record['latitude']}")
            print(f"  Longitude: {problem_record['longitude']}")

            if problem_record['longitude'] == -77.196556:
                print("[PASS] Longitude correctly parsed as -77.196556")
            else:
                print(f"[FAIL] Expected -77.196556, got {problem_record['longitude']}")
        else:
            print("[FAIL] Problem record not found")

    except Exception as e:
        print(f"[FAIL] Exception occurred: {e}")
        import traceback
        traceback.print_exc()