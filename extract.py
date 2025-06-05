import requests
import time
import pandas as pd


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


def get_latest_match_data(api: RiotAPI, player_name: str, queue_id=450) -> dict:
    puuid = get_puuid_from_discord(player_name)
    if not puuid:
        raise ValueError(f"Username '{player_name}' not found.")

    match_ids = api.get_match_ids(puuid, no_games=1, queue_id=queue_id)
    if not match_ids:
        raise ValueError(f"No recent matches found for '{player_name}'.")

    return api.get_match_data(match_ids[0])


def extract_teammates_df(match_data: dict, player_name: str) -> pd.DataFrame:
    puuid = get_puuid_from_discord(player_name)
    df = pd.json_normalize(match_data["info"]["participants"])
    df["matchId"] = match_data["metadata"]["matchId"]

    player_team_id = df.loc[df["puuid"] == puuid, "teamId"]
    if player_team_id.empty:
        raise ValueError("Player's team ID not found in match data.")

    return df[df["teamId"] == player_team_id.iloc[0]]


if __name__ == "__main__":
    TOKEN = "RGAPI-a384a673-d288-42ec-a860-55a1602dba94"
    api = RiotAPI(TOKEN)

    player = "tuandao1311"
    match_data = get_latest_match_data(api, player)
    teammates_df = extract_teammates_df(match_data, player)

    print(teammates_df[["riotIdGameName",
          "championName", "kills", "deaths", "assists"]])
