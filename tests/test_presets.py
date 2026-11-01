"""Presets: Vollständigkeit, gültige Werte, Standard-Preset = Standardeinstellungen, jedes Preset einzeln erkennbar."""

import vhg_constants as C
import vhg_presets as P
from vhg_scenario import Settings


def test_every_preset_has_help_and_all_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP)
    for name, preset in C.PRESETS.items():
        assert set(preset) == set(P.PRESET_KEYS), name
        assert C.PRESET_HELP[name]


def test_preset_values_are_inside_the_slider_bounds_and_choices():
    for name, preset in C.PRESETS.items():
        for key, state_key in P.PRESET_KEYS.items():
            spec = P.SETTING_SPECS[state_key]
            if spec.choices is not None:
                assert preset[key] in spec.choices, (name, key)
            else:
                assert spec.lo <= preset[key] <= spec.hi, (name, key)


def test_default_preset_equals_the_default_settings():
    first = next(iter(C.PRESETS.values()))
    s = Settings(v=(first["v1"], first["v2"], first["v3"], first["v4"]), s=(first["s1"], first["s2"], first["s3"], first["s4"]), price=first["price"], bundle=first["bundle"],
                 rs=first["rs"], rv=first["rv"], term=first["term"], gs=first["gs"], gv=first["gv"], q=first["q"], pv=first["pv"], ps=first["ps"], bonus=first["bonus"], gb=first["gb"],
                 dv=first["dv"], ds=first["ds"], k=first["k"], r=first["r"], est=first["est"], seed=first["seed"])
    assert s == Settings()


def test_setting_specs_cover_every_preset_key_and_defaults_match_base():
    assert set(P.PRESET_KEYS.values()) == set(P.SETTING_SPECS)
    for key, state_key in P.PRESET_KEYS.items():
        assert P.SETTING_SPECS[state_key].default == C.BASE[key]


def test_presets_are_pairwise_different_so_that_each_can_be_highlighted():
    values = [tuple(sorted(p.items())) for p in C.PRESETS.values()]
    assert len(set(values)) == len(values)


def test_a_point_worth_nothing_to_both_sides_is_not_negotiated():
    """Das Handbeispiel hat zwei Punkte: Punkt 3 und 4 haben v = s = 0 und fehlen; ein Punkt mit nur einem Wert 0 bleibt."""
    from vhg_scenario import point_values
    v, s, names = point_values(Settings(v=(80, 20, 0, 0), s=(30, 70, 0, 0)))
    assert v == [80.0, 20.0] and s == [30.0, 70.0] and names == ["Lieferfenster", "Zahlungsziel"]
    v, s, names = point_values(Settings(v=(0, 20, 0, 5), s=(30, 0, 0, 0)))
    assert v == [0.0, 20.0, 5.0] and s == [30.0, 0.0, 0.0] and names == ["Lieferfenster", "Zahlungsziel", "Rampenzeit"]


def test_effective_bundle_is_clipped_to_the_number_of_points():
    from vhg_scenario import effective_bundle
    two = dict(v=(80, 20, 0, 0), s=(30, 70, 0, 0))
    assert effective_bundle(Settings(**two, bundle=4)) == 2 and effective_bundle(Settings(bundle=1)) == 1 and effective_bundle(Settings(bundle=3)) == 3
    assert effective_bundle(Settings(v=(0, 0, 0, 0), s=(0, 0, 0, 0), bundle=3)) == 1
