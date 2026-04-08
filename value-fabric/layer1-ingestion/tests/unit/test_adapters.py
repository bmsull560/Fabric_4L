"""Unit tests for SEC EDGAR adapter."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

from src.adapters.sec_edgar import SECEdgarAdapter
from src.adapters.base import AdapterType, FilingType


class TestSECEdgarAdapter:
    """Test cases for SEC EDGAR adapter."""
    
    @pytest.fixture
    def adapter(self):
        """Create adapter instance for testing."""
        return SECEdgarAdapter()
    
    @pytest.mark.asyncio
    async def test_adapter_type(self, adapter):
        """Test adapter type is correct."""
        assert adapter.adapter_type == AdapterType.SEC_EDGAR
    
    @pytest.mark.asyncio
    async def test_supported_formats(self, adapter):
        """Test supported formats include expected types."""
        formats = adapter.supported_formats
        assert "html" in formats
        assert "xbrl" in formats
        assert "json" in formats
    
    @pytest.mark.asyncio
    async def test_get_company_cik_success(self, adapter):
        """Test CIK lookup for known ticker."""
        # Mock the HTTP response
        mock_response = Mock()
        mock_response.json.return_value = {
            "0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."}
        }
        mock_response.status_code = 200
        
        with patch.object(adapter, '_rate_limited_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            cik = await adapter.get_company_cik("AAPL")
            
            assert cik == "0000320193"
            mock_request.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_company_cik_not_found(self, adapter):
        """Test CIK lookup for unknown ticker."""
        mock_response = Mock()
        mock_response.json.return_value = {}
        mock_response.status_code = 200
        
        with patch.object(adapter, '_rate_limited_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            cik = await adapter.get_company_cik("UNKNOWN")
            
            assert cik is None
    
    @pytest.mark.asyncio
    async def test_search_filings(self, adapter):
        """Test filing search."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "cik": "0000320193",
            "entityName": "Apple Inc.",
            "filings": {
                "recent": {
                    "form": ["10-K", "10-Q", "8-K"],
                    "filingDate": ["2023-11-03", "2023-08-04", "2023-11-02"],
                    "accessionNumber": ["0000320193-23-000106", "0000320193-23-000070", "0000320193-23-000104"],
                    "primaryDocument": ["aapl-20230930.htm", "aapl-20230701.htm", "aapl-20231102.htm"],
                    "primaryDocDescription": ["Annual Report", "Quarterly Report", "Current Report"]
                }
            }
        }
        mock_response.status_code = 200
        
        with patch.object(adapter, '_rate_limited_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=365)
            
            results = await adapter.search(
                query="AAPL",
                start_date=start_date,
                end_date=end_date,
                form_types=["10-K", "10-Q"]
            )
            
            assert len(results) == 2  # Should filter to 10-K and 10-Q only
            assert all(r.metadata['form_type'] in ["10-K", "10-Q"] for r in results)
    
    @pytest.mark.asyncio
    async def test_rate_limiting_config(self, adapter):
        """Test rate limiting is configured correctly."""
        assert adapter.config.rate_limit_per_second == 10.0  # SEC limit
        assert "ValueFabric" in adapter.config.user_agent
    
    @pytest.mark.asyncio
    async def test_fetch_document_not_found(self, adapter):
        """Test fetch with invalid accession number."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "filings": {"recent": {"accessionNumber": []}}
        }
        mock_response.status_code = 200
        
        with patch.object(adapter, '_rate_limited_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            
            result = await adapter.fetch_document(
                "INVALID-ACCESSION",
                ticker="AAPL",
                cik="0000320193"
            )
            
            assert result is None


class TestXBRLParser:
    """Test cases for XBRL parser."""
    
    @pytest.fixture
    def parser(self):
        """Create parser instance."""
        from src.adapters.xbrl_parser import XBRLParser
        return XBRLParser()
    
    def test_parse_empty(self, parser):
        """Test parsing empty XBRL."""
        xbrl_xml = "<?xml version=\"1.0\"?><xbrl xmlns=\"http://www.xbrl.org/2003/instance\"></xbrl>"
        result = parser.parse(xbrl_xml)
        
        assert result is not None
        assert result.all_facts == []
    
    def test_parse_revenue_fact(self, parser):
        """Test parsing a simple revenue fact."""
        xbrl_xml = '''<?xml version="1.0"?>
        <xbrl xmlns="http://www.xbrl.org/2003/instance"
              xmlns:us-gaap="http://fasb.org/us-gaap/2023">
            <context id="ctx-2023">
                <entity><identifier scheme="http://www.sec.gov/CIK">0000320193</identifier></entity>
                <period>
                    <startDate>2023-01-01</startDate>
                    <endDate>2023-12-31</endDate>
                </period>
            </context>
            <unit id="USD"><measure>iso4217:USD</measure></unit>
            <us-gaap:Revenues contextRef="ctx-2023" unitRef="USD" decimals="-6">394328000000</us-gaap:Revenues>
        </xbrl>'''
        
        result = parser.parse(xbrl_xml)
        
        assert len(result.all_facts) == 1
        fact = result.all_facts[0]
        assert fact.concept == "Revenues"
        assert fact.value == 394328000000
        assert fact.unit == "iso4217:USD"
    
    def test_extract_key_metrics(self, parser):
        """Test extracting key financial metrics."""
        xbrl_xml = '''<?xml version="1.0"?>
        <xbrl xmlns="http://www.xbrl.org/2003/instance"
              xmlns:us-gaap="http://fasb.org/us-gaap/2023">
            <context id="ctx-2023">
                <entity><identifier>0000320193</identifier></entity>
                <period><endDate>2023-12-31</endDate></period>
            </context>
            <unit id="USD"><measure>iso4217:USD</measure></unit>
            <us-gaap:Assets contextRef="ctx-2023" unitRef="USD">352755000000</us-gaap:Assets>
            <us-gaap:Revenues contextRef="ctx-2023" unitRef="USD">394328000000</us-gaap:Revenues>
        </xbrl>'''
        
        result = parser.parse(xbrl_xml)
        
        assert "total_assets" in result.key_metrics
        assert "revenue" in result.key_metrics
        assert result.key_metrics["total_assets"]["value"] == 352755000000
        assert result.key_metrics["revenue"]["value"] == 394328000000


class TestAdapterRegistry:
    """Test cases for adapter registry."""
    
    @pytest.fixture
    def registry(self):
        """Create fresh registry for testing."""
        from src.adapters.registry import AdapterRegistry
        return AdapterRegistry()
    
    def test_register_adapter(self, registry):
        """Test registering a new adapter."""
        from src.adapters.base import DataSourceAdapter, AdapterConfig
        
        class TestAdapter(DataSourceAdapter):
            @property
            def adapter_type(self):
                from src.adapters.base import AdapterType
                return AdapterType.WEBSITE
            
            @property
            def supported_formats(self):
                return ["html"]
            
            async def health_check(self):
                return True
            
            async def search(self, query, **kwargs):
                return []
            
            async def fetch_document(self, document_id, **kwargs):
                return None
        
        from src.adapters.base import AdapterType
        registry.register(AdapterType.WEBSITE, TestAdapter)
        
        assert AdapterType.WEBSITE in registry.list_adapters()
    
    def test_get_sec_edgar_adapter(self, registry):
        """Test retrieving SEC EDGAR adapter."""
        from src.adapters.base import AdapterType
        
        adapter = registry.get_adapter(AdapterType.SEC_EDGAR)
        
        assert adapter is not None
        assert adapter.adapter_type == AdapterType.SEC_EDGAR
    
    def test_get_adapter_caching(self, registry):
        """Test that adapter instances are cached."""
        from src.adapters.base import AdapterType
        
        adapter1 = registry.get_adapter(AdapterType.SEC_EDGAR)
        adapter2 = registry.get_adapter(AdapterType.SEC_EDGAR)
        
        assert adapter1 is adapter2  # Same instance
