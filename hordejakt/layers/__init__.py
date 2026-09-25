"""Evidence layers.

Every layer module exposes ``build(grid, cfg) -> list[LayerResult]``; the
registry below lists them in evaluation order. See base.py for semantics.
"""
LAYER_MODULES = [
    "hordejakt.layers.elevation",
    "hordejakt.layers.forest",
    "hordejakt.layers.aircraft",
    "hordejakt.layers.weather",
    "hordejakt.layers.travel",
    "hordejakt.layers.exclusions",
    "hordejakt.layers.defaultno_fusion",
    "hordejakt.layers.organizer_prior",
    "hordejakt.layers.live",
]
