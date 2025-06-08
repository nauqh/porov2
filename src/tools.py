import requests
import time
import pandas as pd
import re
import json
import os
from dotenv import load_dotenv

load_dotenv()


def search_youtube(query, max_results=5):
    """
    Search YouTube and retrieve video links based on a search query.

    Args:
        query (str): The search term or phrase to look up on YouTube
        max_results (int, optional): Maximum number of video links to return. Defaults to 5.

    Returns:
        list[str]: A list of YouTube video URLs matching the search query.
                  Returns an empty list if no results are found or if there's an error.

    Example:
        >>> get_youtube_search_results("python tutorial")
        ['https://www.youtube.com/watch?v=hVzlmOomLRU,'https://www.youtube.com/watch?v=Zq5fmkH0T78']
    """
    # Build search URL (replace spaces with '+')
    url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"

    # Basic desktop User-Agent to reduce chance of blocks or alternate HTML
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36"
        )
    }
    response = requests.get(url, headers=headers)

    # 1. Extract JSON from 'ytInitialData'
    match = re.search(r"var ytInitialData = ({.*?});", response.text)
    if not match:
        return []

    data = json.loads(match.group(1))

    # 2. Traverse JSON to find videoRenderer -> videoId
    try:
        sections = data["contents"]["twoColumnSearchResultsRenderer"]["primaryContents"]["sectionListRenderer"]["contents"]
    except KeyError:
        return []

    video_links = []
    for section in sections:
        items = section.get("itemSectionRenderer", {}).get("contents", [])
        for item in items:
            video_data = item.get("videoRenderer")
            if video_data and "videoId" in video_data:
                video_id = video_data["videoId"]
                video_links.append(
                    f"https://www.youtube.com/watch?v={video_id}")
                if len(video_links) >= max_results:
                    return video_links[0]

    return video_links


class RiotAPI:
    def __init__(self, token):
        self.token = token

    def _make_request(self, url):
        while True:
            resp = requests.get(url)
            if resp.status_code == 429:
                print("Rate limit hit. Sleeping 10s...")
                time.sleep(10)
            elif resp.status_code == 404:
                print("Resource not found:", url)
                return None
            else:
                resp.raise_for_status()
                return resp.json()

    def get_match_ids(self, puuid, no_games=1, queue_id=450):
        url = (
            f"https://sea.api.riotgames.com/lol/match/v5/matches/by-puuid/"
            f"{puuid}/ids?start=0&count={no_games}&queue={queue_id}&api_key={self.token}"
        )
        return self._make_request(url) or []

    def get_match_data(self, match_id):
        url = f"https://sea.api.riotgames.com/lol/match/v5/matches/{match_id}?api_key={self.token}"
        return self._make_request(url)


def get_puuid_from_discord(username: str) -> str:
    PUUIDS = {
        'tuandao1311': '8UIhStkspIglog9paowA4mXzlckT-xySwWNIFac3o2ojumva9ffkFMda_jGpW_hhInKWpvUp5pPPrA',
        'cozybearrrrr': 'mh3B8Naz1MbJ6RE7dJTu3ZCLh7Rwo6CCJQiA-fVlLXUuQmkibMVMztpCLALJMMJQm4QOevN1-u0lnA',
        'tuanardo': 'DV0Aad31H16g3lItoojolWMPZQYOj0l90KzVSUV-qF3QlF92hOC_WLLssdR1MqPS-3UMEKp0Mn5woA',
        'nauqh': 'aTa5_43m0w8crNsi-i9nxGpSVU06WZBuK-h9bZEOK0g_lJox3XF4Dv4BzVwZieRj0QwlGnJ4SZbftg',
        'wavepin': 'idASdW5eSrO5Oih-ViK07RdeXE33JM1Mm3FwV7JiveTwbqfjl1vQUvToJ95c1B4EeQd8BAZgXkGSUw',
    }
    return PUUIDS.get(username)


def get_latest_teammates_df(puuid: str) -> list[dict]:
    """
    Retrieves the latest match data for the given player (by PUUID) and returns
    a list of dictionaries representing all players' performance in the most recent match.
    Item IDs are automatically converted to item names and Hidden Impact Scores are calculated
    for each team separately.

    Parameters:
    - puuid: The Riot PUUID of the player
    - queue_id: Match type queue (default is 450 for ARAM)

    Returns:
    - List[dict]: List of all 10 players' stats with item names and Hidden Impact Scores
    """
    TOKEN = os.environ["RIOT_TOKEN"]
    api = RiotAPI(TOKEN)

    match_ids = api.get_match_ids(puuid, no_games=1, queue_id=450)
    if not match_ids:
        raise ValueError("No recent matches found for this PUUID.")

    match_data = api.get_match_data(match_ids[0])
    df = pd.json_normalize(match_data["info"]["participants"])
    df["matchId"] = match_data["metadata"]["matchId"]

    player_team_id = df.loc[df["puuid"] == puuid, "teamId"]
    if player_team_id.empty:
        raise ValueError("Player's team ID not found in match data.")

    required_columns = [
        "matchId",
        "riotIdGameName",
        "championName",
        "kills", "deaths", "assists",
        "goldEarned",
        "totalDamageDealtToChampions",
        "totalDamageTaken",
        "totalTimeCCDealt",
        "physicalDamageDealtToChampions",
        "magicDamageDealtToChampions",
        "trueDamageDealtToChampions",
        "challenges.killParticipation",
        "firstBloodKill", "firstBloodAssist",
        "firstTowerKill", "firstTowerAssist",
        "totalHealsOnTeammates",
        "win", "teamId", "puuid",
        "item0", "item1", "item2", "item3", "item4", "item5", "item6"
    ]

    team_df = df[required_columns].copy()

    # Convert item IDs to item names for all players
    item_columns = ["item0", "item1", "item2",
                    "item3", "item4", "item5", "item6"]

    for item_col in item_columns:
        team_df[item_col] = team_df[item_col].apply(
            lambda item_id: get_item_name(
                item_id) if item_id != 0 else "No Item"
        )

    # Calculate Hidden Impact Scores for each team separately
    def calculate_team_hidden_scores(team_id):
        team_players = team_df[team_df['teamId'] == team_id].copy()

        # Calculate team totals for normalization
        team_totals = {
            'damage': team_players['totalDamageDealtToChampions'].sum(),
            'damageTaken': team_players['totalDamageTaken'].sum(),
            'ccTime': team_players['totalTimeCCDealt'].sum(),
            # minimum 1000 for division
            'healing': max(team_players['totalHealsOnTeammates'].sum(), 1000)
        }

        # Calculate Hidden Impact Score for each player in this team
        def calculate_hidden_impact_score(row):
            # Weighted formula: Damage=3.0x, DamageTaken=1.0x, CC=1.0x, Healing=0.5x
            dmg_dealt = (
                row['totalDamageDealtToChampions'] / team_totals['damage']
            ) * 5 * 3.0
            dmg_taken = (
                row['totalDamageTaken'] / team_totals['damageTaken']
            ) * 5 * 1.0
            cc = min(2.0, (
                row['totalTimeCCDealt'] / team_totals['ccTime']
            ) * 5) * 1.0
            healing = min(1.0, (
                row['totalHealsOnTeammates'] / team_totals['healing']
            ) * 5) * 0.5

            return dmg_dealt + dmg_taken + cc + healing

        team_players['hiddenImpactScore'] = team_players.apply(
            calculate_hidden_impact_score, axis=1)
        return team_players

    # Process both teams
    team_100 = calculate_team_hidden_scores(100)
    team_200 = calculate_team_hidden_scores(200)

    # Combine both teams back together
    final_df = pd.concat([team_100, team_200], ignore_index=True)

    # Add a field to identify the target player's team
    target_team_id = player_team_id.iloc[0]
    final_df['isPlayerTeam'] = final_df['teamId'] == target_team_id

    # Sort by team (player's team first) and then by Hidden Impact Score within each team
    final_df = final_df.sort_values(
        ['isPlayerTeam', 'hiddenImpactScore'], ascending=[False, False])

    final_df.to_csv("final_df.csv")

    return final_df.to_dict(orient="records")


def get_item_name(item_id: int) -> str:
    """
    Given an item ID, returns the corresponding item name from Riot's Data Dragon.

    Args:
        item_id (int): The item ID (e.g. 1001).
        version (str): The patch version to use (default "15.11.1").

    Returns:
        str: The name of the item, or 'Unknown Item' if not found.
    """
    if item_id == 0:
        return "No Item"

    version = requests.get(
        "https://ddragon.leagueoflegends.com/api/versions.json").json()[0]
    url = f"https://ddragon.leagueoflegends.com/cdn/{version}/data/en_US/item.json"
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()["data"]

    return data.get(str(item_id), {}).get("name", "Unknown Item")


if __name__ == "__main__":
    puuid = get_puuid_from_discord("nauqh")
    data = get_latest_teammates_df(puuid)

    get_item_name(3032)

    print(data)
