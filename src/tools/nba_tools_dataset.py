"""データセットモードの NBA データ取得ツール。

data/nba_dataset.json から事前取得済みデータを返す。
AgentCore Runtime 上での動作用（stats.nba.com へのアクセス不要）。
"""

import json
from functools import lru_cache
from pathlib import Path

from strands import tool

_DATASET_PATH = Path(__file__).parent.parent.parent / "data" / "nba_dataset.json"


@lru_cache(maxsize=1)
def _load_dataset() -> dict:
    if not _DATASET_PATH.exists():
        raise FileNotFoundError(
            f"データセットファイルが見つかりません: {_DATASET_PATH}\n"
            "scripts/generate_dataset.py を実行してデータセットを生成してください。"
        )
    with open(_DATASET_PATH, encoding="utf-8") as f:
        return json.load(f)


def _find_player(name: str) -> tuple[dict | None, list[str]]:
    """名前（部分一致）で選手データを検索する。"""
    dataset = _load_dataset()
    name_lower = name.lower()
    matches = [
        (full_name, data)
        for full_name, data in dataset["players"].items()
        if name_lower in full_name.lower()
    ]
    if not matches:
        candidates = [
            full_name
            for full_name in dataset["players"]
            if any(part.lower() in full_name.lower() for part in name.split())
        ]
        return None, candidates[:5]
    # 完全一致優先
    exact = [(n, d) for n, d in matches if n.lower() == name_lower]
    full_name, data = (exact or matches)[0]
    return {"full_name": full_name, **data}, []


def _find_team(name: str) -> tuple[dict | None, list[str]]:
    """名前・略称（部分一致）でチームデータを検索する。"""
    dataset = _load_dataset()
    name_lower = name.lower()
    for full_name, data in dataset["teams"].items():
        if (
            name_lower in full_name.lower()
            or name_lower == data.get("abbreviation", "").lower()
        ):
            return {"full_name": full_name, **data}, []
    candidates = [n for n in dataset["teams"]]
    return None, candidates


@tool
def get_player_stats(player_name: str, season: str = "") -> dict:
    """
    指定した選手の個人スタッツ(得点・リバウンド・アシスト・FG%・3P% 等)を取得する。

    Args:
        player_name: 選手名(例: "LeBron James")
        season: シーズン(例: "2024-25")。データセットのシーズンと異なる場合は対象外となる。

    Returns:
        選手のスタッツ情報を含むdict。選手が見つからない場合は候補リストを返す。
    """
    player, candidates = _find_player(player_name)
    if not player:
        return {
            "found": False,
            "message": f"選手 '{player_name}' はデータセットに含まれていません。",
            "candidates": candidates,
        }

    stats = player.get("stats")
    dataset_season = _load_dataset()["season"]

    if season and season != dataset_season:
        return {
            "found": True,
            "player": player["full_name"],
            "message": f"シーズン '{season}' のデータはありません。利用可能なシーズン: {dataset_season}",
        }

    if not stats:
        return {
            "found": True,
            "player": player["full_name"],
            "message": f"シーズン '{dataset_season}' のスタッツデータがありません。",
        }

    return {
        "found": True,
        "player": player["full_name"],
        "season": stats["season"],
        "team": stats["team"],
        "games_played": stats["games_played"],
        "stats_per_game": stats["stats_per_game"],
        "stats_total": stats["stats_total"],
    }


@tool
def get_player_recent_games(player_name: str, season: str = "", last_n: int = 5) -> dict:
    """
    指定した選手の直近の試合結果・スタッツを取得する。

    Args:
        player_name: 選手名(例: "LeBron James")
        season: シーズン(例: "2024-25")。省略時はデータセットのシーズンを使用。
        last_n: 取得する直近の試合数。デフォルトは5試合。

    Returns:
        直近の試合スタッツを含むdict。
    """
    player, candidates = _find_player(player_name)
    if not player:
        return {
            "found": False,
            "message": f"選手 '{player_name}' はデータセットに含まれていません。",
            "candidates": candidates,
        }

    dataset_season = _load_dataset()["season"]
    games = player.get("recent_games", [])[:last_n]

    return {
        "found": True,
        "player": player["full_name"],
        "season": dataset_season,
        "last_n_games": len(games),
        "games": games,
    }


@tool
def get_player_info(player_name: str) -> dict:
    """
    指定した選手の所属チーム・ポジション情報を取得する。

    Args:
        player_name: 選手名(例: "LeBron James")

    Returns:
        選手の所属チーム・ポジション情報を含むdict。
    """
    player, candidates = _find_player(player_name)
    if not player:
        return {
            "found": False,
            "message": f"選手 '{player_name}' はデータセットに含まれていません。",
            "candidates": candidates,
        }

    info = player.get("info")
    if not info:
        return {
            "found": False,
            "message": f"選手 '{player['full_name']}' のプロフィール情報がありません。",
            "candidates": [],
        }

    return {
        "found": True,
        "player": player["full_name"],
        "is_active": info["is_active"],
        "team": info["team"],
        "team_abbreviation": info["team_abbreviation"],
        "position": info["position"],
        "jersey": info["jersey"],
    }


@tool
def get_team_standings(season: str = "") -> dict:
    """
    リーグ全チームの順位・成績を取得する。

    Args:
        season: シーズン(例: "2024-25")。省略時はデータセットのシーズンを使用。

    Returns:
        東西カンファレンス別の順位・成績を含むdict。
    """
    dataset = _load_dataset()
    return dataset["standings"]


@tool
def get_team_game_log(team_name: str, season: str = "", last_n: int = 10) -> dict:
    """
    指定チームの直近の試合結果を取得する。

    Args:
        team_name: チーム名・略称・ニックネーム(例: "Celtics", "BOS", "Boston Celtics")
        season: シーズン(例: "2024-25")。省略時はデータセットのシーズンを使用。
        last_n: 取得する直近の試合数。デフォルトは10試合。

    Returns:
        直近の試合結果を含むdict。チームが見つからない場合は候補リストを返す。
    """
    team, candidates = _find_team(team_name)
    if not team:
        return {
            "found": False,
            "message": f"チーム '{team_name}' はデータセットに含まれていません。利用可能なチーム: {candidates}",
            "candidates": candidates,
        }

    dataset_season = _load_dataset()["season"]
    games = team.get("game_log", [])[:last_n]

    return {
        "found": True,
        "team": team["full_name"],
        "season": dataset_season,
        "last_n_games": len(games),
        "games": games,
    }


@tool
def get_position_avg_stats(position: str, season: str = "") -> dict:
    """
    指定ポジションの選手群の平均スタッツを取得する。

    Args:
        position: ポジション略称("G"=Guard, "F"=Forward, "C"=Center)またはフルネーム
        season: シーズン(例: "2024-25")。省略時はデータセットのシーズンを使用。

    Returns:
        指定ポジションの平均スタッツを含むdict。
    """
    position_abbrev_map = {
        "G": "G", "F": "F", "C": "C",
        "Guard": "G", "Forward": "F", "Center": "C",
        "guard": "G", "forward": "F", "center": "C",
        "PG": "G", "SG": "G", "SF": "F", "PF": "F",
    }

    abbrev = position_abbrev_map.get(position)
    if not abbrev:
        return {
            "found": False,
            "message": f"ポジション '{position}' は認識できません。",
            "available_positions": ["G (Guard)", "F (Forward)", "C (Center)"],
        }

    dataset = _load_dataset()
    data = dataset.get("position_avg_stats", {}).get(abbrev)
    if not data:
        return {
            "found": False,
            "message": f"ポジション '{position}' のデータがありません。",
        }

    return {"found": True, **data}
