config = {

    # Rough elapsed time the program has been running
    "ELAPSED_TIME": 0,

    # Total allowed running length of program; incremented by sleep_mode
    # (seconds * minutes * hours)
    "RUNNING_DURATION": 60 * 60 * 4,

    # (seconds * minutes) - Duration of Sleep Mode between resource check
    "SLEEP_MODE_LENGTH": 60 * 6,

    # Maximum for acceptable CPU usage, in %
    "CPU_THRESHOLD": 30,

    # Maximum for acceptable RAM usage, in %
    "MEMORY_THRESHOLD": 55,

    # Number of resource checks required to determine heavy usage
    "RESOURCE_CHECKS": 3,

    # Number of seconds between resource checks
    "RESOURCE_CHECK_INTERVAL": 3,

    # Failsafe value in case checks keep returning active/inactive
    "MAX_RESOURCE_CHECKS": 10,

    # Number of passed resource checks allowed before terminating program
    "MAX_PASSED_CHECKS": 3,

    # Number of seconds between presence checks
    "PRESENCE_WAIT_TIME": 60,

    # Number of checks for user presence;
    # With PRESENCE_WAIT_TIME of 60, 15 checks = 15 minutes
    "PRESENCE_CHECK_COUNT": 12

}
