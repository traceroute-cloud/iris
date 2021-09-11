import json
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from iris.commons.database.database import Database
from iris.commons.schemas import private, public


@dataclass(frozen=True)
class Agents:
    """
    The Agents database stores the status of each agents and their measurements.
    """

    database: Database

    @property
    def table(self) -> str:
        return self.database.settings.TABLE_NAME_AGENTS

    async def create_table(self, drop: bool = False) -> None:
        if drop:
            await self.database.call(f"DROP TABLE IF EXISTS {self.table}")

        await self.database.call(
            f"""
            CREATE TABLE IF NOT EXISTS {self.table}
            (
                measurement_uuid   UUID,
                agent_uuid         UUID,
                target_file        String,
                probing_rate       Nullable(UInt32),
                probing_statistics String,
                agent_parameters   String,
                tool_parameters    String,
                state              Enum8('ongoing' = 1, 'finished' = 2, 'canceled' = 3),
                timestamp          DateTime
            )
            ENGINE MergeTree
            ORDER BY (measurement_uuid, agent_uuid)
            """,
        )

    async def all(self, measurement_uuid: UUID) -> List[public.MeasurementAgent]:
        """Get all measurement information."""
        responses = await self.database.call(
            f"SELECT * FROM {self.table} WHERE measurement_uuid=%(uuid)s",
            {"uuid": measurement_uuid},
        )
        return [self.formatter(response) for response in responses]

    async def get(
        self, measurement_uuid: UUID, agent_uuid: UUID
    ) -> Optional[public.MeasurementAgent]:
        """Get measurement information about a agent."""
        responses = await self.database.call(
            f"SELECT * FROM {self.table} "
            "WHERE measurement_uuid=%(measurement_uuid)s "
            "AND agent_uuid=%(agent_uuid)s",
            {"measurement_uuid": measurement_uuid, "agent_uuid": agent_uuid},
        )
        if responses:
            return self.formatter(responses[0])
        return None

    async def register(
        self,
        measurement_request: private.MeasurementRequest,
        agent_uuid: UUID,
        agent_parameters: public.AgentParameters,
    ) -> None:
        agent = measurement_request.agent(agent_uuid)
        await self.database.call(
            f"INSERT INTO {self.table} VALUES",
            [
                {
                    "measurement_uuid": measurement_request.uuid,
                    "agent_uuid": agent.uuid,
                    "target_file": agent.target_file,
                    "probing_rate": agent.probing_rate,
                    "probing_statistics": json.dumps({}),
                    "agent_parameters": agent_parameters.json(),
                    "tool_parameters": agent.tool_parameters.json(),
                    "state": public.MeasurementState.Ongoing.value,
                    "timestamp": datetime.now(),
                }
            ],
        )

    async def store_probing_statistics(
        self,
        measurement_uuid: UUID,
        agent_uuid: UUID,
        round_number: str,
        probing_statistics: dict,
    ) -> None:
        # Get the probing statistics already stored
        measurement = await self.get(measurement_uuid, agent_uuid)
        assert measurement
        current_probing_statistics = {
            x.round: x.statistics for x in measurement.probing_statistics
        }

        # Update the probing statistics
        current_probing_statistics[round_number] = probing_statistics

        # Store the updated statistics on the database
        await self.database.call(
            f"""
            ALTER TABLE {self.table}
            UPDATE probing_statistics=%(probing_statistics)s
            WHERE measurement_uuid=%(measurement_uuid)s
            AND agent_uuid=%(agent_uuid)s
            SETTINGS mutations_sync=1
            """,
            {
                "probing_statistics": json.dumps(current_probing_statistics),
                "measurement_uuid": measurement_uuid,
                "agent_uuid": agent_uuid,
            },
        )

    async def stamp_finished(self, measurement_uuid: UUID, agent_uuid: UUID) -> None:
        await self.database.call(
            f"""
            ALTER TABLE {self.table}
            UPDATE state=%(state)s
            WHERE measurement_uuid=%(measurement_uuid)s
            AND agent_uuid=%(agent_uuid)s
            SETTINGS mutations_sync=1
            """,
            {
                "state": public.MeasurementState.Finished.value,
                "measurement_uuid": measurement_uuid,
                "agent_uuid": agent_uuid,
            },
        )

    async def stamp_canceled(self, measurement_uuid: UUID, agent_uuid: UUID) -> None:
        await self.database.call(
            f"""
            ALTER TABLE {self.table}
            UPDATE state=%(state)s
            WHERE measurement_uuid=%(measurement_uuid)s
            AND agent_uuid=%(agent_uuid)s
            SETTINGS mutations_sync=1
            """,
            {
                "state": public.MeasurementState.Canceled.value,
                "measurement_uuid": measurement_uuid,
                "agent_uuid": agent_uuid,
            },
        )

    @staticmethod
    def formatter(row: tuple) -> public.MeasurementAgent:
        return public.MeasurementAgent(
            uuid=row[1],
            state=public.MeasurementState(row[7]),
            specific=public.MeasurementAgentSpecific(
                target_file=row[2],
                target_file_content=[],
                probing_rate=row[3],
                tool_parameters=public.ToolParameters.parse_raw(row[6]),
            ),
            parameters=public.AgentParameters.parse_raw(row[5]),
            probing_statistics=[
                public.ProbingStatistics(round=round_, statistics=statistics)
                for round_, statistics in json.loads(row[4]).items()
            ],
        )
