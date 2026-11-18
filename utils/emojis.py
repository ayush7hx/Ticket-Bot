from __future__ import annotations

import base64

import aiohttp


_SOURCE_IDS = {
    "success": "1518137986095644703",
    "cross": "1518137821355966494",
    "info": "1517892973482868960",
    "warn": "1518063335923257386",
    "ticket": "1513730006910500977",
    "bug": "1518063885855358996",
    "claim": "1518064508948447242",
    "view": "1518064705854373969",
    "reopen": "1518064251405733898",
    "question": "1518064034862076007",
    "delete": "1518064106723217418",
    "setup": "1518064880769568828",
    "customize": "1518065679041957989",
}

_EMOJIS = {
    "success": "✅",
    "cross": "❌",
    "info": "ℹ️",
    "warn": "⚠️",
    "ticket": "🎫",
    "bug": "🐛",
    "claim": "📌",
    "view": "👁️",
    "reopen": "🔄",
    "question": "❓",
    "delete": "🗑️",
    "setup": "⚙️",
    "customize": "✏️",
}


def get_emoji(name: str) -> str:
    return _EMOJIS[name]


async def sync_application_emojis(application_id: int, token: str) -> int:
    headers = {"Authorization": f"Bot {token}"}
    base_url = f"https://discord.com/api/v10/applications/{application_id}/emojis"
    timeout = aiohttp.ClientTimeout(total=30)

    async with aiohttp.ClientSession(headers=headers, timeout=timeout) as session:
        async with session.get(base_url) as response:
            if response.status >= 400:
                body = await response.text()
                raise RuntimeError(f"Could not list application emojis ({response.status}): {body[:500]}")
            data = await response.json()

        existing = {
            item["name"]: item
            for item in data.get("items", [])
            if isinstance(item.get("name"), str) and item.get("id")
        }
        created = 0

        for name, source_id in _SOURCE_IDS.items():
            emoji = existing.get(name)
            if emoji is None:
                image_url = f"https://cdn.discordapp.com/emojis/{source_id}.png?size=128"
                async with session.get(image_url) as response:
                    if response.status >= 400:
                        raise RuntimeError(
                            f"Could not download source emoji {name} ({response.status})"
                        )
                    image = await response.read()

                if len(image) > 262144 or not image.startswith(b"\x89PNG\r\n\x1a\n"):
                    raise RuntimeError(f"Source emoji {name} is not a valid PNG under 256 KiB")

                payload = {
                    "name": name,
                    "image": "data:image/png;base64," + base64.b64encode(image).decode("ascii"),
                }
                async with session.post(base_url, json=payload) as response:
                    if response.status >= 400:
                        body = await response.text()
                        raise RuntimeError(
                            f"Could not create application emoji {name} "
                            f"({response.status}): {body[:500]}"
                        )
                    emoji = await response.json()
                created += 1

            _EMOJIS[name] = f"<:{name}:{emoji['id']}>"

    return created
