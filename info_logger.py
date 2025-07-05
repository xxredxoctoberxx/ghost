import logging
from playsound import playsound

# DEBUG: 10. Detailed information, typically of interest only when diagnosing problems.

# INFO: 20. Confirmation that things are working as expected.

# WARNING: 30. An indication that something unexpected happened, or indicative of some problem in the near future (e.g. ‘disk space low’). The software is still working as expected.

# ERROR: 40. Due to a more serious problem, the software has not been able to perform some function.

# CRITICAL: 40. A serious error, indicating that the program itself may be unable to continue running.

class Info_Logger():
    def __init__():
        pass

    def ghost_log(print_something, level: int):
        assert level in [10,20,30,40,50], f"Logging level value {level} is not in [10,20,30,40,50]"

        logging.basicConfig(filename='info.log', level=logging.INFO,
            encoding='utf-8', format='%(asctime)s:%(levelname)s:%(message)s')
        
        if level == 10:
            logging.debug(print_something)
        elif level == 20:
            logging.info(print_something)
        elif level == 30:
            logging.warning(print_something)
            playsound(r'C:\Users\danil\PythonFiles\Ghost\sound_folder\warning_sound.mp3')
        elif level == 40:
            logging.error(print_something)
        elif level == 50:
            logging.critical(print_something)


