"""
Quick test script for the EcomIQ MCP Server.
Run this from the api_service directory (with fastmcp installed):

    pip install fastmcp
    python test_mcp.py
"""

import asyncio
from fastmcp import Client


async def main():
    client = Client("http://localhost:9500/mcp")

    async with client:
        # 1. List all available tools
        print("=" * 60)
        print("Available MCP Tools:")
        print("=" * 60)
        tools = await client.list_tools()
        for tool in tools:
            print(f"  🔧 {tool.name}")
            print(f"     {tool.description[:80]}...")
        print()

        # 2. Call: Full investigation
        print("=" * 60)
        print("Test 1: run_full_investigation (no filter)")
        print("=" * 60)
        result = await client.call_tool("run_full_investigation", {})
        # Show just the signals from each section
        if isinstance(result, list) and result:
            data = result[0]
            if hasattr(data, 'text'):
                import json
                report = json.loads(data.text)
                for section, content in report.items():
                    if section == "scope":
                        continue
                    if isinstance(content, dict):
                        for sub, sub_content in content.items():
                            if isinstance(sub_content, dict) and sub_content.get("signals"):
                                print(f"\n  ⚠️  Signal in [{section}.{sub}]:")
                                for sig in sub_content["signals"]:
                                    print(f"      {sig['type'].upper()} | {sig['dimension']} = {sig['value']} (avg: {sig['avg']}, severity: {sig['severity']})")
        print()

        # 3. Call: Scoped — only Delhivery
        print("=" * 60)
        print("Test 2: get_shipment_analysis (courier_name = Delhivery)")
        print("=" * 60)
        result = await client.call_tool(
            "get_shipment_analysis",
            {"scope": {"courier_name": "Delhivery"}}
        )
        if isinstance(result, list) and result:
            import json
            data = result[0]
            if hasattr(data, 'text'):
                report = json.loads(data.text)
                print("  Courier performance:")
                for row in report.get("courier_performance", {}).get("breakdown", []):
                    print(f"    {row}")

        print()

        # 4. Call: Payment analysis
        print("=" * 60)
        print("Test 3: get_payment_analysis (West India only)")
        print("=" * 60)
        result = await client.call_tool(
            "get_payment_analysis",
            {"scope": {"region": "West India"}}
        )
        if isinstance(result, list) and result:
            import json
            data = result[0]
            if hasattr(data, 'text'):
                report = json.loads(data.text)
                print("  Payment failure by method:")
                for row in report.get("by_method", {}).get("breakdown", []):
                    print(f"    {row}")

        print("\n✅ MCP Server is working correctly!")


if __name__ == "__main__":
    asyncio.run(main())
