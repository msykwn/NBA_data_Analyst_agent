"""データセット生成スクリプト。

nba_api を使って以下のデータを取得し、data/ ディレクトリに JSON として保存する。
- 得点ランキング上位30名の各種スタッツ
- セルティックス全選手の各種スタッツ

使い方:
    aws-vault exec piyo --no-session -- uv run python scripts/generate_dataset.py
"""

import json
import time
from pathlib import Path

from nba_api.stats.endpoints import (
    commonplayerinfo,
    leaguedashplayerstats,
    leaguestandingsv3,
    playercareerstats,
    playergamelog,
    teamgamelog,
)
from nba_api.stats.static import players, teams

DATA_DIR = Path(__file__).parent.parent / "data"
SEASON = "2024-25"
CELTICS_ABBREV = "BOS"
TOP_SCORERS_COUNT = 30
RECENT_GAMES_COUNT = 10
SLEEP_INTERVAL = 0.6  # stats.nba.com のレート制限対策


def _pct(value) -> float | None:
    import pandas as pd
    if pd.isna(value):
        return None
    return round(float(value) * 100, 1)


def fetch_top_scorer_player_ids() -> list[int]:
    """得点ランキング上位30名の選手IDを取得する。"""
    print(f"得点ランキング上位{TOP_SCORERS_COUNT}名を取得中...")
    stats = leaguedashplayerstats.LeagueDashPlayerStats(
        season=SEASON,
        per_mode_detailed="PerGame",
    )
    df = stats.league_dash_player_stats.get_data_frame()
    df = df.sort_values("PTS", ascending=False).head(TOP_SCORERS_COUNT)
    return df["PLAYER_ID"].tolist()


def fetch_celtics_player_ids() -> list[int]:
    """セルティックスの全選手IDを取得する。"""
    print("セルティックス選手を取得中...")
    team = teams.find_team_by_abbreviation(CELTICS_ABBREV)
    stats = leaguedashplayerstats.LeagueDashPlayerStats(
        season=SEASON,
        per_mode_detailed="PerGame",
        team_id_nullable=team["id"],
    )
    df = stats.league_dash_player_stats.get_data_frame()
    return df["PLAYER_ID"].tolist()


def fetch_player_stats(player_id: int) -> dict | None:
    """選手のシーズンスタッツを取得する。"""
    try:
        career = playercareerstats.PlayerCareerStats(player_id=player_id)
        df = career.season_totals_regular_season.get_data_frame()
        season_rows = df[df["SEASON_ID"] == SEASON]
        if season_rows.empty:
            return None
        tot = season_rows[season_rows["TEAM_ABBREVIATION"] == "TOT"]
        row = (tot if not tot.empty else season_rows).iloc[0].to_dict()
        games = row["GP"]
        return {
            "season": SEASON,
            "team": row["TEAM_ABBREVIATION"],
            "games_played": games,
            "stats_per_game": {
                "points": round(row["PTS"] / games, 1) if games else 0,
                "rebounds": round(row["REB"] / games, 1) if games else 0,
                "assists": round(row["AST"] / games, 1) if games else 0,
                "steals": round(row["STL"] / games, 1) if games else 0,
                "blocks": round(row["BLK"] / games, 1) if games else 0,
                "fg_pct": _pct(row["FG_PCT"]),
                "fg3_pct": _pct(row["FG3_PCT"]),
                "ft_pct": _pct(row["FT_PCT"]),
            },
            "stats_total": {
                "points": row["PTS"],
                "rebounds": row["REB"],
                "assists": row["AST"],
            },
        }
    except Exception as e:
        print(f"  警告: スタッツ取得失敗 player_id={player_id}: {e}")
        return None


def fetch_player_recent_games(player_id: int) -> list[dict]:
    """選手の直近試合ログを取得する。"""
    try:
        log = playergamelog.PlayerGameLog(player_id=player_id, season=SEASON)
        df = log.player_game_log.get_data_frame()
        games = []
        for _, row in df.head(RECENT_GAMES_COUNT).iterrows():
            games.append({
                "date": row["GAME_DATE"],
                "matchup": row["MATCHUP"],
                "result": row["WL"],
                "minutes": row["MIN"],
                "points": row["PTS"],
                "rebounds": row["REB"],
                "assists": row["AST"],
                "fg_pct": _pct(row["FG_PCT"]),
                "fg3_pct": _pct(row["FG3_PCT"]),
            })
        return games
    except Exception as e:
        print(f"  警告: 試合ログ取得失敗 player_id={player_id}: {e}")
        return []


def fetch_player_info(player_id: int) -> dict | None:
    """選手のプロフィール情報を取得する。"""
    try:
        info = commonplayerinfo.CommonPlayerInfo(player_id=player_id)
        df = info.common_player_info.get_data_frame()
        if df.empty:
            return None
        row = df.iloc[0]
        player = next((p for p in players.get_players() if p["id"] == player_id), None)
        return {
            "is_active": player["is_active"] if player else True,
            "team": row["TEAM_NAME"],
            "team_abbreviation": row["TEAM_ABBREVIATION"],
            "position": row["POSITION"],
            "jersey": row["JERSEY"],
        }
    except Exception as e:
        print(f"  警告: プロフィール取得失敗 player_id={player_id}: {e}")
        return None


def fetch_standings() -> dict:
    """リーグ順位を取得する。"""
    print("リーグ順位を取得中...")
    standings = leaguestandingsv3.LeagueStandingsV3(season=SEASON)
    df = standings.standings.get_data_frame()
    result: dict = {"season": SEASON, "East": [], "West": []}
    for _, row in df.iterrows():
        conf = row["Conference"]
        if conf not in ("East", "West"):
            continue
        import pandas as pd
        result[conf].append({
            "rank": int(row["PlayoffRank"]) if pd.notna(row["PlayoffRank"]) else 999,
            "team": f"{row['TeamCity']} {row['TeamName']}",
            "wins": row["WINS"],
            "losses": row["LOSSES"],
            "win_pct": round(row["WINS"] / (row["WINS"] + row["LOSSES"]), 3) if (row["WINS"] + row["LOSSES"]) > 0 else None,
            "conference_record": row["ConferenceRecord"],
            "division": row["Division"],
            "division_rank": row["DivisionRank"],
        })
    result["East"].sort(key=lambda x: x["rank"])
    result["West"].sort(key=lambda x: x["rank"])
    return result


def fetch_team_game_log(team_id: int) -> list[dict]:
    """チームの直近試合ログを取得する。"""
    try:
        log = teamgamelog.TeamGameLog(team_id=team_id, season=SEASON)
        df = log.team_game_log.get_data_frame()
        games = []
        for _, row in df.head(RECENT_GAMES_COUNT).iterrows():
            games.append({
                "date": row["GAME_DATE"],
                "matchup": row["MATCHUP"],
                "result": row["WL"],
                "points": row["PTS"],
                "wins": row["W"],
                "losses": row["L"],
            })
        return games
    except Exception as e:
        print(f"  警告: チーム試合ログ取得失敗 team_id={team_id}: {e}")
        return []


def fetch_position_avg_stats() -> dict:
    """ポジション別平均スタッツを取得する。"""
    import pandas as pd
    print("ポジション別平均スタッツを取得中...")
    result = {}
    position_map = {"G": "Guard", "F": "Forward", "C": "Center"}
    for abbrev, label in position_map.items():
        try:
            stats = leaguedashplayerstats.LeagueDashPlayerStats(
                season=SEASON,
                per_mode_detailed="PerGame",
                player_position_abbreviation_nullable=abbrev,
            )
            df = stats.league_dash_player_stats.get_data_frame()
            avg = df[["PTS", "REB", "AST", "STL", "BLK", "FG_PCT", "FG3_PCT", "FT_PCT"]].mean()
            result[abbrev] = {
                "position": label,
                "season": SEASON,
                "player_count": len(df),
                "avg_stats_per_game": {
                    "points": round(float(avg["PTS"]), 1) if pd.notna(avg["PTS"]) else None,
                    "rebounds": round(float(avg["REB"]), 1) if pd.notna(avg["REB"]) else None,
                    "assists": round(float(avg["AST"]), 1) if pd.notna(avg["AST"]) else None,
                    "steals": round(float(avg["STL"]), 1) if pd.notna(avg["STL"]) else None,
                    "blocks": round(float(avg["BLK"]), 1) if pd.notna(avg["BLK"]) else None,
                    "fg_pct": round(float(avg["FG_PCT"]) * 100, 1) if pd.notna(avg["FG_PCT"]) else None,
                    "fg3_pct": round(float(avg["FG3_PCT"]) * 100, 1) if pd.notna(avg["FG3_PCT"]) else None,
                    "ft_pct": round(float(avg["FT_PCT"]) * 100, 1) if pd.notna(avg["FT_PCT"]) else None,
                },
            }
            time.sleep(SLEEP_INTERVAL)
        except Exception as e:
            print(f"  警告: ポジション {abbrev} の取得失敗: {e}")
    return result


def main():
    DATA_DIR.mkdir(exist_ok=True)

    # 対象選手IDを収集
    top_scorer_ids = fetch_top_scorer_player_ids()
    time.sleep(SLEEP_INTERVAL)
    celtics_ids = fetch_celtics_player_ids()
    time.sleep(SLEEP_INTERVAL)

    target_ids = list(set(top_scorer_ids + celtics_ids))
    print(f"対象選手数: {len(target_ids)}名（上位{TOP_SCORERS_COUNT}名 + セルティックス）\n")

    # 選手データを収集
    players_data = {}
    all_players = {p["id"]: p for p in players.get_players()}

    for i, player_id in enumerate(target_ids, 1):
        player = all_players.get(player_id)
        if not player:
            continue
        name = player["full_name"]
        print(f"[{i}/{len(target_ids)}] {name} を取得中...")

        stats = fetch_player_stats(player_id)
        time.sleep(SLEEP_INTERVAL)
        recent_games = fetch_player_recent_games(player_id)
        time.sleep(SLEEP_INTERVAL)
        info = fetch_player_info(player_id)
        time.sleep(SLEEP_INTERVAL)

        players_data[name] = {
            "id": player_id,
            "full_name": name,
            "info": info,
            "stats": stats,
            "recent_games": recent_games,
        }

    # チームデータ（セルティックス）
    celtics = teams.find_team_by_abbreviation(CELTICS_ABBREV)
    print(f"\n{celtics['full_name']} の試合ログを取得中...")
    celtics_game_log = fetch_team_game_log(celtics["id"])
    time.sleep(SLEEP_INTERVAL)

    teams_data = {
        celtics["full_name"]: {
            "id": celtics["id"],
            "abbreviation": CELTICS_ABBREV,
            "game_log": celtics_game_log,
        }
    }

    # 順位
    standings = fetch_standings()
    time.sleep(SLEEP_INTERVAL)

    # ポジション別平均
    position_avg = fetch_position_avg_stats()

    # 保存
    output = {
        "season": SEASON,
        "generated_at": __import__("datetime").date.today().isoformat(),
        "players": players_data,
        "teams": teams_data,
        "standings": standings,
        "position_avg_stats": position_avg,
    }

    output_path = DATA_DIR / "nba_dataset.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\nデータセット生成完了: {output_path}")
    print(f"  選手数: {len(players_data)}")
    print(f"  チーム数: {len(teams_data)}")


if __name__ == "__main__":
    main()
