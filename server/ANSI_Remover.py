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
    """
    # Regex to match ANSI escape codes
    ansi_escape = re.compile(r'\033[@-_][0-?]*[ -/]*[@-~]')

    # Ensure the provided file path is a `.log` file
    if not log_file_path.endswith('.log'):
        raise ValueError("Input file must have a .log extension")

    output_file_path = log_file_path.replace('color', 'noColor')

    try:
        # Get the size of the input file
        total_size = os.path.getsize(log_file_path)
        processed_size = 0

        # Open the input and output files
        with open(log_file_path, 'r') as infile, open(output_file_path, 'w') as outfile:
            for line in infile:
                # Remove ANSI escape codes from the current line
                cleaned_line = ansi_escape.sub('', line)
                outfile.write(cleaned_line)

                # Update processed size and display progress
                processed_size += len(line.encode('utf-8'))
                progress = (processed_size / total_size) * 100
                sys.stdout.write(f"\rProcessing: {progress:.2f}% completed")
                sys.stdout.flush()

        # Ensure progress bar finishes at 100%
        sys.stdout.write("\rProcessing: 100.00% completed\n")
        print(f"Cleaned log file written to: {output_file_path}")
        return output_file_path

    except FileNotFoundError:
        raise FileNotFoundError(f"The file {log_file_path} does not exist.")
    except IOError as e:
        raise IOError(f"An error occurred while processing the file: {e}")
