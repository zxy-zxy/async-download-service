import subprocess
import os
import logging
import argparse

import asyncio
import aiofiles
from aiohttp import web

from logger_config import get_logger


class DownloadService:
    def __init__(self, mimic_download_latency, photos_directory, logger):
        self._mimic_download_latency = mimic_download_latency
        self._photos_directory = photos_directory
        self._logger = logger

    def _is_photo_directory_exists(self, directory_hash):
        return os.path.exists(os.path.join(self._photos_directory, directory_hash))

    async def _get_archive(self, directory_hash):
        directory_hash_full_path = os.path.join(self._photos_directory, directory_hash)

        archive_process = await asyncio.create_subprocess_exec(
            'zip',
            '-jr', '-', directory_hash_full_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        return archive_process

    async def archivate(self, request):
        directory_hash = request.match_info['archive_hash']
        directory_exists = self._is_photo_directory_exists(directory_hash)
        if not directory_exists:
            raise web.HTTPNotFound(
                reason=f'Directory {directory_hash} does not exists or has been moved.'
            )

        archive_process = await self._get_archive(directory_hash)

        response = web.StreamResponse()
        response.headers['Content-Disposition'] = f'attachment; filename="{directory_hash}.zip"'
        await response.prepare(request)

        try:
            while True:
                self._logger.info('Sending archive chunk.')
                if self._mimic_download_latency:
                    await asyncio.sleep(self._mimic_download_latency)
                archive_chunk = await archive_process.stdout.readline()
                if not archive_chunk:
                    break
                await response.write(archive_chunk)
        except asyncio.CancelledError:
            self._logger.info('Handling canceled error exception.')
            archive_process.terminate()
            raise
        finally:
            self._logger.info('Force close executed.')
            response.force_close()

        return response

    async def handle_index_page(self, request):
        async with aiofiles.open('templates/index.html', mode='r') as index_file:
            index_contents = await index_file.read()
        return web.Response(text=index_contents, content_type='text/html')


def create_parser():
    parser = argparse.ArgumentParser(description='aiohttp server for photos downloading.')
    parser.add_argument('--mimic_download_latency', type=float, help='Mimic latency download ms.')
    parser.add_argument('--photos_directory', help='Path to directory with photos.')
    parser.add_argument('--enable_logging', dest='enable_logging', action='store_true')
    parser.add_argument('--no_enable_logging', dest='enable_logging', action='store_false')
    parser.set_defaults(enable_logging=False)

    return parser


def main():
    parser = create_parser()
    args = parser.parse_args()

    mimic_download_latency = args.mimic_download_latency or float(os.environ.get('MIMIC_DOWNLOAD_LATENCY'))
    photos_directory = args.photos_directory or os.environ.get('PHOTOS_DIRECTORY')

    logging_lvl = logging.INFO if args.enable_logging else logging.NOTSET
    logger = get_logger(__file__, logging_lvl)

    app = web.Application()
    download_service = DownloadService(
        mimic_download_latency,
        photos_directory,
        logger
    )

    app.add_routes([
        web.get('/', download_service.handle_index_page),
        web.get('/archive/{archive_hash}/', download_service.archivate),
    ])

    web.run_app(app)


if __name__ == '__main__':
    main()
