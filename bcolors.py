colors = {
  'HEADER': '\033[95m',
  'OKBLUE': '\033[94m',
  'OKCYAN': '\033[96m',
  'OKGREEN': '\033[92m',
  'WARNING': '\033[93m',
  'FAIL': '\033[91m',
  'ENDC': '\033[0m',
  'BOLD': '\033[1m',
  'UNDERLINE': '\033[4m'
}

def color_print(message, color):
  print(f"{color}{message}{colors['ENDC']}")

def info_print(message):
  print(f"{colors['OKCYAN']}{message}{colors['ENDC']}")

def warning_print(message):
  print(f"{colors['WARNING']}{message}{colors['ENDC']}")

def error_print(message):
  print(f"{colors['FAIL']}{message}{colors['ENDC']}")

def success_print(message):
  print(f"{colors['OKGREEN']}{message}{colors['ENDC']}")

def instruction_print(message):
  print(f"{colors['HEADER']}{message}{colors['ENDC']}")

def color_input(message):
  return input(f"{colors['BOLD']}{colors['UNDERLINE']}{message}{colors['ENDC']} ")

