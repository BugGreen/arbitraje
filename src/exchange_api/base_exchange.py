from abc import ABC, abstractmethod
from typing import List, Dict, Optional


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

    @abstractmethod
    def create_withdraw_request(self, coin: str, address: str, amount: float,
                                network: Optional[str] = None, **kwargs) -> Dict:
        """
        Abstract method for creating a withdrawal request.

        :param coin: The symbol of the cryptocurrency to withdraw (e.g., 'BTC').
        :param address: The destination address for the withdrawal.
        :param amount: The amount of cryptocurrency to withdraw.
        :param network: Optional, the network to use for withdrawal.
        :param kwargs: Additional optional parameters (withdrawOrderId, addressTag, etc.).
        :return: A dictionary containing the withdrawal request ID.
        """
        pass

