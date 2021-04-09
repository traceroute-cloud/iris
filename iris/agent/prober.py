"""Prober executor."""

import asyncio

from iris.commons.subprocess import CancelProcessException, start_stream_subprocess


async def stopper(settings, redis, measurement_uuid, logger, logger_prefix=""):
    """Cancel prober conditions."""
    while True:
        measurement_state = await redis.get_measurement_state(measurement_uuid)
        if measurement_state is None:
            logger.warning(logger_prefix + "Measurement canceled")
            raise CancelProcessException
        await asyncio.sleep(settings.WORKER_STOPPER_REFRESH)


async def probe(
    settings,
    parameters,
    round_number,
    results_filepath,
    logger,
    stdin=None,
    probes_filepath=None,
    stopper=None,
    logger_prefix="",
    n_packets=None,
):
    """Execute measurement."""
    cmd = (
        str(settings.AGENT_PROBER_PATH)
        + " --output-file-csv "
        + str(results_filepath)
        + " --probing-rate "
        + str(parameters.probing_rate)
        + " --protocol "
        + str(parameters.tool_parameters["protocol"])
        + " --filter-min-ttl="
        + str(parameters.tool_parameters["min_ttl"])
        + " --filter-max-ttl="
        + str(parameters.tool_parameters["max_ttl"])
        + " --meta-round="
        + str(round_number)
    )

    if settings.AGENT_DEBUG_MODE:
        cmd += " --log-level=trace"

    # Excluded prefixes
    if settings.AGENT_PROBER_EXCLUDE_PATH is not None:
        cmd += f" --filter-from-prefix-file-excl={settings.AGENT_PROBER_EXCLUDE_PATH}"

    # Probes file for round > 1
    if probes_filepath is not None:
        cmd += f" --input-file={probes_filepath}"

    if probes_filepath and stdin:
        logger.error("Cannot pass `probes_filepath` and `stdin` at the same time")
        return

    if n_packets:
        cmd += f" --n-packets={n_packets}"

    if settings.AGENT_PROBER_NO_SLEEP:
        cmd += " --no-sleep"

    logger.info(logger_prefix + cmd)

    return await start_stream_subprocess(
        cmd,
        stdout=logger.info,
        stdin=stdin,
        stderr=logger.warning,
        stopper=stopper,
        prefix=logger_prefix,
    )
