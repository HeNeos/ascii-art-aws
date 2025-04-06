from ..dithering import DitheringStrategy
from ..dithering.atkinson import DitheringAtkinson
from ..dithering.floyd_steinberg import DitheringFloydSteinberg
from ..dithering.jarvis_judice_ninke import DitheringJarvisJudiceNinke
from ..dithering.riemersma_naive import DitheringRiemersmaNaive

ditherings: dict[str, type[DitheringStrategy]] = {
    "atkinson": DitheringAtkinson,
    "floyd_steinberg": DitheringFloydSteinberg,
    "jarvis_judice_ninke": DitheringJarvisJudiceNinke,
    "riemersma_naive": DitheringRiemersmaNaive,
}


def get_dithering_strategy(dithering_name: str) -> type[DitheringStrategy]:
    return ditherings.get(dithering_name, DitheringAtkinson)
