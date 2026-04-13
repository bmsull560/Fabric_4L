"""Unit tests for PDF adapter."""

import tempfile
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import Mock, patch, AsyncMock, MagicMock, mock_open
import pytest
import httpx

from src.adapters.pdf_adapter import PDFAdapter, PDFAdapterConfig
from src.adapters.base import AdapterType, FilingDocument


class TestPDFAdapter:
    """Test cases for PDF adapter."""

    @pytest.fixture
    def adapter(self):
        """Create adapter instance for testing."""
        return PDFAdapter()

    @pytest.fixture
    def adapter_no_ocr(self):
        """Create adapter with OCR disabled."""
        config = PDFAdapterConfig(enable_ocr=False)
        return PDFAdapter(config)

    @pytest.mark.asyncio
    async def test_adapter_type(self, adapter):
        """Test adapter type is correct."""
        assert adapter.adapter_type == AdapterType.PDF

    @pytest.mark.asyncio
    async def test_supported_formats(self, adapter):
        """Test supported formats include expected types."""
        formats = adapter.supported_formats
        assert "pdf" in formats
        assert "markdown" in formats
        assert "txt" in formats
        assert "json" in formats

    @pytest.mark.asyncio
    async def test_health_check_success(self, adapter):
        """Test health check passes with dependencies available."""
        # PyMuPDF4LLM should be importable in test environment
        result = await adapter.health_check()
        assert result is True

    @pytest.mark.asyncio
    async def test_health_check_without_ocr(self, adapter_no_ocr):
        """Test health check passes when OCR disabled."""
        result = await adapter_no_ocr.health_check()
        assert result is True

    @pytest.mark.asyncio
    async def test_search_not_supported(self, adapter):
        """Test search returns empty list with warning."""
        results = await adapter.search("test query")
        assert results == []

    @pytest.mark.asyncio
    async def test_fetch_document_local_file_not_found(self, adapter):
        """Test handling of non-existent local file."""
        result = await adapter.fetch_document("/nonexistent/file.pdf")
        assert result is None

    @pytest.mark.asyncio
    async def test_fetch_document_from_url_success(self, adapter, tmp_path):
        """Test downloading and processing PDF from URL."""
        pdf_content = b"%PDF-1.4 fake pdf content"

        mock_response = Mock()
        mock_response.content = pdf_content
        mock_response.raise_for_status = Mock()

        with patch.object(adapter, '_get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.is_closed = False
            mock_get_client.return_value = mock_client

            with patch('src.adapters.pdf_adapter.pymupdf4llm.to_markdown') as mock_to_md:
                mock_to_md.return_value = "# Extracted content\n\nTest paragraph."

                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    tmp.write(pdf_content)
                    tmp_path = Path(tmp.name)

                with patch.object(adapter, '_download_to_temp', return_value=tmp_path):
                    result = await adapter.fetch_document("https://example.com/test.pdf")

                    assert result is not None
                    assert isinstance(result, FilingDocument)
                    assert result.markdown_content == "# Extracted content\n\nTest paragraph."
                    assert result.metadata["extraction_method"] == "pymupdf4llm"

    @pytest.mark.asyncio
    async def test_ocr_not_triggered_for_good_text(self, adapter, tmp_path):
        """Test OCR is skipped when sufficient text extracted."""
        good_content = "# Title\n\nThis is a long document with enough text content that should not trigger OCR fallback. It has multiple paragraphs and information."

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(b"%PDF fake")
            tmp_path = Path(tmp.name)

        with patch('src.adapters.pdf_adapter.pymupdf4llm.to_markdown', return_value=good_content):
            with patch.object(adapter, '_ocr_extract') as mock_ocr:
                mock_ocr.return_value = ("", None)

                result = await adapter._process_pdf(tmp_path, str(tmp_path))

                assert result is not None
                assert result.markdown_content == good_content
                assert result.metadata["extraction_method"] == "pymupdf4llm"
                # OCR should not be called
                mock_ocr.assert_not_called()

    @pytest.mark.asyncio
    async def test_ocr_triggered_for_low_text(self, adapter, tmp_path):
        """Test OCR fallback triggered when text is below threshold."""
        low_content = "Short"
        ocr_content = "OCR extracted this longer text from scanned document."

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(b"%PDF fake")
            tmp_path = Path(tmp.name)

        with patch('src.adapters.pdf_adapter.pymupdf4llm.to_markdown', return_value=low_content):
            with patch.object(adapter, '_ocr_extract', new_callable=AsyncMock) as mock_ocr:
                mock_ocr.return_value = (ocr_content, 85.5)

                result = await adapter._process_pdf(tmp_path, str(tmp_path))

                assert result is not None
                assert result.markdown_content == ocr_content
                assert result.metadata["extraction_method"] == "ocr"
                assert result.metadata["ocr_confidence"] == 85.5
                mock_ocr.assert_called_once()

    @pytest.mark.asyncio
    async def test_ocr_disabled_fallback_skipped(self, adapter_no_ocr, tmp_path):
        """Test OCR fallback is skipped when disabled."""
        low_content = "Short"

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(b"%PDF fake")
            tmp_path = Path(tmp.name)

        with patch('src.adapters.pdf_adapter.pymupdf4llm.to_markdown', return_value=low_content):
            with patch.object(adapter_no_ocr, '_ocr_extract') as mock_ocr:
                result = await adapter_no_ocr._process_pdf(tmp_path, str(tmp_path))

                assert result is not None
                assert result.markdown_content == low_content
                assert result.metadata["extraction_method"] == "pymupdf4llm"
                # OCR should not be called even with low text
                mock_ocr.assert_not_called()

    @pytest.mark.asyncio
    async def test_detect_filing_type_analyst_report(self, adapter):
        """Test detection of analyst report from content."""
        content = "Gartner Magic Quadrant for Cloud Infrastructure 2024"
        filing_type = adapter._detect_filing_type(content)
        assert filing_type == "ANALYST_REPORT"

    @pytest.mark.asyncio
    async def test_detect_filing_type_patent(self, adapter):
        """Test detection of patent filing from content."""
        content = "United States Patent USPTO Claims Invention Assignee"
        filing_type = adapter._detect_filing_type(content)
        assert filing_type == "PATENT_FILING"

    @pytest.mark.asyncio
    async def test_detect_filing_type_sec_filing(self, adapter):
        """Test detection of SEC filing from content."""
        content = "FORM 10-K SECURITIES AND EXCHANGE COMMISSION Annual Report"
        filing_type = adapter._detect_filing_type(content)
        assert filing_type == "SEC_FILING"

    @pytest.mark.asyncio
    async def test_detect_filing_type_white_paper(self, adapter):
        """Test detection of white paper from content."""
        content = "White Paper Executive Summary Abstract"
        filing_type = adapter._detect_filing_type(content)
        assert filing_type == "WHITE_PAPER"

    @pytest.mark.asyncio
    async def test_detect_filing_type_generic(self, adapter):
        """Test fallback to generic document type."""
        content = "Some random content without specific markers"
        filing_type = adapter._detect_filing_type(content)
        assert filing_type == "PDF_DOCUMENT"

    @pytest.mark.asyncio
    async def test_download_to_temp_success(self, adapter):
        """Test downloading PDF to temporary file."""
        pdf_content = b"%PDF-1.4 test content"

        mock_response = Mock()
        mock_response.content = pdf_content
        mock_response.raise_for_status = Mock()

        with patch.object(adapter, '_get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.is_closed = False
            mock_get_client.return_value = mock_client

            result = await adapter._download_to_temp("https://example.com/doc.pdf")

            assert result.exists()
            assert result.suffix == ".pdf"
            assert result.read_bytes() == pdf_content

            # Clean up
            result.unlink()

    @pytest.mark.asyncio
    async def test_download_to_temp_failure(self, adapter):
        """Test handling of failed download."""
        with patch.object(adapter, '_get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(side_effect=httpx.HTTPError("Download failed"))
            mock_client.is_closed = False
            mock_get_client.return_value = mock_client

            with pytest.raises(httpx.HTTPError):
                await adapter._download_to_temp("https://example.com/doc.pdf")

    @pytest.mark.asyncio
    async def test_ocr_extract_success(self, adapter, tmp_path):
        """Test OCR text extraction from scanned PDF."""
        mock_image = Mock()

        with patch('src.adapters.pdf_adapter.convert_from_path', return_value=[mock_image, mock_image]):
            with patch('src.adapters.pdf_adapter.pytesseract.image_to_string', return_value="OCR text"):
                with patch('src.adapters.pdf_adapter.pytesseract.image_to_data', return_value={
                    "conf": [80, 85, 90]
                }):
                    text, confidence = await adapter._ocr_extract(tmp_path, "eng")

                    assert text == "OCR text\n\nOCR text"
                    assert confidence == 85.0  # Average of [80, 85, 90]

    @pytest.mark.asyncio
    async def test_ocr_extract_no_confidence(self, adapter, tmp_path):
        """Test OCR when confidence data unavailable."""
        mock_image = Mock()

        with patch('src.adapters.pdf_adapter.convert_from_path', return_value=[mock_image]):
            with patch('src.adapters.pdf_adapter.pytesseract.image_to_string', return_value="OCR text"):
                with patch('src.adapters.pdf_adapter.pytesseract.image_to_data', return_value={"conf": []}):
                    text, confidence = await adapter._ocr_extract(tmp_path, "eng")

                    assert text == "OCR text"
                    assert confidence is None

    @pytest.mark.asyncio
    async def test_ocr_extract_failure(self, adapter, tmp_path):
        """Test OCR handling of extraction failure."""
        with patch('src.adapters.pdf_adapter.convert_from_path', side_effect=Exception("OCR failed")):
            text, confidence = await adapter._ocr_extract(tmp_path, "eng")

            assert text == ""
            assert confidence is None

    @pytest.mark.asyncio
    async def test_fetch_document_with_file_path_kwarg(self, adapter):
        """Test using file_path kwarg instead of document_id."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(b"%PDF fake")
            tmp_path = Path(tmp.name)

        with patch('src.adapters.pdf_adapter.pymupdf4llm.to_markdown', return_value="Content"):
            result = await adapter.fetch_document("ignored", file_path=str(tmp_path))

            assert result is not None
            assert result.markdown_content == "Content"

    @pytest.mark.asyncio
    async def test_fetch_document_with_url_kwarg(self, adapter):
        """Test using url kwarg instead of document_id."""
        pdf_content = b"%PDF-1.4 test"

        mock_response = Mock()
        mock_response.content = pdf_content
        mock_response.raise_for_status = Mock()

        with patch.object(adapter, '_get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.is_closed = False
            mock_get_client.return_value = mock_client

            with patch('src.adapters.pdf_adapter.pymupdf4llm.to_markdown', return_value="Downloaded content"):
                result = await adapter.fetch_document("ignored", url="https://example.com/doc.pdf")

                assert result is not None
                assert result.markdown_content == "Downloaded content"

    @pytest.mark.asyncio
    async def test_process_pdf_tables_detected(self, adapter, tmp_path):
        """Test table detection in PDF content."""
        content_with_tables = "| Col1 | Col2 | Col3 |\n|------|------|------|\n| A | B | C |"

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(b"%PDF fake")
            tmp_path = Path(tmp.name)

        with patch('src.adapters.pdf_adapter.pymupdf4llm.to_markdown', return_value=content_with_tables):
            result = await adapter._process_pdf(tmp_path, str(tmp_path))

            assert result is not None
            assert result.metadata["tables_detected"] > 0
            assert "tables" in result.metadata

    @pytest.mark.asyncio
    async def test_close_client(self, adapter):
        """Test closing HTTP client."""
        mock_client = AsyncMock()
        mock_client.is_closed = False
        adapter._client = mock_client

        await adapter.close()

        mock_client.aclose.assert_called_once()


class TestPDFAdapterConfig:
    """Test cases for PDF adapter configuration."""

    def test_default_config(self):
        """Test default configuration values."""
        config = PDFAdapterConfig()
        assert config.enable_ocr is True
        assert config.ocr_language == "eng"
        assert config.min_text_length == 100
        assert config.preserve_tables is True
        assert config.dpi == 300

    def test_custom_config(self):
        """Test custom configuration values."""
        config = PDFAdapterConfig(
            enable_ocr=False,
            ocr_language="fra",
            min_text_length=50,
            preserve_tables=False,
            dpi=200
        )
        assert config.enable_ocr is False
        assert config.ocr_language == "fra"
        assert config.min_text_length == 50
        assert config.preserve_tables is False
        assert config.dpi == 200

    def test_inherited_config(self):
        """Test inherited base config attributes."""
        config = PDFAdapterConfig()
        assert config.rate_limit_per_second == 1.0
        assert config.user_agent == "ValueFabric/1.0"
        assert config.timeout_seconds == 30
