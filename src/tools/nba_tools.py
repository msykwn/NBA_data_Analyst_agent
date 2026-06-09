"""NBA data retrieval tools for the data fetching agent."""

import time
from typing import Any

from nba_api.stats.endpoints import (
    commonplayerinfo,
    leaguedashplayerstats,
    leaguestandingsv3,
    playercareerstats,
    playergamelog,
    teamgamelog,
)
from nba_api.stats.static import players, teams
from strands import tool

DEFAULT_SEASON = "2024-25"
MAX_RETRIES = 3
RETRY_INTERVAL = 2.0


def _find_player(name: str) -> dict | None:
    """選手名(部分一致)でIDを解決する。見つからない場合はNoneを返す。"""
    results = players.find_players_by_full_name(name)
    if results:
        # アクティブな選手を優先
        active = [p for p in results if p["is_active"]]
        return active[0] if active else results[0]
    return None


def _find_player_candidates(name: str) -> list[str]:
    """選手名の候補リストを返す。"""
    results = players.find_players_by_full_name(name)
    if results:
        return [p["full_name"] for p in results[:5]]
    # 苗字・名前で再検索
    parts = name.strip().split()
    candidates = set()
    for part in parts:
        for p in players.find_players_by_last_name(part):
            candidates.add(p["full_name"])
        for p in players.find_players_by_first_name(part):
            candidates.add(p["full_name"])
    return list(candidates)[:5]


def _find_team(name: str) -> dict | None:
    """チーム名・略称(部分一致)でIDを解決する。見つからない場合はNoneを返す。"""
    results = teams.find_teams_by_full_name(name)
    if results:
        return results[0]
    # ニックネームで検索
    results = teams.find_teams_by_nickname(name)
    if results:
        return results[0]
    # 略称で検索
    result = teams.find_team_by_abbreviation(name.upper())
    if result:
        return result
    return None


def _find_team_candidates(name: str) -> list[str]:
    """チーム名の候補リストを返す。"""
    all_teams = teams.get_teams()
    name_lower = name.lower()
    candidates = [
        t["full_name"]
        for t in all_teams
        if name_lower in t["full_name"].lower()
        or name_lower in t["nickname"].lower()
        or name_lower in t["abbreviation"].lower()
        or name_lower in t["city"].lower()
    ]
    return candidates[:5]


def _call_with_retry(fn, *args, **kwargs) -> Any:
    """API呼び出しを最大MAX_RETRIES回リトライする。"""
    last_exc = None
    for attempt in range(MAX_RETRIES):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            last_exc = e
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_INTERVAL)
    raise last_exc


@tool
def get_player_stats(player_name: str, season: str = DEFAULT_SEASON) -> dict:
    """
    指定した選手の個人スタッツ(得点・リバウンド・アシスト・FG%・3P% 等)を取得する。

    Args:
        player_name: 選手名(例: "LeBron James")
        season: シーズン(例: "2024-25")。省略時は2024-25シーズン。

    Returns:
        選手のスタッツ情報を含むdict。選手が見つからない場合は候補リストを返す。
    """
    player = _find_player(player_name)
    if not player:
        candidates = _find_player_candidates(player_name)
        return {
            "found": False,
            "message": f"選手 '{player_name}' が見つかりませんでした。",
            "candidates": candidates,
        }

    career = _call_with_retry(playercareerstats.PlayerCareerStats, player_id=player["id"])
    df = career.season_totals_regular_season.get_data_frame()
    season_row = df[df["SEASON_ID"] == season]

    if season_row.empty:
        available = df["SEASON_ID"].tolist()
        return {
            "found": True,
            "player": player["full_name"],
            "message": f"シーズン '{season}' のデータが見つかりませんでした。",
            "available_seasons": available,
        }

    row = season_row.iloc[0].to_dict()
    games = row["GP"]
    return {
        "found": True,
        "player": player["full_name"],
        "season": season,
        "team": row["TEAM_ABBREVIATION"],
        "games_played": games,
        "stats_per_game": {
            "points": round(row["PTS"] / games, 1) if games else 0,
            "rebounds": round(row["REB"] / games, 1) if games else 0,
            "assists": round(row["AST"] / games, 1) if games else 0,
            "steals": round(row["STL"] / games, 1) if games else 0,
            "blocks": round(row["BLK"] / games, 1) if games else 0,
            "fg_pct": round(row["FG_PCT"] * 100, 1) if row["FG_PCT"] else 0,
            "fg3_pct": round(row["FG3_PCT"] * 100, 1) if row["FG3_PCT"] else 0,
            "ft_pct": round(row["FT_PCT"] * 100, 1) if row["FT_PCT"] else 0,
        },
        "stats_total": {
            "points": row["PTS"],
            "rebounds": row["REB"],
            "assists": row["AST"],
        },
    }


@tool
def get_player_recent_games(player_name: str, season: str = DEFAULT_SEASON, last_n: int = 5) -> dict:
    """
    指定した選手の直近の試合結果・スタッツを取得する。

    Args:
        player_name: 選手名(例: "LeBron James")
        season: シーズン(例: "2024-25")。省略時は2024-25シーズン。
        last_n: 取得する直近の試合数。デフォルトは5試合。

    Returns:
        直近の試合スタッツを含むdict。
    """
    player = _find_player(player_name)
    if not player:
        candidates = _find_player_candidates(player_name)
        return {
            "found": False,
            "message": f"選手 '{player_name}' が見つかりませんでした。",
            "candidates": candidates,
        }

    log = _call_with_retry(
        playergamelog.PlayerGameLog,
        player_id=player["id"],
        season=season,
    )
    df = log.player_game_log.get_data_frame()

    if df.empty:
        return {
            "found": True,
            "player": player["full_name"],
            "season": season,
            "message": "該当シーズンの試合データが見つかりませんでした。",
            "games": [],
        }

    recent = df.head(last_n)
    games = []
    for _, row in recent.iterrows():
        games.append({
            "date": row["GAME_DATE"],
            "matchup": row["MATCHUP"],
            "result": row["WL"],
            "minutes": row["MIN"],
            "points": row["PTS"],
            "rebounds": row["REB"],
            "assists": row["AST"],
            "fg_pct": round(row["FG_PCT"] * 100, 1) if row["FG_PCT"] else 0,
            "fg3_pct": round(row["FG3_PCT"] * 100, 1) if row["FG3_PCT"] else 0,
        })

    return {
        "found": True,
        "player": player["full_name"],
        "season": season,
        "last_n_games": len(games),
        "games": games,
    }


@tool
def get_team_standings(season: str = DEFAULT_SEASON) -> dict:
    """
    リーグ全チームの順位・成績を取得する。

    Args:
        season: シーズン(例: "2024-25")。省略時は2024-25シーズン。

    Returns:
        東西カンファレンス別の順位・成績を含むdict。
    """
    standings = _call_with_retry(
        leaguestandingsv3.LeagueStandingsV3,
        season=season,
    )
    df = standings.standings.get_data_frame()

    result = {"season": season, "East": [], "West": []}
    for _, row in df.iterrows():
        entry = {
            "rank": row["PlayoffRank"],
            "team": f"{row['TeamCity']} {row['TeamName']}",
            "wins": row["WINS"],
            "losses": row["LOSSES"],
            "win_pct": round(row["WINS"] / (row["WINS"] + row["LOSSES"]), 3) if (row["WINS"] + row["LOSSES"]) > 0 else 0,
            "conference_record": row["ConferenceRecord"],
            "division": row["Division"],
            "division_rank": row["DivisionRank"],
        }
        conf = row["Conference"]
        if conf == "East":
            result["East"].append(entry)
        else:
            result["West"].append(entry)

    result["East"].sort(key=lambda x: x["rank"])
    result["West"].sort(key=lambda x: x["rank"])
    return result


@tool
def get_team_game_log(team_name: str, season: str = DEFAULT_SEASON, last_n: int = 10) -> dict:
    """
    指定チームの直近の試合結果を取得する。

    Args:
        team_name: チーム名・略称・ニックネーム(例: "Lakers", "LAL", "Los Angeles Lakers")
        season: シーズン(例: "2024-25")。省略時は2024-25シーズン。
        last_n: 取得する直近の試合数。デフォルトは10試合。

    Returns:
        直近の試合結果を含むdict。チームが見つからない場合は候補リストを返す。
    """
    team = _find_team(team_name)
    if not team:
        candidates = _find_team_candidates(team_name)
        return {
            "found": False,
            "message": f"チーム '{team_name}' が見つかりませんでした。",
            "candidates": candidates,
        }

    log = _call_with_retry(
        teamgamelog.TeamGameLog,
        team_id=team["id"],
        season=season,
    )
    df = log.team_game_log.get_data_frame()

    if df.empty:
        return {
            "found": True,
            "team": team["full_name"],
            "season": season,
            "message": "該当シーズンの試合データが見つかりませんでした。",
            "games": [],
        }

    recent = df.head(last_n)
    games = []
    for _, row in recent.iterrows():
        games.append({
            "date": row["GAME_DATE"],
            "matchup": row["MATCHUP"],
            "result": row["WL"],
            "points": row["PTS"],
            "wins": row["W"],
            "losses": row["L"],
        })

    return {
        "found": True,
        "team": team["full_name"],
        "season": season,
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
    player = _find_player(player_name)
    if not player:
        candidates = _find_player_candidates(player_name)
        return {
            "found": False,
            "message": f"選手 '{player_name}' が見つかりませんでした。",
            "candidates": candidates,
        }

    info = _call_with_retry(commonplayerinfo.CommonPlayerInfo, player_id=player["id"])
    df = info.common_player_info.get_data_frame()
    row = df.iloc[0]

    return {
        "found": True,
        "player": player["full_name"],
        "is_active": player["is_active"],
        "team": row["TEAM_NAME"],
        "team_abbreviation": row["TEAM_ABBREVIATION"],
        "position": row["POSITION"],
        "jersey": row["JERSEY"],
    }


@tool
def get_position_avg_stats(position: str, season: str = DEFAULT_SEASON) -> dict:
    """
    指定ポジションの選手群の平均スタッツを取得する。

    Args:
        position: ポジション略称("G"=Guard, "F"=Forward, "C"=Center)またはフルネーム
        season: シーズン(例: "2024-25")。省略時は2024-25シーズン。

    Returns:
        指定ポジションの平均スタッツを含むdict。
    """
    # nba_api の player_position_abbreviation_nullable は "G", "F", "C" を受け付ける
    position_abbrev_map = {
        "G": "G", "F": "F", "C": "C",
        "Guard": "G", "Forward": "F", "Center": "C",
        "guard": "G", "forward": "F", "center": "C",
        "PG": "G", "SG": "G", "SF": "F", "PF": "F",
    }
    position_label_map = {"G": "Guard", "F": "Forward", "C": "Center"}

    abbrev = position_abbrev_map.get(position)
    if not abbrev:
        return {
            "found": False,
            "message": f"ポジション '{position}' は認識できません。",
            "available_positions": ["G (Guard)", "F (Forward)", "C (Center)"],
        }

    stats = _call_with_retry(
        leaguedashplayerstats.LeagueDashPlayerStats,
        season=season,
        per_mode_detailed="PerGame",
        player_position_abbreviation_nullable=abbrev,
    )
    df = stats.league_dash_player_stats.get_data_frame()

    if df.empty:
        return {
            "found": False,
            "message": f"ポジション '{position}' に該当する選手が見つかりませんでした。",
        }

    avg = df[["PTS", "REB", "AST", "STL", "BLK", "FG_PCT", "FG3_PCT", "FT_PCT"]].mean()

    return {
        "found": True,
        "position": position_label_map[abbrev],
        "season": season,
        "player_count": len(df),
        "avg_stats_per_game": {
            "points": round(float(avg["PTS"]), 1),
            "rebounds": round(float(avg["REB"]), 1),
            "assists": round(float(avg["AST"]), 1),
            "steals": round(float(avg["STL"]), 1),
            "blocks": round(float(avg["BLK"]), 1),
            "fg_pct": round(float(avg["FG_PCT"]) * 100, 1),
            "fg3_pct": round(float(avg["FG3_PCT"]) * 100, 1),
            "ft_pct": round(float(avg["FT_PCT"]) * 100, 1),
        },
    }
