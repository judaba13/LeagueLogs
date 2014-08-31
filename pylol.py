from collections import deque
import time
import requests

#######################
#------CONSTANTS------#
#######################
BRAZIL = 'br'
EUROPE_NORDIC_EAST = 'eune'
EUROPE_WEST = 'euw'
KOREA = 'kr'
LATIN_AMERICA_SOUTH = 'las'
LATIN_AMERICA_NORTH = 'lan'
OCEANIA = 'oce'
TURKEY = 'tr'
RUSSIA = 'ru'
NORTH_AMERICA = 'na'

maps = [
    {'map_id': 1, 'name': "Summoner's Rift", 'notes': "Summer Variant"},
    {'map_id': 2, 'name': "Summoner's Rift", 'notes': "Autumn Variant"},
    {'map_id': 3, 'name': "The Proving Grounds", 'notes': "Tutorial Map"},
    {'map_id': 4, 'name': "Twisted Treeline", 'notes': "Original Version"},
    {'map_id': 8, 'name': "The Crystal Scar", 'notes': "Dominion Map"},
    {'map_id': 10, 'name': "Twisted Treeline", 'notes': "Current Version"},
    {'map_id': 12, 'name': "Howling Abyss", 'notes': "ARAM Map"},
]

game_modes = [
    'CLASSIC',				# Classic Summoner's Rift and Twisted Treeline games
    'ODIN',					# Dominion/Crystal Scar games
    'ARAM',					# ARAM games
    'TUTORIAL',				# Tutorial games
    'ONEFORALL',			# One for All games
    'FIRSTBLOOD',			# Snowdown Showdown games
]

game_types = [
    'CUSTOM_GAME',			# Custom games
    'TUTORIAL_GAME',		# Tutorial games
    'MATCHED_GAME',			# All other games
]

sub_types = [
    'NONE',					# Custom games
    'NORMAL',				# Summoner's Rift unranked games
    'NORMAL_3x3',			# Twisted Treeline unranked games
    'ODIN_UNRANKED',		# Dominion/Crystal Scar games
    'ARAM_UNRANKED_5v5',	# ARAM / Howling Abyss games
    'BOT',					# Summoner's Rift and Crystal Scar games played against AI
    'BOT_3x3',				# Twisted Treeline games played against AI
    'RANKED_SOLO_5x5',		# Summoner's Rift ranked solo queue games
    'RANKED_TEAM_3x3',		# Twisted Treeline ranked team games
    'RANKED_TEAM_5x5',		# Summoner's Rift ranked team games
    'ONEFORALL_5x5',		# One for All games
    'FIRSTBLOOD_1x1',		# Snowdown Showdown 1x1 games
    'FIRSTBLOOD_2x2',		# Snowdown Showdown 2x2 games
    'SR_6x6',				# Hexakill games
    'CAP_5x5',				# Team Builder games
    'URF',					# Ultra Rapid Fire games
    'URF_BOT',				# Ultra Rapid Fire games against AI
    'NIGHTMARE_BOT'			# Summoner's Rift games played against Nightmare AI
]

player_stat_summary_types = [
    'Unranked',				# Summoner's Rift unranked games
    'Unranked3x3',			# Twisted Treeline unranked games
    'OdinUnranked',			# Dominion/Crystal Scar games
    'AramUnranked5x5',		# ARAM / Howling Abyss games
    'CoopVsAI',				# Summoner's Rift and Crystal Scar games played against AI
    'CoopVsAI3x3',			# Twisted Treeline games played against AI
    'RankedSolo5x5',		# Summoner's Rift ranked solo queue games
    'RankedTeams3x3',		# Twisted Treeline ranked team games
    'RankedTeams5x5',		# Summoner's Rift ranked team games
    'OneForAll5x5',			# One for All games
    'FirstBlood1x1',		# Snowdown Showdown 1x1 games
    'FirstBlood2x2',		# Snowdown Showdown 2x2 games
    'SummonersRift6x6',		# Hexakill games
    'CAP5x5',				# Team Builder games
    'URF',					# Ultra Rapid Fire games
    'URFBots',				# Ultra Rapid Fire games played against AI
]

solo_queue, ranked_5s, ranked_3s = 'RANKED_SOLO_5x5', 'RANKED_TEAM_5x5', 'RANKED_TEAM_3x3'

api_versions = {
    'champion': 1.2,
    'game': 1.3,
    'league': 2.5,
    'lol-static-data': 1.2,
    'match': 2.2,
    'matchhistory': 2.2,
    'stats': 1.3,
    'summoner': 1.4,
    'team': 2.4
}

#######################
#-------ERRORS--------#
#######################
class PyLoLException(Exception):
    def __init__(self, error):
        self.error = error

    def __str__(self):
        return self.error


error_400 = PyLoLException("Bad request")
error_401 = PyLoLException("Unauthorized")
error_404 = PyLoLException("Game data not found")
error_429 = PyLoLException("Too many requests")
error_500 = PyLoLException("Internal server error")
error_503 = PyLoLException("Service unavailable")


def raise_response_status(response):
    if response.status_code == 400:
        raise error_400
    elif response.status_code == 401:
        raise error_401
    elif response.status_code == 404:
        raise error_404
    elif response.status_code == 429:
        raise error_429
    elif response.status_code == 500:
        raise error_500
    elif response.status_code == 503:
        raise error_503
    else:
        response.raise_for_status()

#######################
#---API ACCESS RATE---#
#######################
class AcessLimit:
    def __init__(self, allowed_requests, seconds):
        self.allowed_requests = allowed_requests
        self.seconds = seconds
        self.made_requests = deque()

    def __reload(self):
        t = time.time()
        while len(self.made_requests) > 0 and self.made_requests[0] < t:
            self.made_requests.popleft()

    def add_request(self):
        self.made_requests.append(time.time() + self.seconds)

    def request_available(self):
        self.__reload()
        return len(self.made_requests) < self.allowed_requests