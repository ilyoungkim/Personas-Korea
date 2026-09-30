"""Core Persona 12개에 LLM 기반 자연스러운 별칭을 생성해 PostgreSQL에 저장.

규칙 기반 라벨("수도권 무직")을 사람이 읽기 좋은 별칭으로 바꿉니다.
OpenRouter API를 사용합니다. (key.txt의 sk-or-... 키)
"""

import json
import os
import ssl
import urllib.request

PG_DSN = os.getenv("PG_DSN", "postgresql://persona:persona@localhost:15432/persona")
MODEL = "openai/gpt-6-luna"


def load_key() -> str:
    with open("key.txt", encoding="utf-8") as f:
        for line in f:
            if line.startswith("sk-or-"):
                return line.strip()
    raise RuntimeError("key.txt에서 OpenRouter 키를 찾을 수 없음")


def llm_name(key: str, labels: list[dict]) -> list[str]:
    """Core Persona 라벨 목록 → LLM이 자연스러운 별칭 생성."""
    prompt = (
        "다음은 한국 합성 페르소나 데이터의 최상위 12개 집단(Core Persona)입니다. "
        "각 집단에 대해 짧고 자연스러운 한국어 별칭(3~6글자)을 만들어 주세요. "
        "예: '수도권 관리자·전문가' → '수도권 화이트칼라', '비수도권 무직' → '지방 은퇴·비경제활동층'. "
        "직업군 의미를 살리되 딱딱한 원문 그대로 쓰지 말 것.\n\n"
    )
    for c in labels:
        prompt += f"- {c['core_id']}: {c['label']} (인구 {c['population']:,})\n"
    prompt += "\nJSON 배열로만 응답: [{\"core_id\":\"P01\",\"alias\":\"...\"}, ...]"

    body = json.dumps({
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 2000,
        "temperature": 0.7,
    }).encode()

    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=body,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
    )
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    with urllib.request.urlopen(req, timeout=60, context=ctx) as resp:
        data = json.loads(resp.read())
    content = data["choices"][0]["message"]["content"] or ""
    # JSON 배열 추출
    start = content.find("[")
    end = content.rfind("]")
    if start == -1 or end == -1:
        raise RuntimeError(f"응답에서 JSON을 찾을 수 없음: {content[:200]}")
    return json.loads(content[start:end + 1])


def main() -> None:
    import psycopg
    from psycopg.rows import dict_row

    key = load_key()
    with psycopg.connect(PG_DSN, row_factory=dict_row) as conn:
        labels = conn.execute(
            "SELECT core_id, label, population FROM core_persona ORDER BY population DESC"
        ).fetchall()

    print(f"Core Persona {len(labels)}개 → LLM 별칭 생성 중...")
    aliases = llm_name(key, labels)
    print("생성 결과:")
    for a in aliases:
        print(f"  {a['core_id']}: {a['alias']}")

    # 저장
    with psycopg.connect(PG_DSN) as conn:
        for a in aliases:
            conn.execute(
                "UPDATE core_persona SET alias = %s WHERE core_id = %s",
                (a["alias"], a["core_id"]),
            )
        conn.commit()
    print("저장 완료")


if __name__ == "__main__":
    main()
