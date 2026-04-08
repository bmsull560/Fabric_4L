"""Data source adapters for Layer 1 Ingestion.

Provides adapters for:
- SEC EDGAR (financial filings)
- USPTO Patents (patent search)
- News sources (GDELT, NewsAPI)
- Website crawling (via PlaywrightCrawler)
"""

from .base import (
    DataSourceAdapter,
    AdapterType,
    AdapterConfig,
    FilingType,
    FilingDocument,
    SearchResult,
)
from .sec_edgar import SECEdgarAdapter
from .xbrl_parser import XBRLParser, ParsedXBRL, FinancialFact, FinancialStatement
from .registry import AdapterRegistry, get_registry

__all__ = [
    # Base classes
    'DataSourceAdapter',
    'AdapterType',
    'AdapterConfig',
    'FilingType',
    'FilingDocument',
    'SearchResult',
    # Implementations
    'SECEdgarAdapter',
    'XBRLParser',
    'ParsedXBRL',
    'FinancialFact',
    'FinancialStatement',
    # Registry
    'AdapterRegistry',
    'get_registry',
]
