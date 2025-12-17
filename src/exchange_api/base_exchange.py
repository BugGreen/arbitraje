from abc import ABC, abstractmethod
from typing import List, Dict


class BaseExchange(ABC):
    """
    Abstract base class defining the interface for exchange proxies.
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
    def create_deposit_address(self, coin: str, network: str = None) -> Dict:
        """
        Abstract method for creating a deposit address.

        :param coin: The symbol of the cryptocurrency.
        :param network: The network for the deposit.
        :return: A dictionary with deposit address details.
        """
        pass