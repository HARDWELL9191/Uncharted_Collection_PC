#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Writes the option rows of packaging/windows/recomplauncher.json from launcher/uc_launcher.py, so
RecompLauncher's game page always has the same Advanced options and Controls as the launcher window.

The rows it makes have ids starting with 'opt_' (Options > Advanced, passed as --on/--off) and 'ctl_'
(the Controls window, in input.ini and launcher.json); every other part of the file is kept
as written. package_uc.sh runs it before zipping. Usage: make_recomplauncher_json.py [json path]
"""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / 'launcher'))
import uc_launcher as L  # noqa: E402

NAMES = {'uc1': 'UC1', 'uc2': 'UC2', 'uc3': 'UC3'}


def games_using(name):
    """The games that start with this option (or can: experimental ones)."""
    games = [key for key, _t, _e, _s, extra in L.GAMES if name in L.COMMON or name in extra]
    for table in (L.EXPERIMENTAL, L.DEBUG):
        if name in table:
            games = list(table[name][0])
    return games


def option_rows():
    rows = []
    for name, (_pt, en) in L.TOGGLE_HELP.items():
        if name in L.FIXED:
            continue
        games = games_using(name)
        if not games:
            continue
        flag = L.public_name(name)
        on = {'label': 'On', 'args': ['--on', flag]}
        off = {'label': 'Off', 'args': ['--off', flag]}
        experimental = name in L.EXPERIMENTAL
        rows.append({
            'id': 'opt_' + name[len('GOW3_'):].lower(),
            'label': en,
            'in': 'args',
            'help': (f"Advanced ({'experimental, off by default' if experimental else 'on by default'}). "
                     f"Used by {', '.join(NAMES[g] for g in games)}. Option {flag}."),
            'choices': [off, on] if experimental else [on, off],
        })
    return rows


def control_rows():
    """The Controls window's values, read and written where the game and the launcher keep them, so the
    page, the port menu (Insert or F1 > Controls) and the launcher window always show the same thing:
    input.ini (the game reads it at start and the port menu writes it; the launcher adopts what changed)
    and, for the icons, launcher.json."""
    d = L.CONTROL_DEFAULTS
    menu = ' Also in the game\'s menu (Insert or F1 > Controls).'

    def onoff(row_id, label, key, help_text):
        return {'id': row_id, 'label': label, 'in': 'input', 'help': help_text + menu,
                'choices': [{'label': 'On', 'set': {key: '1'}}, {'label': 'Off', 'set': {key: '0'}}],
                'defaults': {key: '1' if d.get(key, key == 'vibration') else '0'}}

    def scale(row_id, label, key, help_text, top):
        # every 0.1 up to the port menu's slider top (5 and 3): RecompLauncher has no slider yet
        values = [n / 10 for n in range(1, int(top * 10) + 1)]
        return {'id': row_id, 'label': label, 'in': 'input', 'help': help_text + menu,
                'choices': [{'label': f'{v:g}', 'set': {key: f'{v:.2f}'}} for v in values],
                'defaults': {key: f"{float(d.get(key) or 1.0):.2f}"}}

    return [
        {'id': 'ctl_icons', 'label': 'Button icons', 'in': 'launcher',
         'help': 'The buttons the games show: PlayStation (the original), Xbox, or your keyboard keys.',
         'choices': [{'label': 'PlayStation', 'set': {'controls/icons': '"ps"'}},
                     {'label': 'Xbox', 'set': {'controls/icons': '"xbox"'}},
                     {'label': 'Keyboard keys', 'set': {'controls/icons': '"keys"'}}],
         'defaults': {'controls/icons': '"ps"'}},
        onoff('ctl_mouse_look', 'Mouse look', 'mouse_look', 'The mouse turns the camera.'),
        scale('ctl_mouse_sensitivity', 'Mouse sensitivity', 'mouse_sensitivity', 'How fast the mouse turns the camera.', 5.0),
        scale('ctl_aim_sensitivity', 'Aim sensitivity', 'mouse_aim_sensitivity',
              'Multiplies the mouse sensitivity while aiming; 1 is the same as normal.', 3.0),
        onoff('ctl_invert_y', 'Invert mouse Y', 'mouse_invert_y', 'Mouse up looks down.'),
        onoff('ctl_pad_invert_y', 'Invert controller Y', 'pad_invert_y', 'Right stick up looks down.'),
        onoff('ctl_vibration', 'Vibration', 'vibration', 'Controller rumble.'),
    ]


def main():
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / 'packaging' / 'windows' / 'recomplauncher.json'
    data = json.loads(path.read_text(encoding='utf-8'))
    kept = [s for s in data.get('settings', []) if not s['id'].startswith(('opt_', 'ctl_'))]
    # Advanced options stay in the port's own launcher (Matheus, 2026-11-04): option_rows() is kept for when
    # RecompLauncher can hide advanced rows; --play --on/--off still work.
    data['settings'] = kept + control_rows()
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8', newline='\n')
    print(f'{path}: {len(kept)} rows kept, {len(data["settings"]) - len(kept)} made')


if __name__ == '__main__':
    main()
