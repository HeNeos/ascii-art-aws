from typing import TypedDict


class LambdaEventWarm(TypedDict):
    warm: bool


class LambdaResponseWarm(TypedDict):
    warmed: bool
