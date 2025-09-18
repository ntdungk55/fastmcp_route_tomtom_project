#!/usr/bin/env python3
"""Entry point cho TomTom MCP Server với Clean Architecture.

Sử dụng file này để khởi chạy server đã được refactor theo Clean Architecture.
"""

from app.interfaces.mcp.server import main

if __name__ == "__main__":
    main()
