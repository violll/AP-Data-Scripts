import argparse
import enum
import json
from collections import Counter
from pathlib import Path
from typing import Any

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
    def __init__(self, args) -> None:
        self.args = args

        # validate and load required data
        self._validate_required_data()
        self.n_slots = len(self.slot_data["player_status"])

        # load mapping dicts
        with open(Path("resources/pokemon_emerald/item_mapping.json")) as f:
            self.item_id_to_name = json.load(f)
        with open(Path("resources/pokemon_emerald/setting_mapping.json")) as f:
            self.setting_id_to_name = json.load(f)
        with open(Path("resources/pokemon_emerald/location_mapping.json")) as f:
            self.location_id_to_name = json.load(f)

        self._clean_slot_configs()

        # route logic for each game
        self.goal_status = self._check_goal_status()

    def _clean_slot_configs(self):
        for config in self.slot_config:
            config["slot_data"]["free_fly_location_id"] = self.setting_id_to_name["SLOT_CODES"]["free_fly_location_id"]["mapping"][str(config["slot_data"]["free_fly_location_id"])]

    def _validate_required_data(self) -> None:
        goal_data_path = self.args.data_folder / "goal_data.json"
        slot_data_path = self.args.data_folder / "tracker.json"
        slot_config_path = self.args.data_folder / "slot_data_tracker.json"
        # hints_processed_path = self.args.data_folder / "hints_processed.json"

        # validate paths
        if not self.args.data_folder.exists():
            parser.error(f"Data folder={self.args.data_folder} does not exist")

        if not (slot_data_path.is_file() and slot_config_path.is_file()):
            # TODO is this the correct arg type?
            raise ValueError("Room data does not exist. Run get_room_data.py to generate it")

        if not goal_data_path.is_file():
            raise ValueError(f"Goal data={goal_data_path} does not exist. Run create_goal_data.py to generate it")

        # load data
        with open(goal_data_path) as f:
            self.goal_data = json.load(f)

        with open(slot_data_path) as f:
            self.slot_data = json.load(f)

        with open(slot_config_path) as f:
            self.slot_config = json.load(f)

    def _is_slot_goaled(self, player_status) -> bool:
        return player_status["status"] == ClientStatus.CLIENT_GOAL

    def _get_events(self, checks) -> list[str]:
        return [self.location_id_to_name[str(c)][0] for c in checks["locations"]] # NOTE ignoring additional items in list because they are associated with the same id

    def _get_slot_items(self, slot, flag):
        return Counter([self.item_id_to_name[str(item[0])] for item in slot["items"] if item[-1] == flag])

    def _check_logic(self, goal, items, metadata):
        sl = SlotLogic(goal, items, metadata)
        goal_status = sl.check_goal()
        if goal_status:
            print(sl.goal["player"], sl.goal["goal"])

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

            # get config
            config = self.slot_config[slot]

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
