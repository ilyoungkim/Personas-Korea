"""MCP 연결 POC 테스트 클라이언트.

ChatGPT(또는 MCP 클라이언트)가 하는 것과 동일한 방식으로 persona-mcp 서버에
연결하여 4개 툴을 실제 호출해 봅니다. 이를 통해 문제가 DB인지 MCP인지 호출인지
분리해 확인할 수 있습니다.

사용법:
    .venv/bin/python mcp_client_test.py
"""

import asyncio
import json

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def call_tool(session: ClientSession, name: str, args: dict) -> dict:
    result = await session.call_tool(name, arguments=args)
    out = []
    for c in result.content:
        if hasattr(c, "text"):
            out.append(c.text)
    text = "\n".join(out)
    try:
        return json.loads(text)
    except Exception:
        return {"raw": text}


async def main() -> None:
    params = StdioServerParameters(
        command="docker",
        args=[
            "exec", "-i", "persona-mcp",
            "python", "server.py",  # stdio 모드
        ],
    )

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            print("== 등록된 툴 ==")
            for t in tools.tools:
                print(f"  - {t.name}: {t.description[:60]}")
            print()

            print("== 1) search_persona: 경기 40대 여성 ==")
            r = await call_tool(session, "search_persona", {
                "province": "경기", "age_min": 40, "age_max": 49,
                "sex": "여자", "limit": 3,
            })
            print(json.dumps(r, ensure_ascii=False, indent=2)[:1500])
            print()

            print("== 2) aggregate_persona: 경기 40대 여성 통계 ==")
            r = await call_tool(session, "aggregate_persona", {
                "province": "경기", "age_min": 40, "age_max": 49, "sex": "여자",
            })
            print(json.dumps(r, ensure_ascii=False, indent=2)[:2000])
            print()

            print("== 3) similar_persona: 자연어 ==")
            r = await call_tool(session, "similar_persona", {
                "query": "자녀 교육과 건강관리에 관심이 많은 수도권 40대 맞벌이 여성",
                "limit": 3,
            })
            print(json.dumps(r, ensure_ascii=False, indent=2)[:1200])
            print()

            print("== 4) compare_persona ==")
            r = await call_tool(session, "compare_persona", {
                "group_a": {"label": "서울 30대 여성 1인가구", "sex": "여자",
                            "province": "서울", "age_min": 30, "age_max": 39,
                            "family_type": "혼자 거주"},
                "group_b": {"label": "경기 40대 여성 자녀가구", "sex": "여자",
                            "province": "경기", "age_min": 40, "age_max": 49,
                            "family_type": "배우자·자녀와 거주"},
            })
            print(json.dumps(r, ensure_ascii=False, indent=2)[:2500])


if __name__ == "__main__":
    asyncio.run(main())
