import os
import requests
from logger import setup_logger
from tqdm import tqdm

logger = setup_logger("downloader")


def download_file(session, url, save_path, pbar):
    try:
        response = session.get(url, stream=True)
        response.raise_for_status()

        file_name = os.path.basename(url)
        full_path = os.path.join(save_path, file_name)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        total_size = int(response.headers.get('content-length', 0))

        with open(full_path, 'wb') as f, tqdm(
                desc=file_name[:20],
                total=total_size,
                unit='B',
                unit_scale=True,
                unit_divisor=1024,
                leave=False
        ) as bar:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
                    bar.update(len(chunk))

        pbar.update(1)
        logger.info(f"Downloaded {file_name} ({total_size} bytes)")
    except Exception as e:
        logger.error(f"Download failed for {url}: {str(e)}")
