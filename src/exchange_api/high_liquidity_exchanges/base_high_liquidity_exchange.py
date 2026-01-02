from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Union, Any
from src.exchange_api.base_exchange import BaseExchange
from src.exchange_api.utils import load_api_keys
import json
import logging

logger = logging.getLogger(__name__)


class BaseHighLiquidityExchange(BaseExchange, ABC):
    """
    Abstract base class for high liquidity exchanges.
    Inherits all abstract methods from BaseExchange and may include additional methods
    specific to high liquidity trading environments.
    """

    @abstractmethod
    def get_coin_info(self) -> List[Dict]:
        """
        Fetch information about all coins available for deposit and withdrawal.

        :return: A list of dictionaries containing coin information.
        """
        pass

    @abstractmethod
    def supports_lightning_network(self, coin: str) -> bool:
        """
        Check if the exchange supports the Lightning Network for a specific coin.

        :param coin: The symbol of the coin (e.g., 'BTC').
        :return: True if supported, False otherwise.
        """
        pass

    @abstractmethod
    def _validate_deposit_availability(self, coin: str, network_name: str) -> bool:
        """
        Check the availability of a given crypto address

        :param coin: Coin to deposit
        :param network_name: network to check
        :return: True if it is available, False otherwise
        """