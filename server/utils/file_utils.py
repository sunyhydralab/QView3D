import os
import gzip
import shutil

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