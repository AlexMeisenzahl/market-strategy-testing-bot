from strategies.arbitrage_strategy import ArbitrageStrategy


def _base_config():
    return {
        "min_profit_margin": 0.02,
        "max_trade_size": 20,
        "arbitrage_types": {
            "cross_exchange": {
                "enabled": True,
                "min_spread_pct": 1.0,
                "min_match_score": 0.2,
                "fee_bps": 20,
                "max_quote_age_seconds": 30,
            }
        },
    }


def test_detect_cross_exchange_opportunity_builds_pipeline_plan():
    strategy = ArbitrageStrategy(_base_config())

    markets = [
        {
            "id": "m1",
            "question": "Will Bitcoin be above 100k by end of 2026",
            "liquidity": 5000,
            "external_quotes": [
                {
                    "exchange": "opinion",
                    "market_name": "Bitcoin above 100k by end 2026",
                    "yes_price": 0.63,
                    "liquidity": 6000,
                    "quote_age_seconds": 3,
                    "fee_bps": 20,
                }
            ],
        }
    ]
    prices = {"m1": {"yes": 0.55, "no": 0.45}}

    opportunities = strategy.detect_cross_exchange_arbitrage(markets, prices)

    assert len(opportunities) == 1
    opportunity = opportunities[0]
    assert opportunity.arbitrage_type == "Cross-Exchange"
    assert opportunity.metadata["pipeline"] == [
        "match_markets",
        "watch_odds",
        "arbitrage_math",
        "risk_analysis",
        "execute",
        "validate",
    ]
    assert opportunity.metadata["execution_plan"]["mode"] == "simultaneous"
    assert opportunity.metadata["validation_plan"]["liquidate_unhedged"] is True


def test_cross_exchange_skips_stale_quotes():
    strategy = ArbitrageStrategy(_base_config())

    markets = [
        {
            "id": "m1",
            "question": "Will ETH hit 10k this year",
            "liquidity": 8000,
            "external_quotes": [
                {
                    "exchange": "opinion",
                    "market_name": "Will ETH hit 10k this year",
                    "yes_price": 0.71,
                    "liquidity": 9000,
                    "quote_age_seconds": 120,
                }
            ],
        }
    ]
    prices = {"m1": {"yes": 0.60, "no": 0.40}}

    opportunities = strategy.detect_cross_exchange_arbitrage(markets, prices)
    assert opportunities == []


def test_cross_exchange_profit_margin_uses_net_edge_and_is_enterable():
    strategy = ArbitrageStrategy(_base_config())

    markets = [
        {
            "id": "m2",
            "question": "Will SOL be above 300 this year",
            "liquidity": 7000,
            "external_quotes": [
                {
                    "exchange": "opinion",
                    "market_name": "SOL above 300 this year",
                    "yes_price": 0.58,
                    "liquidity": 7000,
                    "quote_age_seconds": 2,
                    "fee_bps": 20,
                }
            ],
        }
    ]
    prices = {"m2": {"yes": 0.50, "no": 0.50}}

    opportunities = strategy.detect_cross_exchange_arbitrage(markets, prices)

    assert len(opportunities) == 1
    opportunity = opportunities[0]
    assert opportunity.profit_margin > 2.0
    assert opportunity.expected_profit > 0
    assert strategy.should_enter(opportunity) is True
