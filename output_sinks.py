import os
import subprocess


def env_flag(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class OutputRouter:
    def __init__(self, enable_clipboard=False):
        self.enable_clipboard = enable_clipboard

    def handle_translation(self, translation):
        if self.enable_clipboard:
            copy_to_clipboard(translation["natural_zh"])


def build_output_router():
    return OutputRouter(
        enable_clipboard=env_flag("TRACKPAD_COPY_TO_CLIPBOARD", default=False),
    )


def copy_to_clipboard(text):
    subprocess.run(
        ["pbcopy"],
        input=text,
        text=True,
        check=False,
    )
