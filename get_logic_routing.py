import argparse
from collections import Counter
import enum
import json
from pathlib import Path
from logic.pokemon_emerald.logic_rules import SlotLogic


class ClientStatus(enum.IntEnum):
    CLIENT_UNKNOWN = 0
    CLIENT_CONNECTED = 5
    CLIENT_READY = 10
    CLIENT_PLAYING = 20
    CLIENT_GOAL = 30


class ItemFlag(enum.IntEnum):
    ITEM_NOTHING_SPECIAL = 0
    ITEM_LOGIC = 1
    ITEM_USEFUL = 2
    ITEM_TRAP = 3


class LogicRouter:
    def __init__(self, args):
        self.args = args

        # validate and load required data
        self.goal_data, self.slot_data, self.game_data, self.slot_config = self._validate_required_data()
        self.n_slots = len(self.slot_data["player_status"])

        # load mapping dicts
        with open("resources/pokemon_emerald/item_mapping.json") as f:
            self.item_id_to_name = json.load(f)
        with open("resources/pokemon_emerald/setting_mapping.json") as f:
            self.setting_id_to_name = json.load(f)
        with open("resources/pokemon_emerald/location_mapping.json") as f:
            self.location_id_to_name = json.load(f)

        # route logic for each game
        self.goal_status = self._check_goal_status()

    def _validate_required_data(self):
        goal_data_path = self.args.data_folder / "goal_data.json"
        slot_data_path = self.args.data_folder / "tracker.json"
        slot_config_path = self.args.data_folder / "slot_data_tracker.json"
        game_data_path = self.args.data_folder / "room_datapackages.json"

        # validate paths
        if not self.args.data_folder.exists():
            parser.error(f"Data folder={self.args.data_folder} does not exist")

        if not (slot_data_path.is_file() and game_data_path.is_file() and slot_config_path.is_file()):
            # TODO is this the correct arg type?
            raise ValueError(f"Room data does not exist. Run get-room-data.py to generate it")

        if not goal_data_path.is_file():
            raise ValueError(f"Goal data={goal_data_path} does not exist. Run create-goal-data.py to generate it")

        # load data
        with open(goal_data_path) as f:
            goal_data = json.load(f)

        with open(slot_data_path) as f:
            slot_data = json.load(f)

        with open(game_data_path) as f:
            game_data = json.load(f)

        with open(slot_config_path) as f:
            slot_config = json.load(f)

        return goal_data, slot_data, game_data, slot_config

    def _is_slot_goaled(self, player_status):
        return player_status["status"] == ClientStatus.CLIENT_GOAL

    def _get_events(self, checks):
        return [self.location_id_to_name[str(c)][0] for c in checks["locations"]] # NOTE ignoring additional items in list because they are associated with the same id

    def _get_slot_config(self, slot):
        # TODO implement data transformations
        config = self.slot_config[slot]
        config["slot_data"]["free_fly_location_id"] = self.setting_id_to_name["SLOT_CODES"]["free_fly_location_id"]["mapping"][str(config["slot_data"]["free_fly_location_id"])]
        return config

    def _get_slot_items(self, slot, flag):
        return Counter([self.item_id_to_name[str(item[0])] for item in slot["items"] if item[-1] == flag])

    def _check_logic(self, goal, items, metadata): 
        sl = SlotLogic(goal, items, metadata)
        goal_status = sl.check_goal()
        print(sl.goal["player"], sl.goal["goal"], goal_status)

        return goal_status

    def _check_goal_status(self):
        goal_status = {}

        for slot in range(self.n_slots): 
            goal = self.goal_data[slot]
               
            # filter out completed game
            if self._is_slot_goaled(self.slot_data["player_status"][slot]):
                continue

            # get progression items 
            items = self._get_slot_items(self.slot_data["player_items_received"][slot], ItemFlag.ITEM_LOGIC)

            # get event flags from checks
            events = self._get_events(self.slot_data["player_checks_done"][slot])

            # get config
            config = self._get_slot_config(slot)
    
            # check logic to determine whether goal is reachable
            res = self._check_logic(goal, items, config)
            goal_status[slot] = res

        return goal_status
            


if __name__ == "__main__":
    # Parse arguments
    parser = argparse.ArgumentParser(description="Tracks various progression logic required for goaling slots. Requires output from get-room-data.py and create-goal-data.py")
    parser.add_argument(
        "-f", "--data-folder",
        required=True,
        type=Path,
        metavar="FOLDER",
        help="(Required) Folder containing room data retrieved by get-room-data.py and create-goal-data.py")
    args = parser.parse_args()


    # init class
    lr = LogicRouter(args)  