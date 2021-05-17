"""External compression processor interface."""

from iris.commons.subprocess import start_stream_subprocess


async def compress_next_round_csv(
    settings, csv_filepath, compressed_csv_filepath, logger, logger_prefix=""
):
    cmd = f"zstd --rm {csv_filepath}  --threads=0 -o {compressed_csv_filepath}"

    await start_stream_subprocess(
        cmd,
        stdout=logger.debug,
        stderr=logger.info,
        prefix=logger_prefix,
    )