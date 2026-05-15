from __future__ import annotations

import json
import os
import platform
from dataclasses import dataclass
from pathlib import Path

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.properties import BooleanProperty, ListProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.togglebutton import ToggleButton


CONFIG_PATH = Path(__file__).with_name("relays.json")


@dataclass(frozen=True)
class RelayConfig:
    name: str
    pin: int
    active_low: bool = True
    initial_on: bool = False


class GpioBackend:
    def __init__(self, relays: list[RelayConfig], demo: bool = False) -> None:
        self.relays = relays
        self.demo = demo
        self.states = {relay.pin: relay.initial_on for relay in relays}
        self._gpio = None

        if not demo:
            try:
                import RPi.GPIO as GPIO  # type: ignore

                self._gpio = GPIO
                GPIO.setwarnings(False)
                GPIO.setmode(GPIO.BCM)
                for relay in relays:
                    GPIO.setup(relay.pin, GPIO.OUT)
                    self.set_state(relay, relay.initial_on)
            except Exception as exc:
                self.demo = True
                print(f"GPIO unavailable, running in demo mode: {exc}")

    def set_state(self, relay: RelayConfig, on: bool) -> None:
        self.states[relay.pin] = on
        if self.demo or self._gpio is None:
            return

        output_on = self._gpio.LOW if relay.active_low else self._gpio.HIGH
        output_off = self._gpio.HIGH if relay.active_low else self._gpio.LOW
        self._gpio.output(relay.pin, output_on if on else output_off)

    def all_off(self) -> None:
        for relay in self.relays:
            self.set_state(relay, False)

    def cleanup(self) -> None:
        self.all_off()
        if not self.demo and self._gpio is not None:
            self._gpio.cleanup()


class RelayTile(ToggleButton):
    relay_name = StringProperty("")
    pin_label = StringProperty("")
    on = BooleanProperty(False)

    def __init__(self, relay: RelayConfig, callback, **kwargs) -> None:
        super().__init__(**kwargs)
        self.relay = relay
        self.callback = callback
        self.relay_name = relay.name
        self.pin_label = f"GPIO {relay.pin}"
        self.on = relay.initial_on
        self.state = "down" if self.on else "normal"
        self.font_size = "28sp"
        self.bold = True
        self.halign = "center"
        self.valign = "middle"
        self.background_normal = ""
        self.background_down = ""
        self.bind(size=self._update_text, state=self._on_state)
        self._apply_style()
        self._update_text()

    def _on_state(self, *_args) -> None:
        self.on = self.state == "down"
        self.callback(self.relay, self.on)
        self._apply_style()
        self._update_text()

    def _apply_style(self) -> None:
        self.background_color = (0.11, 0.56, 0.36, 1) if self.on else (0.18, 0.22, 0.27, 1)
        self.color = (1, 1, 1, 1)

    def _update_text(self, *_args) -> None:
        status = "ON" if self.on else "OFF"
        self.text = f"{self.relay_name}\n{self.pin_label}\n{status}"
        self.text_size = self.size


class Root(BoxLayout):
    status_text = StringProperty("")
    status_color = ListProperty([0.7, 0.76, 0.82, 1])

    def __init__(self, relays: list[RelayConfig], backend: GpioBackend, **kwargs) -> None:
        super().__init__(orientation="vertical", padding=18, spacing=14, **kwargs)
        self.relays = relays
        self.backend = backend
        self.tiles: list[RelayTile] = []

        header = BoxLayout(orientation="horizontal", size_hint_y=None, height=78, spacing=12)
        title = Label(
            text="Relay Control",
            font_size="34sp",
            bold=True,
            halign="left",
            valign="middle",
            color=(0.94, 0.97, 1, 1),
        )
        title.bind(size=lambda instance, _value: setattr(instance, "text_size", instance.size))
        header.add_widget(title)

        all_off = Button(
            text="ALL OFF",
            font_size="24sp",
            bold=True,
            size_hint_x=None,
            width=210,
            background_normal="",
            background_color=(0.76, 0.2, 0.22, 1),
            color=(1, 1, 1, 1),
        )
        all_off.bind(on_release=self._all_off)
        header.add_widget(all_off)
        self.add_widget(header)

        grid = GridLayout(cols=2, spacing=14)
        for relay in relays:
            tile = RelayTile(relay, self._set_relay)
            self.tiles.append(tile)
            grid.add_widget(tile)
        self.add_widget(grid)

        footer = BoxLayout(orientation="horizontal", size_hint_y=None, height=54, spacing=12)
        self.status = Label(font_size="18sp", halign="left", valign="middle")
        self.status.bind(size=lambda instance, _value: setattr(instance, "text_size", instance.size))
        self.bind(status_text=lambda *_: self._refresh_status())
        footer.add_widget(self.status)

        quit_button = Button(
            text="Exit",
            font_size="20sp",
            size_hint_x=None,
            width=120,
            background_normal="",
            background_color=(0.28, 0.32, 0.38, 1),
            color=(1, 1, 1, 1),
        )
        quit_button.bind(on_release=lambda *_args: App.get_running_app().stop())
        footer.add_widget(quit_button)
        self.add_widget(footer)

        mode = "DEMO" if backend.demo else "GPIO"
        self.status_text = f"{mode} mode ready"
        self._refresh_status()

    def _set_relay(self, relay: RelayConfig, on: bool) -> None:
        self.backend.set_state(relay, on)
        state = "ON" if on else "OFF"
        self.status_text = f"{relay.name} set to {state}"

    def _all_off(self, *_args) -> None:
        self.backend.all_off()
        for tile in self.tiles:
            tile.state = "normal"
        self.status_text = "All relays are OFF"

    def _refresh_status(self) -> None:
        self.status.text = self.status_text
        self.status.color = self.status_color


class RelayControlApp(App):
    backend: GpioBackend | None = None

    def build(self):
        Window.clearcolor = (0.07, 0.08, 0.1, 1)
        Window.fullscreen = os.environ.get("RELAY_FULLSCREEN", "1") != "0"
        relays = load_config()
        demo = os.environ.get("RELAY_DEMO", "").lower() in {"1", "true", "yes"}
        demo = demo or platform.system() != "Linux"
        self.backend = GpioBackend(relays, demo=demo)
        Clock.schedule_once(lambda *_: self._show_demo_notice(), 0.4)
        return Root(relays, self.backend)

    def _show_demo_notice(self) -> None:
        if not self.backend or not self.backend.demo:
            return

        popup = Popup(
            title="Demo mode",
            content=Label(
                text="GPIO არ არის ხელმისაწვდომი.\nღილაკები იმუშავებს სატესტოდ, რელეები არ ჩაირთვება.",
                font_size="20sp",
                halign="center",
            ),
            size_hint=(0.72, 0.38),
            auto_dismiss=True,
        )
        popup.open()

    def on_stop(self) -> None:
        if self.backend:
            self.backend.cleanup()


def load_config() -> list[RelayConfig]:
    if not CONFIG_PATH.exists():
        return [
            RelayConfig("Relay 1", 17),
            RelayConfig("Relay 2", 27),
            RelayConfig("Relay 3", 22),
            RelayConfig("Relay 4", 23),
        ]

    data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    return [RelayConfig(**item) for item in data["relays"]]


if __name__ == "__main__":
    RelayControlApp().run()
