import json
import os
import random
import appdaemon.plugins.hass.hassapi as hass
import time
import asyncio


class RandomFragezeichen(hass.Hass):
    def initialize(self):
        event_name = "RANDOM_FRAGEZEICHEN"
        self.log(f"setting up listen_event for {event_name}")
        self.listen_event(self.handle_event, event_name)
        self.log("Init done!")

    def handle_event(self, event_name, data, kwargs):
        self.log("A RANDOM FRAGEZEICHEN WAS REQUESTED!!")
        json_path = data.get("json_file", "/homeassistant/dreifragezeichen_folgen.json")
        cache_path = json_path.replace(".json", "_cache.json")
        target = data.get("target", "media_player.schlafzimmer_mini_2")
        user_volume_level = data.get("volume", 0.05)
        sleep_timer = data.get("sleep_time")

        if self.get_state("input_boolean.fragezeichen_episode_playing") == "on":
            self.log("There is currently already a episode playing")
            return

        try:
            with open(json_path, "r") as f:
                episodes = json.load(f)
        except Exception as e:
            self.log(f"Failed to load episodes JSON: {e}", level="ERROR")
            return
        try:
            if os.path.isfile(cache_path):
                with open(cache_path, "r") as f:
                    cache = json.load(f)
            else:
                cache = []
        except Exception as e:
            self.log(f"Failed to load cache JSON: {e}", level="ERROR")
            cache = []

        if len(episodes) == len(cache):
            cache = []

        candidate_episodes = [
            episode_id for episode_id in episodes.keys() if episode_id not in cache
        ]
        if not candidate_episodes or len(candidate_episodes) == 0:
            self.log("No episode candidates found to select from.", level="WARNING")
            return

        episode_id = random.choice(candidate_episodes)

        cache.append(episode_id)

        with open(cache_path, "w") as f:
            json.dump(cache, f)

        orig_volume=0.5
        attrs = self.get_state(target, attribute="all")
        if attrs.get("state") == "playing":
            self.log(f"Target {target} is already playing something. Turning off...")
            self.call_service("media_player/turn_off", entity_id=target)
        if attrs and "attributes" in attrs:
            if attrs.get("state") == "off":
                self.log(f"media player {target} is currently turned off. Turning on to get last volume-state.")
                self.call_service("media_player/turn_on", entity_id=target)
                attrs = self.get_state(target, attribute="all")
            orig_volume = attrs["attributes"].get("volume_level", 0.5)
        self.log(f"Original volume of {target} is {orig_volume}")

        self.call_service("media_player/volume_set", entity_id=target, volume_level=user_volume_level)


        service_payload = {
            "entity_id": target,
            "media_id": episodes[episode_id]["uri"],
            "media_type": "album",
        }

        self.log(f"calling play_media service using {str(service_payload)}")
        self.call_service("music_assistant/play_media", **service_payload)
        self.sleep(0.5)
        self.set_state("input_boolean.fragezeichen_episode_playing", state="on")

        if sleep_timer is not None:
            try:
                if isinstance(sleep_timer, str):
                    if "m" in sleep_timer.lower():
                        sleep_timer = sleep_timer.lower().replace("m","")
                        sleep_timer = 60*int(sleep_timer)
                    elif "h" in sleep_timer.lower():
                        sleep_timer = sleep_timer.lower().replace("h","")
                        sleep_timer = 60*60*int(sleep_timer)

                sleep_timer = int(sleep_timer)
            except Exception:
                self.log(f"Invalid sleep_timer value: {sleep_timer}", level="WARNING")
                return
        
            self.log(f"Sleep timer is set for {sleep_timer} seconds")

            self.run_in(self._fade_out_and_stop, sleep_timer, target=target, orig_volume=orig_volume)

    async def _fade_out_and_stop(self, kwargs):
        target = kwargs["target"]
        orig_volume = kwargs["orig_volume"]

        self.log(f"Starting fade out for {target}")
        fade_duration = 10
        steps = 20
        step_duration=fade_duration/steps
        start_volume=0.15
        for i in range(steps):
            vol = start_volume * (1-i/steps)
            self.call_service("media_player/volume_set", entity_id=target, volume_level=vol)
            await asyncio.sleep(step_duration)
        self.call_service("media_player/volume_set", entity_id=target, volume_level=0.0)
        self.sleep(0.5)
        self.call_service("media_player/media_stop", entity_id=target)
        self.log(f"Stopped playback on {target}")
        self.sleep(0.5)
        self.set_state("input_boolean.fragezeichen_episode_playing", state="off")
        self.sleep(0.5)
        self.call_service("media_player/volume_set", entity_id=target, volume_level=orig_volume)
        self.log(f"Restored original volume on {target} to {orig_volume}")