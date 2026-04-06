import requests, os, json
from datetime import datetime, timezone

BOT_ID = os.environ["GROUPME_BOT_ID"]

PLAYERS = {
    "Half Cup Kent": [
        "Munetaka Murakami", "Alex Bregman", "Ketel Marte", "Bryce Harper",
        "James Wood", "Shohei Ohtani", "Bobby Witt", "Teoscar Hernández",
        "Fernando Tatis", "Taylor Ward", "Pete Crow-Armstrong", "Tyler Soderstrom"
    ],
    "Tommy Cold Takes": [
        "Shea Langeliers", "Oneil Cruz", "Aaron Judge", "Eugenio Suárez",
        "Corbin Carroll", "Mookie Betts", "Matt Olson", "Rafael Devers",
        "Riley Greene", "Byron Buxton", "Cody Bellinger", "Willson Contreras"
    ],
    "Gymbag": [
        "Yordan Alvarez", "Kyle Schwarber", "Giancarlo Stanton", "Max Muncy",
        "Willy Adames", "Junior Caminero", "Marcell Ozuna", "Julio Rodriguez",
        "Jo Adell", "Jazz Chisholm", "Manny Machado", "Christian Walker"
    ],
    "Huncho Vos": [
        "Mike Trout", "Pete Alonso", "Roman Anthony", "Ben Rice",
        "Nick Kurtz", "Ronald Acuna", "Brent Rooker", "Vinnie Pasquantino",
        "Michael Busch", "Jac Caglianone", "Trent Grisham", "Francisco Lindor"
    ],
    "Terrorist Moran": [
        "Corey Seager", "Zach Neto", "Cal Raleigh", "Juan Soto",
        "Vladimir Guerrero Jr.", "Gunnar Henderson", "Kyle Tucker", "Jose Ramirez",
        "Austin Riley", "Hunter Goodman", "Seiya Suzuki", "Spencer Torkelson"
    ]
}

SEEN_FILE = "seen_hrs.json"

def load_seen():
    try:
        with open(SEEN_FILE) as f:
            return set(json.load(f))
    except:
        return set()

def save_seen(seen):
    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen), f)

def send_groupme(msg):
    requests.post("https://api.groupme.com/v3/bots/post", json={
        "bot_id": BOT_ID,
        "text": msg
    })

def get_player_team(name):
    for team, players in PLAYERS.items():
        for player in players:
            if player.lower() in name.lower():
                return team, player
    return None, None

def get_today_games():
    from datetime import timedelta
    now_et = datetime.now(timezone.utc) - timedelta(hours=4)
    today = now_et.strftime("%Y-%m-%d")
    print(f"Checking schedule for date: {today}")
    url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={today}"
    r = requests.get(url)
    games = []
    for date in r.json().get("dates", []):
        for game in date.get("games", []):
            state = game.get("status", {}).get("abstractGameState")
            detailed = game.get("status", {}).get("detailedState", "")
            print(f"Game {game['gamePk']}: state={state} | detailed={detailed}")
            if state == "Live" or "In Progress" in detailed:
                games.append(game["gamePk"])
    print(f"Total live games found: {len(games)}")
    return games

def check_game_for_hrs(game_pk, seen):
    url = f"https://statsapi.mlb.com/api/v1/game/{game_pk}/playByPlay"
    r = requests.get(url)
    plays = r.json().get("allPlays", [])
    print(f"Game {game_pk}: {len(plays)} plays found")
    new_seen = set()
    for play in plays:
        result = play.get("result", {})
        if result.get("eventType") == "home_run":
            batter = play["matchup"]["batter"]["fullName"]
            play_id = f"{game_pk}_{play['atBatIndex']}"
            print(f"HR found: {batter} | play_id: {play_id} | in seen: {play_id in seen}")
            fantasy_team, matched_player = get_player_team(batter)
            print(f"Fantasy team match: {fantasy_team}")
            if play_id not in seen and fantasy_team:
                inning = play["about"]["inning"]
                inning_half = "Top" if play["about"]["isTopInning"] else "Bot"
                desc = result.get("description", "")
                msg = f"🚨 DINGER ALERT 🚨\n{batter} just went yard!\nFantasy Team: {fantasy_team}\n{inning_half} {inning} | {desc}"
                send_groupme(msg)
                new_seen.add(play_id)
    return new_seen

def main():
    seen = load_seen()
    games = get_today_games()
    for game_pk in games:
        new = check_game_for_hrs(game_pk, seen)
        seen.update(new)
    save_seen(seen)

if __name__ == "__main__":
    main()
