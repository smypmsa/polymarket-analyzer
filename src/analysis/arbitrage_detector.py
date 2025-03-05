# src/analysis/arbitrage_detector.py

from dataclasses import dataclass
from typing import List, Dict, Optional
from decimal import Decimal
from src.data.models import Market

@dataclass
class ArbitrageOpportunity:
    markets: List[Market]
    profit_potential: Decimal
    risk_level: str  # 'LOW', 'MEDIUM', 'HIGH'
    required_capital: Decimal
    action_steps: List[Dict[str, any]]  # detailed trading steps
    transaction_costs: Decimal
    net_profit: Decimal

class ArbitrageDetector:
    def __init__(self):
        self.min_profit_threshold = Decimal('0.02')  # 2% minimum profit
        self.transaction_fee = Decimal('0.02')  # 2% per trade

    def check_complementary_markets(self, market1: Market, market2: Market) -> Optional[ArbitrageOpportunity]:
        """Check for arbitrage in complementary markets (sum should be 1)"""
        try:
            # Get best prices
            market1_yes = Decimal(str(market1.prices['YES']))
            market1_no = Decimal(str(market1.prices['NO']))
            market2_yes = Decimal(str(market2.prices['YES']))
            market2_no = Decimal(str(market2.prices['NO']))

            # Check if sum of YES prices < 1
            if market1_yes + market2_yes < Decimal('1'):
                capital_required = (Decimal('1') * 100)  # $100 position size
                transaction_costs = capital_required * self.transaction_fee * Decimal('2')
                potential_profit = ((Decimal('1') - (market1_yes + market2_yes)) * capital_required) - transaction_costs

                if potential_profit > self.min_profit_threshold * capital_required:
                    return ArbitrageOpportunity(
                        markets=[market1, market2],
                        profit_potential=potential_profit,
                        risk_level='LOW',
                        required_capital=capital_required,
                        action_steps=[
                            {'market': market1.question, 'action': 'BUY', 'side': 'YES', 'price': market1_yes},
                            {'market': market2.question, 'action': 'BUY', 'side': 'YES', 'price': market2_yes}
                        ],
                        transaction_costs=transaction_costs,
                        net_profit=potential_profit
                    )

            # Check if sum of NO prices < 1
            if market1_no + market2_no < Decimal('1'):
                capital_required = (Decimal('1') * 100)
                transaction_costs = capital_required * self.transaction_fee * Decimal('2')
                potential_profit = ((Decimal('1') - (market1_no + market2_no)) * capital_required) - transaction_costs

                if potential_profit > self.min_profit_threshold * capital_required:
                    return ArbitrageOpportunity(
                        markets=[market1, market2],
                        profit_potential=potential_profit,
                        risk_level='LOW',
                        required_capital=capital_required,
                        action_steps=[
                            {'market': market1.question, 'action': 'BUY', 'side': 'NO', 'price': market1_no},
                            {'market': market2.question, 'action': 'BUY', 'side': 'NO', 'price': market2_no}
                        ],
                        transaction_costs=transaction_costs,
                        net_profit=potential_profit
                    )

        except Exception as e:
            logger.error(f"Error checking complementary markets: {str(e)}")
        
        return None

    def check_nested_markets(self, subset_market: Market, superset_market: Market) -> Optional[ArbitrageOpportunity]:
        """Check for arbitrage in nested markets (subset should have lower probability)"""
        try:
            subset_yes = Decimal(str(subset_market.prices['YES']))
            superset_yes = Decimal(str(superset_market.prices['YES']))

            # If subset price > superset price, potential arbitrage
            if subset_yes > superset_yes:
                capital_required = (Decimal('1') * 100)
                transaction_costs = capital_required * self.transaction_fee * Decimal('2')
                potential_profit = ((subset_yes - superset_yes) * capital_required) - transaction_costs

                if potential_profit > self.min_profit_threshold * capital_required:
                    return ArbitrageOpportunity(
                        markets=[subset_market, superset_market],
                        profit_potential=potential_profit,
                        risk_level='MEDIUM',
                        required_capital=capital_required,
                        action_steps=[
                            {'market': subset_market.question, 'action': 'SELL', 'side': 'YES', 'price': subset_yes},
                            {'market': superset_market.question, 'action': 'BUY', 'side': 'YES', 'price': superset_yes}
                        ],
                        transaction_costs=transaction_costs,
                        net_profit=potential_profit
                    )

        except Exception as e:
            logger.error(f"Error checking nested markets: {str(e)}")

        return None

    def check_temporal_markets(self, earlier_market: Market, later_market: Market) -> Optional[ArbitrageOpportunity]:
        """Check for arbitrage in markets with temporal relationships"""
        try:
            earlier_yes = Decimal(str(earlier_market.prices['YES']))
            later_yes = Decimal(str(later_market.prices['YES']))

            # Earlier event should have lower or equal probability
            if earlier_yes > later_yes:
                capital_required = (Decimal('1') * 100)
                transaction_costs = capital_required * self.transaction_fee * Decimal('2')
                potential_profit = ((earlier_yes - later_yes) * capital_required) - transaction_costs

                if potential_profit > self.min_profit_threshold * capital_required:
                    return ArbitrageOpportunity(
                        markets=[earlier_market, later_market],
                        profit_potential=potential_profit,
                        risk_level='MEDIUM',
                        required_capital=capital_required,
                        action_steps=[
                            {'market': earlier_market.question, 'action': 'SELL', 'side': 'YES', 'price': earlier_yes},
                            {'market': later_market.question, 'action': 'BUY', 'side': 'YES', 'price': later_yes}
                        ],
                        transaction_costs=transaction_costs,
                        net_profit=potential_profit
                    )

        except Exception as e:
            logger.error(f"Error checking temporal markets: {str(e)}")

        return None

    def find_arbitrage_opportunities(self, markets: List[Market]) -> List[ArbitrageOpportunity]:
        """Find all arbitrage opportunities in the given markets"""
        opportunities = []

        for i, market1 in enumerate(markets):
            for market2 in markets[i+1:]:
                # Check various types of relationships
                if self._are_complementary(market1, market2):
                    if opp := self.check_complementary_markets(market1, market2):
                        opportunities.append(opp)
                
                if self._is_nested(market1, market2):
                    if opp := self.check_nested_markets(market1, market2):
                        opportunities.append(opp)
                
                if self._are_temporal(market1, market2):
                    if opp := self.check_temporal_markets(market1, market2):
                        opportunities.append(opp)

        # Sort by profit potential
        return sorted(opportunities, key=lambda x: x.profit_potential, reverse=True)

    def _are_complementary(self, market1: Market, market2: Market) -> bool:
        """Check if markets are logically complementary"""
        # Implementation needed: Use NLP or rules to determine if markets are complementary
        pass

    def _is_nested(self, market1: Market, market2: Market) -> bool:
        """Check if one market is nested within another"""
        # Implementation needed: Use NLP or rules to determine if markets are nested
        pass

    def _are_temporal(self, market1: Market, market2: Market) -> bool:
        """Check if markets have a temporal relationship"""
        # Implementation needed: Compare end dates and market descriptions
        pass
