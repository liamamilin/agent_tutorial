"""
第 4 章：工具系统 — 工具函数

包含天气查询和景点推荐两个工具。
"""

import requests
from urllib.parse import quote


def get_weather(city: str) -> str:
    """查询指定城市的实时天气（使用 wttr.in 免费服务）"""
    try:
        url = f"https://wttr.in/{quote(city)}?format=j1&lang=zh"
        resp = requests.get(
            url,
            headers={"User-Agent": "weather-agent/0.1"},
            timeout=8,
        )
        resp.raise_for_status()
        data = resp.json()

        current = data["current_condition"][0]
        desc = current["weatherDesc"][0]["value"]
        temp = current["temp_C"]

        return f"{city} 当前天气：{desc}，气温 {temp}°C"

    except Exception as e:
        return f"错误：查询天气失败 - {e}"


def get_attraction(city: str, weather: str) -> str:
    """根据城市和天气推荐旅游景点"""
    city = city.strip()
    weather_lower = weather.lower()

    # 天气 → 出行类型
    if any(w in weather_lower for w in ["雨", "rain", "snow", "雪", "storm", "小雨", "中雨", "大雨"]):
        scene = "indoor"
    elif any(w in weather_lower for w in ["晴", "sunny", "clear"]):
        scene = "outdoor"
    else:
        scene = "mixed"

    # 城市 → 景点库
    attraction_db = {
        "北京": {
            "outdoor": ["颐和园", "天坛公园", "八达岭长城"],
            "mixed":   ["故宫", "什刹海"],
            "indoor":  ["中国国家博物馆", "中国美术馆"],
        },
        "上海": {
            "outdoor": ["外滩", "世纪公园"],
            "mixed":   ["豫园", "新天地"],
            "indoor":  ["上海博物馆", "中华艺术宫"],
        },
        "杭州": {
            "outdoor": ["西湖", "九溪十八涧"],
            "mixed":   ["灵隐寺"],
            "indoor":  ["浙江省博物馆"],
        },
        "长沙": {
            "outdoor": ["岳麓山", "橘子洲头"],
            "mixed":   ["太平街", "坡子街"],
            "indoor":  ["湖南省博物馆"],
        },
    }

    # 城市名映射（支持英文输入）
    city_map = {"Beijing": "北京", "Shanghai": "上海",
                "Hangzhou": "杭州", "Changsha": "长沙"}
    city = city_map.get(city, city)

    if city not in attraction_db:
        return f"我暂时没有 {city} 的详细景点数据，建议选择当地知名景点游览。"

    recs = attraction_db[city][scene]
    scene_name = {"outdoor": "户外", "indoor": "室内", "mixed": "灵活选择"}[scene]

    return (
        f"{city} 当前天气适合游览【{scene_name}景点】。\n"
        f"推荐景点：{'、'.join(recs)}"
    )


# ============================================================
# 独立测试
# ============================================================
if __name__ == "__main__":
    print("--- 测试 get_weather ---")
    print(get_weather("Beijing"))

    print("\n--- 测试 get_attraction ---")
    print(get_attraction("Hangzhou", "Sunny"))
    print()
    print(get_attraction("Beijing", "雨"))
