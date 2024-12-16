import re
import os
import sys

def remove_ansi_codes_with_progress(log_file_path):
    """
    Removes ANSI escape codes from a log file and writes the cleaned content to a new file,
    with progress tracking.

    Parameters:
        log_file_path (str): Path to the input log file.

    Returns:
        str: Path to the output file containing cleaned content.
    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If the input file is not a `.log` file.
        IOError: For any I/O operation errors.
    """
    # Regex to match ANSI escape codes
    ansi_escape = re.compile(r'\033[@-_][0-?]*[ -/]*[@-~]')

    # Ensure the provided file path is a `.log` file
    if not log_file_path.endswith('.log'):
        raise ValueError("Input file must have a .log extension")

    output_file_path = log_file_path.replace('color', 'noColor')

    try:
        # Open the input and output files
        with open(log_file_path, 'r') as infile, open(output_file_path, 'w') as outfile:
            for line in infile:
                # Remove ANSI escape codes from the current line
                cleaned_line = ansi_escape.sub('', line)
                outfile.write(cleaned_line)
        return output_file_path

    except FileNotFoundError:
        raise FileNotFoundError(f"The file {log_file_path} does not exist.")
    except IOError as e:
        raise IOError(f"An error occurred while processing the file: {e}")


import gzip
import shutil
import os


def compress_with_gzip(log_file_path):
    """
    Compresses a log file using gzip compression.

    Parameters:
        log_file_path (str): Path to the input log file.

    Returns:
        str: Path to the compressed file if successful.

    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If the input path is a directory or invalid.
        IOError: For any I/O operation errors.
    """
    # Validate the input path
    if not os.path.isfile(log_file_path):
        raise ValueError(f"The specified path '{log_file_path}' is not a valid file.")

    compressed_file_path = log_file_path + '.gz'

    try:
        # Compress the file
        with open(log_file_path, 'rb') as f_in, gzip.open(compressed_file_path, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
        return compressed_file_path

    except FileNotFoundError:
        raise FileNotFoundError(f"The file '{log_file_path}' does not exist.")
    except IOError as e:
        raise IOError(f"An error occurred while compressing the file: {e}")

