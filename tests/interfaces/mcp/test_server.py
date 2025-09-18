"""Tests cho TomTomMCPServer."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
import os

from app.interfaces.mcp.server import TomTomMCPServer


class TestTomTomMCPServer:
    """Test suite cho TomTomMCPServer."""
    
    @patch.dict(os.environ, {"TOMTOM_API_KEY": "test_api_key"})
    def test_server_initialization_success(self):
        """Test khởi tạo server thành công với API key."""
        # Act
        server = TomTomMCPServer()
        
        # Assert
        assert server._api_key == "test_api_key"
        assert server._container is not None
        assert server._mcp is not None
    
    @patch.dict(os.environ, {}, clear=True)
    def test_server_initialization_missing_api_key(self):
        """Test khởi tạo server thất bại khi thiếu API key."""
        # Act & Assert
        with pytest.raises(ValueError, match="TOMTOM_API_KEY environment variable is required"):
            TomTomMCPServer()
    
    @patch.dict(os.environ, {"TOMTOM_API_KEY": "test_api_key"})
    @patch('app.interfaces.mcp.server.Container')
    def test_server_uses_dependency_injection(self, mock_container):
        """Test server sử dụng dependency injection."""
        # Arrange
        mock_container_instance = Mock()
        mock_container.return_value = mock_container_instance
        
        # Act
        server = TomTomMCPServer()
        
        # Assert
        mock_container.assert_called_once()
        assert server._container == mock_container_instance
    
    @patch.dict(os.environ, {"TOMTOM_API_KEY": "test_api_key"})
    @patch('app.interfaces.mcp.server.FastMCP')
    def test_server_registers_mcp_tools(self, mock_fastmcp):
        """Test server đăng ký các MCP tools."""
        # Arrange
        mock_mcp_instance = Mock()
        mock_fastmcp.return_value = mock_mcp_instance
        
        # Act
        server = TomTomMCPServer()
        
        # Assert
        mock_fastmcp.assert_called_once_with("RouteMCP_TomTom_CleanArch")
        # Verify tools được đăng ký (check số lần gọi tool decorator)
        assert mock_mcp_instance.tool.call_count >= 8  # Có ít nhất 8 tools
    
    @patch.dict(os.environ, {"TOMTOM_API_KEY": "test_api_key"})
    @patch('builtins.print')
    def test_server_run_prints_info(self, mock_print):
        """Test server.run() in thông tin startup."""
        # Arrange
        server = TomTomMCPServer()
        server._mcp.run = Mock(side_effect=KeyboardInterrupt())  # Simulate user stop
        
        # Act
        server.run(host="localhost", port=8080)
        
        # Assert
        print_calls = [call[0][0] for call in mock_print.call_args_list]
        assert any("Starting TomTom Route MCP Server" in call for call in print_calls)
        assert any("Clean Architecture" in call for call in print_calls)
        assert any("localhost:8080" in call for call in print_calls)
    
    @patch.dict(os.environ, {"TOMTOM_API_KEY": "test_api_key"})
    def test_server_run_handles_keyboard_interrupt(self):
        """Test server xử lý KeyboardInterrupt gracefully."""
        # Arrange
        server = TomTomMCPServer()
        server._mcp.run = Mock(side_effect=KeyboardInterrupt())
        
        # Act & Assert (không raise exception)
        with patch('builtins.print'):
            server.run()
    
    @patch.dict(os.environ, {"TOMTOM_API_KEY": "test_api_key"})
    def test_server_run_handles_general_exception(self):
        """Test server xử lý general exception."""
        # Arrange
        server = TomTomMCPServer()
        server._mcp.run = Mock(side_effect=Exception("Server error"))
        
        # Act & Assert
        with patch('builtins.print'), patch('sys.exit') as mock_exit:
            server.run()
            mock_exit.assert_called_once_with(1)
