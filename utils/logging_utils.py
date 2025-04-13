import gzip
import logging
import os
from datetime import datetime, timedelta


def setup_logger(log_dir="logs", days_to_keep=30):
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    if logger.hasHandlers():
        return logger

    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    cleanup_old_logs(log_dir, days_to_keep)

    current_date = datetime.now().strftime("%Y-%m-%d")
    log_file = os.path.join(log_dir, f"bot_{current_date}.log")

    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(file_formatter)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter("%(levelname)s - %(message)s")
    console_handler.setFormatter(console_formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

def cleanup_old_logs(log_dir, days_to_keep=30):
    now = datetime.now()
    cutoff_archive = now - timedelta(days=1)
    cutoff_delete = now - timedelta(days=days_to_keep)

    for log_file in os.listdir(log_dir):
        log_path = os.path.join(log_dir, log_file)

        if not os.path.isfile(log_path):
            continue

        if log_file.endswith(".log"):
            last_modified_date = datetime.fromtimestamp(os.path.getmtime(log_path))
            if last_modified_date < cutoff_archive:
                archive_log_file(log_path)

        if log_file.endswith(".gz"):  # Перевіряємо архіви (.gz)
            last_modified_date = datetime.fromtimestamp(os.path.getmtime(log_path))
            if last_modified_date < cutoff_delete:
                os.remove(log_path)
                print(f"Deleted old log file: {log_file}")

def archive_log_file(log_path):
    with open(log_path, "rb") as f_in:
        with gzip.open(f"{log_path}.gz", "wb") as f_out:
            f_out.writelines(f_in)
    os.remove(log_path)
    print(f"Archived log file: {log_path}")