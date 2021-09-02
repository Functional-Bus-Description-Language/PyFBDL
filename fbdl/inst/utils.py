def get_file_path(symbol):
    while True:
        if symbol['Kind'] != 'File':
            symbol = symbol['Parent']
        else:
            return symbol['Path']

def file_line_msg(symbol):
    line = symbol['Line Number']
    while True:
        if symbol['Kind'] != 'File':
            symbol = symbol['Parent']
        else:
            return f"File '{symbol['Path']}', line {line}."
