import logging
import os

from filip.clients.ngsi_ld.cb import ContextBrokerLDClient
from filip.models.base import FiwareLDHeader

logger = logging.getLogger(__name__)


class DataSource:
    """NGSI-LD data of the service: the provider's broker, through the data
    space connector (Level 2) or directly (Level 1 / local broker).

    Level 2 is used when DS_ISSUER_URL is set: every request carries an
    access token of the data space (ds-consumer-auth).
    """

    def __init__(self):
        self.url = os.environ.get("NGSI_LD_URL", "http://localhost:1026")
        self.container_type = os.environ.get("WASTE_CONTAINER_TYPE", "WasteContainer")
        # Openroute optimization accepts up to 70 locations, and the UI waits 7 s
        self.container_limit = int(os.environ.get("WASTE_CONTAINER_LIMIT", "100"))

        session = None
        if os.environ.get("DS_ISSUER_URL"):
            from ds_consumer_auth import data_space_session

            session = data_space_session()
            logger.info("Reading %s through the data space", self.url)

        header = FiwareLDHeader()
        if os.environ.get("NGSILD_TENANT"):
            header.ngsild_tenant = os.environ["NGSILD_TENANT"]
        self.client = ContextBrokerLDClient(
            url=self.url, session=session, fiware_header=header, create_tenant=False
        )

    def waste_containers(self):
        """WasteContainer entities, normalized NGSI-LD (as the UI expects)."""
        entities = self.client.get_entity_list(
            entity_type=self.container_type, limit=self.container_limit
        )
        return [entity.model_dump(exclude_none=True, by_alias=True) for entity in entities]
