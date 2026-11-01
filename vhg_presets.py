"""Permalink (Begrenzen), Presets und Zufalls-Seed-Button (Standardmuster aus dem Demo-Portfolio)."""

import random
from collections.abc import Callable
from dataclasses import dataclass

import streamlit as st

import vhg_constants as C
from vhg_scenario import Settings


@dataclass(frozen=True)
class SettingSpec:
    url_param: str
    caster: Callable
    default: object
    lo: float | None = None
    hi: float | None = None
    choices: tuple | None = None      # bei Auswahlreglern: die erlaubten Werte


B = C.BASE
SETTING_SPECS = {
    "v1_slider": SettingSpec("v1", int, B["v1"], C.VALUE_MIN, C.VALUE_MAX),
    "v2_slider": SettingSpec("v2", int, B["v2"], C.VALUE_MIN, C.VALUE_MAX),
    "v3_slider": SettingSpec("v3", int, B["v3"], C.VALUE_MIN, C.VALUE_MAX),
    "v4_slider": SettingSpec("v4", int, B["v4"], C.VALUE_MIN, C.VALUE_MAX),
    "s1_slider": SettingSpec("s1", int, B["s1"], C.VALUE_MIN, C.VALUE_MAX),
    "s2_slider": SettingSpec("s2", int, B["s2"], C.VALUE_MIN, C.VALUE_MAX),
    "s3_slider": SettingSpec("s3", int, B["s3"], C.VALUE_MIN, C.VALUE_MAX),
    "s4_slider": SettingSpec("s4", int, B["s4"], C.VALUE_MIN, C.VALUE_MAX),
    "price_slider": SettingSpec("preis", int, B["price"], C.PRICE_MIN, C.PRICE_MAX),
    "bundle_slider": SettingSpec("buendel", int, B["bundle"], C.BUNDLE_MIN, C.BUNDLE_MAX),
    "rs_slider": SettingSpec("rs", float, B["rs"], C.RATE_MIN, C.RATE_MAX),
    "rv_slider": SettingSpec("rv", float, B["rv"], C.RATE_MIN, C.RATE_MAX),
    "term_slider": SettingSpec("ziel", int, B["term"], C.TERM_MIN, C.TERM_MAX),
    "gs_slider": SettingSpec("gs", float, B["gs"], C.GAMMA_MIN, C.GAMMA_MAX),
    "gv_slider": SettingSpec("gv", float, B["gv"], C.GAMMA_MIN, C.GAMMA_MAX),
    "q_slider": SettingSpec("q", int, B["q"], C.Q_MIN, C.Q_MAX),
    "pv_slider": SettingSpec("pv", float, B["pv"], C.P_MIN, C.P_MAX),
    "ps_slider": SettingSpec("ps", float, B["ps"], C.P_MIN, C.P_MAX),
    "bonus_slider": SettingSpec("bonus", int, B["bonus"], C.BONUS_MIN, C.BONUS_MAX),
    "gb_slider": SettingSpec("gb", float, B["gb"], C.BET_GAMMA_MIN, C.BET_GAMMA_MAX),
    "dv_slider": SettingSpec("dv", float, B["dv"], C.DELTA_MIN, C.DELTA_MAX),
    "ds_slider": SettingSpec("ds", float, B["ds"], C.DELTA_MIN, C.DELTA_MAX),
    "k_slider": SettingSpec("k", int, B["k"], C.MESO_K_MIN, C.MESO_K_MAX),
    "r_slider": SettingSpec("runden", int, B["r"], C.MESO_R_MIN, C.MESO_R_MAX),
    "est_select": SettingSpec("schaetzer", str, B["est"], choices=("Posterior-Mittel", "Max-Rand")),
    "seed_input": SettingSpec("seed", int, B["seed"], 0, C.SEED_MAX),
}
PRESET_KEYS = {"v1": "v1_slider", "v2": "v2_slider", "v3": "v3_slider", "v4": "v4_slider", "s1": "s1_slider", "s2": "s2_slider", "s3": "s3_slider", "s4": "s4_slider",
               "price": "price_slider", "bundle": "bundle_slider", "rs": "rs_slider", "rv": "rv_slider", "term": "term_slider", "gs": "gs_slider", "gv": "gv_slider", "q": "q_slider",
               "pv": "pv_slider", "ps": "ps_slider", "bonus": "bonus_slider", "gb": "gb_slider", "dv": "dv_slider", "ds": "ds_slider", "k": "k_slider", "r": "r_slider",
               "est": "est_select", "seed": "seed_input"}


def init_session_state_defaults():
    for state_key, spec in SETTING_SPECS.items():
        if state_key not in st.session_state:
            st.session_state[state_key] = spec.default


def bounds(state_key):
    spec = SETTING_SPECS[state_key]
    return spec.lo, spec.hi


def load_permalink_settings():
    """Einmal je Sitzung: Werte aus der Adresszeile übernehmen, auf die Reglergrenzen begrenzt bzw. auf erlaubte Werte geprüft."""
    if "permalink_loaded" in st.session_state:
        return
    qp = st.query_params
    for state_key, spec in SETTING_SPECS.items():
        if spec.url_param in qp:
            try:
                value = spec.caster(qp[spec.url_param])
            except (ValueError, TypeError):
                continue
            if spec.choices is not None:
                if value not in spec.choices:
                    continue
            else:
                if value != value:      # NaN
                    continue
                if spec.lo is not None:
                    value = max(spec.lo, value)
                if spec.hi is not None:
                    value = min(spec.hi, value)
            st.session_state[state_key] = value
    st.session_state["permalink_loaded"] = True


def sync_query_params(values):
    """`values`: {state_key: aktueller Wert}; die Adresszeile spiegelt die Konfiguration."""
    try:
        for state_key, value in values.items():
            st.query_params[SETTING_SPECS[state_key].url_param] = str(value)
    except Exception:
        pass


def apply_preset(name):
    for key, state_key in PRESET_KEYS.items():
        if key in C.PRESETS[name]:
            st.session_state[state_key] = C.PRESETS[name][key]


def settings_from_state() -> Settings:
    """Die Einstellungen aus dem Session State (vor dem Zeichnen der Regler gesetzt durch Voreinstellung, Permalink oder Standard)."""
    g = st.session_state.get
    d = {k: g(k, SETTING_SPECS[k].default) for k in SETTING_SPECS}
    return Settings(
        v=tuple(int(d[f"v{i}_slider"]) for i in range(1, 5)), s=tuple(int(d[f"s{i}_slider"]) for i in range(1, 5)), price=int(d["price_slider"]), bundle=int(d["bundle_slider"]),
        rs=float(d["rs_slider"]), rv=float(d["rv_slider"]), term=int(d["term_slider"]), gs=float(d["gs_slider"]), gv=float(d["gv_slider"]), q=int(d["q_slider"]),
        pv=float(d["pv_slider"]), ps=float(d["ps_slider"]), bonus=int(d["bonus_slider"]), gb=float(d["gb_slider"]), dv=float(d["dv_slider"]), ds=float(d["ds_slider"]),
        k=int(d["k_slider"]), r=int(d["r_slider"]), est=str(d["est_select"]), seed=int(d["seed_input"]))


def aktives_preset():
    """Name des Presets, dessen Werte GENAU den aktuellen Einstellungen entsprechen, sonst None.

    Zustandslos: verglichen wird jeder Regler aus SETTING_SPECS (ein Preset ohne Eintrag für einen Regler meint dessen
    Standardwert) mit dem Session State. Ein später ergänzter Regler braucht nur seinen Eintrag in SETTING_SPECS,
    dann hebt auch seine Änderung die Markierung auf (tests/test_layout.py prüft das für jeden Regler)."""
    preset_key_of = {state_key: key for key, state_key in PRESET_KEYS.items()}
    for name, preset in C.PRESETS.items():
        if all(
            st.session_state.get(state_key, spec.default) == preset.get(preset_key_of.get(state_key), spec.default)
            for state_key, spec in SETTING_SPECS.items()
        ):
            return name
    return None


def sidebar_presets():
    """Schnellstart oben in der Seitenleiste; das aktive Preset ist hervorgehoben (`type="primary"`)."""
    if not C.PRESETS:
        return
    st.header("🎯 Schnellstart")
    st.caption("Ein Beispielszenario laden:")
    aktiv = aktives_preset()
    for name in C.PRESETS:
        st.button(
            name, width="stretch", on_click=apply_preset, args=(name,), help=C.PRESET_HELP.get(name, ""), key=f"preset_{name}",
            type="primary" if aktiv == name else "secondary",
        )


def randomize_seed():
    st.session_state["seed_input"] = random.randint(0, C.SEED_MAX)
