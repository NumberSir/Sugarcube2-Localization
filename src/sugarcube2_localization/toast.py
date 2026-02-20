"""Notify you after the script running done."""

import platform
import subprocess

from pathlib import Path

from windows_toasts import WindowsToaster, Toast, ToastDisplayImage, ToastImagePosition

from sugarcube2_localization.config import settings


class Toaster:
    def __init__(self, title: str = settings.project.name, body: str = "Done", logo: Path = None):
        self._title = title
        self._body = body
        self._logo = logo

    def _windows(self):
        """actually, win10 & win11"""
        toast_main = WindowsToaster(applicationText=self.title)
        logo = ToastDisplayImage.fromPath(self.logo)
        logo.position = ToastImagePosition.AppLogo
        toast_body = Toast(
            text_fields=[self.body],
            images=[logo]
        )
        toast_main.show_toast(toast_body)

    def _macos(self):
        """macOS native notification via osascript"""
        safe_title = self.title.replace('"', '\\"')
        safe_body = self.body.replace('"', '\\"')
        script = f'display notification "{safe_body}" with title "{safe_title}"'
        subprocess.run(["osascript", "-e", script], check=False)

    def _linux(self):
        """Linux notification via libnotify (notify-send)"""
        cmd = ["notify-send", self.title, self.body]
        if self.logo and self.logo.exists():
            cmd.extend(["-i", str(self.logo.absolute())])
        subprocess.run(cmd, check=False)

    def notify(self):
        match platform.system().lower():
            case "windows":
                return self._windows()
            case "macos":
                return self._macos()
            case "linux":
                return self._linux()
            case _:
                raise NotImplementedError

    @property
    def title(self) -> str:
        return self._title

    @property
    def body(self) -> str:
        return self._body

    @property
    def logo(self) -> Path:
        return self._logo


__all__ = [
    "Toaster",
]
