'''
Item & game progression logic adapted from Archipelago-Emerald-AP-Tracker by seto10987 
Copyright (c) 2024 seto10987
Licensed under the MIT License. The full MIT license text is included below:

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

This file is a Python translation of the original logic
'''

import json
import pathlib


class SlotLogic:
    def __init__(self, goal, items, checks, data, ignore_flash=True):
        self.BADGES = {"stone_badge","knuckle_badge","dynamo_badge","heat_badge","balance_badge","feather_badge","mind_badge","rain_badge"}
        self.GYMS = {"defeat_roxanne","defeat_brawly","defeat_wattson","defeat_flannery","defeat_norman","defeat_winona","defeat_tate_and_liza","defeat_juan"}

        self.check_dependencies = {}
        for resource in ["cities", "dungeons", "routes"]:
            f_path = pathlib.Path(f"resources/pokemon_emerald/{resource}.json")
            with open(f_path) as f:
                self.check_dependencies[resource] = json.load(f)

        with open(pathlib.Path("resources/pokemon_emerald/events.json")) as f:
            self.events = json.load(f)[:-1] #ignoring legendary hunt event - last entry in list

        self.goal = goal
        self.items = items
        self.checks = checks # event flags
        self.data = data
        self.ignore_flash = ignore_flash
        self._add_data_flags(data)
        self._add_event_logic()

    # internal functions
    def _add_data_flags(self, data):
        # fly requirement
        fly_req = data["slot_data"]["hm_requirements"]["HM02 Fly"]
        if len(fly_req) == 0:
            self.items["feather_badge_on"] = 1

        # flash requirment
        flash_req = data["slot_data"]["require_flash"]
        match flash_req:
            case 0:
                # not required
                pass
            case 1:
                self.items["flash_granite_cave"] = 1
            case 2:
                self.items["flash_victory_road"] = 1
            case 3:
                self.items["flash_both"] = 1

        # itemfinder requirement
        itemfinder_req = data["slot_data"]["require_itemfinder"]
        if itemfinder_req:
            self.items["itemfinder_off"] = 1

        # roadblocks 
        removed_roadblocks = data["slot_data"]["remove_roadblocks"]
        for roadblock in removed_roadblocks:
            if "Wailmer" in roadblock:
                roadblock_formatted = "wailmer"
            else:
                roadblock_formatted = roadblock.replace("Route", "rt")          \
                                               .replace("Aqua ", "")            \
                                               .replace("Magma ", "")           \
                                               .replace("Hideout ", "")         \
                                               .replace("Seafloor", "sea floor")\
                                               .replace(" ", "_")               \
                                               .lower()                         \
                                 
            self.items[f"{roadblock_formatted}_on"] = 1

        # route 115 boulders
        extra_boulders = data["slot_data"]["extra_boulders"]
        if not extra_boulders:
            self.items["route_115_boulders_off"] = 1

        # route 115 bumpy slope
        bumpy_slope = data["slot_data"]["extra_bumpy_slope"]
        if bumpy_slope:
            self.items["route_115_bumpy_slope_on"] = 1

        # route 118 rails
        modify_118 = data["slot_data"]["modify_118"]
        if modify_118:
            self.items["route_118_rails_on"] = 1

        

    def _add_event_logic(self):
        # update self.items to include event logic
        for event in self.events:
            # find the event in self.check_dependencies
            event_name, access_rules = self._get_event_data(event)

            if self.is_in_logic(event_name, self.clean_access_rules(access_rules)):
                self.items[event["codes"]] = 1


    def _exec_func(self, f):
        match f:
            case "$dewford_access": 
                return self.dewford_access(),
            case "[$flash|cave]":
                return self.flash("cave")
            case "$slateport_access":
                return self.slateport_access()
            case "$mauville_access":
                return self.mauville_access()
            case "$fallarbor_access":
                return self.fallarbor_access()
            case "$mt_chimney_access":
                return self.mt_chimney_access()
            case "$lavaridge_access":
                return self.lavaridge_access()
            case "$has_norman_req":
                return self.has_norman_req()
            case "$route_119_access":
                return self.route_119_access()
            case "$fortree_access":
                return self.fortree_access()
            case "$mt_chimney_access":
                return self.mt_chimney_access()
            case "$strength":
                return self.strength()
            case "$aqua_hideout_access":
                return self.aqua_hideout_access()
            case "$mossdeep_access":
                return self.mossdeep_access()
            case "$seafloor_cavern_access":
                return self.seafloor_cavern_acces()
            case "$sootopolis_access":
                return self.sootopolis_access()
            case "$sealed_chamber_access":
                return self.sealed_chamber_access()
            case "$e4_access":
                return self.e4_access()
            case "[$flash|road]":
                return self.flash("road")
            case "$surf":
                return self.surf()
            case "$waterfall":
                return self.waterfall()

    def _get_event_data(self, event, untracked=False):
        if untracked:
            loc, event_location, event_name = event[1:].split("/")
            name_entry_to_check = "name"
            
        else:
            event_name = f"{event["codes"]}_hosted"
            event_location = event["name"].split("-")[0].strip()

            if "Route" in event_location or event_location in ["Trick House", "Mt. Chimney", "Jagged Pass", "Weather Institute"]:
                loc = "routes"
            elif "Town" in event_location or "City" in event_location or "Gym" in event_location:
                loc = "cities"
            else:
                loc = "dungeons"

            name_entry_to_check = "hosted_item"

        event_data = False
        for check in self.check_dependencies[loc][0]["children"]:
            if event_location in check["name"]:
                for c in check["sections"]:
                    if c.get(name_entry_to_check,"") == event_name:
                        event_data = c
                        break

                if event_data:
                    location_data = check
                    break

        if not event_data:
            raise ValueError(f"Event {event_name} at {event_location} could not be found")

        access_rules = location_data.get("access_rules", []) + event_data.get("access_rules", [])

        return event_name, access_rules

    def _get_event_data_from_name(self, event):
        event_name = f"{event}_hosted"
        event_data = False
        for loc in self.check_dependencies.keys():
            for check in self.check_dependencies[loc][0]["children"]:
                for c in check["sections"]:
                    if c.get("hosted_item") == event_name:
                        event_data = c
                        break

                if event_data:
                    location_data = check
                    break

        if not event_data:
            raise ValueError(f"Event {event} could not be located")

        access_rules = location_data.get("access_rules", []) + event_data.get("access_rules", [])

        return event_name, access_rules


    # util functions
    def clean_access_rules(self, rules):
        # ensure one rule per entry
        access_rules = []
        for rule in rules:
            access_rules.extend(rule.split(","))

        return [r for r in access_rules if not ("flash" in r and self.ignore_flash)]


    def is_in_logic(self, event_name, access_rules, untracked=False):
        # check if requirements are in logic
        print(f"Checking {event_name}")
            
        for rule in access_rules:       
            print(f"\t{rule}")
            if rule[0] == "$" or rule[:2] == "[$":
                # run the appropriate function defined below
                if not self._exec_func(rule):
                    return False
            elif rule[0] == "@":
                # return NotImplementedError
                if not self.is_in_logic(rule, untracked=True):
                    return False
            else:
                # return NotImplementedError
                if not (self.has(rule) or self.is_in_logic(*self._get_event_data_from_name(rule))):
                    return False

        return True

    def has(self, item, amount=False):
        # compare to amount if amount
        if not amount: 
            return self.items.get(item, 0) > 0
        else:
            return self.items.get(item, 0) >= amount

    # access functions
    def free_fly(self, location):
        return self.data["slot_data"]["free_fly_location_id"] == location and self.fly()


    def cut(self):
        return self.has("hm01_cut") and self.has("stone_badge")


    def fly(self):
        return self.has("hm02_fly") and (self.has("feather_badge_on") or self.has("feather_badge"))


    def surf(self):
        return self.has("hm03_surf") and self.has("balance_badge")


    def strength(self):
        return self.has("hm04_strength") and self.has("heat_badge")


    def flash(self, dungeon):
        if self.has("flash_both") or self.has(f"flash_{dungeon}") or dungeon == "tomb":
            return self.has("hm05_flash") and self.has("knuckle_badge")
        return True


    def rock_smash(self):
        return self.has("hm06_rock_smash") and self.has("dynamo_badge")


    def waterfall(self):
        return self.has("hm07_waterfall") and self.has("rain_badge")


    def dive(self):
        return self.has("hm08_dive") and self.has("mind_badge")


    def bike(self):
        return self.has("acro_bike") or self.has("mach_bike")


    def hidden(self):
        return self.has("itemfinder") or not self.has("require_itemfinder")


    def has_norman_req(self):
        if self.goal["goal"] != "norman":
            return False
        
        req_count = 0
        req = self.goal["norman_count"]
        req_item = {}

        if self.goal["norman_requirement"] == "badges":
            req_item = self.BADGES
        elif self.goal["norman_requirement"] == "gyms":
            req_item = self.GYMS

        for item in req_item:
            if self.has(item):
                req_count += 1

        return req_count >= req


    def has_e4_req(self):
        req_count = 0
        req = self.goal.get("elite_four_count", -1)
        if req == -1:
            return False
        
        req_item = {}

        if self.goal["elite_four_requirement"] == "badges":
            req_item = self.BADGES
        elif self.goal["elite_four_requirement"] == "gyms":
            req_item = self.GYMS

        for item in req_item:
            if self.has(item):
                req_count += 1

        return req_count >= req


    def pass_route_110(self):
        return self.has("rt_110_grunts_on") or self.has("rescue_stern") or self.bike()


    def pass_cable_car(self):
        return self.has("rt_112_grunts_on") or self.has("magma_steals_meteorite")


    def route_115_boulders(self):
        return self.has("route_115_boulders_off") or self.strength()


    def pass_route_115(self):
        return (self.surf() and self.route_115_boulders()) or (self.has("route_115_bumpy_slope_on") and self.has("acro_bike"))


    def pass_route_118(self):
        if self.has("route_118_rails_on"):
            return self.has("acro_bike")

        return self.surf()


    def pass_route_119(self):
        return self.has("rt_119_grunts_on") or self.has("defeat_shelly")


    def pass_route_124(self, direction):
        if direction == "left":
            return self.surf() and (self.has("wailmer_on") or self.has("defeat_matt"))

        return self.surf()


    def dewford_access(self):
        return self.has("talk_mr_stone") or self.surf()


    def slateport_access(self):
        return self.free_fly("slateport")                       \
                or self.surf()                                       \
                or (self.dewford_access() and self.has("deliver_letter")) \
                or (self.free_fly("mauville") and self.pass_route_110())  \
                or (self.free_fly("verdanturf") and self.pass_route_110()) \
                or (self.rock_smash() and self.pass_route_110())              \
                or (self.free_fly("fortree") and (self.has("ss_ticket") or (self.pass_route_119() and self.pass_route_118() and self.pass_route_110()))) \
                or (self.free_fly("lilycove") and (self.has("ss_ticket") or (self.cut() and self.pass_route_119() and self.pass_route_118() and self.pass_route_110())))


    def mauville_access(self):
        return self.free_fly("mauville") \
                or self.free_fly("verdanturf") \
                or self.rock_smash() \
                or self.surf() \
                or (self.slateport_access() and self.pass_route_110()) \
                or (self.free_fly("fortree") and self.pass_route_119() and self.pass_route_118()) \
                or (self.free_fly("lilycove") and self.cut() and self.pass_route_119() and self.pass_route_118())


    def fallarbor_access(self):
        return self.free_fly("fallarbor") \
                or self.free_fly("lavaridge") \
                or self.pass_route_115() \
                or self.rock_smash() \


    def mt_chimney_access(self):
        return (self.fallarbor_access() and self.pass_cable_car())    \
                or (self.free_fly("lavaridge") and self.has("acro_bike"))


    def lavaridge_access(self):
        return self.free_fly("lavaridge") \
                or (self.fallarbor_access() and self.pass_cable_car() and self.has("defeat_maxie_mt_chimney"))


    def route_119_access(self):
        return (self.mauville_access() and self.pass_route_118()) \
                or (self.free_fly("fortree") and (self.pass_route_119() or self.surf())) \
                or (self.free_fly("lilycove") and (self.surf() or (self.cut() and self.pass_route_119()))) \
                or (self.slateport_access() and self.has("ss_ticket") and (self.surf() or (self.cut() and self.pass_route_119()))) \
                or (self.free_fly("mossdeep") and self.pass_route_124()) \
                or (self.free_fly("sootopolis") and self.dive() and self.pass_route_124()) \
                or (self.free_fly("ever_grande") and self.pass_route_124())


    def fortree_access(self):
        return self.free_fly("fortree") \
                or (self.route_119_access() and self.pass_route_119()) \
                or (self.free_fly("lilycove") and self.cut()) \
                or (self.slateport_access() and self.has("ss_ticket") and self.cut()) \
                or (self.free_fly("mossdeep") and self.pass_route_124() and self.cut()) \
                or (self.free_fly("sootopolis") and self.dive() and self.pass_route_124() and self.cut()) \
                or (self.free_fly("ever_grande") and self.pass_route_124() and self.cut())


    def lilycove_access(self):
        return self.free_fly("lilycove") \
                or self.fortree_access() \
                or (self.slateport_access() and self.has("ss_ticket")) \
                or (self.free_fly("mossdeep") and self.pass_route_124()) \
                or (self.free_fly("sootopolis") and self.dive() and self.pass_route_124()) \
                or (self.free_fly("ever_grande") and self.pass_route_124())


    def aqua_hideout_access(self):
        return self.lilycove_access() and self.surf() and (self.has("hideout_grunts_on") or self.has("aqua_steals_submarine"))


    def route_124_access(self):
        return (self.lilycove_access() and self.pass_route_124("left")) \
                or (self.free_fly("mossdeep") and self.surf()) \
                or (self.free_fly("sootopolis") and self.dive() and self.surf()) \
                or (self.free_fly("ever_grande") and self.surf())


    def mossdeep_access(self):
        return self.free_fly("mossdeep") or self.route_124_access()


    def sootopolis_access(self):
        return self.free_fly("sootopolis") or (self.route_124_access() and self.dive())


    def seafloor_cavern_access(self):
        return self.route_124_access() and self.dive() and (self.has("sea_floor_grunts_on") or self.has("steven_gives_dive")) and self.rock_smash() and self.strength()


    def sealed_chamber_access(self):
        return self.route_124_access() and self.dive()


    def desert_ruins_access(self):
        return self.fallarbor_access() and self.has("go_goggles")


    def island_cave_access(self):
        return self.surf()


    def ancient_tomb_access(self):
        return self.fortree_access()


    def victory_road_access(self):
        return self.free_fly("ever_grande") or (self.route_124_access() and self.waterfall())


    def e4_access(self):
        return self.victory_road_access() and self.rock_smash() and self.strength() and self.surf() and self.has_e4_req()


    def battle_frontier_access(self):
        return (self.slateport_access() or self.lilycove_access()) and self.has("ss_ticket")


    def terra_cave_access(self):
        return self.has("defeat_champion") and self.has("defeat_shelly")


    def marine_cave_access(self):
        return self.dive() and self.has("defeat_champion") and self.has("defeat_shelly")


    # visibility defs
    def legary_hunt_defeat(self):
        return self.has("goal_legary_hunt") and self.has("legary_hunt_req_defeat")


    def legary_hunt_catch(self):
        return self.has("goal_legary_hunt") and self.has("legary_hunt_req_catch")
